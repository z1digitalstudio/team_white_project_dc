from auth_app.helpers import check_user_authenticated  # Para graphQL
import graphene  # pyright: ignore[reportMissingImports]
from graphene_django import DjangoObjectType  # pyright: ignore[reportMissingImports]
import graphql_jwt  # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import (  # pyright: ignore[reportMissingImports]
    RefreshToken,  # pyright: ignore[reportMissingImports]
)

from blog_app.constants import (
    DEFAULT_BLOG_DESCRIPTION,
    ERROR_BLOG_USER_HAS_BLOG,
)
from blog_app.helpers import get_or_create_tag, get_user_blog, validate_posts_for_user
from blog_app.models import Blog, Post, Tag
from blog_app.serializers import (
    BlogSerializer,
    PostSerializer,
    RegisterSerializer,
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
        user = check_user_authenticated(info)

        # Verificar si el usuario ya tiene blog (no superuser)
        if not user.is_superuser:
            if Blog.objects.filter(user=user).exists():
                return CreateBlog(blog=None, errors=[ERROR_BLOG_USER_HAS_BLOG])

        data = {
            "title": title,
            "description": description or DEFAULT_BLOG_DESCRIPTION,
            "user": user.id,  # necesario para DRF serializer
        }

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
        tag_ids = graphene.List(graphene.Int, required=False)

    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, content, tag_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        # Obtener blog y validar
        try:
            blog = get_user_blog(user)
        except PermissionDenied as e:
            return CreatePost(post=None, errors=[str(e)])

        # Serializador DRF
        serializer = PostSerializer(
            data={"title": title, "content": content}, context={"request": info.context}
        )

        if serializer.is_valid():
            post = serializer.save(blog=blog)

            # Asociar tags si se pasan
            if tag_ids:
                posts_tags_qs = Post.objects.filter(id__in=tag_ids)
                validate_posts_for_user(user, posts_tags_qs)
                post.tags.set(posts_tags_qs)

            return CreatePost(post=post, errors=[])

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return CreatePost(post=None, errors=errors)


class CreateTag(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        post_ids = graphene.List(graphene.Int, required=True)

    tag = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, name, post_ids):  # noqa: PLR6301
        user = check_user_authenticated(info)

        # Validar blog del usuario
        try:
            blog = get_user_blog(user)
        except PermissionDenied as e:
            return CreateTag(tag=None, errors=[str(e)])

        # Obtener posts y validar propiedad
        posts_qs = Post.objects.filter(id__in=post_ids)
        validate_posts_for_user(user, posts_qs)

        # Crear tag usando helper
        tag = get_or_create_tag(blog, name)
        tag.posts.set(posts_qs)

        return CreateTag(tag=tag, errors=[])


class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=False)
        password = graphene.String(required=True)

    # --- Outputs ---
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

    # Mutaciones JWT
    login_token_auth = graphql_jwt.ObtainJSONWebToken.Field()  # obtener token - login
    refresh_token = (
        graphql_jwt.Refresh.Field()
    )  # refrescar token para que el usuario siga logueado
    # verify_token = graphql_jwt.Verify.Field()  # verificar token - para debugging


schema = graphene.Schema(query=Query, mutation=Mutation)
