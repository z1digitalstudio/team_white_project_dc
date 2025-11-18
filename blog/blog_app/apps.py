# import os

from django.apps import AppConfig


# from django.contrib.auth import get_user_model
# from django.db import OperationalError, ProgrammingError


class BlogAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog_app"
    """
    def ready(self):  # noqa: PLR6301
        try:
            user_model = get_user_model()
            username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
            email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
            password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

            if not user_model.objects.filter(username=username).exists():
                user_model.objects.create_superuser(username, email, password)
                print(f"Superuser '{username}' creado automáticamente")
        except (OperationalError, ProgrammingError):
            print("Error al crear el superuser")
    """
