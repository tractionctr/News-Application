"""
Custom permission classes for role-based access control.

Defines access rules for:
- Readers (view-only access)
- Journalists (manage own content)
- Editors (full content control)
- Mixed role access combinations
"""

from rest_framework import permissions


class IsReader(permissions.BasePermission):
    """
    Allows access only to users with the Reader role.

    Readers can view content but cannot modify it.
    """

    message = "Readers can only view content."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Reader'

    def has_object_permission(self, request, view, obj):
        """
        Readers are restricted to safe (read-only) operations.
        """
        return request.method in permissions.SAFE_METHODS


class IsJournalist(permissions.BasePermission):
    """
    Allows access only to users with the Journalist role.

    Journalists can create and manage their own content.
    """

    message = "Journalists can only manage their own content."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Journalist'

    def has_object_permission(self, request, view, obj):
        """
        Journalists can only modify objects they own.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'author'):
            return obj.author == request.user

        return False


class IsEditor(permissions.BasePermission):
    """
    Allows access only to users with the Editor role.

    Editors have full permissions over content management.
    """

    message = "Only Editors can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "Editor"

    def has_object_permission(self, request, view, obj):
        """
        Editors can access and modify all objects.
        """
        return True


class IsJournalistOrEditor(permissions.BasePermission):
    """
    Allows access to Journalists and Editors.

    - Journalists: limited to their own content
    - Editors: full access to all content
    """

    message = "Only Journalists or Editors can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['Journalist', 'Editor']
        )

    def has_object_permission(self, request, view, obj):
        """
        Journalists can only modify their own content.
        Editors can modify everything.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.role == 'Editor':
            return True

        if request.user.role == 'Journalist' and hasattr(obj, 'author'):
            return obj.author == request.user

        return False


class IsReaderOrJournalistOrEditor(permissions.BasePermission):
    """
    Allows access to all authenticated roles.

    - Readers: read-only
    - Journalists: own content management
    - Editors: full access
    """

    message = "Authentication required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['Reader', 'Journalist', 'Editor']
        )

    def has_object_permission(self, request, view, obj):
        """
        Enforces role-based object-level access rules.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.role == 'Editor':
            return True

        if request.user.role == 'Journalist' and hasattr(obj, 'author'):
            return obj.author == request.user

        return False


class IsAuthenticatedWithRole(permissions.BasePermission):
    """
    Base permission ensuring user is authenticated and has a valid role.

    Used as a general safety gate across API endpoints.
    """

    message = "Authentication required with valid role."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['Reader', 'Journalist', 'Editor']
        )
