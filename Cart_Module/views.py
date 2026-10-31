"""
ویوهای سبد خرید - سشن‌بیس، افزودن/حذف/به‌روزرسانی، فاکتور، کد تخفیف
"""
import logging
from decimal import Decimal
from urllib.parse import quote

import jdatetime
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods
from django_ratelimit.decorators import ratelimit

from Products_Module.models import Product, ProductImage
from .models import Order, OrderItem, CartItem
from .services import (
    sync_cart_to_db,
    load_cart_from_db,
    cart_cache_key,
    CART_SESSION_KEY,
    DISCOUNT_SESSION_KEY,
    get_active_discount_code,
    validate_discount_code,
    apply_discount_to_session,
    remove_discount_from_session,
    build_cart_totals,
    N8nOrderService,
)
from .forms import CheckoutAddressForm
from Core_Module.templatetags.number_tags import toman as format_toman


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _cart_payload(cart_items, totals):
    """JSON مشترک پاسخ‌های سبد (افزودن/حذف)."""
    return {
        'ok': True,
        'cart': {
            'count': sum(item['quantity'] for item in cart_items),
            'total': int(totals['subtotal']),
            'total_display': format_toman(totals['subtotal']),
            'discount': int(totals['discount_amount']),
            'goods_net': int(totals['goods_net']),
            'shipping_cost': int(totals['shipping_cost']),
            'shipping_display': (
                'رایگان' if totals['shipping_cost'] == 0 else format_toman(totals['shipping_cost'])
            ),
            'total_payable': int(totals['total_payable']),
            'total_payable_display': format_toman(totals['total_payable']),
            'free_shipping_remaining': int(totals['free_shipping_remaining']),
            'free_shipping_remaining_display': format_toman(totals['free_shipping_remaining']),
            'free_shipping_percent': totals['free_shipping_percent'],
            'is_free_shipping': totals['is_free_shipping'],
        },
    }


def _totals_for_request(request):
    items, _ = _cart_item_list(request)
    totals = build_cart_totals(items, get_active_discount_code(request))
    return items, totals


def _get_cart(request):
    """دیکشنری سبد از سشن: { product_id: quantity }"""
    if request.user.is_authenticated and not request.session.get('_cart_loaded'):
        load_cart_from_db(request)
        request.session['_cart_loaded'] = True

    cart = request.session.get(CART_SESSION_KEY)
    if cart is None:
        request.session[CART_SESSION_KEY] = {}
        cart = request.session[CART_SESSION_KEY]
    return cart


def _clear_cart_cache(request):
    """پاک کردن کش سبد خرید - هنگام تغییر سبد فراخوانی شود"""
    key = cart_cache_key(request)
    if key:
        cache.delete(key)


def _read_cart(request):
    """خواندن سبد بدون ساختن سشن جدید برای بازدیدکننده بدون سبد"""
    if request.user.is_authenticated and not request.session.get('_cart_loaded'):
        load_cart_from_db(request)
        request.session['_cart_loaded'] = True
    return request.session.get(CART_SESSION_KEY) or {}


def _cart_item_list(request):
    """لیست آیتم‌های سبد با شیء محصول و تعداد و جمع - برای قالب"""
    cart = _read_cart(request)
    items = []
    total = Decimal('0')
    if not cart:
        return items, total

    try:
        product_ids = [int(pid) for pid in cart.keys()]
    except (ValueError, TypeError):
        return items, total

    products = Product.objects.filter(
        pk__in=product_ids, is_active=True, is_available=True
    ).select_related('category', 'brand').prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.order_by('order', 'created_at'))
    )
    products_map = {p.pk: p for p in products}

    for product_id_str, qty in cart.items():
        try:
            product_id = int(product_id_str)
            product = products_map.get(product_id)
            if product and qty > 0:
                price = product.price
                line_total = price * qty
                total += line_total
                items.append({
                    'product': product,
                    'quantity': qty,
                    'price': price,
                    'total': line_total,
                })
        except (ValueError, TypeError):
            continue
    return items, total


