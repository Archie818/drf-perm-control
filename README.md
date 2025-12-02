# drf-perm-control

A flexible Django REST Framework permission class with caching support.

[![PyPI version](https://badge.fury.io/py/drf-perm-control.svg)](https://badge.fury.io/py/drf-perm-control)
[![Python Versions](https://img.shields.io/pypi/pyversions/drf-perm-control.svg)](https://pypi.org/project/drf-perm-control/)
[![Django Versions](https://img.shields.io/badge/Django-4.0%20%7C%204.1%20%7C%204.2%20%7C%205.0-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔐 **Django Permission Integration** - Uses Django's built-in permission system
- ⚡ **Caching Support** - Built-in permission caching for better performance
- 🎯 **Simple Configuration** - Just set `perm_control` on your views
- 🔧 **Highly Customizable** - Extend and customize to fit your needs
- 📦 **Zero Dependencies** - Only requires Django and DRF (Redis optional)

## Installation

```bash
pip install drf-perm-control
```

With Redis caching support:

```bash
pip install drf-perm-control[redis]
```

## Quick Start

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_perm_control import ApiPermission


class MyView(APIView):
    permission_classes = [ApiPermission]
    perm_control = "myapp.mymodel"  # Maps to Django permissions

    def get(self, request):
        # Requires 'myapp.view_mymodel' permission
        return Response({"message": "Hello, World!"})

    def post(self, request):
        # Requires 'myapp.add_mymodel' permission
        return Response({"message": "Created!"})
```

## Permission Mapping

The `perm_control` attribute maps HTTP methods to Django permissions:

| HTTP Method | Django Permission |
|-------------|-------------------|
| GET | `{app}.view_{model}` |
| POST | `{app}.add_{model}` |
| PUT | `{app}.change_{model}` |
| PATCH | `{app}.change_{model}` |
| DELETE | `{app}.delete_{model}` |

## Customization

### Custom Permission Class

```python
from drf_perm_control import ApiPermission


class CustomApiPermission(ApiPermission):
    # Cache timeout in seconds (default: 300)
    cache_timeout = 600  # 10 minutes
    
    # Cache key prefix (default: "user_perms")
    cache_key_prefix = "my_app_perms"
    
    # User types that bypass permission checks
    admin_user_types = ["ADMIN", "DEV"]
```

### Custom Permission Mapping

```python
from drf_perm_control import ApiPermission


class CustomApiPermission(ApiPermission):
    permission_map = {
        "GET": "{app_label}.view_{model_name}",
        "POST": "{app_label}.add_{model_name}",
        "PUT": "{app_label}.change_{model_name}",
        "PATCH": "{app_label}.change_{model_name}",
        "DELETE": "{app_label}.delete_{model_name}",
        "OPTIONS": "{app_label}.view_{model_name}",  # Add OPTIONS support
    }
```

### Using the Mixin

You can also use `PermControlMixin` to build your own permission classes:

```python
from rest_framework.permissions import BasePermission
from drf_perm_control import PermControlMixin


class MyCustomPermission(PermControlMixin, BasePermission):
    def has_permission(self, request, view):
        # Your custom logic here
        perm = self.get_permission_string(request.method, view.perm_control)
        return self.check_permission(request.user, perm)
```

## Configuration

### Django Settings

No additional Django settings are required. The package uses Django's built-in cache framework.

For Redis caching, configure Django's cache backend:

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
```

## API Reference

### `ApiPermission`

Main permission class for DRF views.

**Attributes:**
- `permission_map` - Dict mapping HTTP methods to permission string templates
- `cache_timeout` - Cache timeout in seconds (default: 300)
- `cache_key_prefix` - Prefix for cache keys (default: "user_perms")
- `admin_user_types` - List of user types that bypass permission checks

**Methods:**
- `has_permission(request, view)` - Check view-level permission
- `has_object_permission(request, view, obj)` - Check object-level permission

### `PermControlMixin`

Mixin providing permission control utilities.

**Methods:**
- `get_cache_key(user_id)` - Generate cache key for user permissions
- `get_permission_string(method, perm_control)` - Get required permission string
- `get_cached_permissions(user)` - Get user permissions from cache or database
- `check_permission(user, perm)` - Check if user has the specified permission
- `is_admin_user(user)` - Check if user is an admin-level user

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/drf-perm-control.git
cd drf-perm-control

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=drf_perm_control

# Format code
black src tests
ruff check src tests --fix
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

