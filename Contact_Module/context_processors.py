from django.core.cache import cache
from .models import ContactInfo


def contact_info(request):
    """اطلاعات تماس (آدرس، تلفن، شبکه‌های اجتماعی) در همه تمپلیت‌ها — با کش"""
    info = cache.get('contact_info_active')
    if info is None:
        info = ContactInfo.objects.filter(is_active=True).first()
        cache.set('contact_info_active', info, 60 * 15)
    return {'contact_info': info}