def _cart_page_context(request):
    """Context مشترک صفحهٔ سبد (برای نمایش اولیه و خطاهای فرم آدرس)."""
    items, _ = _cart_item_list(request)
    if not items:
        return None

    discount_code = get_active_discount_code(request)
    totals = build_cart_totals(items, discount_code)

    profile = None
    if request.user.is_authenticated:
        from Accounts_Module.models import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()

    return {
        'cart_items': items,
        'cart_total': totals['subtotal'],
        'shipping_cost': totals['shipping_cost'],
        'discount_code': discount_code,
        'discount_amount': totals['discount_amount'],
        'discounted_product_id': totals['discounted_product_id'],
        'total_payable': totals['total_payable'],
        'free_shipping_remaining': totals['free_shipping_remaining'],
        'free_shipping_percent': totals['free_shipping_percent'],
        'free_shipping_threshold': totals['free_shipping_threshold'],
        'is_free_shipping': totals['is_free_shipping'],
        'profile': profile,
    }


@never_cache
def cart_detail(request):
    """صفحه سبد خرید - جدول محصولات + جمع سبد (طبق قالب cart.html)"""
    context = _cart_page_context(request)
    if context is None:
        return redirect('cart:empty')
    if 'address_form' not in context:
        context['address_form'] = CheckoutAddressForm(profile=context['profile'])
    return render(request, 'cart/cart.html', context)


@never_cache
def cart_empty(request):
    """صفحه سبد خرید خالی (طبق قالب cart-empty.html)"""
    return render(request, 'cart/cart_empty.html')


@require_POST
@ratelimit(key='ip', rate='40/m', block=True)
def cart_add(request, product_id):
    """افزودن به سبد - برای مهمان و کاربر واردشده، با پاسخ JSON برای AJAX."""
    ajax = _is_ajax(request)
    product = Product.objects.filter(pk=product_id, is_active=True).first()
    if product is None:
        if ajax:
            return JsonResponse(
                {'ok': False, 'code': 'not_found', 'message': 'محصول مورد نظر یافت نشد.'},
                status=404,
            )
        raise Http404('محصول مورد نظر یافت نشد.')
    if not product.is_available or product.stock < 1:
        if ajax:
            return JsonResponse(
                {'ok': False, 'code': 'out_of_stock', 'message': 'این محصول در حال حاضر موجود نیست.'},
                status=409,
            )
        messages.error(request, 'این محصول در حال حاضر موجود نیست.')
        return redirect(product.get_absolute_url())

    cart = _get_cart(request)
    qty = request.POST.get('quantity', 1)
    try:
        qty = max(1, min(int(qty), product.stock if product.stock else 99))
    except (ValueError, TypeError):
        qty = 1

    pid = str(product.id)
    current_qty = cart.get(pid, 0)
    notice = None
    if current_qty + qty > product.stock:
        available = product.stock - current_qty
        if available <= 0:
            message = f'«{product.name}» به مقدار درخواستی در انبار موجود نیست.'
            if ajax:
                items, totals = _totals_for_request(request)
                payload = _cart_payload(items, totals)
                payload.update({'ok': False, 'code': 'capped', 'message': message})
                return JsonResponse(payload, status=409)
            messages.error(request, message)
            return redirect(product.get_absolute_url())
        qty = available
        notice = {
            'level': 'warning',
            'text': f'حداکثر {available} عدد از «{product.name}» قابل افزودن به سبد است.',
        }

    cart[pid] = current_qty + qty
    request.session.modified = True
    sync_cart_to_db(request)
    _clear_cart_cache(request)

    success_text = f'«{product.name}» به سبد خرید اضافه شد.'
    if ajax:
        items, totals = _totals_for_request(request)
        payload = _cart_payload(items, totals)
        payload['added'] = {
            'id': product.pk,
            'name': product.name,
            'quantity': qty,
            'line_quantity': cart[pid],
        }
        payload['notice'] = notice or {'level': 'success', 'text': success_text}
        return JsonResponse(payload)

    if notice:
        messages.warning(request, notice['text'])
    messages.success(request, success_text)
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    return redirect(next_url or reverse('cart:detail'))


