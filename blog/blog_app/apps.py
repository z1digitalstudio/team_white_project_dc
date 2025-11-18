# import os

from django.apps import AppConfig


# from django.contrib.auth import get_user_model
# from django.db import OperationalError, ProgrammingError, connections


class BlogAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog_app"


"""
    def ready(self):  # noqa: PLR6301
        try:
            connections["default"].ensure_connection()
            print("DB lista, se puede crear el superuser")
        except (OperationalError, ProgrammingError):
            print("Error al crear el superuser")
            return  # DB no lista, sale sin error

        user_model = get_user_model()
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

        if not user_model.objects.filter(username=username).exists():
            user_model.objects.create_superuser(username, email, password)
            print(f"Superuser '{username}' creado automáticamente")
"""
