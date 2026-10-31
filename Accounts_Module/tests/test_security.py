from unittest.mock import patch

from django.contrib.auth import authenticate, get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from Accounts_Module.models import UserVerification, PasswordResetToken
from Accounts_Module.services import N8nAuthService

User = get_user_model()


@override_settings(RATELIMIT_ENABLE=False)
class OtpLockoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='otp-user', email='otp@example.com', password='StrongPass123!',
            is_active=False,
        )
        self.verification = UserVerification.objects.create(user=self.user, code='123456')

    def test_verification_code_locks_after_five_wrong_attempts(self):
        session = self.client.session
        session['verify_email'] = self.user.email
        session.save()

        for _ in range(5):
            self.client.post(reverse('accounts:verify_email'), {'code': '000000'})

        self.verification.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.verification.attempts, 5)
        self.assertEqual(self.verification.code, '')
        self.assertLessEqual(self.verification.expires_at, timezone.now())
        self.assertFalse(self.verification.is_verified)
        self.assertFalse(self.user.is_active)

        # حتی کد صحیح قبلی هم دیگر پذیرفته نمی‌شود.
        self.client.post(reverse('accounts:verify_email'), {'code': '123456'})
        self.verification.refresh_from_db()
        self.assertFalse(self.verification.is_verified)


@override_settings(RATELIMIT_ENABLE=False)
class PasswordResetHardeningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reset-user', email='reset@example.com', password='OldPass123!',
        )
        self.token = PasswordResetToken.objects.create(user=self.user, code='654321')

    def _post(self, code, password):
        session = self.client.session
        session['reset_email'] = self.user.email
        session.save()
        return self.client.post(reverse('accounts:forget_password_verify'), {
            'code': code,
            'new_password1': password,
            'new_password2': password,
        })

    def test_weak_password_is_rejected_by_validators(self):
        response = self._post('654321', '123456')

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.token.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))
        self.assertFalse(self.token.is_used)

    def test_strong_password_is_accepted_and_token_consumed(self):
        response = self._post('654321', 'Ario-Strong-2026!')

        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        self.user.refresh_from_db()
        self.token.refresh_from_db()
        self.assertTrue(self.user.check_password('Ario-Strong-2026!'))
        self.assertTrue(self.token.is_used)
        self.assertEqual(self.token.code, '')

    def test_wrong_code_increments_attempts(self):
        self._post('000000', 'Ario-Strong-2026!')

        self.token.refresh_from_db()
        self.assertEqual(self.token.attempts, 1)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    def test_reset_token_locks_after_five_wrong_attempts(self):
        for _ in range(5):
            self._post('000000', 'Ario-Strong-2026!')

        self.token.refresh_from_db()
        self.assertEqual(self.token.attempts, 5)
        self.assertTrue(self.token.is_used)
        self.assertEqual(self.token.code, '')


@override_settings(RATELIMIT_ENABLE=False)
class EmailEnumerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='enum-user', email='user@example.com', password='StrongPass123!',
        )

    @patch.object(N8nAuthService, 'send_password_reset_email', return_value=True)
    def test_known_and_unknown_emails_get_the_same_response(self, send_email):
        known = self.client.post(reverse('accounts:forget_password'), {'email': self.user.email})
        known_messages = [m.message for m in get_messages(known.wsgi_request)]
        self.client.session.flush()
        unknown = self.client.post(
            reverse('accounts:forget_password'), {'email': 'nobody@example.com'}
        )
        unknown_messages = [m.message for m in get_messages(unknown.wsgi_request)]

        self.assertRedirects(known, reverse('accounts:forget_password_verify'))
        self.assertRedirects(unknown, reverse('accounts:forget_password_verify'))
        self.assertEqual(known_messages[0], unknown_messages[-1])
        self.assertEqual(send_email.call_count, 1)
        self.assertFalse(
            PasswordResetToken.objects.filter(user__email='nobody@example.com').exists()
        )


class EmailBackendTests(TestCase):
    def test_duplicate_emails_do_not_break_authentication(self):
        User.objects.create_user(
            username='first', email='dup@example.com', password='StrongPass123!',
        )
        User.objects.create_user(
            username='second', email='Dup@Example.com', password='OtherPass123!',
        )

        user = authenticate(username='dup@example.com', password='StrongPass123!')

        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'first')
