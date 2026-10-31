from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from Cart_Module.services import CART_SESSION_KEY
from Products_Module.models import Category, Product

AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class CartPageAjaxTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat', slug='cat')
        self.product = Product.objects.create(
            name='Live Product',
            slug='live-product',
            category=self.category,
            description='Test product',
            price=Decimal('420000'),
            stock=3,
            is_available=True,
            is_active=True,
        )
        self._set_cart({self.product.id: 1})

    def _set_cart(self, items):
        session = self.client.session
        session[CART_SESSION_KEY] = {str(pid): qty for pid, qty in items.items()}
        session.save()

    def _cart(self):
        return self.client.session.get(CART_SESSION_KEY) or {}

    def test_update_returns_quantity_after_stock_cap(self):
        response = self.client.post(
            reverse('cart:update'),
            {f'qty_{self.product.id}': '9'},
            **AJAX
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['updated'][0]['quantity'], 3)
        self.assertEqual(data['updated'][0]['line_total'], 1260000)
        self.assertIn('تومان', data['updated'][0]['line_total_display'])
        self.assertEqual(self._cart()[str(self.product.id)], 3)

    def test_update_payload_carries_live_summary(self):
        response = self.client.post(
            reverse('cart:update'),
            {f'qty_{self.product.id}': '1'},
            **AJAX
        )

        cart = response.json()['cart']
        self.assertEqual(cart['count'], 1)
        self.assertEqual(cart['total'], 420000)
        self.assertEqual(cart['shipping_cost'], 49000)
        self.assertEqual(cart['total_payable'], 469000)
        self.assertFalse(cart['is_free_shipping'])
        self.assertIn('discount_display', cart)

    def test_update_zero_quantity_removes_line(self):
        response = self.client.post(
            reverse('cart:update'),
            {f'qty_{self.product.id}': '0'},
            **AJAX
        )

        data = response.json()
        self.assertTrue(data['updated'][0]['removed'])
        self.assertEqual(data['cart']['count'], 0)
        self.assertEqual(self._cart(), {})

    def test_remove_ajax_returns_cart(self):
        response = self.client.post(
            reverse('cart:remove', args=[self.product.id]),
            **AJAX
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['removed'])
        self.assertEqual(data['cart']['count'], 0)

    def test_non_ajax_update_still_redirects(self):
        response = self.client.post(
            reverse('cart:update'),
            {f'qty_{self.product.id}': '2'}
        )

        self.assertRedirects(response, reverse('cart:detail'))
        self.assertEqual(self._cart()[str(self.product.id)], 2)

    def test_cart_page_exposes_live_hooks_and_no_newsletter(self):
        html = self.client.get(reverse('cart:detail')).content.decode()

        for hook in (
            'data-ar-cart-page',
            'data-ar-cart-empty-url',
            'data-ar-cart-qty-form',
            f'data-ar-line-total="{self.product.id}"',
            'data-ar-summary-payable',
            'data-ar-cartbar',
            'data-ar-ship-text',
        ):
            self.assertIn(hook, html)
        self.assertNotIn('data-ar-promo', html)
