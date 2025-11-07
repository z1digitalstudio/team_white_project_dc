from auth_app.permissions import IsBlogOwnerOrAdmin, IsOwnerOrAdmin, is_superuser
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny

from .models import Blog, Post, Tag
from .serializers import (
    BlogSerializer,
    PostSerializer,
    RegisterSerializer,
    TagSerializer,
)

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


# --- ViewSets ---
# ViewSet para Blog
class BlogViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Blogs:
    - GET: el blog del usuario (o todos si es superusuario)
    - POST: bloqueado, los blogs se crean automáticamente al crear un post
    """

    serializer_class = BlogSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Blog.objects.all()
        return Blog.objects.filter(user=user)

    def create(self, request, *args, **kwargs):  # noqa: PLR6301
        # Bloquea la creación manual de blogs.
        raise PermissionDenied("Ya existe un blog creado para este usuario.")


# ViewSet para Post
class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Posts:
    - GET: posts del usuario o todos si es superusuario
    - POST: crea un post y crea automáticamente el blog si no existía
    - PUT: permite editar posts del usuario
    - DELETE: permite eliminar posts del usuario
    """

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
class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Posts:
    - GET: tags del usuario o todos si es superusuario
    - POST: crea un tag y asocia posts al tag
    - PUT: permite editar tags del usuario
    - DELETE: permite eliminar tags del usuario
    """

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

        validate_user_owns_posts(user, posts)  # Valida propiedad de posts

        tag = get_or_create_tag_by_name(name)  # Obtiene o crea tag

        tag.posts.add(*posts)  # Asocia posts (evita duplicados automáticamente)

        serializer.instance = tag  # Asigna la instancia creada al serializer

    def get_serializer_context(
        self,
    ):  # Añade el objeto 'request' al contexto del serializer para permitir validaciones basadas en el usuario autenticado
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]  # cualquiera puede registrarse
