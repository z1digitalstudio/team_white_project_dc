from auth_app.helpers import check_user_authenticated  # Para graphQL
import graphene  # pyright: ignore[reportMissingImports]
from graphene_django import DjangoObjectType  # pyright: ignore[reportMissingImports]
from rest_framework_simplejwt.tokens import (  # pyright: ignore[reportMissingImports]
    RefreshToken,  # pyright: ignore[reportMissingImports]
)

from blog_app.constants import (
    DEFAULT_BLOG_DESCRIPTION,
    ERROR_BLOG_USER_HAS_BLOG,
    ERROR_TAG_PERMISSION_DENIED,
    ERROR_TAG_POSTS_NOT_FOUND,
)
from blog_app.helpers import get_user_blog, validate_user_owns_posts
from blog_app.models import Blog, Post, Tag
from blog_app.serializers import (
    BlogSerializer,
    PostSerializer,
    RegisterSerializer,
    TagSerializer,
)


# === Tipos (equivalentes a serializers, pero para GraphQL) ===
class BlogType(DjangoObjectType):
    class Meta:
        model = Blog
        fields = "__all__"


class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "title", "content", "created_at", "updated_at", "blog", "tags")


class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = ("id", "name", "posts")


class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()


# === Consultas (queries) ===
class Query(graphene.ObjectType):
    all_blogs = graphene.List(BlogType)
    all_posts = graphene.List(PostType)
    all_tags = graphene.List(TagType)

    def resolve_all_blogs(self, info):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if user.is_superuser:
            return Blog.objects.all()
        return Blog.objects.filter(user=user)

    def resolve_all_posts(self, info):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if user.is_superuser:
            return Post.objects.all()
        return Post.objects.filter(blog__user=user)

    def resolve_all_tags(self, info):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if user.is_superuser:
            return Tag.objects.all()
        return Tag.objects.filter(posts__blog__user=user).distinct()


# === Mutations ===
class CreateBlog(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    blog = graphene.Field(BlogType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, description=None):  # noqa: PLR6301
        user = check_user_authenticated(info)  # extrae el usuario del token

        # Verificar si ya tiene un blog
        if not user.is_superuser and Blog.objects.filter(user=user).exists():
            return CreateBlog(blog=None, errors=[ERROR_BLOG_USER_HAS_BLOG])

        # Preparar datos
        data = {
            "title": title,
            "description": description or DEFAULT_BLOG_DESCRIPTION,
            "user": user.id,  # aunque sea read_only, algunos serializers lo usan
        }

        # Reutilizar serializer DRF
        serializer = BlogSerializer(data=data, context={"request": info.context})
        if serializer.is_valid():
            blog = serializer.save(user=user)
            return CreateBlog(blog=blog, errors=[])

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return CreateBlog(blog=None, errors=errors)


class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        tag_ids = graphene.List(graphene.Int)

    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, content, tag_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        # Obtener o crear blog del usuario
        blog = Blog.objects.filter(user=user).first()
        if not blog:
            blog = get_user_blog(user)  # usa tu helper DRF

        # Datos del post
        data = {"title": title, "content": content}

        # Reutilizar serializer DRF
        serializer = PostSerializer(data=data, context={"request": info.context})
        if serializer.is_valid():
            post = serializer.save(blog=blog)  # pasar la instancia de blog

            # Asociar tags si se pasan IDs
            if tag_ids:
                tags = Tag.objects.filter(id__in=tag_ids)
                post.tags.set(tags)

            return CreatePost(post=post, errors=[])

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return CreatePost(post=None, errors=errors)


class CreateTag(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        post_ids = graphene.List(
            graphene.Int, required=True
        )  # IDs de los posts a asociar

    tag = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, name, post_ids):  # noqa: PLR6301
        user = check_user_authenticated(info)  # usuario autenticado

        # Solo staff o superusuario puede crear tags
        if not user.is_staff and not user.is_superuser:
            return CreateTag(tag=None, errors=[ERROR_TAG_PERMISSION_DENIED])

        # Obtener los posts a asociar
        posts_qs = Post.objects.filter(id__in=post_ids)
        if not posts_qs.exists():
            return CreateTag(tag=None, errors=[ERROR_TAG_POSTS_NOT_FOUND])

        # Validar que el usuario es propietario de los posts
        validate_user_owns_posts(user, posts_qs)

        # Pasar solo los IDs al serializer, que es lo que espera
        data = {"name": name, "posts": [p.id for p in posts_qs]}
        serializer = TagSerializer(data=data, context={"request": info.context})
        if serializer.is_valid():
            tag = serializer.save()
            return CreateTag(tag=tag, errors=[])

        # Si hay errores del serializer, los devolvemos
        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return CreateTag(tag=None, errors=errors)


class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=False)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    token = graphene.String()  # JWT
    refresh_token = graphene.String()  # JWT refresh
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, password, email=None):  # noqa: PLR6301
        data = {"username": username, "email": email, "password": password}

        serializer = RegisterSerializer(data=data, context={"request": info.context})
        if serializer.is_valid():
            user = serializer.save()

            # Generar JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return RegisterUser(
                user=user, token=access_token, refresh_token=refresh_token, errors=[]
            )

        # Si hay errores de validación
        errors = [
            f"{field}: {', '.join(msgs)}" for field, msgs in serializer.errors.items()
        ]
        return RegisterUser(user=None, token=None, refresh_token=None, errors=errors)


# === Schema principal ===
class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    create_post = CreatePost.Field()
    create_tag = CreateTag.Field()
    register_user = RegisterUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
