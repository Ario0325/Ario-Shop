from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
import csv
import jdatetime

from Core_Module.utils import gregorian_to_jalali, gregorian_to_jalali_long
from Core_Module.admin_widgets import JalaliDateWidget, JalaliDateTimeWidget
from Core_Module.admin_filters import DateRangeFilter

from .models import DiscountCode, Order, OrderItem


# Persian month names (kept for backward compatibility)
PERSIAN_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
]


def to_persian_date_admin(value):
    """تبدیل تاریخ به فرمت شمسی برای ادمین پنل"""
    return gregorian_to_jalali_long(value)


def to_persian_date_short(value):
    """تبدیل تاریخ به فرمت کوتاه شمسی برای ادمین پنل"""
    return gregorian_to_jalali(value)


# ─────────────────────────────────────────────────────────────────────────────
# فرم سفارشی برای DiscountCode با label و help_text فارسی
# ─────────────────────────────────────────────────────────────────────────────

class DiscountCodeAdminForm(forms.ModelForm):
    class Meta:
        model = DiscountCode
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ── اطلاعات پایه ──────────────────────────────────────────────────────
        self.fields['code'].label = 'کد'
        self.fields['code'].help_text = (
            'کد تخفیف را بدون فاصله وارد کنید. سیستم آن را خودکار به حروف بزرگ تبدیل می‌کند.'
        )
        self.fields['title'].label = 'عنوان'
        self.fields['title'].help_text = (
            'یک عنوان توصیفی برای این کد تخفیف وارد کنید. مثال: تخفیف ویژه نوروز'
        )
        self.fields['description'].label = 'توضیحات'
        self.fields['description'].help_text = 'توضیحات اضافی درباره این کد تخفیف (اختیاری).'

        # ── نوع و محدوده تخفیف ────────────────────────────────────────────────
        self.fields['discount_type'].label = 'نوع تخفیف'
        self.fields['discount_type'].help_text = (
            '«درصدی»: مثلاً ۱۰٪ از مبلغ کسر می‌شود. '
            '«مبلغ ثابت»: مبلغ مشخصی به تومان کسر می‌شود.'
        )
        self.fields['scope'].label = 'محدوده تخفیف'
        self.fields['scope'].help_text = (
            '«کل سبد خرید»: تخفیف روی مجموع سبد اعمال می‌شود. '
            '«محصول خاص»: تخفیف فقط روی قیمت یک محصول مشخص اعمال می‌شود.'
        )
        self.fields['product'].label = 'محصول مرتبط'
        self.fields['product'].help_text = (
            'فقط در صورتی که محدوده تخفیف «محصول خاص» باشد، این فیلد را پر کنید. '
            'در غیر این صورت خالی بگذارید.'
        )
        self.fields['value'].label = 'مقدار تخفیف'
        self.fields['value'].help_text = (
            'اگر نوع تخفیف «درصدی» است، عدد درصد را وارد کنید (مثلاً ۱۰ برای ۱۰٪). '
            'اگر «مبلغ ثابت» است، مبلغ به تومان وارد کنید (مثلاً ۵۰۰۰۰).'
        )
        self.fields['max_discount_amount'].label = 'سقف مبلغ تخفیف (تومان)'
        self.fields['max_discount_amount'].help_text = (
            'فقط برای تخفیف درصدی: حداکثر مبلغی که تخفیف می‌تواند داشته باشد. '
            'مثلاً اگر ۱۰٪ تخفیف با سقف ۵۰,۰۰۰ تومان، حتی اگر ۱۰٪ بیشتر شود، '
            'بیشتر از ۵۰,۰۰۰ تومان کسر نمی‌شود. برای تخفیف ثابت خالی بگذارید.'
        )

        # ── شرایط استفاده ─────────────────────────────────────────────────────
        self.fields['min_order_amount'].label = 'حداقل مبلغ سفارش (تومان)'
        self.fields['min_order_amount'].help_text = (
            'کاربر باید حداقل این مبلغ در سبد خرید داشته باشد تا بتواند از این کد استفاده کند. '
            'صفر یعنی بدون محدودیت مبلغ.'
        )
        self.fields['starts_at'].label = 'تاریخ شروع'
        self.fields['starts_at'].help_text = (
            'از چه تاریخ و ساعتی این کد فعال می‌شود. '
            'خالی بگذارید اگر از همین لحظه فعال باشد.'
        )
        self.fields['ends_at'].label = 'تاریخ انقضا'
        self.fields['ends_at'].help_text = (
            'تا چه تاریخ و ساعتی این کد معتبر است. '
            'خالی بگذارید اگر بدون تاریخ انقضا باشد.'
        )

        # ── محدودیت استفاده ───────────────────────────────────────────────────
        self.fields['usage_limit_total'].label = 'سقف کل استفاده'
        self.fields['usage_limit_total'].help_text = (
            'حداکثر چند بار این کد می‌تواند توسط همه کاربران استفاده شود. '
            'خالی بگذارید برای بدون محدودیت.'
        )
        self.fields['usage_limit_per_user'].label = 'سقف استفاده هر کاربر'
        self.fields['usage_limit_per_user'].help_text = (
            'هر کاربر حداکثر چند بار می‌تواند از این کد استفاده کند. '
            'خالی بگذارید برای بدون محدودیت.'
        )

        # ── وضعیت ─────────────────────────────────────────────────────────────
        self.fields['is_active'].label = 'فعال'
        self.fields['is_active'].help_text = (
            'اگر غیرفعال باشد، کاربران نمی‌توانند از این کد استفاده کنند.'
        )

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get('scope')
        product = cleaned_data.get('product')
        discount_type = cleaned_data.get('discount_type')
        value = cleaned_data.get('value')
        starts_at = cleaned_data.get('starts_at')
        ends_at = cleaned_data.get('ends_at')

        if scope == DiscountCode.SCOPE_PRODUCT and not product:
            self.add_error('product', 'برای تخفیف محصول خاص، باید یک محصول انتخاب کنید.')

        if discount_type == DiscountCode.TYPE_PERCENT and value and value > 100:
            self.add_error('value', 'درصد تخفیف نمی‌تواند بیشتر از ۱۰۰ باشد.')

        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error('ends_at', 'تاریخ انقضا باید بعد از تاریخ شروع باشد.')

        return cleaned_data


