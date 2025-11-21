from auth_app.helpers import check_user_authenticated
import graphene  # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied

from blog_app.models import Post, Tag
from blog_app.schema.types import PostType
from blog_app.serializers import PostSerializer
from blog_app.utils.constants import ERROR_POST_NOT_FOUND
from blog_app.utils.helpers import get_user_blog, validate_posts_for_user


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
