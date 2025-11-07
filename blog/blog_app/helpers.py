from auth_app.permissions import is_superuser
from rest_framework.exceptions import PermissionDenied

from blog_app.models import Blog, Tag

from django.contrib.auth.models import User


# --- Funciones auxiliares ---
def get_user_blog(user):  # Obtiene o crea el blog del usuario.
    blog, created = Blog.objects.get_or_create(
        user=user,
        defaults={
            "title": f"Blog de {user.username}",
            "description": "Blog creado automáticamente.",
        },
    )
    return blog


def validate_user_owns_posts(
    user, posts
):  # Verifica que el usuario sea dueño de todos los posts indicados.
    for post in posts:
        if post.blog.user != user and not is_superuser(user):
            raise PermissionDenied(
                f"No puedes asignar tags a posts que no son tuyos ({post.title})."
            )


def get_or_create_tag_by_name(
    name,
):  # Normaliza el nombre y obtiene el primer tag existente o crea uno nuevo.
    name = name.strip().lower()
    tag = Tag.objects.filter(name=name).first()
    if not tag:
        tag = Tag.objects.create(name=name)
    return tag


def create_user(validated_data):  # Crea un usuario y cifra la contraseña.

    user = User.objects.create_user(
        username=validated_data["username"],
        email=validated_data.get("email"),
        password=validated_data["password"],
    )
    # Dar acceso al admin
    user.is_staff = True
    user.save()
    return user