# ─────────────────────────────────────────────────────────────────────────────
# DiscountCodeAdmin
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    form = DiscountCodeAdminForm

    # Use Jalali date widgets for date fields
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }

    list_display = (
        'code',
        'title',
        'discount_type_badge',
        'scope_badge',
        'product',
        'value_display',
        'used_count',
        'usage_limit_total',
        'is_active_badge',
        'validity_status',
        'ends_at_persian',
    )
    list_filter = ('is_active', 'discount_type', 'scope')
    search_fields = ('code', 'title', 'description', 'product__name')
    readonly_fields = ('used_count', 'created_at', 'updated_at', 'usage_stats_display')
    ordering = ('-created_at',)

    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('code', 'title', 'description'),
            'description': 'اطلاعات اصلی کد تخفیف را وارد کنید.',
        }),
        ('نوع و محدوده تخفیف', {
            'fields': ('discount_type', 'scope', 'product', 'value', 'max_discount_amount'),
            'description': (
                'نوع تخفیف (درصدی یا ثابت) و محدوده آن (کل سبد یا محصول خاص) را مشخص کنید. '
                'اگر محدوده «محصول خاص» است، حتماً محصول مورد نظر را انتخاب کنید.'
            ),
        }),
        ('شرایط استفاده', {
            'fields': ('min_order_amount', 'starts_at', 'ends_at'),
            'description': 'شرایط لازم برای استفاده از این کد تخفیف را تعیین کنید.',
        }),
        ('محدودیت استفاده', {
            'fields': ('usage_limit_total', 'usage_limit_per_user'),
            'description': 'تعداد دفعات مجاز استفاده از این کد را محدود کنید.',
        }),
        ('وضعیت و آمار', {
            'fields': ('is_active', 'used_count', 'usage_stats_display', 'created_at', 'updated_at'),
            'description': 'وضعیت فعال/غیرفعال و آمار استفاده از این کد.',
        }),
    )

    class Media:
        js = ('admin/js/discount_code_admin.js',)

    # ── نمایش‌های سفارشی در list_display ─────────────────────────────────────

    @admin.display(description='نوع تخفیف')
    def discount_type_badge(self, obj):
        if obj.discount_type == DiscountCode.TYPE_PERCENT:
            return format_html('<span class="adm-pill adm-pill--info">{}</span>', 'درصدی')
        return format_html('<span class="adm-pill adm-pill--ok">{}</span>', 'مبلغ ثابت')

    @admin.display(description='محدوده')
    def scope_badge(self, obj):
        if obj.scope == DiscountCode.SCOPE_CART:
            return format_html('<span class="adm-pill adm-pill--brass">{}</span>', 'کل سبد')
        return format_html('<span class="adm-pill adm-pill--muted">{}</span>', 'محصول خاص')

    @admin.display(description='مقدار')
    def value_display(self, obj):
        if obj.discount_type == DiscountCode.TYPE_PERCENT:
            text = f'{obj.value}٪'
            if obj.max_discount_amount:
                text += f' (سقف: {obj.max_discount_amount:,.0f} ت)'
        else:
            text = f'{obj.value:,.0f} تومان'
        return text

    @admin.display(description='وضعیت', boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="adm-pill adm-pill--ok">فعال</span>')
        return format_html('<span class="adm-pill adm-pill--err">غیرفعال</span>')

    @admin.display(description='اعتبار زمانی')
    def validity_status(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return format_html('<span class="adm-pill adm-pill--muted">غیرفعال</span>')
        if obj.starts_at and now < obj.starts_at:
            return format_html('<span class="adm-pill adm-pill--warn">هنوز شروع نشده</span>')
        if obj.ends_at and now > obj.ends_at:
            return format_html('<span class="adm-pill adm-pill--err">منقضی شده</span>')
        return format_html('<span class="adm-pill adm-pill--ok">معتبر</span>')

    @admin.display(description='تاریخ انقضا', ordering='ends_at')
    def ends_at_persian(self, obj):
        return to_persian_date_admin(obj.ends_at)

    @admin.display(description='آمار استفاده')
    def usage_stats_display(self, obj):
        if not obj.pk:
            return '—'

        stats = obj.orders.aggregate(total_orders=Count('id'), total_discount=Sum('discount_amount'))
        total_orders = stats['total_orders'] or 0
        unique_users = obj.orders.values('user').distinct().count()
        total_discount_formatted = f'{int(stats["total_discount"] or 0):,}'

        return format_html(
            '<div class="adm-stats">'
            '<div class="adm-stats__row"><span>تعداد کل سفارش‌های استفاده‌شده</span><strong>{}</strong></div>'
            '<div class="adm-stats__row"><span>تعداد کاربران منحصربه‌فرد</span><strong>{}</strong></div>'
            '<div class="adm-stats__row"><span>مجموع تخفیف داده‌شده</span><strong>{} تومان</strong></div>'
            '</div>',
            total_orders,
            unique_users,
            total_discount_formatted,
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


# ─────────────────────────────────────────────────────────────────────────────
# OrderItemInline و OrderAdmin
# ─────────────────────────────────────────────────────────────────────────────

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)
    readonly_fields = ('total',)
    fields = ('product', 'product_name', 'quantity', 'price', 'total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }

    list_display = (
        'order_number',
        'full_name',
        'subtotal_display',
        'discount_code',
        'discount_amount_display',
        'total',
        'status_badge',
        'created_at_persian',
    )
    list_filter = ('status', DateRangeFilter)
    search_fields = ('order_number', 'full_name', 'phone')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    actions = ['bulk_mark_shipped', 'bulk_mark_delivered', 'export_orders_csv']

    STATUS_META = {
        'pending':    ('warn', 'در انتظار'),
        'paid':       ('ok', 'پرداخت شده'),
        'processing': ('info', 'در حال پردازش'),
        'shipped':    ('teal', 'ارسال شده'),
        'delivered':  ('ok', 'تحویل داده شده'),
        'cancelled':  ('err', 'لغو شده'),
    }

    @admin.display(description='وضعیت')
    def status_badge(self, obj):
        tone, label = self.STATUS_META.get(obj.status, ('muted', obj.get_status_display()))
        return format_html('<span class="adm-pill adm-pill--{}">{}</span>', tone, label)

    @admin.action(description='علامت‌گذاری ارسال شده')
    def bulk_mark_shipped(self, request, queryset):
        count = queryset.filter(status__in=['paid', 'processing']).update(status='shipped')
        self.message_user(request, f'{count} سفارش ارسال شد.')

    @admin.action(description='علامت‌گذاری تحویل داده شده')
    def bulk_mark_delivered(self, request, queryset):
        count = queryset.filter(status='shipped').update(status='delivered')
        self.message_user(request, f'{count} سفارش تحویل داده شد.')

    @admin.action(description='خروجی CSV سفارشات')
    def export_orders_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename=orders.csv'
        writer = csv.writer(response)
        writer.writerow(['شماره سفارش', 'نام مشتری', 'تلفن', 'مبلغ کل', 'وضعیت', 'تاریخ'])
        for o in queryset:
            writer.writerow([o.order_number, o.full_name, o.phone, o.total, o.get_status_display(), o.created_at])
        return response

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'discount_code')

    @admin.display(description='تاریخ ثبت', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at)

    @admin.display(description='جمع قبل از تخفیف')
    def subtotal_display(self, obj):
        if obj.subtotal:
            return f'{obj.subtotal:,.0f} تومان'
        return '—'

    @admin.display(description='مبلغ تخفیف')
    def discount_amount_display(self, obj):
        if obj.discount_amount and float(obj.discount_amount) > 0:
            formatted_amount = f'{int(obj.discount_amount):,}'
            return format_html(
                '<span class="adm-pill adm-pill--err adm-pill--plain">− {} تومان</span>',
                formatted_amount,
            )
        return '—'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'price', 'total')
    list_filter = ('order',)
