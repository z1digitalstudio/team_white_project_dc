from auth_app.utils.helpers import check_user_authenticated  # Para graphQL
import graphene  # pyright: ignore[reportMissingImports]
from graphene_django import DjangoObjectType  # pyright: ignore[reportMissingImports]
import graphql_jwt  # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import (  # pyright: ignore[reportMissingImports]
    RefreshToken,  # pyright: ignore[reportMissingImports]
)

from blog_app.models import Blog, Post, Tag
from blog_app.serializers import (
    BlogSerializer,
    PostSerializer,
    RegisterSerializer,
)
from blog_app.utils.constants import (
    DEFAULT_BLOG_DESCRIPTION,
    ERROR_BLOG_NOT_FOUND,
    ERROR_BLOG_USER_HAS_BLOG,
    ERROR_POST_NOT_FOUND,
    ERROR_TAG_NOT_FOUND,
    SUCCESS_BLOG_CREATED,
)
from blog_app.utils.helpers import (
    get_or_create_tag,
    get_user_blog,
    validate_posts_for_user,
)


# === Tipos (equivalentes a serializers, pero para GraphQL) ===
class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()


class BlogType(DjangoObjectType):
    user = graphene.Field(UserType)

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


class CreateBlog(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    blog = graphene.Field(BlogType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, description=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        if not user.is_superuser:
            if Blog.objects.filter(user=user).exists():
                return CreateBlog(blog=None, errors=[ERROR_BLOG_USER_HAS_BLOG])

        data = {
            "title": title,
            "description": description or DEFAULT_BLOG_DESCRIPTION,
            "user": user.id,
        }

        serializer = BlogSerializer(data=data, context={"request": info.context})
        if serializer.is_valid():
            blog = serializer.save(user=user)
            return CreateBlog(blog=blog, errors=[])

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return CreateBlog(
            blog=None, errors=errors, success_message=SUCCESS_BLOG_CREATED
        )


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


class UpdateBlog(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String(required=False)
        description = graphene.String(required=False)

    blog = graphene.Field(BlogType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, title=None, description=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            blog = Blog.objects.get(id=id)
        except Blog.DoesNotExist:
            return UpdateBlog(blog=None, errors=[ERROR_BLOG_NOT_FOUND])

        # Validación de propietario
        if not user.is_superuser and blog.user != user:
            return UpdateBlog(
                blog=None, errors=["No tienes permiso para editar este blog"]
            )

        data = {
            "title": title if title is not None else blog.title,
            "description": description if description is not None else blog.description,
            "user": blog.user.id,
        }

        serializer = BlogSerializer(blog, data=data, partial=True)

        if serializer.is_valid():
            blog = serializer.save()
            return UpdateBlog(blog=blog, errors=[])

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return UpdateBlog(blog=None, errors=errors)


class UpdatePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String(required=False)
        content = graphene.String(required=False)
        tag_ids = graphene.List(graphene.Int, required=False)

    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, title=None, content=None, tag_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return UpdatePost(post=None, errors=[ERROR_POST_NOT_FOUND])

        # Validación de permisos
        validate_posts_for_user(user, Post.objects.filter(id=id))

        data = {
            "title": title if title is not None else post.title,
            "content": content if content is not None else post.content,
        }

        serializer = PostSerializer(post, data=data, partial=True)

        if serializer.is_valid():
            post = serializer.save()

            if tag_ids is not None:
                tags = Tag.objects.filter(id__in=tag_ids)
                post.tags.set(tags)

            return UpdatePost(post=post, errors=[])

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return UpdatePost(post=None, errors=errors)


class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return DeletePost(ok=False, errors=[ERROR_POST_NOT_FOUND])

        # Validar permisos
        validate_posts_for_user(user, Post.objects.filter(id=id))

        post.delete()
        return DeletePost(ok=True, errors=[])


class UpdateTag(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=False)
        post_ids = graphene.List(graphene.Int, required=False)

    tag = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, name=None, post_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            tag = Tag.objects.get(id=id)
        except Tag.DoesNotExist:
            return UpdateTag(tag=None, errors=[ERROR_TAG_NOT_FOUND])

        # Validar permisos
        validate_posts_for_user(user, tag.posts.all())

        if name:
            tag.name = name
            tag.save()

        if post_ids is not None:
            posts = Post.objects.filter(id__in=post_ids)
            validate_posts_for_user(user, posts)
            tag.posts.set(posts)

        return UpdateTag(tag=tag, errors=[])


class DeleteTag(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            tag = Tag.objects.get(id=id)
        except Tag.DoesNotExist:
            return DeleteTag(ok=False, errors=["Tag no encontrado"])

        validate_posts_for_user(user, tag.posts.all())

        tag.delete()
        return DeleteTag(ok=True, errors=[])


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
    update_blog = UpdateBlog.Field()

    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()

    create_tag = CreateTag.Field()
    update_tag = UpdateTag.Field()
    delete_tag = DeleteTag.Field()
    register_user = RegisterUser.Field()

    # Mutaciones JWT
    login_token_auth = graphql_jwt.ObtainJSONWebToken.Field()  # obtener token - login
    refresh_token = (
        graphql_jwt.Refresh.Field()
    )  # refrescar token para que el usuario siga logueado


schema = graphene.Schema(query=Query, mutation=Mutation)
