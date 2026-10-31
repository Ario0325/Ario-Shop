from django.core.cache import cache
from .models import MenuItem


def menu_items(request):
    """Context processor for main menu items with caching"""
    cache_key = 'main_menu_items'
    main_menu = cache.get(cache_key)

    if main_menu is None:
        main_menu = list(MenuItem.objects.filter(
            menu_type='main',
            is_active=True,
            parent__isnull=True
        ).prefetch_related('children').order_by('order'))
        cache.set(cache_key, main_menu, 60 * 15)

    return {'main_menu_items': main_menu}