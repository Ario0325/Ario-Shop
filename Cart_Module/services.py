"""
سرویس‌های سبد خرید و کد تخفیف
"""
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import CartItem

logger = logging.getLogger(__name__)

CART_SESSION_KEY = 'cart'
DISCOUNT_SESSION_KEY = 'discount_code'


# ─────────────────────────────────────────────────────────────────────────────
# سرویس‌های سبد خرید (DB sync)
# ─────────────────────────────────────────────────────────────────────────────

def load_cart_from_db(request):
    """وقتی کاربر وارد شد، سبد ذخیره شده را به سشن منتقل می‌کند."""
    if not request.user.is_authenticated:
        return

    session_cart = request.session.get(CART_SESSION_KEY) or {}
    items = CartItem.objects.filter(user=request.user).select_related('product')
    if not items.exists():
        return

    for item in items:
        pid = str(item.product_id)
        session_cart[pid] = max(session_cart.get(pid, 0), item.quantity)

    request.session[CART_SESSION_KEY] = session_cart
    request.session.modified = True


def sync_cart_to_db(request):
    """سبد سشن را در خروج/ورود در دیتابیس ذخیره می‌کند."""
    if not request.user.is_authenticated:
        return

    session_cart = request.session.get(CART_SESSION_KEY) or {}
    if not session_cart:
        CartItem.objects.filter(user=request.user).delete()
        return

    with transaction.atomic():
        for pid, qty in session_cart.items():
            if qty < 1:
                continue
            CartItem.objects.update_or_create(
                user=request.user,
                product_id=int(pid),
                defaults={'quantity': qty},
            )

        CartItem.objects.filter(user=request.user).exclude(
            product_id__in=list(session_cart.keys())
        ).delete()


# ─────────────────────────────────────────────────────────────────────────────
# سرویس‌های کد تخفیف
# ─────────────────────────────────────────────────────────────────────────────

def get_active_discount_code(request):
    """
    کد تخفیف فعال در سشن را برمی‌گرداند.
    اگر کدی در سشن نباشد یا کد دیگر معتبر نباشد، None برمی‌گرداند.
    """
    from .models import DiscountCode

    code_str = request.session.get(DISCOUNT_SESSION_KEY)
    if not code_str:
        return None

    try:
        code = DiscountCode.objects.select_related('product').get(
            code=code_str.upper(),
            is_active=True,
        )
    except DiscountCode.DoesNotExist:
        # کد دیگر وجود ندارد یا غیرفعال شده - از سشن پاک کن
        request.session.pop(DISCOUNT_SESSION_KEY, None)
        request.session.modified = True
        return None

    return code


def validate_discount_code(code_str, cart_items, user, request=None):
    """
    اعتبارسنجی کامل یک کد تخفیف.

    پارامترها:
        code_str: رشته کد تخفیف
        cart_items: لیست آیتم‌های سبد (از _cart_item_list)
        user: شیء کاربر
        request: درخواست HTTP (اختیاری)

    برمی‌گرداند:
        (discount_code_obj, error_message)
        اگر معتبر باشد: (DiscountCode, None)
        اگر نامعتبر باشد: (None, 'پیام خطا')
    """
    from .models import DiscountCode

    if not code_str:
        return None, 'کد تخفیف وارد نشده است.'

    code_str = code_str.strip().upper()

    try:
        code = DiscountCode.objects.select_related('product').get(code=code_str)
    except DiscountCode.DoesNotExist:
        return None, 'کد تخفیف وارد شده معتبر نیست.'

    # بررسی فعال بودن
    if not code.is_active:
        return None, 'این کد تخفیف فعال نیست.'

    # بررسی تاریخ شروع
    now = timezone.now()
    if code.starts_at and now < code.starts_at:
        return None, 'این کد تخفیف هنوز فعال نشده است.'

    # بررسی تاریخ انقضا
    if code.ends_at and now > code.ends_at:
        return None, 'این کد تخفیف منقضی شده است.'

    # بررسی سقف کل استفاده
    if not code.has_usage_remaining():
        return None, 'ظرفیت استفاده از این کد تخفیف تمام شده است.'

    # بررسی سقف استفاده هر کاربر
    if not code.user_can_use(user):
        return None, 'شما قبلاً از این کد تخفیف استفاده کرده‌اید.'

    # بررسی حداقل مبلغ سفارش
    cart_total = sum(item['total'] for item in cart_items)
    if code.min_order_amount and cart_total < code.min_order_amount:
        return None, (
            f'حداقل مبلغ سفارش برای استفاده از این کد '
            f'{code.min_order_amount:,.0f} تومان است.'
        )

    # بررسی وجود محصول در سبد (برای scope=product)
    if code.scope == DiscountCode.SCOPE_PRODUCT:
        product_ids_in_cart = {item['product'].id for item in cart_items}
        if code.product_id not in product_ids_in_cart:
            product_name = code.product.name if code.product else 'محصول مورد نظر'
            return None, f'این کد تخفیف فقط برای «{product_name}» معتبر است و آن محصول در سبد شما نیست.'

    return code, None


