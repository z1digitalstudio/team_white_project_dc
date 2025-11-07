from rest_framework import permissions

from blog_app.models import Blog, Post, Tag

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


# --- Helpers ---
def is_authenticated(user):
    return user and user.is_authenticated


def is_superuser(user):
    return user.is_superuser


def is_owner(user, obj):
    """
    Verifica si el usuario es propietario del objeto
    """
    if hasattr(obj, "user"):
        return obj.user == user
    if hasattr(obj, "blog"):
        return obj.blog.user == user
    return False


def is_owner_of_any_post(user, obj):
    """
    Verifica si el usuario es dueño de al menos un post asociado (para Tags).
    """
    if hasattr(obj, "posts"):
        return obj.posts.filter(blog__user=user).exists()
    return False


# --- Permissions ---
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite acceso a:
    - Superusuarios
    - Propietarios del objeto (obj.user)
    """

    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        return is_superuser(user) or is_owner(user, obj)


class IsBlogOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso para recursos relacionados con blogs:
    - Posts: obj.blog.user
    - Tags: al menos un post asociado
    """

    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        if is_superuser(user):
            return True
        if hasattr(obj, "blog"):
            return is_owner(user, obj)
        if hasattr(obj, "posts"):
            return is_owner_of_any_post(user, obj)
        return False


class IsAuthenticatedOrReadOnlyOwner(permissions.BasePermission):
    """
    - Usuarios no autenticados: sin acceso
    - Usuarios autenticados: acceso solo a sus propios recursos
    - Superusuarios: acceso total
    """

    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        if is_superuser(user):
            return True
        return is_owner(user, obj)


def admin_permissions(user):
    """
    Asigna permisos en el admin  para un usuario staff
    """
    # Obtiene el tipo de contenido (ContentType) asociado al modelo Blog
    content_type_blog = ContentType.objects.get_for_model(Blog)

    # Busca los permisos 'ver' y 'editar' del modelo Blog
    permisos_blog = Permission.objects.filter(
        content_type=content_type_blog, codename__in=["view_blog", "change_blog"]
    )

    # Asigna esos permisos al usuario
    user.user_permissions.add(*permisos_blog)

    # Obtiene el tipo de contenido asociado al modelo Post
    content_type_post = ContentType.objects.get_for_model(Post)

    # Busca los permisos 'ver', 'añadir', 'editar' y 'eliminar' del modelo Post
    permisos_post = Permission.objects.filter(
        content_type=content_type_post,
        codename__in=["view_post", "add_post", "change_post", "delete_post"],
    )

    # Asigna esos permisos al usuario
    user.user_permissions.add(*permisos_post)

    # Obtiene el tipo de contenido asociado al modelo Tag
    content_type_tag = ContentType.objects.get_for_model(Tag)

    # Busca los permisos 'ver', 'añadir', 'editar' y 'eliminar' del modelo Tag
    permisos_tag = Permission.objects.filter(
        content_type=content_type_tag,
        codename__in=["view_tag", "add_tag", "change_tag", "delete_tag"],
    )

    # Asigna esos permisos al usuario
    user.user_permissions.add(*permisos_tag)
