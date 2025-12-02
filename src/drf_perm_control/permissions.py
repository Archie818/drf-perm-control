from rest_framework.permissions import BasePermission
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class PermControlMixin:
    """
    Mixin providing permission control utilities.
    Extend this class to customize behavior.
    """

    permission_map = {
        "GET": "{app_label}.view_{model_name}",
        "POST": "{app_label}.add_{model_name}",
        "PUT": "{app_label}.change_{model_name}",
        "PATCH": "{app_label}.change_{model_name}",
        "DELETE": "{app_label}.delete_{model_name}",
    }

    # Override these in subclass for customization
    cache_timeout = 300  # 5 minutes
    cache_key_prefix = "user_perms"
    admin_user_types = []  # e.g., ["ADMIN", "DEV"]

    def get_cache_key(self, user_id):
        """Generate cache key for user permissions."""
        return f"{self.cache_key_prefix}:{user_id}"

    def get_permission_string(self, method, perm_control):
        """Get the required permission string based on HTTP method."""
        if "." not in perm_control:
            raise ValueError(
                f"perm_control must be in 'app.model' format, got: {perm_control}"
            )

        app, model = perm_control.split(".", 1)

        if method not in self.permission_map:
            raise ValueError(f"Method {method} not in permission_map")

        return self.permission_map[method].format(app_label=app, model_name=model)

    def get_cached_permissions(self, user):
        """Get user permissions from cache or database."""
        cache_key = self.get_cache_key(user.id)
        cached_perms = cache.get(cache_key)

        if cached_perms is None:
            cached_perms = list(user.get_all_permissions())
            cache.set(cache_key, cached_perms, self.cache_timeout)

        return cached_perms

    def check_permission(self, user, perm):
        """Check if user has the specified permission."""
        if user.is_superuser:
            return True

        cached_perms = self.get_cached_permissions(user)
        return perm in cached_perms

    def is_admin_user(self, user):
        """Check if user is an admin-level user."""
        if user.is_superuser:
            return True

        if self.admin_user_types and hasattr(user, "user_type"):
            return user.user_type in self.admin_user_types

        return False


class ApiPermission(PermControlMixin, BasePermission):
    """
    DRF permission class using Django's permission system with caching.

    Usage:
        class MyView(APIView):
            permission_classes = [ApiPermission]
            perm_control = "myapp.mymodel"
    """

    def has_permission(self, request, view):
        """Check if the user has the required permission."""
        if self.is_admin_user(request.user):
            return True

        if not hasattr(view, "perm_control"):
            logger.warning(
                f"View {view.__class__.__name__} missing perm_control attribute"
            )
            return False

        try:
            perm = self.get_permission_string(
                method=request.method,
                perm_control=view.perm_control,
            )
            return self.check_permission(request.user, perm)
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    def has_object_permission(self, request, view, obj):
        """Object-level permission check."""
        if self.is_admin_user(request.user):
            return True

        if not hasattr(view, "perm_control"):
            return False

        try:
            perm = self.get_permission_string(
                method=request.method,
                perm_control=view.perm_control,
            )
            has_perm = self.check_permission(request.user, perm)

            if has_perm:
                # Default: check if user owns the object
                if hasattr(obj, "user_id"):
                    return obj.user_id == request.user.id
                if hasattr(obj, "id") and hasattr(request.user, "id"):
                    return obj.id == request.user.id

            return False
        except Exception as e:
            logger.error(f"Object permission check failed: {e}")
            return False

