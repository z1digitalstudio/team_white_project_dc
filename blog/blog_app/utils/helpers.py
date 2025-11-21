from rest_framework.exceptions import PermissionDenied

from blog_app.models import Blog, Tag

from .constants import (
    ERROR_NEED_CREATE_BLOG,
    ERROR_TAG_POSTS_NOT_FOUND,
)


# --- Funciones auxiliares del blog ---
def get_user_blog(user):
    try:
        return user.blog
    except Blog.DoesNotExist:
        raise PermissionDenied(ERROR_NEED_CREATE_BLOG)  # noqa: B904


def validate_posts_for_user(user, posts):
    if not posts:
        return
    if not user.is_superuser:
        for post in posts:
            if post.blog.user != user:
                raise PermissionDenied(ERROR_TAG_POSTS_NOT_FOUND)


def get_or_create_tag(blog, name):

    name = name.strip().lower()
    tag, _ = Tag.objects.get_or_create(blog=blog, name=name)
    return tag
