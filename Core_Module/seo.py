"""Helpers for building canonical, Open Graph and JSON-LD absolute URLs.

The site is reachable through several PythonAnywhere hostnames, so URLs that
search engines and social crawlers see must be pinned to one public origin
(``settings.SITE_BASE_URL``) instead of following the request Host header.
"""
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.utils.encoding import iri_to_uri


def site_base_url(request):
    """Pinned public origin, falling back to the current request host."""
    base = (getattr(settings, 'SITE_BASE_URL', '') or '').rstrip('/')
    if not base:
        base = f'{request.scheme}://{request.get_host()}'
    return base


def absolute_url(request, path='', params=None):
    """Build an absolute URL on the pinned origin.

    ``path`` may contain Persian slugs; it is IRI-encoded the same way Django
    encodes the sitemap and ``reverse()`` output. ``params`` is an optional
    mapping (or list of pairs) appended as a query string.
    """
    base = site_base_url(request)
    path = iri_to_uri(path or '/')
    if not path.startswith('/'):
        path = '/' + path
    url = urljoin(base + '/', path.lstrip('/'))
    if params:
        query = urlencode(params, doseq=True)
        if query:
            url += ('&' if '?' in url else '?') + query
    return url
