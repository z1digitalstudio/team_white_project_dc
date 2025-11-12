from auth_app.constants import ERROR_USER_NOT_AUTHENTICATED
from auth_app.helpers import admin_permissions, create_user
from rest_framework import serializers

from blog_app.helpers import validate_user_owns_posts
from blog_app.models import Blog, Post, Tag

from django.contrib.auth.models import User


# --- Serializers ---
# Serializador para Tag
class TagSerializer(serializers.ModelSerializer):
    posts = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Post.objects.all(), required=False
    )
    blog = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "posts", "blog"]

    def validate_posts(
        self, posts
    ):  # Validar que los posts pertenecen al usuario autenticado.

        user = self.context["request"].user
        if not user.is_authenticated:
            raise serializers.ValidationError(ERROR_USER_NOT_AUTHENTICATED)

        validate_user_owns_posts(user, posts)
        return posts


# Serializador para Post
class PostSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)  # Mostrar tags dentro del post
    blog = serializers.StringRelatedField(read_only=True)  # Mostrar nombre del blog

    class Meta:
        model = Post
        fields = ["id", "title", "content", "created_at", "updated_at", "blog", "tags"]


# Serializador para Blog
class BlogSerializer(serializers.ModelSerializer):
    posts = PostSerializer(many=True, read_only=True)  # Mostrar posts del blog

    class Meta:
        model = Blog
        fields = ["id", "title", "description", "user", "posts"]
        read_only_fields = [
            "user"
        ]  # esto hace que no sea obligatorio enviarlo al crear un blog


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):  # noqa: PLR6301
        user = create_user(validated_data)
        # Asignar permisos mínimos después de crear usuario
        admin_permissions(user)
        return user
