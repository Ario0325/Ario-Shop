"""Helpers for building catalogue URLs that keep the rest of the query string."""
from django import template

register = template.Library()


def _build(request, path, mutate):
    query = request.GET.copy()
    mutate(query)
    encoded = query.urlencode()
    return f'{path}?{encoded}' if encoded else path


@register.simple_tag
def query_url(request, path):
    """Current query string applied to another path."""
    return _build(request, path, lambda q: None)


@register.simple_tag
def query_remove(request, path, key):
    """Drop every value of a key (used by group-level filter chips)."""
    return _build(request, path, lambda q: q.pop(key, None))


@register.simple_tag
def query_set(request, path, key, value):
    """Replace a key, or remove it when the value is empty."""
    def mutate(q):
        if value in (None, ''):
            q.pop(key, None)
        else:
            q[key] = value
    return _build(request, path, mutate)


@register.simple_tag
def query_remove_value(request, path, key, value):
    """Drop one value from a multi-value key (brand/size/color chips)."""
    def mutate(q):
        values = [v for v in q.getlist(key) if v != str(value)]
        if values:
            q.setlist(key, values)
        else:
            q.pop(key, None)
    return _build(request, path, mutate)
