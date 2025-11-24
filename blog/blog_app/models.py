from django.contrib.auth.models import User
from django.db import models


class Blog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="blog")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Blog de {self.user.username})"


class Post(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=150)
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.blog.user.username})"


class Tag(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    blog = models.ForeignKey(
        "Blog",
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(
        max_length=50, db_index=True
    )  # searches for a specific value or range of values much faster than traversing the entire table
    posts = models.ManyToManyField("Post", related_name="tags")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blog", "name"], name="unique_tag_per_blog")
        ]

    def __str__(self):
        return self.name
