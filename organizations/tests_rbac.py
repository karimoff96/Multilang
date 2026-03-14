"""
Critical tests for the RBAC (Role-Based Access Control) system.

Covers:
- `has_permission()` with direct permission grant
- `has_permission()` with master permission that implies sub-permissions
- `has_permission()` correctly denied when permission absent
- Inactive role denies all permissions
- Missing role denies all permissions
- `permission_required` decorator: allows user with correct permission
- `permission_required` decorator: redirects user lacking permission
- `permission_required` decorator: inactive profile is rejected
- Superuser bypasses all permission checks

Run with:
    python manage.py test organizations.tests_rbac
"""

from django.contrib.auth.models import User
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.urls import reverse

from organizations.models import TranslationCenter, Branch, Role, AdminUser
from organizations.rbac import permission_required, RBACMiddleware


def _dummy_view(request, *args, **kwargs):
    return HttpResponse("OK")


_protected_view = permission_required("can_manage_orders")(_dummy_view)


class RBACTestBase(TestCase):
    """Shared fixtures for all RBAC tests."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(
            username="rbac_owner", password="secret123"
        )
        cls.center = TranslationCenter.objects.create(
            name="RBAC Test Center", owner=cls.owner
        )
        cls.branch = (
            cls.center.branches.first()
            or Branch.objects.create(name="Main", center=cls.center)
        )

    def _make_user_with_role(self, username, **role_kwargs):
        """Create a Django user + AdminUser with a Role configured by role_kwargs."""
        role_name = role_kwargs.pop("name", f"role_{username}")
        role = Role.objects.create(
            name=role_name,
            display_name=role_name,
            **role_kwargs,
        )
        user = User.objects.create_user(username=username, password="pass123")
        AdminUser.objects.create(
            user=user,
            role=role,
            center=self.center,
            branch=self.branch,
        )
        return user, role

    def _attach_middleware(self, request, user):
        """Run RBACMiddleware so request.admin_profile etc. are set."""
        request.user = user
        middleware = RBACMiddleware(lambda req: HttpResponse("next"))
        middleware(request)
        return request

    def _get_request(self, user):
        rf = RequestFactory()
        req = rf.get("/")
        self._attach_middleware(req, user)
        # The permission_required decorator calls messages.error(), which
        # requires message storage on the request.
        req._messages = CookieStorage(req)
        return req


class HasPermissionTests(RBACTestBase):
    """AdminUser.has_permission() unit tests (no HTTP layer)."""

    def test_direct_permission_granted(self):
        user, _ = self._make_user_with_role(
            "perm_direct_user", can_manage_orders=True
        )
        profile = user.admin_profile
        self.assertTrue(profile.has_permission("can_manage_orders"))

    def test_direct_permission_denied(self):
        user, _ = self._make_user_with_role(
            "perm_denied_user", can_manage_orders=False
        )
        profile = user.admin_profile
        self.assertFalse(profile.has_permission("can_manage_orders"))

    def test_master_permission_grants_sub_permission(self):
        """can_manage_orders should grant can_view_all_orders via master-perm map."""
        user, _ = self._make_user_with_role(
            "master_perm_user",
            can_manage_orders=True,
            can_view_all_orders=False,
        )
        profile = user.admin_profile
        # Direct can_manage_orders = True → has_permission("can_view_all_orders") = True
        self.assertTrue(profile.has_permission("can_view_all_orders"))

    def test_inactive_role_denies_permission(self):
        user, role = self._make_user_with_role(
            "inactive_role_user", can_manage_orders=True
        )
        role.is_active = False
        role.save()
        profile = user.admin_profile
        self.assertFalse(profile.has_permission("can_manage_orders"))

    def test_no_role_denies_permission(self):
        plain_user = User.objects.create_user(
            username="norole_user", password="pass123"
        )
        profile = AdminUser.objects.create(
            user=plain_user,
            role=None,
            center=self.center,
        )
        self.assertFalse(profile.has_permission("can_manage_orders"))

    def test_superuser_with_profile_has_permission(self):
        super_user = User.objects.create_superuser(
            username="superuser_with_profile", password="pass"
        )
        profile = AdminUser.objects.create(
            user=super_user,
            role=None,
            center=self.center,
        )
        self.assertTrue(profile.has_permission("can_manage_orders"))


class PermissionRequiredDecoratorTests(RBACTestBase):
    """Tests for the @permission_required decorator."""

    def test_user_with_permission_gets_response(self):
        user, _ = self._make_user_with_role("dec_allow_user", can_manage_orders=True)
        req = self._get_request(user)
        response = _protected_view(req)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    def test_user_without_permission_is_redirected(self):
        user, _ = self._make_user_with_role("dec_deny_user", can_manage_orders=False)
        req = self._get_request(user)
        response = _protected_view(req)
        # Decorator returns a redirect (302) when permission denied
        self.assertEqual(response.status_code, 302)

    def test_inactive_profile_is_redirected(self):
        user, _ = self._make_user_with_role("dec_inactive_user", can_manage_orders=True)
        profile = user.admin_profile
        profile.is_active = False
        profile.save()
        req = self._get_request(user)
        response = _protected_view(req)
        self.assertEqual(response.status_code, 302)

    def test_user_with_no_admin_profile_is_redirected(self):
        plain_user = User.objects.create_user(
            username="dec_noprofile_user", password="pass"
        )
        rf = RequestFactory()
        req = rf.get("/")
        req.user = plain_user
        req._messages = CookieStorage(req)
        # Simulate middleware result for a user without an admin_profile
        req.admin_profile = None
        req.user_role = None
        req.is_owner = False
        req.is_manager = False
        req.is_staff_member = False
        response = _protected_view(req)
        self.assertEqual(response.status_code, 302)

    def test_superuser_bypasses_permission_check(self):
        req = self._get_request(self.owner)
        response = _protected_view(req)
        self.assertEqual(response.status_code, 200)

    def test_multiple_permissions_all_required(self):
        """All specified permissions must be satisfied; lacking one is enough to deny."""
        multi_view = permission_required("can_manage_orders", "can_manage_staff")(
            _dummy_view
        )

        # User has only one of the two required permissions
        user, _ = self._make_user_with_role(
            "partial_perm_user",
            can_manage_orders=True,
            can_manage_staff=False,
        )
        req = self._get_request(user)
        response = multi_view(req)
        self.assertEqual(response.status_code, 302)

        # User has both permissions
        user2, _ = self._make_user_with_role(
            "full_perm_user",
            can_manage_orders=True,
            can_manage_staff=True,
        )
        req2 = self._get_request(user2)
        response2 = multi_view(req2)
        self.assertEqual(response2.status_code, 200)