@require_POST
@ratelimit(key='ip', rate='40/m', block=True)
def cart_remove(request, product_id):
    """حذف یک محصول از سبد - برای مهمان و کاربر واردشده."""
    cart = _get_cart(request)
    pid = str(product_id)
    removed = False
    if pid in cart:
        del cart[pid]
        request.session.modified = True
        sync_cart_to_db(request)
        _clear_cart_cache(request)
        removed = True

    if _is_ajax(request):
        items, totals = _totals_for_request(request)
        payload = _cart_payload(items, totals)
        payload['removed'] = removed
        return JsonResponse(payload)

    if removed:
        messages.info(request, 'محصول از سبد خرید حذف شد.')
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    return redirect(next_url or reverse('cart:detail'))


@require_POST
def cart_update(request):
    """به‌روزرسانی تعداد چند آیتم - از جدول سبد (نام اینپوت: qty_{product_id})"""
    cart = _get_cart(request)
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            try:
                product_id = int(key.replace('qty_', ''))
                qty = int(value)
                if qty < 1:
                    cart.pop(str(product_id), None)
                else:
                    product = Product.objects.filter(pk=product_id, is_active=True, is_available=True).first()
                    if product:
                        max_qty = product.stock if product.stock else 99
                        cart[str(product_id)] = min(qty, max_qty)
            except (ValueError, TypeError):
                continue
    request.session.modified = True
    sync_cart_to_db(request)
    _clear_cart_cache(request)  # پاک کردن کش سبد
    messages.success(request, 'سبد خرید به‌روزرسانی شد.')
    return redirect('cart:detail')


def cart_context(request):
    """برای استفاده در هدر: تعداد آیتم، جمع کل و چند آیتم اول برای دراپ‌داون - با کشینگ"""
    cache_key = cart_cache_key(request)

    if cache_key:
        cached_context = cache.get(cache_key)
        if cached_context is not None:
            return cached_context

    items, totals = _totals_for_request(request)
    context = {
        'cart_count': sum(i['quantity'] for i in items),
        'cart_total': totals['subtotal'],
        'cart_items_preview': items,  # همهٔ اقلام برای دراور سبد
        'cart_shipping_cost': totals['shipping_cost'],
        'cart_total_payable': totals['total_payable'],
        'free_shipping_remaining': totals['free_shipping_remaining'],
        'free_shipping_percent': totals['free_shipping_percent'],
        'free_shipping_threshold': totals['free_shipping_threshold'],
        'is_free_shipping': totals['is_free_shipping'],
    }

    if cache_key:
        cache.set(cache_key, context, 60 * 2)

    return context


