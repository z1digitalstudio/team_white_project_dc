from auth_app.utils.helpers import check_user_authenticated
import graphene  # pyright: ignore[reportMissingImports]

from blog_app.models import Blog
from blog_app.schema.types import BlogType
from blog_app.serializers import BlogSerializer
from blog_app.utils.constants import (
    DEFAULT_BLOG_DESCRIPTION,
    ERROR_BLOG_NOT_FOUND,
    ERROR_BLOG_USER_HAS_BLOG,
    SUCCESS_BLOG_CREATED,
)


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
