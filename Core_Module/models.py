from django.core.cache import cache
from django.db import models

SITE_SETTINGS_CACHE_KEY = 'site_settings_singleton'


class SiteSetting(models.Model):
    show_newsletter_popup = models.BooleanField(
        default=True,
        verbose_name='نمایش پاپ‌آپ خبرنامه',
        help_text='در صورت غیرفعال بودن، پاپ‌آپ خبرنامه در سایت نمایش داده نمی‌شود.'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return 'تنظیمات سایت'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(SITE_SETTINGS_CACHE_KEY)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(SITE_SETTINGS_CACHE_KEY)

    @classmethod
    def load(cls):
        return cache.get_or_set(
            SITE_SETTINGS_CACHE_KEY,
            lambda: cls.objects.get_or_create(pk=1)[0],
            60 * 5,
        )
