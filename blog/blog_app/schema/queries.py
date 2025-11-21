from auth_app.utils.helpers import check_user_authenticated
import graphene  # pyright: ignore[reportMissingImports]

from blog_app.models import Blog, Post, Tag
from blog_app.schema.types import BlogType, PostType, TagType


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
