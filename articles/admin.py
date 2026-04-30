"""
Django admin configuration for the News Application.

Registers models in the Django admin interface and customizes:
- User management
- Publisher management
- Article moderation
- Newsletter management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Publisher, Article, Newsletter


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.

    Extends Django's default UserAdmin to include:
    - role management
    - subscription relationships
    """

    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
        ('Subscriptions', {'fields': ('subscriptions_publishers', 'subscriptions_journalists')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """
    Admin interface for Publisher model.

    Allows management of publishers and their relationships
    with journalists and editors.
    """

    list_display = ['name', 'created_at']
    filter_horizontal = ['journalists', 'editors']
    search_fields = ['name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin interface for Article model.

    Used for content moderation and editorial management.
    """

    list_display = ['title', 'author', 'publisher', 'approved', 'created_at']
    list_filter = ['approved', 'created_at', 'publisher']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        """
        Automatically assigns the logged-in user as author
        if no author is set during article creation.
        """
        if not obj.pk and not obj.author_id:
            obj.author = request.user

        super().save_model(request, obj, form, change)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """
    Admin interface for Newsletter model.

    Allows editors and journalists to curate article collections.
    """

    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'description']
    filter_horizontal = ['articles']
