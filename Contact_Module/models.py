from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام')
    email = models.EmailField(verbose_name='ایمیل')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='شماره موبایل')
    subject = models.CharField(max_length=200, blank=True, null=True, verbose_name='موضوع')
    message = models.TextField(verbose_name='پیام')
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ارسال')

    class Meta:
        verbose_name = 'پیام تماس'
        verbose_name_plural = 'پیام های تماس'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read', '-created_at'], name='contact_read_date_idx'),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class ContactInfo(models.Model):
    office_address = models.TextField(verbose_name='آدرس دفتر')
    email = models.EmailField(verbose_name='ایمیل')
    phone1 = models.CharField(max_length=15, verbose_name='تلفن اول')
    phone2 = models.CharField(max_length=15, blank=True, null=True, verbose_name='تلفن دوم')
    map_embed = models.TextField(verbose_name='کد iframe نقشه گوگل')
    facebook_url = models.URLField(blank=True, null=True, verbose_name='لینک فیسبوک')
    twitter_url = models.URLField(blank=True, null=True, verbose_name='لینک توییتر')
    instagram_url = models.URLField(blank=True, null=True, verbose_name='لینک اینستاگرام')
    youtube_url = models.URLField(blank=True, null=True, verbose_name='لینک یوتیوب')
    pinterest_url = models.URLField(blank=True, null=True, verbose_name='لینک پینترست')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'اطلاعات تماس'
        verbose_name_plural = 'اطلاعات تماس'

    def __str__(self):
        return f"اطلاعات تماس - {self.email}"

    def save(self, *args, **kwargs):
        if self.is_active:
            ContactInfo.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)