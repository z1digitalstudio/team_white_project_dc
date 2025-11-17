# Blog CMS – Headless CMS con Django

Proyecto que implementa un **CMS (Content Management System)** headless básico utilizando **Django** y **GRAPHQL**.
Permite a los usuarios registrarse, crear un blog personal, gestionar posts y etiquetas, y acceder a los datos mediante una API REST documentada.

---

## Tecnologías Utilizadas

| Tecnología                | Uso                           |
| ------------------------- | ----------------------------- |
| **Python 3.14+**          | Lenguaje principal            |
| **Django 5.2,7**          | Framework backend             |
| **Django REST Framework** | API REST                      |
| **GraphQL**               | API REST principal            |
| **django-tinymce**        | Editor HTML en el admin       |
| **django-import-export**  | Exportación de datos          |
| **drf-yasg**              | Documentación Swagger / Redoc |
| **SQLite**                | Base de datos para desarrollo |
| **POSTGRE**               | Base de datos para producción |

---


## Requisitos Previos
Asegúrate de tener instalado:

- **Docker 20+**
- **Docker Compose 2+**

## Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/danielachg28/proyecto1-blog-cms.git
cd blog-cms
```

## 2. Configuración del entorno

Este proyecto utiliza variables de entorno definidas en un archivo `.env`.
**Por seguridad, los archivos `.env` no se incluyen en el repositorio.**

Para ejecutar el proyecto, crea un archivo `.env` en la raíz del proyecto con las variables necesarias:

DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_SETTINGS_MODULE=blog.settings.dev

# Para levantar el proyecto:
docker compose up --build

# Para ejecutar en segundo plano:
docker compose up -d

# Para detener y eliminar contenedores:
docker compose down

# Acceder a un contenedor:
docker exec <nombre del contenedor> bash


### 3. Ejecutar el servidor

Abrir en el navegador:
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Funcionalidades Principales

- **Registro y login de usuarios**
- **Blog personal por usuario** (1:1 con `User`)
- **Gestión de posts y etiquetas** desde panel admin y API
- **TinyMCE** como editor de texto enriquecido
- **Exportación de datos a CSV/JSON** desde el admin
- **Autenticación por token en API REST GraphQL**
- **Documentación Swagger y Redoc automática**

---

## Arquitectura de Modelos

```
User (Django built-in)
└── Blog (1:1 con User)
    └── Post (N:1 con Blog)
        └── Tag (M:N con Post)
