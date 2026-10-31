from django import template

from Core_Module.thumbnails import thumb_url as _thumb_url

register = template.Library()


@register.simple_tag
def thumb_url(image_field, width=480, quality=76):
    return _thumb_url(image_field, width=width, quality=quality)
