import graphene  # pyright: ignore[reportMissingImports]

from .blog_mutations import CreateBlog, UpdateBlog
from .post_mutations import CreatePost, DeletePost, UpdatePost
from .tag_mutations import CreateTag, DeleteTag, UpdateTag


class BlogMutation(graphene.ObjectType):
    # Blog
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()

    # Post
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()

    # Tag
    create_tag = CreateTag.Field()
    update_tag = UpdateTag.Field()
    delete_tag = DeleteTag.Field()
