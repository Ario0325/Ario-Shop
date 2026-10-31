from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache
from django.db.models import Count, Q
from Products_Module.models import Product, Category


def index(request):
    """صفحه اصلی با کشینگ برای بهبود عملکرد"""

    # کش برای محصولات جدید (5 دقیقه)
    new_products_cache_key = 'home_new_products'
    new_products = cache.get(new_products_cache_key)
    if new_products is None:
        new_products = list(Product.objects.filter(
            is_active=True,
            is_available=True
        ).for_cards().order_by('-created_at')[:8])
        cache.set(new_products_cache_key, new_products, 60 * 5)  # 5 minutes

    # کش برای محصولات پرفروش (10 دقیقه)
    trending_products_cache_key = 'home_trending_products'
    trending_products = cache.get(trending_products_cache_key)
    if trending_products is None:
        trending_products = list(Product.objects.filter(
            is_active=True,
            is_available=True
        ).for_cards().order_by('-views_count')[:8])
        cache.set(trending_products_cache_key, trending_products, 60 * 10)  # 10 minutes

    # کش برای دسته‌بندی‌های اصلی (15 دقیقه)
    categories_cache_key = 'home_main_categories'
    main_categories = cache.get(categories_cache_key)
    if main_categories is None:
        main_categories = list(Category.objects.filter(
            is_active=True,
            parent=None
        ).annotate(
            active_product_count=Count('products', filter=Q(products__is_active=True, products__is_available=True))
        )[:6])
        cache.set(categories_cache_key, main_categories, 60 * 15)  # 15 minutes

    context = {
        'new_products': new_products,
        'trending_products': trending_products,
        'main_categories': main_categories,
    }

    return render(request, 'Home_Module/index.html', context)


def robots_txt(request):
    """Generate robots.txt for search engine crawlers"""
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /accounts/',
        'Disallow: /cart/',
        'Disallow: /admin/core/',
        '',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')