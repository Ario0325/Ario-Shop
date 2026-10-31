"""Admin dashboard aggregates shared by the template tag and the JSON API."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

PAID_STATUSES = ('paid', 'processing', 'shipped', 'delivered')
VALID_RANGES = (7, 30, 90)


def normalize_days(value):
    try:
        days = int(value)
    except (TypeError, ValueError):
        return 30
    return days if days in VALID_RANGES else 30


def _revenue(queryset):
    return int(queryset.aggregate(total=Sum('total'))['total'] or 0)


def _delta(current, previous):
    if not previous:
        return 100 if current else 0
    return round((current - previous) / previous * 100)


def period_stats(days=30):
    from Cart_Module.models import Order
    from Contact_Module.models import ContactMessage
    from Products_Module.models import Product, ProductReview

    days = normalize_days(days)
    now = timezone.now()
    start = now - timedelta(days=days)
    previous_start = start - timedelta(days=days)

    current = Order.objects.filter(created_at__gte=start, status__in=PAID_STATUSES)
    previous = Order.objects.filter(
        created_at__gte=previous_start, created_at__lt=start, status__in=PAID_STATUSES
    )

    revenue = _revenue(current)
    previous_revenue = _revenue(previous)
    order_count = current.count()
    previous_order_count = previous.count()
    aov = round(revenue / order_count) if order_count else 0
    previous_aov = round(previous_revenue / previous_order_count) if previous_order_count else 0

    User = get_user_model()
    new_customers = User.objects.filter(date_joined__gte=start).count()
    previous_customers = User.objects.filter(
        date_joined__gte=previous_start, date_joined__lt=start
    ).count()

    return {
        'days': days,
        'revenue': revenue,
        'revenue_delta': _delta(revenue, previous_revenue),
        'orders': order_count,
        'orders_delta': _delta(order_count, previous_order_count),
        'aov': aov,
        'aov_delta': _delta(aov, previous_aov),
        'new_customers': new_customers,
        'new_customers_delta': _delta(new_customers, previous_customers),
        'total_products': Product.objects.filter(is_active=True).count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'pending_reviews': ProductReview.objects.filter(is_approved=False).count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'low_stock': Product.objects.filter(is_active=True, stock__lte=5).count(),
    }


def sales_series(days=30):
    from Cart_Module.models import Order

    days = normalize_days(days)
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    rows = (
        Order.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end,
            status__in=PAID_STATUSES,
        )
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total'), count=Count('id'))
    )
    by_day = {row['day']: row for row in rows}
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = by_day.get(day)
        series.append({
            'date': day.isoformat(),
            'total': int(row['total'] or 0) if row else 0,
            'count': row['count'] if row else 0,
        })
    return series


def status_breakdown():
    from Cart_Module.models import Order

    return [
        {'status': row['status'], 'count': row['count']}
        for row in Order.objects.values('status').annotate(count=Count('id'))
    ]


def top_products(days=30, limit=5):
    from Cart_Module.models import OrderItem

    days = normalize_days(days)
    start = timezone.now() - timedelta(days=days)
    rows = (
        OrderItem.objects.filter(
            order__created_at__gte=start, order__status__in=PAID_STATUSES
        )
        .values('product_id', 'product_name')
        .annotate(sold=Sum('quantity'), revenue=Sum('total'))
        .order_by('-sold')[:limit]
    )
    return [
        {
            'product_id': row['product_id'],
            'name': row['product_name'],
            'sold': row['sold'] or 0,
            'revenue': int(row['revenue'] or 0),
        }
        for row in rows
    ]


def recent_orders(limit=8):
    from Cart_Module.models import Order

    return Order.objects.select_related('user').order_by('-created_at')[:limit]


def low_stock_products(limit=6):
    from Products_Module.models import Product

    return (
        Product.objects.filter(is_active=True, stock__lte=5)
        .select_related('category')
        .order_by('stock', '-created_at')[:limit]
    )


def alert_counts():
    """Counts for the sidebar badges and the notification centre (60s cache)."""
    cached = cache.get('ario_admin_alerts')
    if cached is not None:
        return cached

    from Cart_Module.models import Order
    from Contact_Module.models import ContactMessage
    from Products_Module.models import Product, ProductReview

    counts = {
        'pending_orders': Order.objects.filter(status='pending').count(),
        'pending_reviews': ProductReview.objects.filter(is_approved=False).count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'out_of_stock': Product.objects.filter(is_active=True, stock=0).count(),
    }
    cache.set('ario_admin_alerts', counts, 60)
    return counts


def alerts():
    counts = alert_counts()
    items = [
        {
            'key': 'orders',
            'label': 'سفارش در انتظار پرداخت',
            'count': counts['pending_orders'],
            'url': reverse('admin:Cart_Module_order_changelist') + '?status__exact=pending',
            'tone': 'warn',
            'icon': 'clock',
        },
        {
            'key': 'reviews',
            'label': 'نظر در انتظار تایید',
            'count': counts['pending_reviews'],
            'url': reverse('admin:Products_Module_productreview_changelist') + '?is_approved__exact=0',
            'tone': 'info',
            'icon': 'star',
        },
        {
            'key': 'messages',
            'label': 'پیام خوانده‌نشده',
            'count': counts['unread_messages'],
            'url': reverse('admin:Contact_Module_contactmessage_changelist') + '?is_read__exact=0',
            'tone': 'accent',
            'icon': 'mail',
        },
        {
            'key': 'stock',
            'label': 'محصول ناموجود',
            'count': counts['out_of_stock'],
            'url': reverse('admin:Products_Module_product_changelist') + '?stock_level=out',
            'tone': 'danger',
            'icon': 'alert',
        },
    ]
    return {'items': items, 'total': sum(item['count'] for item in items)}
