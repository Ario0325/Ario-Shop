from .models import SiteSetting
from .seo import absolute_url, site_base_url


def site_settings(request):
    return {
        'site_settings': SiteSetting.load(),
    }


def seo(request):
    """Default SEO values for the shared <head>.

    Catalog views override ``seo_canonical``/``seo_robots`` with page-aware
    values; everything else (product detail, home, static pages) can use the
    clean path without query parameters.
    """
    match = getattr(request, 'resolver_match', None)
    namespace = getattr(match, 'namespace', '') or ''
    private = namespace in ('cart', 'accounts')
    return {
        'seo_canonical': absolute_url(request, request.path),
        'seo_base_url': site_base_url(request),
        'seo_robots': 'noindex, follow' if private else 'index, follow',
    }
