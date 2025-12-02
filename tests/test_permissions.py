import pytest
from unittest.mock import Mock, patch

from drf_perm_control import ApiPermission, PermControlMixin


class TestPermControlMixin:
    """Tests for PermControlMixin."""

    def setup_method(self):
        self.mixin = PermControlMixin()

    def test_get_cache_key(self):
        """Test cache key generation."""
        cache_key = self.mixin.get_cache_key(123)
        assert cache_key == "user_perms:123"

    def test_get_permission_string_get(self):
        """Test permission string for GET request."""
        perm = self.mixin.get_permission_string("GET", "myapp.mymodel")
        assert perm == "myapp.view_mymodel"

    def test_get_permission_string_post(self):
        """Test permission string for POST request."""
        perm = self.mixin.get_permission_string("POST", "myapp.mymodel")
        assert perm == "myapp.add_mymodel"

    def test_get_permission_string_put(self):
        """Test permission string for PUT request."""
        perm = self.mixin.get_permission_string("PUT", "myapp.mymodel")
        assert perm == "myapp.change_mymodel"

    def test_get_permission_string_patch(self):
        """Test permission string for PATCH request."""
        perm = self.mixin.get_permission_string("PATCH", "myapp.mymodel")
        assert perm == "myapp.change_mymodel"

    def test_get_permission_string_delete(self):
        """Test permission string for DELETE request."""
        perm = self.mixin.get_permission_string("DELETE", "myapp.mymodel")
        assert perm == "myapp.delete_mymodel"

    def test_get_permission_string_invalid_format(self):
        """Test permission string with invalid perm_control format."""
        with pytest.raises(ValueError, match="perm_control must be in 'app.model' format"):
            self.mixin.get_permission_string("GET", "invalid_format")

    def test_get_permission_string_invalid_method(self):
        """Test permission string with invalid HTTP method."""
        with pytest.raises(ValueError, match="Method OPTIONS not in permission_map"):
            self.mixin.get_permission_string("OPTIONS", "myapp.mymodel")

    def test_is_admin_user_superuser(self):
        """Test is_admin_user returns True for superuser."""
        user = Mock(is_superuser=True)
        assert self.mixin.is_admin_user(user) is True

    def test_is_admin_user_regular_user(self):
        """Test is_admin_user returns False for regular user."""
        user = Mock(is_superuser=False)
        assert self.mixin.is_admin_user(user) is False

    def test_is_admin_user_with_admin_user_types(self):
        """Test is_admin_user with custom admin_user_types."""
        self.mixin.admin_user_types = ["ADMIN", "DEV"]
        user = Mock(is_superuser=False, user_type="ADMIN")
        assert self.mixin.is_admin_user(user) is True

    def test_is_admin_user_non_admin_type(self):
        """Test is_admin_user with non-admin user_type."""
        self.mixin.admin_user_types = ["ADMIN", "DEV"]
        user = Mock(is_superuser=False, user_type="USER")
        assert self.mixin.is_admin_user(user) is False

    @patch("drf_perm_control.permissions.cache")
    def test_check_permission_superuser(self, mock_cache):
        """Test check_permission returns True for superuser."""
        user = Mock(is_superuser=True)
        assert self.mixin.check_permission(user, "myapp.view_mymodel") is True
        mock_cache.get.assert_not_called()

    @patch("drf_perm_control.permissions.cache")
    def test_check_permission_with_cached_perms(self, mock_cache):
        """Test check_permission uses cached permissions."""
        user = Mock(is_superuser=False, id=1)
        mock_cache.get.return_value = ["myapp.view_mymodel", "myapp.add_mymodel"]

        result = self.mixin.check_permission(user, "myapp.view_mymodel")

        assert result is True
        mock_cache.get.assert_called_once_with("user_perms:1")

    @patch("drf_perm_control.permissions.cache")
    def test_check_permission_cache_miss(self, mock_cache):
        """Test check_permission fetches permissions on cache miss."""
        user = Mock(is_superuser=False, id=1)
        user.get_all_permissions.return_value = {"myapp.view_mymodel"}
        mock_cache.get.return_value = None

        result = self.mixin.check_permission(user, "myapp.view_mymodel")

        assert result is True
        mock_cache.set.assert_called_once()

    @patch("drf_perm_control.permissions.cache")
    def test_check_permission_denied(self, mock_cache):
        """Test check_permission returns False when permission not in cache."""
        user = Mock(is_superuser=False, id=1)
        mock_cache.get.return_value = ["myapp.add_mymodel"]

        result = self.mixin.check_permission(user, "myapp.view_mymodel")

        assert result is False


class TestApiPermission:
    """Tests for ApiPermission."""

    def setup_method(self):
        self.permission = ApiPermission()

    @patch("drf_perm_control.permissions.cache")
    def test_has_permission_superuser(self, mock_cache):
        """Test has_permission returns True for superuser."""
        request = Mock(user=Mock(is_superuser=True))
        view = Mock(perm_control="myapp.mymodel")

        assert self.permission.has_permission(request, view) is True

    @patch("drf_perm_control.permissions.cache")
    def test_has_permission_missing_perm_control(self, mock_cache):
        """Test has_permission returns False when perm_control is missing."""
        request = Mock(user=Mock(is_superuser=False))
        view = Mock(spec=[])  # No perm_control attribute

        assert self.permission.has_permission(request, view) is False

    @patch("drf_perm_control.permissions.cache")
    def test_has_permission_allowed(self, mock_cache):
        """Test has_permission returns True when user has permission."""
        user = Mock(is_superuser=False, id=1)
        mock_cache.get.return_value = ["myapp.view_mymodel"]
        request = Mock(user=user, method="GET")
        view = Mock(perm_control="myapp.mymodel")

        assert self.permission.has_permission(request, view) is True

    @patch("drf_perm_control.permissions.cache")
    def test_has_permission_denied(self, mock_cache):
        """Test has_permission returns False when user lacks permission."""
        user = Mock(is_superuser=False, id=1)
        mock_cache.get.return_value = ["myapp.add_mymodel"]
        request = Mock(user=user, method="GET")
        view = Mock(perm_control="myapp.mymodel")

        assert self.permission.has_permission(request, view) is False

    @patch("drf_perm_control.permissions.cache")
    def test_has_object_permission_owner(self, mock_cache):
        """Test has_object_permission returns True for object owner."""
        user = Mock(is_superuser=False, id=1)
        mock_cache.get.return_value = ["myapp.view_mymodel"]
        request = Mock(user=user, method="GET")
        view = Mock(perm_control="myapp.mymodel")
        obj = Mock(user_id=1)

        assert self.permission.has_object_permission(request, view, obj) is True

    @patch("drf_perm_control.permissions.cache")
    def test_has_object_permission_not_owner(self, mock_cache):
        """Test has_object_permission returns False for non-owner."""
        user = Mock(is_superuser=False, id=1)
        mock_cache.get.return_value = ["myapp.view_mymodel"]
        request = Mock(user=user, method="GET")
        view = Mock(perm_control="myapp.mymodel")
        obj = Mock(user_id=2)

        assert self.permission.has_object_permission(request, view, obj) is False

