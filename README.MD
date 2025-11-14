# 📰 Blog CMS – Headless CMS con Django

Proyecto que implementa un **CMS (Content Management System)** headless básico utilizando **Django** y **Django REST Framework**.
Permite a los usuarios registrarse, crear un blog personal, gestionar posts y etiquetas, y acceder a los datos mediante una API REST documentada.

---

## Tecnologías Utilizadas

| Tecnología                | Uso                           |
| ------------------------- | ----------------------------- |
| **Python 3.14+**          | Lenguaje principal            |
| **Django 5.2,7**            | Framework backend             |
| **Django REST Framework** | API REST                      |
| **django-tinymce**        | Editor HTML en el admin       |
| **django-import-export**  | Exportación de datos          |
| **drf-yasg**              | Documentación Swagger / Redoc |
| **SQLite**                | Base de datos para desarrollo |

---

## Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/danielachg28/proyecto1-blog-cms.git
cd blog-cms
```

### 2. Crear y activar entorno virtual

```bash
python -m venv myvenv
source myvenv/bin/activate   # En macOS/Linux
myvenv\Scripts\activate      # En Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear superusuario

```bash
python manage.py createsuperuser
```

### 6. Ejecutar el servidor

```bash
python manage.py runserver
```

Abrir en el navegador:
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Funcionalidades Principales

- **Registro y login de usuarios**
- **Blog personal por usuario** (1:1 con `User`)
- **Gestión de posts y etiquetas** desde panel admin y API
- **TinyMCE** como editor de texto enriquecido
- **Exportación de datos a CSV/JSON** desde el admin
- **Autenticación por sesión en API REST**
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
Usuario: *superuser* creado en el paso 5

Desde el admin se puede:

* Crear/editar blogs, posts y etiquetas
* Editar contenido con **TinyMCE**
* Exportar datos con **django-import-export**

---

## Pruebas de la API (DRF)

Cómo probar con Postman

1. Registrar usuario
POST http://127.0.0.1:8000/api/register/

2. Autenticarse
En cada petición → pestaña Authorization → Basic Auth
Usar usuario y contraseña creados.

3. Crear post
POST /api/posts/

{
  "title": "Primer post",
  "content": "Contenido del post"
}

---

## Pruebas de la API (GRAPHQL)

Como probar con Postman (GraphQL):
- Seleccionar pestaña de GraphQL y se visualizarán las queries
- en la casilla de url: Método: POST  https://teamwhiteprojectdc-production.up.railway.app/graphql/
- Al hacer el login, copiar el token y la pestaña de headers añadir:
  Key: Authorization
  Value: Bearer <token>
-Realizar las consultas


Como probar con GraphQL interfaz:

- Acceder a https://teamwhiteprojectdc-production.up.railway.app/graphql/
-Al hacer el login, copiar el token y la sección de headers añadir:
{
  "Authorization": "Bearer <token>"
}


Consultas:
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
  tokenAuth(username: "tu_usuario", password: "tu_password") {
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


6. Crear un post
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


7. Crear un tag:
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






---


## 📘 Documentación de la API

* **Swagger UI:** [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
* **Redoc UI:** [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

Ambas interfaces permiten probar los endpoints directamente desde el navegador.

---

## 🧾 Estructura del Proyecto

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
