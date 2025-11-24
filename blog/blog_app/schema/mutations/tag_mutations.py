from auth_app.utils.helpers import check_user_authenticated
import graphene  # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied

from blog_app.models import Post, Tag
from blog_app.schema.types import TagType
from blog_app.utils.constants import (
    ERROR_TAG_NOT_FOUND,
    SUCCESS_TAG_CREATED,
    SUCCESS_TAG_DELETED,
    SUCCESS_TAG_UPDATED,
)
from blog_app.utils.helpers import (
    get_or_create_tag,
    get_user_blog,
    validate_posts_for_user,
)


class CreateTag(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        post_ids = graphene.List(graphene.Int, required=True)

    tag = graphene.Field(TagType)
    errors = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, name, post_ids):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            blog = get_user_blog(user)
        except PermissionDenied as e:
            return CreateTag(tag=None, errors=[str(e)], message=None)

        posts_qs = Post.objects.filter(id__in=post_ids)

        try:
            validate_posts_for_user(user, post_ids, posts_qs)
        except (ValueError, PermissionDenied) as e:
            return CreateTag(tag=None, errors=[str(e)], message=None)

        tag = get_or_create_tag(blog, name)
        tag.posts.set(posts_qs)

        return CreateTag(tag=tag, errors=[], message=SUCCESS_TAG_CREATED)


class UpdateTag(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=False)
        post_ids = graphene.List(graphene.Int, required=False)

    tag = graphene.Field(TagType)
    errors = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, id, name=None, post_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            tag = Tag.objects.get(id=id)
        except Tag.DoesNotExist:
            return UpdateTag(tag=None, errors=[ERROR_TAG_NOT_FOUND], message=None)

        if not user.is_superuser and tag.blog.user != user:
            return UpdateTag(tag=None, errors=[ERROR_TAG_NOT_FOUND], message=None)

        if name:
            tag.name = name
            tag.save()

        if post_ids is not None:
            posts_qs = Post.objects.filter(id__in=post_ids)

            try:
                validate_posts_for_user(user, post_ids, posts_qs)
            except (ValueError, PermissionDenied) as e:
                return UpdateTag(tag=None, errors=[str(e)], message=None)

            tag.posts.set(posts_qs)

        return UpdateTag(tag=tag, errors=[], message=SUCCESS_TAG_UPDATED)


class DeleteTag(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        post_ids = graphene.List(graphene.Int, required=False)

    errors = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, id, post_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        try:
            tag = Tag.objects.get(id=id)
        except Tag.DoesNotExist:
            return DeleteTag(errors=[ERROR_TAG_NOT_FOUND])

        if not user.is_superuser and tag.blog.user != user:
            return DeleteTag(errors=[ERROR_TAG_NOT_FOUND])

        if post_ids is not None:
            posts_qs = Post.objects.filter(id__in=post_ids)
            try:
                validate_posts_for_user(user, post_ids, posts_qs)
            except (ValueError, PermissionDenied) as e:
                return DeleteTag(errors=[str(e)])

        tag.delete()
        return DeleteTag(errors=[], message=SUCCESS_TAG_DELETED)
