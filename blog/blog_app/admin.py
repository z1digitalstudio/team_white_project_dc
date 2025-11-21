from import_export import resources
from import_export.admin import ImportExportModelAdmin
from tinymce.widgets import TinyMCE

from blog_app.utils.helpers import get_user_blog

from .models import Blog, Post, Tag

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


# Define qué campos se pueden exportar o importar
class PostResource(resources.ModelResource):
    class Meta:
        model = Post
        fields = ("id", "title", "content", "created_at", "updated_at", "blog")


# Admin posts
@admin.register(Post)
class PostAdmin(ImportExportModelAdmin):
    # Vincula el recurso de import/export
    resource_class = PostResource

    # Qué columnas mostrar en la lista del admin de posts
    list_display = ("title", "blog", "created_at", "updated_at")

    # Campos por los que se puede buscar
    search_fields = ("title", "content", "blog__title")

    # Usa TinyMCE para el campo de texto "content"
    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 20})},
    }

    # Filtra los posts del usuario (o todos si es superusuario)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset  # Ve todos los posts
        return queryset.filter(blog__user=request.user)  # Ve los posts del usuario

    # Crea automáticamente el blog del usuario antes de mostrar el formulario
    def get_form(self, request, obj=None, **kwargs):
        if (
            not request.user.is_superuser
        ):  # Si no es superusuario, crea el blog del usuario
            get_user_blog(request.user)  # Crea el blog del usuario
        return super().get_form(request, obj, **kwargs)

    # Filtra el desplegable de blog
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "blog" and not request.user.is_superuser
        ):  # Si no es superusuario, filtra los blogs del usuario
            kwargs["queryset"] = Blog.objects.filter(
                user=request.user
            )  # Filtra los blogs del usuario
        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )  # Llama al método original para que se ejecute el resto de la lógica

    # Asigna automáticamente el blog al crear el post
    def save_model(self, request, obj, form, change):  # noqa: PLR6301
        if not obj.pk:  # Nuevo post
            obj.blog = get_user_blog(request.user)  # Asigna el blog del usuario
        obj.save()  # Guarda el post


# Admin blogs
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "title",
        "description",
        "created_at",
        "updated_at",
    )  # Mostrar título y dueño del blog

    # Filtra los blogs del usuario (o todos si es superusuario)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        # Solo los blogs del usuario
        return queryset.filter(user=request.user)

    # Filtra el desplegable de usuarios al crear/editar un blog
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "user" and not request.user.is_superuser
        ):  # Staff solo puede ver su propio blog
            kwargs["queryset"] = User.objects.filter(
                id=request.user.id
            )  # Filtra los usuarios del blog
        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )  # Llama al método original para que se ejecute el resto de la lógica


# Admin tags
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "blog", "created_at", "updated_at")
    search_fields = ("name", "blog__user__username")

    # Filtra los tags del usuario (o todos si es superusuario)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        # Solo tags asociados a posts del usuario
        return queryset.filter(posts__blog__user=request.user).distinct()

    # Filtra el campo blog del formulario según el usuario
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "blog" and not request.user.is_superuser:
            kwargs["queryset"] = Blog.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Filtra posts visibles en el formulario (ManyToMany)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (
            db_field.name == "posts" and not request.user.is_superuser
        ):  # Staff solo puede ver los posts del usuario
            kwargs["queryset"] = Post.objects.filter(
                blog__user=request.user
            )  # Filtra los posts del usuario
        return super().formfield_for_manytomany(
            db_field, request, **kwargs
        )  # Llama al método original para que se ejecute el resto de la lógica
