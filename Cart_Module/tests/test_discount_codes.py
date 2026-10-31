from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Accounts_Module.models import UserProfile
from Cart_Module.admin import DiscountCodeAdmin
from Cart_Module.models import DiscountCode, Order
from Cart_Module.services import CART_SESSION_KEY, DISCOUNT_SESSION_KEY
from Products_Module.models import Category, Product


class DiscountCodeModelAndAdminTests(TestCase):
    def test_discount_code_is_normalized_on_save(self):
        code = DiscountCode.objects.create(
            code='  save10  ',
            title='Save 10',
            discount_type=DiscountCode.TYPE_PERCENT,
            value=Decimal('10'),
        )

        self.assertEqual(code.code, 'SAVE10')

    def test_clean_rejects_invalid_date_range(self):
        code = DiscountCode(
            code='TIMEBOX',
            title='Time Box',
            discount_type=DiscountCode.TYPE_PERCENT,
            value=Decimal('10'),
            starts_at=timezone.now(),
            ends_at=timezone.now() - timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            code.full_clean()

    def test_calculate_discount_percent_with_cap(self):
        code = DiscountCode.objects.create(
            code='CAP30',
            title='Cap 30',
            discount_type=DiscountCode.TYPE_PERCENT,
            value=Decimal('30'),
            max_discount_amount=Decimal('15000'),
        )

        self.assertEqual(code.calculate_discount(Decimal('100000')), Decimal('15000'))

    def test_order_snapshot_fields_exist_with_defaults(self):
        order = Order.objects.create(
            full_name='Snapshot User',
            phone='09120000000',
            email='',
            address='Tehran',
            postal_code='',
            city='Tehran',
            total=Decimal('100000'),
        )

        self.assertEqual(order.subtotal, Decimal('0'))
        self.assertEqual(order.discount_amount, Decimal('0'))
        self.assertIsNone(order.discount_code)

    def test_discount_admin_configuration_is_persian(self):
        admin_obj = DiscountCodeAdmin(DiscountCode, AdminSite())
        form = admin_obj.form()

        self.assertIn('used_count', admin_obj.readonly_fields)
        self.assertEqual(admin_obj.fieldsets[0][0], 'اطلاعات پایه')
        self.assertEqual(form.fields['code'].label, 'کد')
        self.assertEqual(
            form.fields['code'].help_text,
            'کد تخفیف را بدون فاصله وارد کنید. سیستم آن را خودکار به حروف بزرگ تبدیل می‌کند.',
        )


class DiscountCodeFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='discount-user',
            email='discount@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(self.user)

        self.category = Category.objects.create(name='Category', slug='category')
        self.product = Product.objects.create(
            name='Discounted Product',
            slug='discounted-product',
            category=self.category,
            description='Test product',
            price=Decimal('100000'),
            stock=10,
            is_available=True,
            is_active=True,
        )

        self._set_cart({self.product.id: 1})

    def _set_cart(self, items, discount_code_value=None):
        session = self.client.session
        session[CART_SESSION_KEY] = {str(product_id): qty for product_id, qty in items.items()}
        if discount_code_value:
            session[DISCOUNT_SESSION_KEY] = discount_code_value
        elif DISCOUNT_SESSION_KEY in session:
            del session[DISCOUNT_SESSION_KEY]
        session.save()

    def _create_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.full_name = 'Test User'
        profile.phone = '09120000000'
        profile.address = 'Tehran, Test St'
        profile.postal_code = '1111111111'
        profile.city = 'Tehran'
        profile.save()

    def _create_discount(self, **overrides):
        payload = {
            'code': 'SAVE10',
            'title': 'Save 10',
            'discount_type': DiscountCode.TYPE_PERCENT,
            'value': Decimal('10'),
            'is_active': True,
        }
        payload.update(overrides)
        return DiscountCode.objects.create(**payload)

    def test_discount_apply_accepts_valid_code(self):
        self._create_discount(code='SAVE10')

        response = self.client.post(reverse('cart:discount_apply'), {'code': 'save10'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        self.assertEqual(self.client.session.get(DISCOUNT_SESSION_KEY), 'SAVE10')

    def test_discount_remove_clears_session_code(self):
        self._set_cart({self.product.id: 1}, discount_code_value='SAVE10')

        response = self.client.post(reverse('cart:discount_remove'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))

    def test_discount_apply_rejects_invalid_code(self):
        response = self.client.post(reverse('cart:discount_apply'), {'code': 'BADCODE'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))

    def test_discount_apply_rejects_expired_code(self):
        self._create_discount(
            code='OLD50',
            value=Decimal('50'),
            ends_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.post(reverse('cart:discount_apply'), {'code': 'OLD50'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))

    def test_discount_apply_rejects_total_usage_limit(self):
        self._create_discount(
            code='LIMITED',
            usage_limit_total=1,
            used_count=1,
        )

        response = self.client.post(reverse('cart:discount_apply'), {'code': 'LIMITED'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))

    def test_discount_apply_rejects_per_user_limit(self):
        code = self._create_discount(
            code='ONCEONLY',
            usage_limit_per_user=1,
        )

        Order.objects.create(
            user=self.user,
            full_name='Test User',
            phone='09120000000',
            email='discount@example.com',
            address='Tehran, Test St',
            postal_code='1111111111',
            city='Tehran',
            subtotal=Decimal('100000'),
            discount_amount=Decimal('10000'),
            discount_code=code,
            total=Decimal('90000'),
        )

        response = self.client.post(reverse('cart:discount_apply'), {'code': 'ONCEONLY'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:detail'))
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))

    def test_cart_template_shows_discount_actions_and_breakdown(self):
        self._create_discount(code='SAVE10')
        self._set_cart({self.product.id: 1}, discount_code_value='SAVE10')

        response = self.client.get(reverse('cart:detail'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cart:discount_remove'))
        self.assertContains(response, 'ar-summary__row--off')
        self.assertContains(response, 'SAVE10')
        self.assertContains(response, 'ar-ship')

        self._set_cart({self.product.id: 1})
        plain_response = self.client.get(reverse('cart:detail'))
        self.assertContains(plain_response, reverse('cart:discount_apply'))

    def test_product_detail_renders_discount_interaction_box(self):
        response = self.client.get(reverse('products:detail', kwargs={'slug': self.product.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pdp-discount')
        self.assertContains(response, reverse('cart:discount_apply'))

    def _address_payload(self):
        return {
            'full_name': 'Test User',
            'phone': '09120000000',
            'address': 'Tehran, Test St',
            'postal_code': '1111111111',
            'city': 'Tehran',
        }

    def test_checkout_revalidates_discount_and_persists_snapshot(self):
        self._create_profile()
        code = self._create_discount(
            code='FIX20',
            discount_type=DiscountCode.TYPE_FIXED,
            value=Decimal('20000'),
        )
        self._set_cart({self.product.id: 1}, discount_code_value='FIX20')

        response = self.client.post(reverse('cart:checkout'), self._address_payload())

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal('100000'))
        self.assertEqual(order.discount_amount, Decimal('20000'))
        self.assertEqual(order.shipping_cost, Decimal('49000'))
        self.assertEqual(order.total, Decimal('129000'))
        self.assertEqual(order.discount_code_id, code.id)

        code.refresh_from_db()
        self.assertEqual(code.used_count, 1)

        self.assertEqual(self.client.session.get(CART_SESSION_KEY), {})
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))

        payment_response = self.client.get(reverse('cart:payment', kwargs={'order_id': order.id}))
        self.assertEqual(payment_response.status_code, 200)
        self.assertContains(payment_response, 'FIX20')

        invoice_response = self.client.get(reverse('cart:invoice', kwargs={'order_id': order.id}))
        self.assertEqual(invoice_response.status_code, 200)
        self.assertContains(invoice_response, 'FIX20')

    def test_checkout_drops_invalid_discount_before_order_snapshot(self):
        self._create_profile()
        code = self._create_discount(
            code='MIN200',
            min_order_amount=Decimal('200000'),
        )
        self._set_cart({self.product.id: 1}, discount_code_value='MIN200')

        response = self.client.post(reverse('cart:checkout'), self._address_payload())

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal('100000'))
        self.assertEqual(order.discount_amount, Decimal('0'))
        self.assertIsNone(order.discount_code)
        self.assertEqual(order.shipping_cost, Decimal('49000'))
        self.assertEqual(order.total, Decimal('149000'))

        code.refresh_from_db()
        self.assertEqual(code.used_count, 0)
        self.assertIsNone(self.client.session.get(DISCOUNT_SESSION_KEY))
