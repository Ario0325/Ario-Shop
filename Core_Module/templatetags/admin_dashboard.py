from django import template
from django.contrib import admin

from Core_Module import admin_stats

register = template.Library()

# Sidebar composition: every registered model still comes from admin.site, so new
# modules appear automatically inside the closest group.
NAV_GROUPS = (
    ('commerce', 'فروش و سفارش‌ها', ('Cart_Module',)),
    ('catalog', 'کاتالوگ محصولات', ('Products_Module',)),
    ('people', 'کاربران و دسترسی', ('Accounts_Module', 'auth')),
    ('content', 'محتوا و صفحات', ('AboutUs_Module', 'Contact_Module', 'Menu_Module')),
    ('system', 'تنظیمات', ('Core_Module',)),
)

APP_TITLES = {'auth': 'کاربران و دسترسی'}

MODEL_ORDER = {
    'Cart_Module': ('Order', 'DiscountCode', 'OrderItem'),
    'Products_Module': (
        'Product', 'Category', 'Brand', 'ProductReview',
        'ProductImage', 'ProductColor', 'ProductSize',
    ),
    'Accounts_Module': ('UserProfile', 'UserVerification', 'PasswordResetToken'),
    'auth': ('User', 'Group'),
    'AboutUs_Module': ('AboutPage', 'TeamMember', 'Testimonial', 'Brand'),
    'Contact_Module': ('ContactMessage', 'ContactInfo'),
    'Menu_Module': ('MenuItem',),
    'Core_Module': ('SiteSetting',),
}

MODEL_ICONS = {
    'Order': 'receipt',
    'DiscountCode': 'tag',
    'OrderItem': 'box',
    'Product': 'box',
    'Category': 'layers',
    'Brand': 'sparkle',
    'ProductReview': 'star',
    'ProductImage': 'image',
    'ProductColor': 'palette',
    'ProductSize': 'ruler',
    'UserProfile': 'user',
    'UserVerification': 'shield',
    'PasswordResetToken': 'key',
    'User': 'users',
    'Group': 'shield',
    'AboutPage': 'file',
    'TeamMember': 'users',
    'Testimonial': 'chat',
    'ContactMessage': 'mail',
    'ContactInfo': 'info',
    'MenuItem': 'menu',
    'SiteSetting': 'settings',
}

BADGE_KEYS = {
    'Order': 'pending_orders',
    'ProductReview': 'pending_reviews',
    'ContactMessage': 'unread_messages',
    'Product': 'out_of_stock',
}


def _ordered(models, app_label):
    order = MODEL_ORDER.get(app_label, ())
    return sorted(
        models,
        key=lambda model: order.index(model['object_name'])
        if model['object_name'] in order else len(order),
    )


@register.simple_tag(takes_context=True)
def admin_navigation(context):
    request = context.get('request')
    if request is None:
        return []

    apps = {app['app_label']: app for app in admin.site.get_app_list(request)}
    counts = admin_stats.alert_counts()
    path = request.path
    grouped_labels = set()

    groups = []
    for key, label, app_labels in NAV_GROUPS:
        group_apps = []
        for app_label in app_labels:
            app = apps.get(app_label)
            if not app:
                continue
            grouped_labels.add(app_label)
            models = []
            for model in _ordered(app['models'], app_label):
                object_name = model['object_name']
                badge_key = BADGE_KEYS.get(object_name)
                models.append({
                    'name': model['name'],
                    'object_name': object_name,
                    'url': model.get('admin_url'),
                    'add_url': model.get('add_url'),
                    'icon': MODEL_ICONS.get(object_name, 'file'),
                    'badge': counts.get(badge_key, 0) if badge_key else 0,
                    'active': bool(model.get('admin_url')) and path.startswith(model['admin_url']),
                })
            group_apps.append({
                'label': app_label,
                'title': APP_TITLES.get(app_label, app['name']),
                'models': models,
            })
        if group_apps:
            groups.append({'key': key, 'label': label, 'apps': group_apps})

    remaining = [
        app for label, app in apps.items()
        if label not in grouped_labels and app['models']
    ]
    if remaining:
        groups.append({
            'key': 'other',
            'label': 'سایر ماژول‌ها',
            'apps': [
                {
                    'label': app['app_label'],
                    'title': APP_TITLES.get(app['app_label'], app['name']),
                    'models': [
                        {
                            'name': model['name'],
                            'object_name': model['object_name'],
                            'url': model.get('admin_url'),
                            'add_url': model.get('add_url'),
                            'icon': MODEL_ICONS.get(model['object_name'], 'file'),
                            'badge': 0,
                            'active': bool(model.get('admin_url')) and path.startswith(model['admin_url']),
                        }
                        for model in _ordered(app['models'], app['app_label'])
                    ],
                }
                for app in remaining
            ],
        })
    return groups


@register.simple_tag
def admin_alerts():
    return admin_stats.alerts()


@register.simple_tag
def dashboard_stats(days=30):
    return admin_stats.period_stats(days)


@register.simple_tag
def dashboard_recent_orders():
    return admin_stats.recent_orders()


@register.simple_tag
def dashboard_low_stock():
    return admin_stats.low_stock_products()


@register.simple_tag
def dashboard_top_products(days=30):
    return admin_stats.top_products(days)


STATUS_META = {
    'pending': ('در انتظار پرداخت', 'warn'),
    'paid': ('پرداخت شده', 'info'),
    'processing': ('در حال پردازش', 'teal'),
    'shipped': ('ارسال شده', 'olive'),
    'delivered': ('تحویل شده', 'ok'),
    'cancelled': ('لغو شده', 'err'),
}


@register.filter
def status_label(value):
    return STATUS_META.get(value, (value, 'muted'))[0]


@register.filter
def status_tone(value):
    return STATUS_META.get(value, (value, 'muted'))[1]


@register.simple_tag
def jalali_today():
    from django.utils import timezone

    from Core_Module.utils import gregorian_to_jalali_long

    return gregorian_to_jalali_long(timezone.localdate()).translate(
        str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    )
