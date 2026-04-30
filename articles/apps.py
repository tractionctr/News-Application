"""
Django application configuration for the Articles app.

Registers the app and ensures signal handlers are loaded
when Django starts.
"""

from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    """
    Configuration class for the Articles Django app.

    Handles app initialization and ensures that signal
    handlers are imported and registered.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'articles'

    def ready(self):
        """
        Called when the Django app is fully loaded.

        Imports signal handlers so they are registered with
        Django's signal system.
        """
        import articles.signals
