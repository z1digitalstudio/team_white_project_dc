from import_export import resources
from import_export.admin import ImportExportModelAdmin
from rest_framework.exceptions import PermissionDenied
from tinymce.widgets import TinyMCE

from blog_app.utils.helpers import get_user_blog

from .models import Blog, Post, Tag

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


# Define fields that can be exported or imported
class PostResource(resources.ModelResource):
    class Meta:
        model = Post
        fields = ("id", "title", "content", "created_at", "updated_at", "blog")


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "title",
        "description",
        "created_at",
        "updated_at",
    )

    # Filter the blogs of the user (or all if superuser)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(user=request.user)

    # Restrict the 'user' field in the form
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "user" and not request.user.is_superuser
        ):  # Staff only can see his own blog
            kwargs["queryset"] = User.objects.filter(
                id=request.user.id
            )  # Filter the users of the blog
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Post)
class PostAdmin(ImportExportModelAdmin):
    # Link the import/export resource
    resource_class = PostResource

    list_display = ("title", "blog", "created_at", "updated_at")

    search_fields = ("title", "content", "blog__title")

    # Use TinyMCE for the "content" text field
    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 20})},
    }

    # Filter the posts of the user (or all if superuser)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(blog__user=request.user)

    # Allow creation of posts only if the user is superuser or has a blog
    def has_add_permission(self, request):  # noqa: PLR6301
        if request.user.is_superuser:
            return True

        try:
            get_user_blog(request.user)  # Validate that the user has a blog
            return True
        except PermissionDenied:
            return False  # If the user does not have a blog, deny creation of posts

    # Restrict the 'blog' field in the form
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "blog" and not request.user.is_superuser
        ):  # If not superuser, filter the blogs of the user
            kwargs["queryset"] = Blog.objects.filter(
                user=request.user
            )  # Filter the blogs of the user

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Validate the blog of the user before saving the post
    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.blog = get_user_blog(request.user)

        super().save_model(request, obj, form, change)


# Admin tags
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "blog", "created_at", "updated_at")
    search_fields = ("name", "blog__user__username")

    # Filter the tags of the user (or all if superuser)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        # Solo tags asociados a posts del usuario
        return queryset.filter(posts__blog__user=request.user).distinct()

    # Allow creation of tags only if the user is superuser or has a blog
    def has_add_permission(self, request):  # noqa: PLR6301
        if request.user.is_superuser:
            return True

        try:
            get_user_blog(request.user)  # Validate that the user has a blog
            return True
        except PermissionDenied:
            return False  # If the user does not have a blog, deny creation of tags

    # Restrict the 'blog' field in the form
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "blog" and not request.user.is_superuser:
            kwargs["queryset"] = Blog.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Filter the posts visible in the form (ManyToMany)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "posts" and not request.user.is_superuser:
            kwargs["queryset"] = Post.objects.filter(
                blog__user=request.user
            )  # Filter the posts of the user

        return super().formfield_for_manytomany(db_field, request, **kwargs)
