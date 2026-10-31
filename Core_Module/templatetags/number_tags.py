"""Display filters for Persian money formatting.

Django's ``fa-ir`` locale ships without a thousand separator, so ``intcomma``
is a no-op here. These filters give the storefront consistent, idiomatic
Persian numbers instead.

Usage::

    {% load number_tags %}
    {{ product.price|toman }}          ->  ۴۲۰٬۰۰۰ تومان
    {{ product.price|ar_digits }}      ->  ۴۲۰٬۰۰۰
"""
from django import template

register = template.Library()

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_GROUP_SEP = "\u066c"  # ٬ Arabic thousands separator, standard in Persian typography


def _group(value):
    """Return the integer part of ``value`` grouped by threes, or None."""
    if value is None or value == "":
        return None
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    sign = "-" if number < 0 else ""
    return sign + f"{abs(number):,}".replace(",", _GROUP_SEP)


@register.filter(name="ar_digits")
def ar_digits(value):
    """Group a number and render it with Persian digits.

    Falls back to the original value when it is not numeric, so it is always
    safe to apply in templates.
    """
    grouped = _group(value)
    if grouped is None:
        return value
    return grouped.translate(_PERSIAN_DIGITS)


@register.filter(name="fa_digits")
def fa_digits(value):
    """Translate every Latin digit inside a string to its Persian form.

    Unlike ``ar_digits`` it leaves grouping alone, so it can be chained after
    date filters (``{{ order.created_at|to_persian_date|fa_digits }}``).
    """
    if value is None or value == "":
        return value
    return str(value).translate(_PERSIAN_DIGITS)


@register.filter(name="toman")
def toman(value, currency="تومان"):
    """Grouped Persian price plus a currency label."""
    grouped = _group(value)
    if grouped is None:
        return value
    return f"{grouped.translate(_PERSIAN_DIGITS)} {currency}"
