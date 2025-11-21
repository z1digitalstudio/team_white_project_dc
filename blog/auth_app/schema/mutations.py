import graphene  # pyright: ignore[reportMissingImports]
import graphql_jwt  # pyright: ignore[reportMissingImports]
from rest_framework_simplejwt.tokens import (  # pyright: ignore[reportMissingImports]
    RefreshToken,  # pyright: ignore[reportMissingImports]
)

from blog_app.schema.types import UserType
from blog_app.serializers import RegisterSerializer


class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=False)
        password = graphene.String(required=True)

    # --- Outputs ---
    user = graphene.Field(UserType)
    token = graphene.String()  # JWT
    refresh_token = graphene.String()  # JWT refresh
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, password, email=None):  # noqa: PLR6301
        data = {"username": username, "email": email, "password": password}

        serializer = RegisterSerializer(data=data, context={"request": info.context})
        if serializer.is_valid():
            user = serializer.save()

            # Generar JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return RegisterUser(
                user=user, token=access_token, refresh_token=refresh_token, errors=[]
            )

        # Si hay errores de validación
        errors = [
            f"{field}: {', '.join(msgs)}" for field, msgs in serializer.errors.items()
        ]
        return RegisterUser(user=None, token=None, refresh_token=None, errors=errors)


class AuthMutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    login_token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    refresh_token = graphql_jwt.Refresh.Field()
