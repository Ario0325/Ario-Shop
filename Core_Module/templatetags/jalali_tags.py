"""
Persian (Jalali) Calendar Template Tags
"""

from django import template

from Core_Module.utils import gregorian_to_jalali

register = template.Library()


@register.filter
def to_jalali(value):
    """Convert a datetime or date to Persian short date format (YYYY/MM/DD)."""
    return gregorian_to_jalali(value)
