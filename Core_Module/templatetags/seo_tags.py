"""JSON-LD structured data for the storefront.

All URLs are built on the pinned public origin (``SITE_BASE_URL``) so the
markup stays consistent across the extra PythonAnywhere hostnames.
"""
import json

from django import template
from django.templatetags.static import static
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from Core_Module.seo import absolute_url, site_base_url

register = template.Library()

DEFAULT_IMAGE = 'assets/images/icons/apple-touch-icon.png'
SOCIAL_FIELDS = (
    'instagram_url',
    'facebook_url',
    'twitter_url',
    'youtube_url',
    'pinterest_url',
)


def _json_ld(data):
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    # Never let user content close the script element.
    payload = payload.replace('<', '\\u003C').replace('>', '\\u003E').replace('&', '\\u0026')
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


@register.simple_tag(takes_context=True)
def organization_jsonld(context):
    request = context.get('request')
    if request is None:
        return ''
    base = site_base_url(request)
    info = context.get('contact_info')
    data = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        '@id': f'{base}/#organization',
        'name': 'آریو شاپ',
        'url': f'{base}/',
        'logo': f'{base}{static(DEFAULT_IMAGE)}',
    }
    if info is not None:
        same_as = [
            getattr(info, field, '')
            for field in SOCIAL_FIELDS
            if getattr(info, field, '')
        ]
        if same_as:
            data['sameAs'] = same_as
        contact = {}
        phone = getattr(info, 'phone1', '')
        email = getattr(info, 'email', '')
        if phone:
            contact['telephone'] = phone
        if email:
            contact['email'] = email
        if contact:
            contact['@type'] = 'ContactPoint'
            contact['contactType'] = 'customer service'
            data['contactPoint'] = contact
    return _json_ld(data)


@register.simple_tag(takes_context=True)
def website_jsonld(context):
    request = context.get('request')
    if request is None:
        return ''
    base = site_base_url(request)
    data = {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        '@id': f'{base}/#website',
        'name': 'آریو شاپ',
        'url': f'{base}/',
        'inLanguage': 'fa-IR',
    }
    return _json_ld(data)


@register.simple_tag(takes_context=True)
def product_jsonld(context):
    product = context.get('product')
    request = context.get('request')
    if product is None or request is None:
        return ''

    base = site_base_url(request)
    canonical = absolute_url(request, product.get_absolute_url())

    images = []
    for image in (context.get('product_images') or [])[:3]:
        try:
            images.append(f'{base}{image.image.url}')
        except (ValueError, AttributeError):
            continue
    if not images:
        images = [f'{base}{static(DEFAULT_IMAGE)}']

    data = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': product.name,
        'image': images,
        'sku': str(product.pk),
        'url': canonical,
        'offers': {
            '@type': 'Offer',
            'url': canonical,
            # Prices are stored in Toman; IRR is the ISO 4217 code and
            # 1 Toman = 10 Rial, so keep the conversion in one place.
            'price': str(int(product.price) * 10),
            'priceCurrency': 'IRR',
            'availability': (
                'https://schema.org/InStock'
                if product.is_available and product.stock > 0
                else 'https://schema.org/OutOfStock'
            ),
            'itemCondition': 'https://schema.org/NewCondition',
        },
    }

    description = ' '.join(strip_tags(product.description or '').split())
    if description:
        data['description'] = description[:500]
    if product.brand_id and product.brand:
        data['brand'] = {'@type': 'Brand', 'name': product.brand.name}
    if product.category_id and product.category:
        data['category'] = product.category.name

    review_count = int(getattr(product, 'review_count', 0) or 0)
    rating = float(product.average_rating or 0)
    if review_count > 0 and rating > 0:
        data['aggregateRating'] = {
            '@type': 'AggregateRating',
            'ratingValue': round(rating, 1),
            'reviewCount': review_count,
            'bestRating': 5,
            'worstRating': 1,
        }

    return _json_ld(data)
