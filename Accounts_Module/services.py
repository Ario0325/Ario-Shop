import logging
import requests
from django.conf import settings
from django.utils.html import escape

logger = logging.getLogger(__name__)


class N8nAuthService:
    """سرویس ارسال رویدادهای احراز هویت به n8n"""

    WEBHOOK_URL = settings.N8N_WEBHOOK_URL
    WEBHOOK_SECRET = settings.N8N_WEBHOOK_SECRET
    TIMEOUT_SECONDS = settings.N8N_TIMEOUT_SECONDS

    @classmethod
    def _build_headers(cls):
        headers = {'Content-Type': 'application/json'}
        if cls.WEBHOOK_SECRET:
            headers['X-Webhook-Secret'] = cls.WEBHOOK_SECRET
        worker_secret = getattr(settings, 'WORKER_SHARED_SECRET', '')
        if worker_secret:
            headers['X-Worker-Secret'] = worker_secret
        return headers

    @classmethod
    def _send_to_n8n(cls, payload):
        try:
            response = requests.post(
                cls.WEBHOOK_URL,
                json=payload,
                headers=cls._build_headers(),
                timeout=cls.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            logger.info(
                "n8n webhook موفق: event=%s", payload.get('event')
            )
            return True
        except requests.exceptions.ConnectionError:
            logger.error(f"اتصال به n8n برقرار نشد: {cls.WEBHOOK_URL}")
            return False
        except requests.exceptions.Timeout:
            logger.error(f"timeout ارسال به n8n (>{cls.TIMEOUT_SECONDS}s)")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"خطای HTTP از n8n: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"خطای ناشناخته در ارسال به n8n: {e}")
            return False

    @classmethod
    def send_verification_email(cls, email, username, code):
        payload = {
            "event": "register",
            "email": email,
            "username": escape(username or "کاربر"),
            "code": code,
            "reset_link": "",
            "sender_email": settings.N8N_SENDER_EMAIL,
            "secret_token": cls.WEBHOOK_SECRET,
        }
        return cls._send_to_n8n(payload)

    @classmethod
    def send_password_reset_email(cls, email, username, code):
        payload = {
            "event": "password_reset",
            "email": email,
            "username": escape(username or "کاربر"),
            "code": code,
            "reset_link": "",
            "sender_email": settings.N8N_SENDER_EMAIL,
            "secret_token": cls.WEBHOOK_SECRET,
        }
        return cls._send_to_n8n(payload)