@never_cache
def cart_drawer(request):
    """HTML تازهٔ دراور سبد برای به‌روزرسانی بدون رفرش."""
    items, totals = _totals_for_request(request)
    return render(request, 'cart/_drawer.html', {
        'cart_count': sum(i['quantity'] for i in items),
        'cart_items_preview': items,
        'cart_total': totals['subtotal'],
        'cart_shipping_cost': totals['shipping_cost'],
        'cart_total_payable': totals['total_payable'],
        'free_shipping_remaining': totals['free_shipping_remaining'],
        'free_shipping_percent': totals['free_shipping_percent'],
        'free_shipping_threshold': totals['free_shipping_threshold'],
        'is_free_shipping': totals['is_free_shipping'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# ویوهای کد تخفیف
# ─────────────────────────────────────────────────────────────────────────────@require_POST
@ratelimit(key='user', rate='10/m', block=True)
def discount_apply(request):
    """اعمال کد تخفیف روی سبد خرید - با Rate Limiting برای جلوگیری از سوء استفاده"""
    if not request.user.is_authenticated:
        messages.info(request, 'برای استفاده از کد تخفیف ابتدا وارد شوید.')
        return redirect(reverse('accounts:login_register') + '?next=' + reverse('cart:detail'))

    code_str = request.POST.get('code', '').strip()
    if not code_str:
        messages.error(request, 'لطفاً یک کد تخفیف وارد کنید.')
        return redirect('cart:detail')

    items, _ = _cart_item_list(request)
    if not items:
        messages.warning(request, 'سبد خرید شما خالی است.')
        return redirect('cart:empty')

    discount_code, error = validate_discount_code(code_str, items, request.user, request)

    if error:
        messages.error(request, error)
        return redirect('cart:detail')

    apply_discount_to_session(request, discount_code.code)
    _clear_cart_cache(request)
    discount_info = build_cart_totals(items, discount_code)
    discount_amount = discount_info['discount_amount']

    if discount_code.scope == 'product' and discount_code.product:
        messages.success(
            request,
            f'کد تخفیف «{discount_code.code}» اعمال شد. '
            f'{discount_amount:,.0f} تومان تخفیف برای «{discount_code.product.name}» دریافت کردید.'
        )
    else:
        messages.success(
            request,
            f'کد تخفیف «{discount_code.code}» اعمال شد. '
            f'{discount_amount:,.0f} تومان تخفیف دریافت کردید.'
        )

    return redirect('cart:detail')


@require_POST
def discount_remove(request):
    """حذف کد تخفیف از سبد خرید"""
    remove_discount_from_session(request)
    _clear_cart_cache(request)
    messages.info(request, 'کد تخفیف حذف شد.')
    return redirect('cart:detail')


# ─────────────────────────────────────────────────────────────────────────────
# ویوهای سفارش و پرداخت
# ─────────────────────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
@ratelimit(key='user', rate='5/m', block=True)
def checkout_view(request):
    """ثبت سفارش از سبد و هدایت به صفحه پرداخت (ساده - بدون درگاه) - با Rate Limiting"""

    if not request.user.is_authenticated:
        messages.info(request, 'برای تکمیل خرید ابتدا وارد شوید؛ سبد شما حفظ می‌شود.')
        target = reverse('cart:detail')
        return redirect(reverse('accounts:login_register') + '?next=' + quote(target, safe=''))

    if request.method != 'POST':
        return redirect('cart:detail')

    items, _ = _cart_item_list(request)
    if not items:
        messages.warning(request, 'سبد خرید شما خالی است.')
        return redirect('cart:empty')

    form = CheckoutAddressForm(request.POST or None)
    if not form.is_valid():
        context = _cart_page_context(request)
        if context is None:
            return redirect('cart:empty')
        context['address_form'] = form
        messages.error(request, 'لطفاً اطلاعات ارسال را کامل و صحیح وارد کنید.')
        return render(request, 'cart/cart.html', context)

    for item in items:
        if item['product'].stock < item['quantity']:
            messages.error(
                request,
                f'موجودی «{item["product"].name}» به {item["product"].stock} عدد کاهش یافته است. '
                'لطفاً تعداد را به‌روزرسانی کنید.',
            )
            return redirect('cart:detail')

    data = form.cleaned_data
    from Accounts_Module.models import UserProfile
    UserProfile.objects.update_or_create(
        user=request.user,
        defaults={
            'full_name': data['full_name'],
            'phone': data['phone'],
            'city': data['city'],
            'address': data['address'],
            'postal_code': data.get('postal_code', ''),
        },
    )

    # ── اعتبارسنجی مجدد کد تخفیف در زمان checkout ────────────────────────────
    discount_code_obj = None
    code_str = request.session.get(DISCOUNT_SESSION_KEY)
    if code_str:
        validated_code, error = validate_discount_code(code_str, items, request.user, request)
        if validated_code:
            discount_code_obj = validated_code
        else:
            remove_discount_from_session(request)
            messages.warning(request, f'کد تخفیف «{code_str}» دیگر معتبر نیست و از سبد حذف شد.')

    totals = build_cart_totals(items, discount_code_obj)

    with transaction.atomic():
        order = Order(
            user=request.user,
            full_name=data['full_name'],
            phone=data['phone'],
            email=request.user.email or '',
            address=data['address'],
            postal_code=data.get('postal_code', ''),
            city=data['city'],
            subtotal=totals['subtotal'],
            discount_code=discount_code_obj,
            discount_amount=totals['discount_amount'],
            total=totals['total_payable'],
            shipping_cost=totals['shipping_cost'],
            tax=Decimal('0'),
            status='pending',
        )
        order.save()

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                product_name=item['product'].name,
                quantity=item['quantity'],
                price=item['price'],
                total=item['total'],
            )

        # افزایش شمارنده استفاده از کد تخفیف
        if discount_code_obj:
            from django.db.models import F
            from .models import DiscountCode
            DiscountCode.objects.filter(pk=discount_code_obj.pk).update(used_count=F('used_count') + 1)

    # خالی کردن سبد و کد تخفیف
    request.session[CART_SESSION_KEY] = {}
    remove_discount_from_session(request)
    request.session.modified = True
    CartItem.objects.filter(user=request.user).delete()
    _clear_cart_cache(request)

    messages.success(request, 'سفارش با موفقیت ثبت شد. لطفاً پرداخت را انجام دهید.')
    return redirect('cart:payment', order_id=order.id)


class _InsufficientStockError(Exception):
    """موجودی یکی از اقلام سفارش کافی نیست - کل تراکنش باید برگردد."""


@never_cache
@ratelimit(key='user', rate='10/m', block=True)
def payment_view(request, order_id):
    """نمایش صفحه پرداخت (شبیه‌سازی درگاه پرداخت) - با Rate Limiting"""
    # Require login to view payment page
    if not request.user.is_authenticated:
        from django.urls import reverse
        return redirect(reverse('accounts:login_register') + '?next=' + reverse('cart:payment', args=[order_id]))
    
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=order_id
    )
    # SECURE: Properly verify ownership - user can only see their own payment page
    if order.user_id != request.user.id:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('دسترسی مجاز نیست.')

    if request.method == 'POST':
        # Reduce product stock
        try:
            with transaction.atomic():
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    if product.stock < item.quantity:
                        raise _InsufficientStockError(product.name)
                    product.stock -= item.quantity
                    if product.stock <= 0:
                        product.is_available = False
                    product.save(update_fields=['stock', 'is_available'])

                order.status = 'paid'
                order.save(update_fields=['status', 'updated_at'])
        except _InsufficientStockError as exc:
            messages.error(request, f'موجودی کافی از «{exc}» وجود ندارد.')
            return redirect('cart:payment', order_id=order.id)
        except Exception:
            logger.exception('payment processing failed for order %s', order.pk)
            messages.error(request, 'خطا در پردازش سفارش. لطفاً دوباره تلاش کنید.')
            return redirect('cart:payment', order_id=order.id)

        # وبهوک‌ها بعد از commit و بدون تاثیر روی نتیجه پرداخت
        N8nOrderService.send_order_confirmation(order)
        N8nOrderService.send_telegram_notification(order)

        messages.success(request, 'پرداخت با موفقیت انجام شد. فاکتور شما آماده است.')
        return redirect('cart:invoice', order_id=order.id)

    return render(request, 'cart/payment.html', {'order': order})


def invoice_view(request, order_id):
    """نمایش فاکتور سفارش (فقط سفارش خود کاربر)"""
    # Require login to view invoice
    if not request.user.is_authenticated:
        from django.contrib.auth.decorators import login_required
        from django.urls import reverse
        return redirect(reverse('accounts:login_register') + '?next=' + reverse('cart:invoice', args=[order_id]))
    
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=order_id)
    # SECURE: Properly verify ownership - user can only see their own orders
    if order.user_id != request.user.id:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('دسترسی مجاز نیست.')
    return render(request, 'cart/invoice.html', {'order': order})


