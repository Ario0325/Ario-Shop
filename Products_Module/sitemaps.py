from django.contrib.sitemaps import Sitemap
from .models import Product, Category


class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True, is_available=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at
