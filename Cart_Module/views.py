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
from django.http import JsonResponse
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
    CART_SESSION_KEY,
    DISCOUNT_SESSION_KEY,
    get_active_discount_code,
    validate_discount_code,
    apply_discount_to_session,
    remove_discount_from_session,
    calculate_cart_with_discount,
    N8nOrderService,
)


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
    if request.user.is_authenticated:
        cache.delete(f'cart_context_user_{request.user.id}')
    elif request.session.session_key:
        cache.delete(f'cart_context_session_{request.session.session_key}')


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


@never_cache
def cart_detail(request):
    """صفحه سبد خرید - جدول محصولات + جمع سبد (طبق قالب cart.html)"""
    items, cart_total = _cart_item_list(request)
    if not items:
        return redirect('cart:empty')

    # هزینه ارسال ساده: رایگان یا ثابت (می‌توان بعداً از تنظیمات خواند)
    shipping_cost = Decimal('0')

    # کد تخفیف فعال
    discount_code = get_active_discount_code(request)
    discount_info = calculate_cart_with_discount(items, discount_code)

    total_payable = discount_info['total_payable'] + shipping_cost

    context = {
        'cart_items': items,
        'cart_total': discount_info['subtotal'],
        'shipping_cost': shipping_cost,
        'discount_code': discount_code,
        'discount_amount': discount_info['discount_amount'],
        'discounted_product_id': discount_info['discounted_product_id'],
        'total_payable': total_payable,
    }
    return render(request, 'cart/cart.html', context)


@never_cache
def cart_empty(request):
    """صفحه سبد خرید خالی (طبق قالب cart-empty.html)"""
    return render(request, 'cart/cart_empty.html')


@require_POST
def cart_add(request, product_id):
    """افزودن به سبد - POST از صفحه محصول"""
    if not request.user.is_authenticated:
        messages.info(request, 'برای افزودن به سبد خرید ابتدا وارد شوید.')
        target = request.POST.get('next') or request.GET.get('next') or reverse('products:list')
        if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
            target = reverse('products:list')
        return redirect(reverse('accounts:login_register') + '?next=' + quote(target, safe=''))

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if not product.is_available or product.stock < 1:
        messages.error(request, 'این محصول در حال حاضر موجود نیست.')
        return redirect(product.get_absolute_url())

    cart = _get_cart(request)
    qty = request.POST.get('quantity', 1)
    try:
        qty = max(1, min(int(qty), product.stock if product.stock else 99))
    except (ValueError, TypeError):
        qty = 1

    # Check if adding this quantity would exceed available stock
    pid = str(product.id)
    current_qty = cart.get(pid, 0)
    if current_qty + qty > product.stock:
        available = product.stock - current_qty
        if available <= 0:
            messages.error(request, f'«{product.name}» به مقدار درخواستی در انبار موجود نیست.')
            return redirect(product.get_absolute_url())
        else:
            qty = available
            messages.warning(request, f'حداکثر {available} عدد از «{product.name}» قابل افزودن به سبد است.')

    cart[pid] = current_qty + qty
    request.session.modified = True
    sync_cart_to_db(request)
    _clear_cart_cache(request)  # پاک کردن کش سبد

    messages.success(request, f'«{product.name}» به سبد خرید اضافه شد.')
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    return redirect(next_url or reverse('cart:detail'))


@require_POST
def cart_remove(request, product_id):
    """حذف یک محصول از سبد"""
    if not request.user.is_authenticated:
        messages.info(request, 'برای مدیریت سبد خرید ابتدا وارد شوید.')
        return redirect(reverse('accounts:login_register') + '?next=' + request.path)

    cart = _get_cart(request)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        request.session.modified = True
        sync_cart_to_db(request)
        _clear_cart_cache(request)  # پاک کردن کش سبد
        messages.info(request, 'محصول از سبد خرید حذف شد.')

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    return redirect(next_url or reverse('cart:detail'))


