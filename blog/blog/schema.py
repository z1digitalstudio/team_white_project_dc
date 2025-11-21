from auth_app.schema import AuthMutation
import graphene  # pyright: ignore[reportMissingImports]

from blog_app.schema import BlogMutation
from blog_app.schema.queries import Query as AllQuery


class Query(AllQuery, graphene.ObjectType):
    """Combines all query classes into a single Query type."""

    pass


class Mutation(BlogMutation, AuthMutation, graphene.ObjectType):
    """Combines all mutation classes into a single Mutation type."""

    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
