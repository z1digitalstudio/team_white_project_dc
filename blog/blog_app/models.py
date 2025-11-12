from django.contrib.auth.models import User
from django.db import models


# 2.1 Blog con relación 1:1 con User
class Blog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="blog")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} (Blog de {self.user.username})"


# 2.2 Post con campos básicos
class Post(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=150)
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # fecha de creación
    updated_at = models.DateTimeField(auto_now=True)  # fecha de actualización

    class Meta:
        ordering = ["-created_at"]  # 2.4 Metadatos: orden descendente por fecha

    def __str__(self):
        return f"{self.title} ({self.blog.user.username})"


# 2.3 Tag y relación M:N con Post
class Tag(models.Model):
    blog = models.ForeignKey(
        "Blog",
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(
        max_length=50, db_index=True
    )  # busca un valor concreto o rango de valores mucho más rápido que recorriendo toda la tabla
    posts = models.ManyToManyField("Post", related_name="tags")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blog", "name"], name="unique_tag_per_blog")
        ]

    def __str__(self):
        return self.name
