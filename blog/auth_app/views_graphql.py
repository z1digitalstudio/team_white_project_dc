from graphene_django.views import GraphQLView  # pyright: ignore[reportMissingImports]
from graphql_jwt.middleware import (  # pyright: ignore[reportMissingImports]
    JSONWebTokenMiddleware,  # pyright: ignore[reportMissingImports]
)


class CustomGraphQLView(GraphQLView):
    def __init__(self, *args, **kwargs):
        middleware = kwargs.pop("middleware", [])
        middleware.append(JSONWebTokenMiddleware())
        kwargs["middleware"] = middleware
        super().__init__(*args, **kwargs)

    def get_context(self, request):  # noqa: PLR6301
        # Esto asegura que info.context.user sea el usuario autenticado por JWT
        return request