def apply_discount_to_session(request, code_str):
    """کد تخفیف را در سشن ذخیره می‌کند."""
    request.session[DISCOUNT_SESSION_KEY] = code_str.strip().upper()
    request.session.modified = True


def remove_discount_from_session(request):
    """کد تخفیف را از سشن حذف می‌کند."""
    request.session.pop(DISCOUNT_SESSION_KEY, None)
    request.session.modified = True


def calculate_cart_with_discount(cart_items, discount_code):
    """
    محاسبه مبالغ سبد خرید با احتساب تخفیف.

    برمی‌گرداند:
        dict با کلیدهای:
            subtotal: جمع قبل از تخفیف
            discount_amount: مبلغ تخفیف
            total_payable: مبلغ قابل پرداخت
            discounted_product_id: شناسه محصول تخفیف‌خورده (یا None)
    """
    subtotal = sum(item['total'] for item in cart_items)

    if discount_code:
        discount_amount, base_amount, discounted_product_id = discount_code.get_discount_for_cart(cart_items)
    else:
        discount_amount = Decimal('0')
        discounted_product_id = None

    total_payable = max(subtotal - discount_amount, Decimal('0'))

    return {
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total_payable': total_payable,
        'discounted_product_id': discounted_product_id,
    }


# ─────────────────────────────────────────────────────────────────────────────
# سرویس ارسال ایمیل تأیید سفارش به n8n
# ─────────────────────────────────────────────────────────────────────────────

class N8nOrderService:
    """سرویس ارسال رویداد تأیید سفارش به n8n برای ارسال ایمیل فاکتور"""

    WEBHOOK_URL = settings.N8N_ORDER_WEBHOOK_URL
    WEBHOOK_SECRET = settings.N8N_ORDER_WEBHOOK_SECRET
    TIMEOUT_SECONDS = settings.N8N_TIMEOUT_SECONDS

    @classmethod
    def _build_headers(cls):
        return {'Content-Type': 'application/json'}

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
                f"[n8n] ایمیل تأیید سفارش ارسال شد: order={payload.get('order_number')}"
            )
            return True
        except requests.exceptions.ConnectionError:
            logger.error(f"[n8n] اتصال به n8n برقرار نشد: {cls.WEBHOOK_URL}")
            return False
        except requests.exceptions.Timeout:
            logger.error(f"[n8n] timeout ارسال وبهوک سفارش (>{cls.TIMEOUT_SECONDS}s)")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"[n8n] خطای HTTP از n8n: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"[n8n] خطای ناشناخته در ارسال وبهوک سفارش: {e}")
            return False

    @classmethod
    def send_order_confirmation(cls, order):
        customer_name = order.full_name
        if not customer_name and order.user:
            customer_name = order.user.get_full_name() or order.user.username
        customer_email = order.email
        if not customer_email and order.user:
            customer_email = order.user.email

        items = []
        for item in order.items.select_related('product').all():
            items.append({
                "name": item.product_name,
                "quantity": item.quantity,
                "unit_price": int(item.price),
                "total_price": int(item.total),
            })

        payload = {
            "secret_token": cls.WEBHOOK_SECRET,
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_name": customer_name or "مشتری",
            "customer_email": customer_email or "",
            "payment_status": "paid",
            "total_price": int(order.subtotal),
            "shipping_cost": int(order.shipping_cost),
            "discount": int(order.discount_amount),
            "created_at": order.created_at.isoformat(),
            "shipping_address": order.address,
            "items": items,
            "sender_email": settings.N8N_SENDER_EMAIL,
        }

        return cls._send_to_n8n(payload)


    @classmethod
    def send_telegram_notification(cls, order):
        customer_name = order.full_name
        if not customer_name and order.user:
            customer_name = order.user.get_full_name() or order.user.username
        customer_email = order.email
        if not customer_email and order.user:
            customer_email = order.user.email
        customer_phone = order.phone or ''

        items = []
        for item in order.items.select_related('product').all():
            items.append({
                "name": item.product_name,
                "quantity": item.quantity,
                "unit_price": int(item.price),
                "total_price": int(item.total),
            })

        payload = {
            "secret_token": cls.WEBHOOK_SECRET,
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_name": customer_name or "?????",
            "customer_email": customer_email or "",
            "customer_phone": customer_phone,
            "total_price": int(order.subtotal),
            "shipping_cost": int(order.shipping_cost),
            "discount": int(order.discount_amount),
            "payment_method": "??????",
            "shipping_address": order.address,
            "items": items,
            "created_at": order.created_at.isoformat(),
            "status": "paid",
        }

        telegram_url = settings.N8N_TELEGRAM_WEBHOOK_URL
        try:
            response = requests.post(
                telegram_url,
                json=payload,
                headers=cls._build_headers(),
                timeout=cls.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            logger.info(
                f"[telegram] ??????????? ????? ????? ??: order={order.order_number}"
            )
            return True
        except Exception as e:
            logger.error(f"[telegram] ??? ?? ????? ??????????? ??????: {e}")
            return False