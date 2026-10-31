from django.contrib import admin
from django.db import models
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils.html import format_html
import csv

from .models import Category, Brand, Product, ProductImage, ProductColor, ProductSize, ProductReview

from Core_Module.utils import gregorian_to_jalali, gregorian_to_jalali_long
from Core_Module.admin_widgets import JalaliDateWidget, JalaliDateTimeWidget
from Core_Module.admin_filters import DateRangeFilter, StockLevelFilter, PriceRangeFilter


def to_persian_date_admin(value):
    """تبدیل تاریخ به فرمت شمسی برای ادمین پنل"""
    return gregorian_to_jalali_long(value)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_main', 'order']


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Use Jalali date widgets
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }
    
    list_display = ['name', 'parent', 'is_active', 'products_count', 'created_at_persian']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    list_select_related = ['parent']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _products_count=Count(
                'products',
                filter=Q(products__is_active=True, products__is_available=True),
                distinct=True,
            )
        )

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    # Use Jalali date widgets
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }
    
    list_display = ['name', 'is_active', 'created_at_persian']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }
    
    list_display = ['thumbnail', 'name', 'category', 'brand', 'price', 'old_price', 'stock_bar', 'is_available', 'is_active', 'label',
                    'views_count']
    list_select_related = ['category', 'brand']
    list_filter = ['is_active', 'is_available', 'category', 'brand', 'label', StockLevelFilter, PriceRangeFilter, DateRangeFilter]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'is_available', 'is_active']
    inlines = [ProductImageInline, ProductColorInline, ProductSizeInline]
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    actions = ['bulk_activate', 'bulk_deactivate', 'export_csv']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'category', 'brand', 'label')
        }),
        ('توضیحات', {
            'fields': ('description', 'full_description', 'additional_info', 'shipping_info')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'old_price', 'stock', 'is_available')
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'views_count', 'created_at', 'updated_at')
        }),
    )

    @admin.display(description='تصویر')
    def thumbnail(self, obj):
        images = list(obj.images.all())
        main_img = next((img for img in images if img.is_main), images[0] if images else None)
        if main_img and main_img.image:
            return format_html(
                '<span class="adm-thumb"><img src="{}" alt=""></span>', main_img.image.url
            )
        return format_html('<span class="adm-thumb adm-thumb--empty">—</span>')

    @admin.display(description='موجودی')
    def stock_bar(self, obj):
        if obj.stock <= 0:
            state, label, pct = 'is-out', 'ناموجود', 0
        elif obj.stock <= 5:
            state, label, pct = 'is-low', f'{obj.stock} عدد', min(obj.stock * 5, 100)
        elif obj.stock <= 20:
            state, label, pct = '', f'{obj.stock} عدد', min(obj.stock * 3, 100)
        else:
            state, label, pct = '', f'{obj.stock} عدد', min(obj.stock * 2, 100)
        return format_html(
            '<span class="adm-stockwrap">'
            '<span class="adm-stockwrap__bar"><span class="adm-stockwrap__fill {}" style="width:{}%"></span></span>'
            '<span class="adm-stockwrap__text">{}</span>'
            '</span>',
            state, pct, label,
        )

    @admin.action(description='فعال‌سازی محصولات انتخاب شده')
    def bulk_activate(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} محصول فعال شد.')

    @admin.action(description='غیرفعال‌سازی محصولات انتخاب شده')
    def bulk_deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} محصول غیرفعال شد.')

    @admin.action(description='خروجی CSV محصولات')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename=products.csv'
        writer = csv.writer(response)
        writer.writerow(['نام', 'دسته‌بندی', 'برند', 'قیمت', 'موجودی', 'وضعیت'])
        for p in queryset.select_related('category', 'brand'):
            writer.writerow([p.name, p.category, p.brand, p.price, p.stock, 'فعال' if p.is_active else 'غیرفعال'])
        return response

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    # Use Jalali date widgets
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }
    
    list_display = ['product', 'is_main', 'order', 'created_at_persian']
    list_filter = ['is_main', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_main', 'order']

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'code', 'is_available']
    list_filter = ['is_available']
    search_fields = ['product__name', 'name']
    list_editable = ['is_available']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'is_available']
    list_filter = ['size', 'is_available']
    search_fields = ['product__name']
    list_editable = ['is_available']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }
    
    list_display = ['product', 'name', 'rating', 'approval_badge', 'created_at_persian']
    list_filter = ['is_approved', 'rating', DateRangeFilter]
    search_fields = ['product__name', 'name', 'email', 'comment']
    list_editable = []
    readonly_fields = ['created_at']
    actions = ['bulk_approve', 'bulk_reject']

    @admin.display(description='وضعیت')
    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html('<span class="adm-pill adm-pill--ok">تایید شده</span>')
        return format_html('<span class="adm-pill adm-pill--warn">در انتظار</span>')

    @admin.action(description='تایید نظرات انتخاب شده')
    def bulk_approve(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} نظر تایید شد.')

    @admin.action(description='رد نظرات انتخاب شده')
    def bulk_reject(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} نظر رد شد.')

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')
