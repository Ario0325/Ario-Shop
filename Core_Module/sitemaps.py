from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticSitemap(Sitemap):
    """Static pages that should stay discoverable regardless of catalog size."""

    def items(self):
        return [
            ('index', 1.0, 'daily'),
            ('products:list', 0.9, 'daily'),
            ('AboutUs_Module:about', 0.5, 'monthly'),
            ('contact', 0.5, 'monthly'),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]

    def changefreq(self, item):
        return item[2]
