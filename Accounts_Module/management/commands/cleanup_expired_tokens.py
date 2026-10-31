from django.core.management.base import BaseCommand
from django.utils import timezone
from Accounts_Module.models import PasswordResetToken, UserVerification


class Command(BaseCommand):
    help = 'پاک‌سازی توکن‌ها و کدهای OTP منقضی شده'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        deleted_tokens, _ = PasswordResetToken.objects.filter(expires_at__lt=now).delete()
        deleted_otps, _ = UserVerification.objects.filter(
            expires_at__lt=now, is_verified=False,
        ).delete()
        self.stdout.write(
            self.style.SUCCESS(f'{deleted_tokens} توکن و {deleted_otps} کد OTP منقضی پاک شد.')
        )
