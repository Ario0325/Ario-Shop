from django.contrib import admin
from .models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent', 'menu_type', 'order', 'is_active', 'created_at']
    list_filter = ['menu_type', 'is_active', 'created_at']
    search_fields = ['title', 'url']
    list_editable = ['order', 'is_active']
    ordering = ['menu_type', 'order', 'id']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'url', 'parent', 'menu_type')
        }),
        ('تنظیمات', {
            'fields': ('order', 'is_active')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent')