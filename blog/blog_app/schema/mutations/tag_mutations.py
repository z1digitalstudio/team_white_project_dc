from auth_app.helpers import check_user_authenticated
import graphene  # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied

from blog_app.models import Post, Tag
from blog_app.schema.types import TagType
from blog_app.utils.constants import ERROR_TAG_NOT_FOUND
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
