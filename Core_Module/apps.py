"""
Django App Configuration for Core Module
"""

from django.apps import AppConfig


class CoreModuleConfig(AppConfig):
    """Configuration for the Core Module."""
    
    name = 'Core_Module'
    verbose_name = 'ماژول هسته‌ای'
    
    def ready(self):
        """Initialize the app when Django starts."""
        # Import and register template tags
        pass
