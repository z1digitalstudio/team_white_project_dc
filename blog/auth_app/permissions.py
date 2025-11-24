from rest_framework import permissions

from auth_app.utils.helpers import (
    is_authenticated,
    is_owner,
    is_owner_of_any_post,
    is_superuser,
)


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        return is_superuser(user) or is_owner(user, obj)


class IsBlogOwnerOrAdmin(permissions.BasePermission):
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
    def has_permission(self, request, view):  # noqa: PLR6301
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):  # noqa: PLR6301
        user = request.user
        if is_superuser(user):
            return True
        return is_owner(user, obj)
