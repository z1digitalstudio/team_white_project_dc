from rest_framework import permissions

from .helpers import is_authenticated, is_owner, is_owner_of_any_post, is_superuser


# Clase para verificar si el usuario es propietario del objeto o admin
class IsOwnerOrAdmin(permissions.BasePermission):
    """Permiso para superusuarios o propietarios del objeto"""

    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        return is_superuser(user) or is_owner(user, obj)


# Clase para verificar si el usuario es propietario del blog o admin
class IsBlogOwnerOrAdmin(permissions.BasePermission):
    """Permiso para recursos relacionados con blogs"""

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


# Clase para verificar si el usuario está autenticado o es propietario del objeto
class IsAuthenticatedOrReadOnlyOwner(permissions.BasePermission):
    """Permiso que restringe acceso a recursos propios"""

    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        if is_superuser(user):
            return True
        return is_owner(user, obj)
