from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from Cart_Module.models import CartItem, DiscountCode, Order, OrderItem
from Cart_Module.services import CART_SESSION_KEY, DISCOUNT_SESSION_KEY, N8nOrderService
from Products_Module.models import Category, Product

User = get_user_model()


@override_settings(RATELIMIT_ENABLE=False)
class SecurityTestBase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Category', slug='category')
        self.product = Product.objects.create(
            name='Demo Product',
            slug='demo-product',
            category=self.category,
            description='Test product',
            price=Decimal('100000'),
            stock=5,
            is_available=True,
            is_active=True,
        )
        self.user = User.objects.create_user(
            username='buyer', email='buyer@example.com', password='StrongPass123!'
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@example.com', password='StrongPass123!',
            is_staff=True,
        )

    def _order(self, user=None, quantity=2, status='pending', discount_code=None):
        order = Order.objects.create(
            user=user or self.user,
            full_name='Buyer',
            phone='09120000000',
            address='Tehran',
            city='Tehran',
            subtotal=Decimal('100000') * quantity,
            total=Decimal('100000') * quantity,
            discount_code=discount_code,
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=quantity,
            price=self.product.price,
        )
        return order

    def _set_cart(self, items):
        session = self.client.session
        session[CART_SESSION_KEY] = {str(pid): qty for pid, qty in items.items()}
        session.save()


class PaymentHardeningTests(SecurityTestBase):
    @override_settings(DEBUG=False)
    def test_non_staff_cannot_simulate_payment_in_production(self):
        self.client.force_login(self.user)
        order = self._order()

        response = self.client.post(reverse('cart:payment', args=[order.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(self.product.stock, 5)

    @override_settings(DEBUG=False)
    @patch.object(N8nOrderService, 'send_telegram_notification', return_value=True)
    @patch.object(N8nOrderService, 'send_order_confirmation', return_value=True)
    def test_staff_payment_decrements_stock_once_and_notifies_once(self, send_email, send_tg):
        self.client.force_login(self.staff)
        order = self._order(user=self.staff)

        first = self.client.post(reverse('cart:payment', args=[order.id]))
        second = self.client.post(reverse('cart:payment', args=[order.id]))

        self.assertRedirects(first, reverse('cart:invoice', args=[order.id]))
        self.assertRedirects(second, reverse('cart:invoice', args=[order.id]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(send_email.call_count, 1)
        self.assertEqual(send_tg.call_count, 1)

    @override_settings(DEBUG=True)
    @patch.object(N8nOrderService, 'send_telegram_notification', return_value=True)
    @patch.object(N8nOrderService, 'send_order_confirmation', return_value=True)
    def test_regular_user_can_pay_in_debug(self, send_email, send_tg):
        self.client.force_login(self.user)
        order = self._order()

        response = self.client.post(reverse('cart:payment', args=[order.id]))

        self.assertRedirects(response, reverse('cart:invoice', args=[order.id]))
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')

    def test_paid_order_is_redirected_to_invoice_without_charging(self):
        self.client.force_login(self.user)
        order = self._order(status='paid')

        response = self.client.post(reverse('cart:payment', args=[order.id]))

        self.assertRedirects(response, reverse('cart:invoice', args=[order.id]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    @override_settings(DEBUG=False)
    def test_non_staff_payment_page_hides_pay_button(self):
        self.client.force_login(self.user)
        order = self._order()

        response = self.client.get(reverse('cart:payment', args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'پرداخت و تکمیل سفارش')
        self.assertContains(response, 'درگاه پرداخت آنلاین به‌زودی فعال می‌شود')


class CancelOrderTests(SecurityTestBase):
    def test_cancel_pending_order_does_not_inflate_stock(self):
        code = DiscountCode.objects.create(
            code='SAVE10', title='Save 10', discount_type=DiscountCode.TYPE_FIXED,
            value=Decimal('10000'), used_count=1,
        )
        self.client.force_login(self.user)
        order = self._order(quantity=2, status='pending', discount_code=code)

        response = self.client.post(reverse('accounts:order_cancel', args=[order.id]))

        self.assertRedirects(response, reverse('accounts:orders'))
        self.product.refresh_from_db()
        code.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(code.used_count, 0)
        self.assertEqual(order.status, 'cancelled')

    def test_cancel_paid_order_restores_stock(self):
        self.client.force_login(self.user)
        order = self._order(quantity=2, status='paid')
        self.product.stock = 3
        self.product.save(update_fields=['stock'])

        response = self.client.post(reverse('accounts:order_cancel', args=[order.id]))

        self.assertRedirects(response, reverse('accounts:orders'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_coupon_counter_never_goes_negative(self):
        code = DiscountCode.objects.create(
            code='ZERO', title='Zero', discount_type=DiscountCode.TYPE_FIXED,
            value=Decimal('10000'), used_count=0,
        )
        self.client.force_login(self.user)
        order = self._order(quantity=1, status='pending', discount_code=code)

        self.client.post(reverse('accounts:order_cancel', args=[order.id]))

        code.refresh_from_db()
        self.assertEqual(code.used_count, 0)


class CouponCheckoutTests(SecurityTestBase):
    def _address(self):
        return {
            'full_name': 'Buyer',
            'phone': '09120000000',
            'city': 'Tehran',
            'address': 'Tehran, Test St',
            'postal_code': '1111111111',
        }

    def test_full_discount_code_is_rejected_at_checkout(self):
        DiscountCode.objects.create(
            code='FREE100', title='Free', discount_type=DiscountCode.TYPE_PERCENT,
            value=Decimal('100'),
        )
        self.client.force_login(self.user)
        self._set_cart({self.product.id: 1})
        session = self.client.session
        session[DISCOUNT_SESSION_KEY] = 'FREE100'
        session.save()

        response = self.client.post(reverse('cart:checkout'), self._address())

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.discount_amount, Decimal('0'))
        self.assertEqual(order.total, Decimal('149000'))
        self.assertIsNone(order.discount_code)
        self.assertNotIn(DISCOUNT_SESSION_KEY, self.client.session)

    def test_coupon_usage_counter_increments_on_checkout(self):
        code = DiscountCode.objects.create(
            code='SAVE10', title='Save 10', discount_type=DiscountCode.TYPE_FIXED,
            value=Decimal('10000'),
        )
        self.client.force_login(self.user)
        self._set_cart({self.product.id: 1})
        session = self.client.session
        session[DISCOUNT_SESSION_KEY] = 'SAVE10'
        session.save()

        self.client.post(reverse('cart:checkout'), self._address())

        code.refresh_from_db()
        self.assertEqual(code.used_count, 1)

    def test_cancelled_order_does_not_consume_per_user_coupon_quota(self):
        code = DiscountCode.objects.create(
            code='ONCE', title='Once per user', discount_type=DiscountCode.TYPE_FIXED,
            value=Decimal('10000'), usage_limit_per_user=1,
        )
        Order.objects.create(
            user=self.user, full_name='Buyer', phone='0912', address='Tehran',
            subtotal=Decimal('100000'), total=Decimal('90000'),
            discount_code=code, status='cancelled',
        )

        self.assertTrue(code.user_can_use(self.user))


class ResponseHeaderTests(SecurityTestBase):
    def test_csp_header_is_present_on_html_pages(self):
        response = self.client.get('/')

        self.assertIn('Content-Security-Policy', response)
        self.assertIn("default-src 'self'", response['Content-Security-Policy'])
        self.assertIn("object-src 'none'", response['Content-Security-Policy'])

    def test_invoice_is_not_cached(self):
        self.client.force_login(self.user)
        order = self._order()

        response = self.client.get(reverse('cart:invoice', args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
