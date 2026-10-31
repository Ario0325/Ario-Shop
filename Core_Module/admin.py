from django.contrib import admin
from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['show_newsletter_popup', 'updated_at']

    fieldsets = (
        ('تنظیمات پاپ‌آپ', {
            'fields': ('show_newsletter_popup',)
        }),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
