import threading
import time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Cart_Module.models import Order, OrderItem
from Cart_Module.services import N8nOrderService
from Products_Module.models import Category, Product

User = get_user_model()


class PaymentWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='payshop',
            email='pay@example.com',
            password='StrongPass123!',
        )
        category = Category.objects.create(name='Cat', slug='cat')
        self.product = Product.objects.create(
            name='Paid Product',
            slug='paid-product',
            category=category,
            description='Test product',
            price=Decimal('420000'),
            stock=5,
            is_available=True,
            is_active=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name='Test Buyer',
            phone='09120000000',
            email='pay@example.com',
            address='Tehran, Test St',
            postal_code='1111111111',
            city='Tehran',
            subtotal=Decimal('420000'),
            total=Decimal('469000'),
            shipping_cost=Decimal('49000'),
            tax=Decimal('0'),
            status='pending',
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            price=Decimal('420000'),
            total=Decimal('420000'),
        )
        self.client.force_login(self.user)

    def test_payment_schedules_background_notification_only(self):
        with patch.object(N8nOrderService, 'notify_order_async') as notify, \
                patch.object(N8nOrderService, 'send_order_confirmation') as sync_mail, \
                patch.object(N8nOrderService, 'send_telegram_notification') as sync_tg, \
                self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('cart:payment', args=[self.order.id]))

        self.assertRedirects(response, reverse('cart:invoice', args=[self.order.id]))
        notify.assert_called_once()
        sync_mail.assert_not_called()
        sync_tg.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_notify_order_async_returns_before_delivery(self):
        delivered = threading.Event()
        seen = {}

        def slow_send(payload):
            seen['n8n'] = payload
            delivered.wait(2)

        def telegram_send(payload):
            seen['telegram'] = payload
            delivered.set()

        with patch.object(N8nOrderService, '_send_to_n8n', side_effect=slow_send), \
                patch.object(N8nOrderService, '_send_telegram', side_effect=telegram_send):
            started = time.monotonic()
            thread = N8nOrderService.notify_order_async(self.order)
            elapsed = time.monotonic() - started

            self.assertLess(elapsed, 1.0)
            self.assertTrue(delivered.wait(3))
            thread.join(2)
            self.assertFalse(thread.is_alive())

        self.assertEqual(seen['n8n']['order_number'], self.order.order_number)
        self.assertEqual(seen['telegram']['status'], 'paid')

    def test_order_payload_keeps_invoice_values(self):
        payload = N8nOrderService.build_order_payload(self.order)

        self.assertEqual(payload['order_id'], self.order.id)
        self.assertEqual(payload['order_number'], self.order.order_number)
        self.assertEqual(payload['total_price'], 420000)
        self.assertEqual(payload['shipping_cost'], 49000)
        self.assertEqual(payload['customer_name'], 'Test Buyer')
        self.assertEqual(payload['items'], [{
            'name': 'Paid Product',
            'quantity': 1,
            'unit_price': 420000,
            'total_price': 420000,
        }])

    def test_telegram_payload_marks_online_payment(self):
        payload = N8nOrderService.build_telegram_payload(self.order)

        self.assertEqual(payload['payment_method'], 'پرداخت آنلاین')
        self.assertEqual(payload['customer_phone'], '09120000000')