@require_POST
def cart_update(request):
    """به‌روزرسانی تعداد چند آیتم - از جدول سبد (نام اینپوت: qty_{product_id})"""
    if not request.user.is_authenticated:
        messages.info(request, 'برای مدیریت سبد خرید ابتدا وارد شوید.')
        return redirect(reverse('accounts:login_register') + '?next=' + request.path)

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
    # کش مخصوص هر کاربر؛ برای مهمان بدون session کلید ساخته نمی‌شود
    if request.user.is_authenticated:
        cache_key = f'cart_context_user_{request.user.id}'
    elif request.session.session_key:
        cache_key = f'cart_context_session_{request.session.session_key}'
    else:
        cache_key = None

    if cache_key:
        cached_context = cache.get(cache_key)
        if cached_context is not None:
            return cached_context

    items, total = _cart_item_list(request)
    context = {
        'cart_count': sum(i['quantity'] for i in items),
        'cart_total': total,
        'cart_items_preview': items[:3],  # حداکثر ۳ آیتم برای دراپ‌داون هدر
    }

    if cache_key:
        cache.set(cache_key, context, 60 * 2)

    return context


# ─────────────────────────────────────────────────────────────────────────────
# ویوهای کد تخفیف
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
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
    discount_info = calculate_cart_with_discount(items, discount_code)
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
    messages.info(request, 'کد تخفیف حذف شد.')
    return redirect('cart:detail')


# ─────────────────────────────────────────────────────────────────────────────
# ویوهای سفارش و پرداخت
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
@ratelimit(key='user', rate='5/m', block=True)
def checkout_view(request):
    """ثبت سفارش از سبد و هدایت به صفحه پرداخت (ساده - بدون درگاه) - با Rate Limiting"""

    items, cart_total = _cart_item_list(request)
    if not items:
        messages.warning(request, 'سبد خرید شما خالی است.')
        return redirect('cart:empty')

    # اگر کاربر لاگین است از پروفایل پر کنیم
    full_name = ''
    phone = ''
    email = ''
    address = ''
    postal_code = ''
    city = ''
    if request.user.is_authenticated:
        try:
            from Accounts_Module.models import UserProfile
            profile = UserProfile.objects.get(user=request.user)
            full_name = profile.full_name or ''
            phone = profile.phone or ''
            address = profile.address or ''
            postal_code = profile.postal_code or ''
            city = profile.city or ''
            email = request.user.email or ''
        except Exception:
            pass

    if not full_name or not phone or not address:
        messages.info(request, 'لطفاً در داشبورد نام، تلفن و آدرس را تکمیل کنید سپس به پرداخت برگردید.')
        return redirect('accounts:dashboard')

    # ── اعتبارسنجی مجدد کد تخفیف در زمان checkout ────────────────────────────
    discount_code_obj = None
    discount_amount = Decimal('0')
    subtotal = sum(item['total'] for item in items)

    code_str = request.session.get(DISCOUNT_SESSION_KEY)
    if code_str:
        validated_code, error = validate_discount_code(code_str, items, request.user, request)
        if validated_code:
            discount_code_obj = validated_code
            discount_info = calculate_cart_with_discount(items, validated_code)
            discount_amount = discount_info['discount_amount']
        else:
            # کد دیگر معتبر نیست - از سشن پاک کن و به کاربر اطلاع بده
            remove_discount_from_session(request)
            messages.warning(request, f'کد تخفیف «{code_str}» دیگر معتبر نیست و از سبد حذف شد.')

    final_total = max(subtotal - discount_amount, Decimal('0'))

    with transaction.atomic():
        order = Order(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
            postal_code=postal_code,
            city=city,
            subtotal=subtotal,
            discount_code=discount_code_obj,
            discount_amount=discount_amount,
            total=final_total,
            shipping_cost=Decimal('0'),
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
