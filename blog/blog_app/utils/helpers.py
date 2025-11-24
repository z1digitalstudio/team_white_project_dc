from rest_framework.exceptions import PermissionDenied

from blog_app.models import Blog, Tag

from .constants import (
    ERROR_NEED_CREATE_BLOG,
    ERROR_POST_IS_REQUERIED,
    ERROR_TAG_NOT_FOUND_POSTS_IDS,
)


# --- Funciones auxiliares del blog ---
def get_user_blog(user):
    try:
        return user.blog
    except Blog.DoesNotExist:
        raise PermissionDenied(ERROR_NEED_CREATE_BLOG)  # noqa: B904


def validate_posts_for_user(user, post_ids, posts_qs):
    if not post_ids:
        raise ValueError(ERROR_POST_IS_REQUERIED)

    if not user.is_superuser:
        posts_qs = posts_qs.filter(blog__user=user)

    # verify that all ids exist and are owned by the user
    if posts_qs.count() != len(list(post_ids)):
        raise ValueError(ERROR_TAG_NOT_FOUND_POSTS_IDS)


def get_or_create_tag(blog, name):

    name = name.strip().lower()
    tag, _ = Tag.objects.get_or_create(blog=blog, name=name)
    return tag
