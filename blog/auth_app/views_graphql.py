from graphene_django.views import GraphQLView  # pyright: ignore[reportMissingImports]
from graphql_jwt.shortcuts import (  # pyright: ignore[reportMissingImports]
    get_user_by_token,  # pyright: ignore[reportMissingImports]
)

from auth_app.utils.constants import ERROR_NOT_OBTAIN_USER_BYTOKEN


class CustomGraphQLView(GraphQLView):
    def get_context(self, request):  # noqa: PLR6301
        # If the middleware doesn't resolve the user by token, try manually:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split("Bearer ")[1]
            try:
                user = get_user_by_token(token)
                request.user = user
            except Exception:
                print(ERROR_NOT_OBTAIN_USER_BYTOKEN)
        return request