# ═══════════════════════════════════════════════════════════════════════════
# API برای اعلان‌های سفارش در پنل ادمین
# ═══════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)


def to_persian_datetime(dt):
    """تبدیل datetime میلادی به شمسی"""
    if not dt:
        return ''
    try:
        # تبدیل به شمسی
        jdate = jdatetime.datetime.fromgregorian(datetime=dt)
        return {
            'full': jdate.strftime('%Y/%m/%d - %H:%M'),
            'date': jdate.strftime('%d %B %Y'),
            'time': jdate.strftime('%H:%M'),
            'day_name': jdate.strftime('%A'),
            'timestamp': dt.isoformat()
        }
    except Exception:
        return {
            'full': str(dt),
            'date': str(dt.date()),
            'time': str(dt.time()),
            'day_name': '',
            'timestamp': dt.isoformat()
        }


@staff_member_required
@require_http_methods(["GET"])
def api_new_orders(request):
    """
    API برای دریافت سفارش‌های جدید
    این API توسط JavaScript در پنل ادمین فراخوانی می‌شود
    
    پارامترها:
    - since: زمان آخرین بررسی (timestamp)
    - limit: تعداد سفارش‌های دریافتی (پیش‌فرض: 10)
    
    خروجی:
    - orders: لیست سفارش‌های جدید
    - total_count: تعداد کل سفارش‌های پرداخت شده
    - last_check: زمان فعلی سرور
    """
    try:
        # دریافت پارامترها
        since_timestamp = request.GET.get('since')
        limit = int(request.GET.get('limit', 10))
        
        # محدود کردن تعداد
        limit = min(limit, 50)
        
        # فیلتر سفارش‌های پرداخت شده - فقط سفارش‌های جدیدتر از since
        orders_query = Order.objects.filter(
            status__in=['paid', 'processing']
        )
        
        # فیلتر بر اساس زمان آخرین بررسی
        if since_timestamp:
            try:
                # تلاش برای پارس کردن timestamp
                since_time = timezone.datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                orders_query = orders_query.filter(created_at__gt=since_time)
            except (ValueError, TypeError):
                # اگر پارس نشد، همه سفارش‌ها را برگردان
                pass
        
        # مرتب‌سازی و محدود کردن
        orders_query = orders_query.select_related('user').order_by('-created_at')[:limit]
        
        # ساخت لیست سفارش‌ها با تاریخ شمسی
        orders_data = []
        for order in orders_query:
            persian_datetime = to_persian_datetime(order.created_at)
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.full_name,
                'phone': order.phone,
                'total': str(order.total),
                'status': order.status,
                'status_display': order.get_status_display(),
                # تاریخ میلادی
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                # تاریخ شمسی
                'persian_datetime': persian_datetime,
                'user_id': order.user_id if order.user else None,
            })
        
        # تعداد کل سفارش‌های پرداخت شده
        total_paid_orders = Order.objects.filter(
            status__in=['paid', 'processing']
        ).count()
        
        # زمان فعلی سرور به شمسی
        now_persian = to_persian_datetime(timezone.now())
        
        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'total_count': total_paid_orders,
            'last_check': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'server_time': timezone.now().isoformat(),
            'server_time_persian': now_persian,
        })
        
    except Exception as e:
        logger.error(f'api_new_orders error: {e}')
        return JsonResponse({
            'success': False,
            'error': 'خطای داخلی سرور',
        }, status=500)
