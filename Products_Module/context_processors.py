"""
Context processors for Products Module
Provides global context data for all templates
"""

from django.core.cache import cache
from .models import Category


def navbar_categories(request):
    """
    Context processor to provide categories for navbar
    Returns only parent categories (where parent is None) that are active
    Cached for 15 minutes to reduce database queries
    """
    cache_key = 'navbar_categories'
    categories = cache.get(cache_key)
    
    if categories is None:
        categories = list(Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).prefetch_related('children').order_by('name'))
        # Cache for 15 minutes
        cache.set(cache_key, categories, 60 * 15)
    
    return {
        'navbar_categories': categories
    }
