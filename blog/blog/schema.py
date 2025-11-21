from auth_app.schema import AuthMutation
import graphene  # pyright: ignore[reportMissingImports]

from blog_app.schema.mutations import (  # pyright: ignore[reportMissingImports]
    Mutation as BlogMutation,  # pyright: ignore[reportMissingImports]
)
from blog_app.schema.queries import (  # pyright: ignore[reportMissingImports]
    BlogQuery,
    PostQuery,
    TagQuery,
)


class Query(BlogQuery, PostQuery, TagQuery, graphene.ObjectType):
    pass


class Mutation(BlogMutation, AuthMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
