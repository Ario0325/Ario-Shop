from django.db import models

from Core_Module.images import optimize_uploaded_fields


# ─────────────────────────────────────────────
# مدل صفحه درباره ما (تنهایی - یک رکورد)
# ─────────────────────────────────────────────
class AboutPage(models.Model):
    """
    تنها یک رکورد از این مدل وجود داشته باشد.
    شامل: دید ما، ماموریت ما، متن بخش "ما چه کسانی هستیم"
    """
    # ── دید ما ──
    vision_title = models.CharField(
        max_length=100,
        default='دید ما',
        verbose_name='عنوان بخش دید ما',
    )
    vision_description = models.TextField(
        verbose_name='متن بخش دید ما',
        blank=True,
    )

    # ── ماموریت ما ──
    mission_title = models.CharField(
        max_length=100,
        default='ماموریت ما',
        verbose_name='عنوان بخش ماموریت ما',
    )
    mission_description = models.TextField(
        verbose_name='متن بخش ماموریت ما',
        blank=True,
    )

    # ── ما چه کسانی هستیم ──
    who_we_are_title = models.CharField(
        max_length=100,
        default='ما چه کسانی هستیم',
        verbose_name='عنوان بخش ما چه کسانی هستیم',
    )
    who_we_are_subtitle = models.TextField(
        verbose_name='زیر عنوان (متن رنگی)',
        blank=True,
    )
    who_we_are_description = models.TextField(
        verbose_name='متن بخش ما چه کسانی هستیم',
        blank=True,
    )
    who_we_are_image_front = models.ImageField(
        upload_to='aboutus/who_we_are/',
        verbose_name='تصویر جلو',
        blank=True,
        null=True,
    )
    who_we_are_image_back = models.ImageField(
        upload_to='aboutus/who_we_are/',
        verbose_name='تصویر پشت',
        blank=True,
        null=True,
    )

    # ── متن بخش برندها ──
    brands_title = models.CharField(
        max_length=100,
        default='برند های معروفی که با ما در حال همکاری هستند.',
        verbose_name='عنوان بخش برندها',
    )
    brands_description = models.TextField(
        verbose_name='متن بخش برندها',
        blank=True,
    )

    # ── عنوان تیم ──
    team_title = models.CharField(
        max_length=100,
        default='آشنایی با تیم ما',
        verbose_name='عنوان بخش تیم',
    )

    # ── عنوان نظرات ──
    testimonials_title = models.CharField(
        max_length=100,
        default='نظرات مشتری های فروشگاه',
        verbose_name='عنوان بخش نظرات',
    )

    class Meta:
        verbose_name = 'صفحه درباره ما'
        verbose_name_plural = 'صفحه درباره ما'

    def __str__(self):
        return 'تنظیمات صفحه درباره ما'

    def save(self, *args, **kwargs):
        """فقط یک رکورد از این مدل اجازه داده می‌شود"""
        self.pk = 1
        optimize_uploaded_fields(self, 'who_we_are_image_front', 'who_we_are_image_back')
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# مدل برندها
# ─────────────────────────────────────────────
class Brand(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='نام برند',
    )
    logo = models.ImageField(
        upload_to='aboutus/brands/',
        verbose_name='لوگو برند',
        blank=True,
        null=True,
    )
    website = models.URLField(
        verbose_name='آدرس سایت برند',
        blank=True,
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتیب نمایش',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
    )

    class Meta:
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'
        ordering = ['order']
        indexes = [
            models.Index(fields=['is_active', 'order'], name='aboutbrand_active_order_idx'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        optimize_uploaded_fields(self, 'logo')
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# مدل اعضای تیم
# ─────────────────────────────────────────────
class TeamMember(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='نام و نام خانوادگی',
    )
    position = models.CharField(
        max_length=100,
        verbose_name='سمت',
    )
    photo = models.ImageField(
        upload_to='aboutus/team/',
        verbose_name='عکس عضو',
        blank=True,
        null=True,
    )
    bio = models.TextField(
        verbose_name='بیوگرافی',
        blank=True,
    )

    # شبکه‌های اجتماعی
    facebook_url = models.URLField(
        verbose_name='آدرس فیسبوک',
        blank=True,
    )
    twitter_url = models.URLField(
        verbose_name='آدرس توییتر',
        blank=True,
    )
    instagram_url = models.URLField(
        verbose_name='آدرس اینستاگرام',
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتیب نمایش',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
    )

    class Meta:
        verbose_name = 'عضو تیم'
        verbose_name_plural = 'اعضای تیم'
        ordering = ['order']
        indexes = [
            models.Index(fields=['is_active', 'order'], name='teammember_active_order_idx'),
        ]

    def __str__(self):
        return f'{self.name} - {self.position}'

    def save(self, *args, **kwargs):
        optimize_uploaded_fields(self, 'photo')
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# مدل نظرات مشتریان
# ─────────────────────────────────────────────
class Testimonial(models.Model):
    customer_name = models.CharField(
        max_length=100,
        verbose_name='نام مشتری',
    )
    customer_role = models.CharField(
        max_length=100,
        default='مشتری',
        verbose_name='نقش مشتری',
    )
    photo = models.ImageField(
        upload_to='aboutus/testimonials/',
        verbose_name='عکس مشتری',
        blank=True,
        null=True,
    )
    review = models.TextField(
        verbose_name='متن نظر',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتیب نمایش',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت',
    )

    class Meta:
        verbose_name = 'نظر مشتری'
        verbose_name_plural = 'نظرات مشتریان'
        ordering = ['order']
        indexes = [
            models.Index(fields=['is_active', 'order'], name='testimonial_active_order_idx'),
        ]

    def __str__(self):
        return f'نظر {self.customer_name}'

    def save(self, *args, **kwargs):
        optimize_uploaded_fields(self, 'photo')
        super().save(*args, **kwargs)