```

---

## API REST (Django Rest Framework)

### Endpoints principales

| Endpoint           | Método     | Descripción                | Autenticación |
| ------------------ | ---------- | -------------------------- | ------------- |
| `/api/register/`   | POST       | Registrar un nuevo usuario | ❌ No requiere |
| `/api-auth/login/` | GET        | Iniciar sesión             | ✅ Sí          |
| `/api/token/`      |
| `/api/blogs/`      | GET / POST | Ver o crear blogs          | ✅ Sí          |
| `/api/posts/`      | GET / POST | Ver o crear posts          | ✅ Sí          |
| `/api/tags/`       | GET / POST | Ver o crear etiquetas      | ✅ Sí          |
| `/swagger/`        | GET        | Documentación Swagger      | ❌ No requiere |
| `/redoc/`          | GET        | Documentación Redoc        | ❌ No requiere |

---

### Ejemplo de Registro (POST `/api/register/`)

```json
{
  "username": "usuario",
  "email": "usuario@example.com",
  "password": "1234"
}
```

Respuesta esperada:

```json
{
  "id": 3,
  "username": "usuario",
  "email": "usuario@example.com"
}
```

---

## Autenticación

Para realizar peticiones a la API (crear posts, blogs, tags), es necesario autenticarse:

1. Ir a `/api-auth/login/`
2. Iniciar sesión con un usuario existente
3. Desde ahí, acceder a `/api/posts/`, `/api/blogs/`, etc.

---

## Panel de Administración

Acceso al panel administrativo:

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)


Desde el admin se puede:

* Crear/editar blogs, posts y etiquetas
* Editar contenido con **TinyMCE**
* Exportar datos con **django-import-export**

## Pruebas de la API (DRF)

Cómo probar con Postman

1. Registrar usuario
POST http://127.0.0.1:8000/api/register/

2. Autenticarse
En `/api/token/` usar método POST -> body:
{
    "username": "usuario",
    "password": "contraseña"
}

Copiar el "access" token y luego en la pestaña de Headers añadir:
Key: Authorization
Value: Bearer <tu_token_access>
Para todas las consultas


3. Crear post
POST /api/posts/

{
  "title": "Primer post",
  "content": "Contenido del post"
}

## API REST (GraphQL)
**Endpoint único:** `/graphql/`
**Método:** POST

| Operación    | Tipo     | Descripción                          | Autenticación  |
|--------------|----------|--------------------------------------|----------------|
| registerUser | Mutation | Registrar un nuevo usuario           | ❌ No requiere |
| tokenAuth    | Mutation | Login de usuario                     | ❌ No requiere |
| createBlog   | Mutation | Crear un blog                        | ✅ Sí          |
| createPost   | Mutation | Crear un post                        | ✅ Sí          |
| createTag    | Mutation | Crear una etiqueta / tag             | ✅ Sí          |
| allBlogs     | Query    | Obtener todos los blogs              | ✅ Sí          |
| allPosts     | Query    | Obtener todos los posts              | ✅ Sí          |
| allTags      | Query    | Obtener todas las etiquetas          | ✅ Sí          |


## Pruebas de la API (GRAPHQL)

# Como probar con Postman (GraphQL):
- Seleccionar pestaña de GraphQL y se visualizarán las queries

- en la casilla de url: Método: POST  https://teamwhiteprojectdc-production.up.railway.app/graphql/

- Al hacer el login, copiar el token y la pestaña de headers añadir:
  Key: Authorization
  Value: Bearer <token>

-Realizar las consultas


# Como probar con GraphQL interfaz:

- Acceder a https://teamwhiteprojectdc-production.up.railway.app/graphql/

-Al hacer el login, copiar el token y la sección de headers añadir:
{
  "Authorization": "Bearer <token>"
}

# Consultas (Postman e intefaz):

1. Registrar un usuario
mutation {
  registerUser(username: "usuario", email: "usuario@mail.com", password: "123456") {
    user {
      id
      username
      email
    }
    token
    refreshToken
    errors
  }
}

2. Login:
mutation {
  loginTokenAuth(username: "tu_usuario", password: "tu_password") {
    token
  }
}

3. Obtener el blog
{
  allBlogs {
    id
    title
    description
  }
}

4. Obtener todos los posts
{
  allPosts {
    id
    title
    content
    createdAt
    updatedAt
    blog {
      id
      title
    }
    tags {
      id
      name
    }
  }
}

5. Obtener todos los tags
{
  allTags {
    id
    name
    posts {
      id
      title
    }
  }
}


6. Crear un blog
mutation CreateBlog {
    createBlog(title: "Blog del usuario", description: "Descripción del blog") {
        errors
        blog {
            id
            title
            description
        }
    }
}


7. Crear un post
mutation {
  createPost(
    title: "Título del post",
    content: "Contenido del post",
  ) {
    post {
      id
      title
      content
      blog {
        id
        title
      }
      tags {
        id
        name
      }
    }
    errors
  }
}

8. Crear un tag:
mutation {
  createTag(
    name: "python"
    postIds: [19, 30]  # IDs de los posts que se quiere asociar
  ) {
    tag {
      id
      name
      posts {
        id
        title
      }
    }
    errors
  }
}


## Documentación de la API

* **Swagger UI:** [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
* **Redoc UI:** [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

Ambas interfaces permiten probar los endpoints directamente desde el navegador.


## Estructura del Proyecto

```
 proyecto1-blog-cms/
│
├── blog/                         # Carpeta raíz del proyecto Django
│   │
│   ├── blog/                     # Proyecto principal de Django (configuración global)
│   │   ├── __init__.py
│   │   ├── settings/             # Configuraciones por entorno
│   │   │   ├── base.py           # Configuración base (común a todos)
│   │   │   ├── prod.py           # Configuración para producción
│   │   │   └── dev.py            # Configuración para desarrollo
│   │   ├── urls.py               # URLs raíz del proyecto
│   │   ├── wsgi.py               # Entrada WSGI (para Gunicorn u otros)
│   │   └── asgi.py               # Entrada ASGI (para Django Channels o async)
│   │
│   ├── auth_app/                 # Aplicación
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── constants.py
│   │   ├── helpers.py
│   │   ├── admin.py
│   │   ├── tests.py
│   │   ├── views_graphql.py
│   │   └── permissions.py
|   |
│   ├── blog_app/                 # Aplicación
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── constants.py
│   │   ├── helpers.py
│   │   ├── api.py
│   │   ├── schema.py
│   │   ├── admin.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── permissions.py
│   │
│   ├── tests/                    # Pruebas unitarias y de integración
│   │   ├── __init__.py
│   │   ├── factories.py
│   │   ├── test_api.py
│   │   └── test_models.py
│   │
│   ├── manage.py                 # Script de gestión principal
│   ├── pytest.py                 # Config opcional o entrada personalizada de pytest
│   │
│   ├── requirements/             # Dependencias por entorno
│   │   ├── base.txt              # Dependencias comunes
│   │   ├── prod.txt              # Dependencias de producción
│   │   └── dev.txt               # Dependencias de desarrollo
│   │
│   ├── Dockerfile                # Dockerfile base de producción
│   ├── Dockerfile-dev            # Dockerfile para entorno de desarrollo
│   └── docker-compose.yml        # Orquestador de servicios (DB, Redis, etc.)
│   ├── .env                      # Variables de entorno locales (desarrollo)
│   ├── .env.prod                 # Variables de entorno para producción
│   ├── start.sh                  # Script de inicio (ej. para Docker o entrypoint)
│   ├── README.md                 #
│   ├── .pre-commit-config.yaml   # Configuración de hooks (en raíz del repo)
│   └── pyproject.toml            # Configuración de herramientas (Black, Ruff, etc.)
│   └── .gitignore                # Archivo de git
```

---
