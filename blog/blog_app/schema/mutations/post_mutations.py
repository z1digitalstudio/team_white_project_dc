from auth_app.utils.helpers import check_user_authenticated
import graphene  # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied

from blog_app.models import Post
from blog_app.schema.types import PostType
from blog_app.serializers import PostSerializer
from blog_app.utils.constants import (
    ERROR_POST_NOT_FOUND,
    SUCCESS_POST_CREATED,
    SUCCESS_POST_DELETED,
    SUCCESS_POST_UPDATED,
)
from blog_app.utils.helpers import get_user_blog, validate_posts_for_user


class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)

    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, title, content):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            blog = get_user_blog(user)
        except PermissionDenied as e:
            return CreatePost(post=None, errors=[str(e)], message=None)

        serializer = PostSerializer(
            data={"title": title, "content": content},
            context={"request": info.context},
        )

        if serializer.is_valid():
            post = serializer.save(blog=blog)
            return CreatePost(post=post, errors=[], message=SUCCESS_POST_CREATED)

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return CreatePost(post=None, errors=errors, message=None)


class UpdatePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String(required=False)
        content = graphene.String(required=False)

    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, id, title=None, content=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return UpdatePost(post=None, errors=[ERROR_POST_NOT_FOUND], message=None)

        # Validación de permisos
        post_ids = [id]
        posts_qs = Post.objects.filter(id__in=post_ids)

        # Validación de permisos
        validate_posts_for_user(user, post_ids, posts_qs)

        data = {
            "title": title if title is not None else post.title,
            "content": content if content is not None else post.content,
        }

        serializer = PostSerializer(post, data=data, partial=True)

        if serializer.is_valid():
            post = serializer.save()
            return UpdatePost(post=post, errors=[], message=SUCCESS_POST_UPDATED)

        errors = [f"{f}: {', '.join(msgs)}" for f, msgs in serializer.errors.items()]
        return UpdatePost(post=None, errors=errors, message=None)


class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, id):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return DeletePost(errors=[ERROR_POST_NOT_FOUND], message=None)

        post_ids = [id]
        posts_qs = Post.objects.filter(id=id)
        validate_posts_for_user(user, post_ids, posts_qs)

        post.delete()
        return DeletePost(errors=[], message=SUCCESS_POST_DELETED)
