from auth_app.utils.helpers import admin_permissions, create_user
from rest_framework import serializers

from blog_app.models import Blog, Post, Tag
from blog_app.utils.helpers import get_user_blog

from django.contrib.auth.models import User


class TagSerializer(serializers.ModelSerializer):
    posts = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Post.objects.all(), required=False
    )
    blog = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "posts", "blog"]

    def validate(self, attrs):
        user = self.context["request"].user
        get_user_blog(user)
        return attrs


class PostSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    blog = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "content", "created_at", "updated_at", "blog", "tags"]


class BlogSerializer(serializers.ModelSerializer):
    posts = PostSerializer(many=True, read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Blog
        fields = ["id", "title", "description", "user", "posts"]
        read_only_fields = ["user"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):  # noqa: PLR6301
        user = create_user(validated_data)
        admin_permissions(user)
        return user
