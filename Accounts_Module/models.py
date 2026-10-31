import secrets
import hashlib
import hmac
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils import timezone


def generate_otp():
    return ''.join(secrets.choice('0123456789') for _ in range(6))


class UserVerification(models.Model):
    """مدل نگهداری کدهای تأیید ثبت‌نام"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification',
        verbose_name='کاربر',
    )
    code = models.CharField(max_length=6, default=generate_otp, verbose_name='کد تأیید')
    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')

    class Meta:
        verbose_name = 'تأیید کاربر'
        verbose_name_plural = 'تأیید کاربران'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 15)
            self.expires_at = timezone.now() + timedelta(minutes=expiry)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def refresh_code(self):
        self.code = generate_otp()
        expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 15)
        self.expires_at = timezone.now() + timedelta(minutes=expiry)
        self.save()

    def __str__(self):
        return f"{self.user.email} - {'تأیید شده' if self.is_verified else 'تأیید نشده'}"


class PasswordResetToken(models.Model):
    """مدل نگهداری کدهای بازیابی رمز عبور"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        verbose_name='کاربر',
    )
    code = models.CharField(max_length=6, default=generate_otp, verbose_name='کد بازیابی')
    is_used = models.BooleanField(default=False, verbose_name='استفاده شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')

    class Meta:
        verbose_name = 'توکن بازیابی رمز'
        verbose_name_plural = 'توکن‌های بازیابی رمز'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 15)
            self.expires_at = timezone.now() + timedelta(minutes=expiry)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def refresh_code(self):
        self.code = generate_otp()
        expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 15)
        self.expires_at = timezone.now() + timedelta(minutes=expiry)
        self.save()

    def __str__(self):
        return f"{self.user.email} - {'استفاده شده' if self.is_used else 'معتبر'}"


class UserProfile(models.Model):
    """پروفایل کاربر - نام، تلفن، آدرس برای داشبورد و فاکتور"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='کاربر',
    )
    full_name = models.CharField(max_length=200, blank=True, verbose_name='نام و نام خانوادگی')
    phone = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')
    address = models.TextField(blank=True, verbose_name='آدرس')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='کد پستی')
    city = models.CharField(max_length=100, blank=True, verbose_name='شهر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
        indexes = [
            # Index for city-based lookups
            models.Index(fields=['city'], name='profile_city_idx'),
        ]

    def __str__(self):
        return self.full_name or self.user.email or str(self.user)
