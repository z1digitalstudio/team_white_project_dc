from rest_framework.exceptions import PermissionDenied

from blog_app.models import Blog, Post, Tag

from .constants import (
    ERROR_GRAPHQL_NOT_AUTHENTICATED,
    ERROR_ONLY_STAFF_CAN_HAVE_ADMIN,
)

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


# --- Helpers de usuario ---
def is_authenticated(user):
    return user and user.is_authenticated


def is_superuser(user):
    return user.is_superuser


def is_owner(user, obj):
    """Verifica si el usuario es propietario del objeto"""
    if hasattr(obj, "user"):
        return obj.user == user
    if hasattr(obj, "blog"):
        return obj.blog.user == user
    return False


def is_owner_of_any_post(user, obj):
    """Verifica si el usuario es dueño de al menos un post asociado (para Tags)"""
    if hasattr(obj, "posts"):
        return obj.posts.filter(blog__user=user).exists()
    return False


# --- Helpers de GraphQL ---
def check_user_authenticated(info):
    user = info.context.user
    if not user or not user.is_authenticated:
        raise PermissionDenied(ERROR_GRAPHQL_NOT_AUTHENTICATED)
    return user


# --- Helpers de creación de usuarios ---
def create_user(validated_data):
    """Crea un usuario y cifra la contraseña."""
    user_model = get_user_model()

    user = user_model.objects.create_user(
        username=validated_data["username"],
        email=validated_data.get("email"),
        password=validated_data["password"],
    )
    user.is_staff = True  # Dar acceso al admin
    user.save()
    return user


def admin_permissions(user):
    """
    Asigna permisos específicos del admin a un usuario staff.
    """
    if not user.is_staff:
        raise ValueError(ERROR_ONLY_STAFF_CAN_HAVE_ADMIN)

    # Define los modelos y los codenames de permisos a asignar
    permisos_por_modelo = {
        Blog: ["view_blog", "change_blog", "add_blog", "delete_blog"],
        Post: ["view_post", "add_post", "change_post", "delete_post"],
        Tag: ["view_tag", "add_tag", "change_tag", "delete_tag"],
    }

    # Asigna los permisos de cada modelo
    for modelo, codenames in permisos_por_modelo.items():
        content_type = ContentType.objects.get_for_model(modelo)
        permisos = Permission.objects.filter(
            content_type=content_type, codename__in=codenames
        )
        user.user_permissions.add(*permisos)
