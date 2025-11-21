from auth_app.schema.mutations import RegisterUser
import graphene  # pyright: ignore[reportMissingImports]
import graphql_jwt  # pyright: ignore[reportMissingImports]

from blog_app.schema.mutations.post_mutations import CreatePost, DeletePost, UpdatePost
from blog_app.schema.mutations.tag_mutations import CreateTag, DeleteTag, UpdateTag

from .mutations.blog_mutations import CreateBlog, UpdateBlog


class Mutation(graphene.ObjectType):
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()

    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()

    create_tag = CreateTag.Field()
    update_tag = UpdateTag.Field()
    delete_tag = DeleteTag.Field()
    register_user = RegisterUser.Field()

    # Mutaciones JWT
    login_token_auth = graphql_jwt.ObtainJSONWebToken.Field()  # obtener token - login
    refresh_token = (
        graphql_jwt.Refresh.Field()
    )  # refrescar token para que el usuario siga logueado
