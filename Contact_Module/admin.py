from django.contrib import admin
from .models import ContactMessage, ContactInfo


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات فرستنده', {
            'fields': ('name', 'email', 'phone')
        }),
        ('محتوای پیام', {
            'fields': ('subject', 'message')
        }),
        ('وضعیت', {
            'fields': ('is_read', 'created_at')
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone1', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['email', 'office_address']

    fieldsets = (
        ('اطلاعات دفتر', {
            'fields': ('office_address', 'email', 'phone1', 'phone2')
        }),
        ('نقشه', {
            'fields': ('map_embed',)
        }),
        ('شبکه های اجتماعی', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'youtube_url', 'pinterest_url')
        }),
        ('تنظیمات', {
            'fields': ('is_active',)
        }),
    )

    def has_add_permission(self, request):
        return not ContactInfo.objects.exists()
