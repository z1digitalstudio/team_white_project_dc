from auth_app.helpers import check_user_authenticated  # Para graphQL
import graphene  # pyright: ignore[reportMissingImports]
from graphene_django import DjangoObjectType  # pyright: ignore[reportMissingImports]

from blog_app.constants import (
    ERROR_BLOG_NOT_ASSOCIATED,
    ERROR_BLOG_USER_HAS_BLOG,
    ERROR_TAG_PERMISSION_DENIED,
)
from blog_app.models import Blog, Post, Tag
from blog_app.serializers import BlogSerializer, PostSerializer, TagSerializer


# === Tipos (equivalentes a serializers, pero para GraphQL) ===
class BlogType(DjangoObjectType):
    class Meta:
        model = Blog
        fields = "__all__"


class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "title", "content", "created_at", "updated_at", "blog", "tags")


class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = ("id", "name", "posts")


# === Consultas (queries) ===
class Query(graphene.ObjectType):
    all_blogs = graphene.List(BlogType)
    all_posts = graphene.List(PostType)
    all_tags = graphene.List(TagType)

    def resolve_all_blogs(self, info):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if user.is_superuser:
            return Blog.objects.all()
        return Blog.objects.filter(user=user)

    def resolve_all_posts(self, info):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if user.is_superuser:
            return Post.objects.all()
        return Post.objects.filter(blog__user=user)

    def resolve_all_tags(self, info):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if user.is_superuser:
            return Tag.objects.all()
        return Tag.objects.filter(posts__blog__user=user).distinct()


# === Mutations ===
class CreateBlog(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    blog = graphene.Field(BlogType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, description=None):  # noqa: PLR6301
        user = check_user_authenticated(info)

        # cada usuario puede tener solo 1 blog
        if not user.is_superuser and Blog.objects.filter(user=user).exists():
            return CreateBlog(blog=None, errors=[ERROR_BLOG_USER_HAS_BLOG])

        data = {"title": title, "description": description, "user": user.id}
        serializer = BlogSerializer(data=data)
        if serializer.is_valid():
            blog = serializer.save(user=user)
            return CreateBlog(blog=blog, errors=[])
        return CreateBlog(blog=None, errors=serializer.errors)


class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        tag_ids = graphene.List(graphene.Int)

    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, content, tag_ids=None):  # noqa: PLR6301
        user = check_user_authenticated(info)
        blog = Blog.objects.filter(user=user).first()

        if not blog:
            return CreatePost(post=None, errors=[ERROR_BLOG_NOT_ASSOCIATED])

        data = {
            "title": title,
            "content": content,
            "blog": blog.id,
            "tags": tag_ids or [],
        }
        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            post = serializer.save()
            return CreatePost(post=post, errors=[])
        return CreatePost(post=None, errors=serializer.errors)


class CreateTag(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    tag = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, name):  # noqa: PLR6301
        user = check_user_authenticated(info)
        if not user.is_staff and not user.is_superuser:
            return CreateTag(tag=None, errors=[ERROR_TAG_PERMISSION_DENIED])

        serializer = TagSerializer(data={"name": name})
        if serializer.is_valid():
            tag = serializer.save()
            return CreateTag(tag=tag, errors=[])
        return CreateTag(tag=None, errors=serializer.errors)


# === Schema principal ===
class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    create_post = CreatePost.Field()
    create_tag = CreateTag.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
