from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Accounts_Module.models import UserProfile
from Cart_Module.models import CartItem, DiscountCode, Order
from Cart_Module.services import (
    CART_SESSION_KEY,
    build_cart_totals,
)
from Products_Module.models import Category, Product

User = get_user_model()

AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class CartFlowTestBase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Category', slug='category')
        self.product = self._product('Demo Product', 'demo-product', Decimal('420000'), stock=5)
        self.other = self._product('Second Product', 'second-product', Decimal('80000'), stock=10)

    def _product(self, name, slug, price, stock=10, **overrides):
        payload = {
            'name': name,
            'slug': slug,
            'category': self.category,
            'description': 'Test product',
            'price': price,
            'stock': stock,
            'is_available': True,
            'is_active': True,
        }
        payload.update(overrides)
        return Product.objects.create(**payload)

    def _set_cart(self, items):
        session = self.client.session
        session[CART_SESSION_KEY] = {str(pid): qty for pid, qty in items.items()}
        session.save()

    def _cart(self):
        return self.client.session.get(CART_SESSION_KEY) or {}


class GuestCartTests(CartFlowTestBase):
    def test_guest_add_returns_json_and_totals(self):
        response = self.client.post(reverse('cart:add', args=[self.product.id]), **AJAX)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['added']['quantity'], 1)
        self.assertEqual(data['cart']['count'], 1)
        self.assertEqual(data['cart']['shipping_cost'], 49000)
        self.assertEqual(self._cart(), {str(self.product.id): 1})

    def test_guest_add_respects_stock_cap(self):
        self._set_cart({self.product.id: 4})

        response = self.client.post(
            reverse('cart:add', args=[self.product.id]),
            {'quantity': 3},
            **AJAX
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['added']['quantity'], 1)
        self.assertEqual(data['notice']['level'], 'warning')
        self.assertEqual(self._cart()[str(self.product.id)], 5)

    def test_guest_add_out_of_stock_returns_409(self):
        empty = self._product('Sold Out', 'sold-out', Decimal('10000'), stock=0)

        response = self.client.post(reverse('cart:add', args=[empty.id]), **AJAX)

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(self._cart(), {})

    def test_guest_update_and_remove(self):
        self._set_cart({self.product.id: 1})

        update = self.client.post(reverse('cart:update'), {
            f'qty_{self.product.id}': '4',
        })
        self.assertEqual(update.status_code, 302)
        self.assertEqual(self._cart()[str(self.product.id)], 4)

        remove = self.client.post(reverse('cart:remove', args=[self.product.id]), **AJAX)
        self.assertEqual(remove.status_code, 200)
        self.assertTrue(remove.json()['removed'])
        self.assertEqual(self._cart(), {})


class MergeOnLoginTests(CartFlowTestBase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='merge-user',
            email='merge@example.com',
            password='StrongPass123!',
        )
        CartItem.objects.create(user=self.user, product=self.product, quantity=3)

    def test_login_merges_guest_cart_with_max_quantity(self):
        self._set_cart({self.product.id: 2, self.other.id: 4})

        response = self.client.post(reverse('accounts:login_register'), {
            'login': '',
            'username': self.user.email,
            'password': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self._cart(), {
            str(self.product.id): 3,
            str(self.other.id): 4,
        })
        stored = {
            item.product_id: item.quantity
            for item in CartItem.objects.filter(user=self.user)
        }
        self.assertEqual(stored, {self.product.id: 3, self.other.id: 4})


class ShippingTotalsTests(CartFlowTestBase):
    def _line(self, price, qty=1):
        price = Decimal(price)
        return {
            'product': self.product,
            'price': price,
            'quantity': qty,
            'total': price * qty,
        }

    def test_fee_applies_below_threshold(self):
        totals = build_cart_totals([self._line('499999')])

        self.assertEqual(totals['shipping_cost'], Decimal('49000'))
        self.assertEqual(totals['total_payable'], Decimal('548999'))
        self.assertEqual(totals['free_shipping_remaining'], Decimal('1'))
        self.assertFalse(totals['is_free_shipping'])

    def test_free_shipping_at_threshold(self):
        totals = build_cart_totals([self._line('500000')])

        self.assertEqual(totals['shipping_cost'], Decimal('0'))
        self.assertEqual(totals['total_payable'], Decimal('500000'))
        self.assertTrue(totals['is_free_shipping'])
        self.assertEqual(totals['free_shipping_percent'], 100)

    def test_discount_can_push_order_below_threshold(self):
        code = DiscountCode.objects.create(
            code='FIX30',
            title='Fixed 30k',
            discount_type=DiscountCode.TYPE_FIXED,
            value=Decimal('30000'),
        )

        totals = build_cart_totals([self._line('520000')], code)

        self.assertEqual(totals['goods_net'], Decimal('490000'))
        self.assertEqual(totals['shipping_cost'], Decimal('49000'))
        self.assertEqual(totals['total_payable'], Decimal('539000'))
        self.assertFalse(totals['is_free_shipping'])


class CheckoutFlowTests(CartFlowTestBase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='checkout-user',
            email='checkout@example.com',
            password='StrongPass123!',
        )

    def _address(self):
        return {
            'full_name': 'Checkout User',
            'phone': '09120000000',
            'city': 'Tehran',
            'address': 'Tehran, Test St',
            'postal_code': '1111111111',
        }

    def test_anonymous_checkout_redirects_to_login(self):
        response = self.client.get(reverse('cart:checkout'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login_register'), response.url)

    def test_authenticated_get_redirects_to_cart(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('cart:checkout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))

    def test_checkout_saves_profile_and_paid_total(self):
        self.client.force_login(self.user)
        self._set_cart({self.product.id: 1})

        response = self.client.post(reverse('cart:checkout'), self._address())

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.shipping_cost, Decimal('49000'))
        self.assertEqual(order.total, order.subtotal - order.discount_amount + order.shipping_cost)
        self.assertEqual(order.total, Decimal('469000'))

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.phone, '09120000000')
        self.assertEqual(profile.city, 'Tehran')

    def test_checkout_over_threshold_ships_free(self):
        self.client.force_login(self.user)
        self.product.price = Decimal('500000')
        self.product.save(update_fields=['price'])
        self._set_cart({self.product.id: 1})

        response = self.client.post(reverse('cart:checkout'), self._address())

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.shipping_cost, Decimal('0'))
        self.assertEqual(order.total, Decimal('500000'))
