# -*- coding: utf-8 -*-
"""
تگ‌های قالب برای تاریخ شمسی
"""

import datetime as dt

from django import template
import jdatetime

register = template.Library()

# نام ماه‌های شمسی به فارسی
PERSIAN_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
]

# نام روزهای هفته به فارسی
PERSIAN_DAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']


def _convert_to_jdatetime(value):
    """کمکی برای تبدیل به datetime شمسی"""
    if not value:
        return None
    
    try:
        if isinstance(value, str):
            from django.utils.dateparse import parse_datetime
            value = parse_datetime(value)
        
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            value = dt.datetime.combine(value, dt.time.min)

        if value:
            return jdatetime.datetime.fromgregorian(datetime=value)
    except Exception:
        pass
    
    return None


@register.filter
def to_persian_date(value, format_string='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی با نام ماه فارسی
    
    استفاده: {{ date_value|to_persian_date }}
    خروجی پیش‌فرض: 1403/12/04
    
    فرمت‌های قابل استفاده:
    - %Y/%m/%d: 1403/12/04
    - %d %B %Y: 04 اسفند 1403
    - %d/%m/%Y: 04/12/1403
    """
    if not value:
        return ''
    
    jdate = _convert_to_jdatetime(value)
    if not jdate:
        return ''
    
    # جایگزینی نام ماه فارسی
    day = jdate.day
    month = PERSIAN_MONTHS[jdate.month - 1]
    year = jdate.year
    
    # پردازش فرمت
    result = format_string
    result = result.replace('%d', f'{day:02d}')
    result = result.replace('%B', month)
    result = result.replace('%Y', str(year))
    result = result.replace('%y', str(year)[-2:])
    result = result.replace('%m', f'{jdate.month:02d}')
    
    return result


@register.filter
def to_persian_datetime(value, format_string='%d %B %Y - %H:%M'):
    """
    تبدیل تاریخ و زمان میلادی به شمسی
    
    استفاده: {{ datetime_value|to_persian_datetime }}
    """
    if not value:
        return ''
    
    jdate = _convert_to_jdatetime(value)
    if not jdate:
        return ''
    
    day = jdate.day
    month = PERSIAN_MONTHS[jdate.month - 1]
    year = jdate.year
    hour = jdate.hour
    minute = jdate.minute
    
    result = format_string
    result = result.replace('%d', f'{day:02d}')
    result = result.replace('%B', month)
    result = result.replace('%Y', str(year))
    result = result.replace('%y', str(year)[-2:])
    result = result.replace('%H', f'{hour:02d}')
    result = result.replace('%M', f'{minute:02d}')
    
    return result


@register.filter
def to_persian_date_only(value):
    """
    تبدیل فقط تاریخ (بدون زمان) به شمسی
    
    استفاده: {{ date_value|to_persian_date_only }}
    خروجی: 2 اسفند 1404
    """
    return to_persian_date(value, '%d %B %Y')


@register.simple_tag
def get_persian_year():
    """
    دریافت سال جاری شمسی
    
    استفاده: {% get_persian_year %}
    """
    return jdatetime.datetime.now().year


@register.filter
def to_persian_time(value):
    """
    تبدیل زمان به فرمت فارسی
    
    استفاده: {{ time_value|to_persian_time }}
    """
    if not value:
        return ''
    
    jdate = _convert_to_jdatetime(value)
    if not jdate:
        return ''
    
    return f'{jdate.hour:02d}:{jdate.minute:02d}'


@register.filter
def to_persian_day_name(value):
    """
    دریافت نام روز هفته
    
    استفاده: {{ date_value|to_persian_day_name }}
    """
    if not value:
        return ''
    
    jdate = _convert_to_jdatetime(value)
    if not jdate:
        return ''
    
    # در jdatetime شنبه = 0
    return PERSIAN_DAYS[jdate.weekday()]


@register.filter
def to_persian_date_ymd(value):
    """
    تبدیل تاریخ به فرمت YYYY/MM/DD
    
    استفاده: {{ date_value|to_persian_date_ymd }}
    خروجی: 1403/12/04
    """
    if not value:
        return ''
    
    jdate = _convert_to_jdatetime(value)
    if not jdate:
        return ''
    
    return f'{jdate.year}/{jdate.month:02d}/{jdate.day:02d}'


@register.filter
def time_ago_persian(value):
    """
    تبدیل زمان به فرمت "فلان وقت پیش" به فارسی
    
    استفاده: {{ date_value|time_ago_persian }}
    خروجی: 2 ساعت پیش، 5 روز پیش
    """
    if not value:
        return ''
    
    from django.utils import timezone
    
    # اطمینان از timezone-aware
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    now = timezone.now()
    delta = now - value
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return 'همین الان'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} دقیقه پیش'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} ساعت پیش'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} روز پیش'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks} هفته پیش'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} ماه پیش'
    else:
        years = int(seconds / 31536000)
        return f'{years} سال پیش'
