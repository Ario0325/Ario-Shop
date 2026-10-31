from django.contrib import admin
from django.utils.html import format_html
from .models import AboutPage, Brand, TeamMember, Testimonial


# ─────────────────────────────────────────────
# صفحه درباره ما (Singleton)
# ─────────────────────────────────────────────
@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    # نمایش فیلدها به صورت گروه‌بندی شده
    fieldsets = (
        ('── بخش دید ما ──', {
            'fields': ('vision_title', 'vision_description'),
        }),
        ('── بخش ماموریت ما ──', {
            'fields': ('mission_title', 'mission_description'),
        }),
        ('── بخش ما چه کسانی هستیم ──', {
            'fields': (
                'who_we_are_title',
                'who_we_are_subtitle',
                'who_we_are_description',
                'who_we_are_image_front',
                'who_we_are_image_back',
            ),
        }),
        ('── بخش برندها ──', {
            'fields': ('brands_title', 'brands_description'),
        }),
        ('── بخش تیم ──', {
            'fields': ('team_title',),
        }),
        ('── بخش نظرات ──', {
            'fields': ('testimonials_title',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)

    def changelist_view(self, request, extra_context=None):
        """
        به جای نمایش لیست، مستقیم به صفحه edit یک رکورد থابت رهنمود می‌دهد.
        """
        obj, created = AboutPage.objects.get_or_create(pk=1)
        from django.shortcuts import redirect
        return redirect(
            f'/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{obj.pk}/change/'
        )


# ─────────────────────────────────────────────
# برندها
# ─────────────────────────────────────────────
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_preview', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order',)

    def logo_preview(self, obj):
        """نمایش پیش‌نمایش لوگو در لیست"""
        if obj.logo:
            return format_html('<span class="adm-thumb adm-thumb--wide"><img src="{}" alt=""></span>', obj.logo.url)
        return '—'
    logo_preview.short_description = 'پیش‌نمایش لوگو'


# ─────────────────────────────────────────────
# اعضای تیم
# ─────────────────────────────────────────────
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'photo_preview', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'position')
    ordering = ('order',)

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'position', 'photo', 'bio'),
        }),
        ('شبکه‌های اجتماعی', {
            'classes': ('collapse',),
            'fields': ('facebook_url', 'twitter_url', 'instagram_url'),
        }),
        ('تنظیمات', {
            'fields': ('order', 'is_active'),
        }),
    )

    def photo_preview(self, obj):
        """نمایش پیش‌نمایش عکس در لیست"""
        if obj.photo:
            return format_html('<span class="adm-thumb adm-thumb--round"><img src="{}" alt=""></span>', obj.photo.url)
        return '—'
    photo_preview.short_description = 'پیش‌نمایش عکس'


# ─────────────────────────────────────────────
# نظرات مشتریان
# ─────────────────────────────────────────────
@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_role', 'photo_preview', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('customer_name', 'review')
    ordering = ('order',)

    def photo_preview(self, obj):
        """نمایش پیش‌نمایش عکس در لیست"""
        if obj.photo:
            return format_html('<span class="adm-thumb adm-thumb--round"><img src="{}" alt=""></span>', obj.photo.url)
        return '—'
    photo_preview.short_description = 'پیش‌نمایش عکس'