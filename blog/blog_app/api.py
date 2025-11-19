from auth_app.permissions import IsBlogOwnerOrAdmin, IsOwnerOrAdmin, is_superuser
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated

from blog_app.constants import ERROR_BLOG_ALREADY_EXISTS
from blog_app.helpers import (
    get_or_create_tag,
    get_user_blog,
    validate_posts_for_user,
)

from .models import Blog, Post, Tag
from .serializers import (
    BlogSerializer,
    PostSerializer,
    RegisterSerializer,
    TagSerializer,
)

from django.contrib.auth.models import User


# --- ViewSets ---
# ViewSet para Blog
class BlogViewSet(viewsets.ModelViewSet):
    serializer_class = BlogSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Blog.objects.all()
        return Blog.objects.filter(user=user)

    def create(self, request, *args, **kwargs):  # noqa: PLR6301
        # Bloquea la creación manual de blogs.
        raise PermissionDenied(ERROR_BLOG_ALREADY_EXISTS)


# ViewSet para Post
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsBlogOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Post.objects.all().select_related("blog")
        if is_superuser(user):
            return qs
        return qs.filter(blog__user=user)

    def perform_create(
        self, serializer
    ):  # Asocia el post al blog del usuario, creando el blog si no existía
        blog = get_user_blog(self.request.user)
        serializer.save(blog=blog)


# ViewSet para Tag
"""
class TagViewSet(viewsets.ModelViewSet):

    serializer_class = TagSerializer
    permission_classes = [IsBlogOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if is_superuser(user):  # Si es superusuario, devuelve todos los tags
            return Tag.objects.all()
        return Tag.objects.filter(
            posts__blog__user=user
        ).distinct()  # Solo los tags asociados a posts cuyo blog pertenece al usuario

    def perform_create(self, serializer):
        user = self.request.user
        validated_data = (
            serializer.validated_data
        )  # Obtiene los datos validados del tag
        posts = validated_data.get("posts", [])  # Obtiene los posts del tag
        name = validated_data.get("name")  # Obtiene el nombre del tag

        try:
            blog = user.blog
        except Blog.DoesNotExist:
            raise PermissionDenied("No puedes crear tags si no tienes un blog.")  # noqa: B904

        # blog = get_user_blog(user)  # Obtiene el blog del usuario
        validate_user_owns_posts(user, posts)  # Valida propiedad de posts
        tag = get_or_create_tag_by_name(blog, name)  # Obtiene o crea tag

        tag.posts.add(*posts)  # Asocia posts (evita duplicados automáticamente)

        serializer.instance = tag  # Asigna la instancia creada al serializer

    def get_serializer_context(
        self,
    ):  # Añade el objeto 'request' al contexto del serializer para permitir validaciones basadas en el usuario autenticado
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
"""


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tag.objects.all()
        return Tag.objects.filter(posts__blog__user=user).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        posts = data.get("posts", [])
        name = data.get("name")

        # Obtener y validar blog del usuario
        blog = get_user_blog(user)

        # Validar que los posts pertenezcan al usuario
        validate_posts_for_user(user, posts)

        # Crear o obtener tag
        tag = get_or_create_tag(blog, name)

        # Asociar posts
        tag.posts.add(*posts)

        serializer.instance = tag


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]  # cualquiera puede registrarse
