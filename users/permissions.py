"""
Role-Based Access Control (RBAC) permissions and utilities.

Provides DRF permission classes and helper functions to enforce
department-level access control across the application.
"""

from rest_framework.permissions import BasePermission

from users.models import Role


class IsAdmin(BasePermission):
    """Allow access only to users with the ADMIN role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsAdminOrOwnerDepartment(BasePermission):
    """
    Allow access if the user is ADMIN or if the resource belongs
    to the user's department.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True
        # Check if the object has a 'department' attribute
        if hasattr(obj, 'department'):
            return obj.department == request.user.department
        return False


def get_accessible_departments(user):
    """
    Return the list of departments a user can access.

    Args:
        user: The authenticated user instance.

    Returns:
        list: Department keys the user can access.
    """
    if user.role == Role.ADMIN:
        return ['hr', 'accounts', 'legal']
    elif user.role in (Role.FINANCE, Role.ACCOUNTS):
        # Finance maps to the Accounts document namespace.
        return ['accounts']
    return [user.department]


def can_access_department(user, department):
    """
    Check if a user can access a specific department.

    Args:
        user: The authenticated user instance.
        department: Department name (string).

    Returns:
        bool: True if the user has access, False otherwise.
    """
    dept = (department or '').lower()
    if dept == 'finance':
        dept = 'accounts'

    if user.role == Role.ADMIN:
        return True
    elif user.role in (Role.FINANCE, Role.ACCOUNTS):
        return dept == 'accounts'
    return user.department == dept
