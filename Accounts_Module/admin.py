from django.contrib import admin
from django.db import models
from .models import UserProfile, UserVerification, PasswordResetToken

# Use Core_Module utilities for date conversion
from Core_Module.utils import gregorian_to_jalali_long
from Core_Module.admin_widgets import JalaliDateWidget, JalaliDateTimeWidget


def to_persian_date_admin(value):
    """تبدیل تاریخ به فرمت شمسی برای ادمین پنل"""
    return gregorian_to_jalali_long(value)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # Use Jalali date widgets for date fields
    formfield_overrides = {
        models.DateTimeField: {'widget': JalaliDateTimeWidget},
        models.DateField: {'widget': JalaliDateWidget},
    }
    
    list_display = ('user', 'full_name', 'phone', 'city', 'created_at_persian')
    search_fields = ('full_name', 'phone', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='تاریخ ثبت نام', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at) if obj.created_at else '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'created_at_persian', 'expires_at_persian')
    list_filter = ('is_verified',)
    search_fields = ('user__email',)
    readonly_fields = ('code', 'created_at')

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at) if obj.created_at else '—'

    @admin.display(description='تاریخ انقضا', ordering='expires_at')
    def expires_at_persian(self, obj):
        return to_persian_date_admin(obj.expires_at) if obj.expires_at else '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'created_at_persian', 'expires_at_persian')
    list_filter = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('code', 'created_at')

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_persian(self, obj):
        return to_persian_date_admin(obj.created_at) if obj.created_at else '—'

    @admin.display(description='تاریخ انقضا', ordering='expires_at')
    def expires_at_persian(self, obj):
        return to_persian_date_admin(obj.expires_at) if obj.expires_at else '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
