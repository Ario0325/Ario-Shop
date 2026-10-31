from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta


class DateRangeFilter(SimpleListFilter):
    title = 'بازه زمانی'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return [
            ('today', 'امروز'),
            ('week', 'هفته اخیر'),
            ('month', 'ماه اخیر'),
            ('3months', '۳ ماه اخیر'),
            ('year', 'سال اخیر'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        ranges = {
            'today': timedelta(days=1),
            'week': timedelta(days=7),
            'month': timedelta(days=30),
            '3months': timedelta(days=90),
            'year': timedelta(days=365),
        }
        delta = ranges.get(self.value())
        if delta:
            return queryset.filter(created_at__gte=now - delta)
        return queryset


class StockLevelFilter(SimpleListFilter):
    title = 'سطح موجودی'
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return [
            ('out', 'ناموجود (۰)'),
            ('low', 'کم (۱-۵)'),
            ('medium', 'متوسط (۶-۲۰)'),
            ('high', 'زیاد (۲۱+)'),
        ]

    def queryset(self, request, queryset):
        mapping = {
            'out': queryset.filter(stock=0),
            'low': queryset.filter(stock__gte=1, stock__lte=5),
            'medium': queryset.filter(stock__gte=6, stock__lte=20),
            'high': queryset.filter(stock__gte=21),
        }
        return mapping.get(self.value(), queryset)


class PriceRangeFilter(SimpleListFilter):
    title = 'محدوده قیمت'
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return [
            ('under_500', 'زیر ۵۰۰ هزار تومان'),
            ('500_1m', '۵۰۰ هزار - ۱ میلیون'),
            ('1m_5m', '۱ - ۵ میلیون'),
            ('over_5m', 'بالای ۵ میلیون'),
        ]

    def queryset(self, request, queryset):
        mapping = {
            'under_500': queryset.filter(price__lt=500000),
            '500_1m': queryset.filter(price__gte=500000, price__lt=1000000),
            '1m_5m': queryset.filter(price__gte=1000000, price__lt=5000000),
            'over_5m': queryset.filter(price__gte=5000000),
        }
        return mapping.get(self.value(), queryset)
