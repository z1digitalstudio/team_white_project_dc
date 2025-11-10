"""
URL configuration for blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from graphene_django.views import GraphQLView  # pyright: ignore[reportMissingImports]
from rest_framework import permissions, routers
from rest_framework_simplejwt.views import (  # pyright: ignore[reportMissingImports]
    TokenObtainPairView,
    TokenRefreshView,
)

from blog_app.api import BlogViewSet, PostViewSet, RegisterView, TagViewSet
from blog_app.schema import schema

from django.contrib import admin
from django.urls import include, path


# Crear router automáticamente
router = routers.DefaultRouter()
router.register(
    r"blogs", BlogViewSet, basename="blog"
)  # r" es para escapar el carácter ". basename si viewset ya no devuelve Blog.objects.all() por defecto
router.register(r"posts", PostViewSet, basename="post")
router.register(r"tags", TagViewSet, basename="tag")


urlpatterns = [
    path("admin/", admin.site.urls),  # Panel de administración
    path("tinymce/", include("tinymce.urls")),  # Rutas de TinyMCE
    path("api/", include(router.urls)),  # API REST
    path("api-auth/", include("rest_framework.urls")),  # Login para DRF
    path("api/register/", RegisterView.as_view(), name="register"),  # registro
    path("", include("blog_app.urls")),  # Rutas normales del blog
    # Endpoints JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # GraphQL (NO usa router)
    path("graphql/", GraphQLView.as_view(graphiql=True, schema=schema)),
]
# Generar la documentación de la API con Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Blog CMS API",
        default_version="v1",
        description="Documentación de la API del Blog CMS",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contacto@blogcms.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns += [
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
