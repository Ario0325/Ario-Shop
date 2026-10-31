"""
Persian (Jalali) Calendar Utilities for Ario Shop

All dates in the database remain in Gregorian format; conversion happens
only at the presentation layer.
"""

import jdatetime
from datetime import datetime, date
from typing import Union


PERSIAN_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
]

PERSIAN_WEEKDAYS = [
    'شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'
]


def gregorian_to_jalali(
    dt: Union[datetime, date],
    include_time: bool = False,
    include_weekday: bool = False
) -> str:
    """
    Convert a Gregorian datetime/date to Persian (Jalali) string.

    Examples:
        >>> gregorian_to_jalali(datetime(2025, 2, 23))
        '1403/12/04'
        >>> gregorian_to_jalali(datetime(2025, 2, 23), include_time=True)
        '1403/12/04 14:30'
    """
    if not dt:
        return ''

    if isinstance(dt, datetime):
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        date_str = f'{jd.year}/{jd.month:02d}/{jd.day:02d}'

        if include_time:
            date_str += f' {jd.hour:02d}:{jd.minute:02d}'

        if include_weekday:
            date_str = f'{PERSIAN_WEEKDAYS[jd.weekday()]} {date_str}'

    elif isinstance(dt, date):
        jd = jdatetime.date.fromgregorian(date=dt)
        date_str = f'{jd.year}/{jd.month:02d}/{jd.day:02d}'

        if include_weekday:
            date_str = f'{PERSIAN_WEEKDAYS[jd.weekday()]} {date_str}'
    else:
        return str(dt)

    return date_str


def gregorian_to_jalali_long(
    dt: Union[datetime, date],
    include_time: bool = False
) -> str:
    """
    Convert a Gregorian datetime/date to long Persian format.

    Examples:
        >>> gregorian_to_jalali_long(datetime(2025, 2, 23))
        '04 اسفند 1403'
    """
    if not dt:
        return ''

    if isinstance(dt, datetime):
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        date_str = f'{jd.day} {PERSIAN_MONTHS[jd.month - 1]} {jd.year}'

        if include_time:
            date_str += f' - ساعت {jd.hour:02d}:{jd.minute:02d}'

    elif isinstance(dt, date):
        jd = jdatetime.date.fromgregorian(date=dt)
        date_str = f'{jd.day} {PERSIAN_MONTHS[jd.month - 1]} {jd.year}'
    else:
        return str(dt)

    return date_str
