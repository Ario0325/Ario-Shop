from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from Products_Module.models import Brand, Category, Product, ProductReview


class CatalogueFilterTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='پیراهن', slug='shirts')
        self.other_category = Category.objects.create(name='شلوار', slug='pants')
        self.alpha = Brand.objects.create(name='آلفا', slug='alpha')
        self.beta = Brand.objects.create(name='بتا', slug='beta')

        self.shirt_a = Product.objects.create(
            name='پیراهن آلفا',
            slug='shirt-alpha',
            category=self.category,
            brand=self.alpha,
            description='پیراهن',
            price=120000,
            stock=5,
        )
        self.shirt_b = Product.objects.create(
            name='پیراهن بتا',
            slug='shirt-beta',
            category=self.category,
            brand=self.beta,
            description='پیراهن',
            price=240000,
            stock=5,
        )
        self.pants = Product.objects.create(
            name='شلوار بتا',
            slug='pants-beta',
            category=self.other_category,
            brand=self.beta,
            description='شلوار',
            price=300000,
            stock=5,
        )

        ProductReview.objects.create(
            product=self.shirt_a,
            name='سارا',
            email='sara@example.com',
            rating=5,
            title='عالی',
            comment='خیلی خوب',
            is_approved=True,
        )
        ProductReview.objects.create(
            product=self.shirt_a,
            name='رضا',
            email='reza@example.com',
            rating=4,
            title='خوب',
            comment='مناسب',
            is_approved=True,
        )
        ProductReview.objects.create(
            product=self.shirt_a,
            name='مهمان',
            email='guest@example.com',
            rating=1,
            title='در انتظار',
            comment='تایید نشده',
            is_approved=False,
        )

    def test_multi_brand_filter_matches_each_brand(self):
        response = self.client.get(reverse('products:list'), {'brand': ['alpha', 'beta']})
        names = {product.slug for product in response.context['products']}
        self.assertEqual(names, {'shirt-alpha', 'shirt-beta', 'pants-beta'})

        response = self.client.get(reverse('products:list'), {'brand': ['alpha']})
        names = {product.slug for product in response.context['products']}
        self.assertEqual(names, {'shirt-alpha'})

    def test_category_filter_chips_remove_one_brand_and_keep_path(self):
        url = reverse('products:category', kwargs={'slug': 'shirts'})
        response = self.client.get(url, {'brand': ['alpha', 'beta'], 'size': ['m']})

        filters = {item['label']: item['url'] for item in response.context['active_filters']}
        self.assertEqual(filters['آلفا'], f'{url}?brand=beta&size=m')
        self.assertEqual(filters['بتا'], f'{url}?brand=alpha&size=m')
        self.assertEqual(filters['پیراهن'], reverse('products:list'))

    def test_filter_clear_url_keeps_category_path(self):
        url = reverse('products:category', kwargs={'slug': 'shirts'})
        response = self.client.get(url, {'brand': 'alpha', 'min_price': '100000'})

        self.assertEqual(response.context['filter_clear_url'], url)
        self.assertEqual(response.context['applied_count'], 2)
        content = response.content.decode()
        self.assertIn(f'action="{url}"', content)
        self.assertNotIn('name="category"', content)

    def test_filter_form_action_keeps_shop_path(self):
        response = self.client.get(reverse('products:list'), {'brand': 'alpha'})

        self.assertEqual(response.context['filter_clear_url'], reverse('products:list'))
        self.assertIn('name="category"', response.content.decode())

    def test_card_annotations_count_only_approved_reviews(self):
        response = self.client.get(reverse('products:list'))
        product = next(item for item in response.context['products'] if item.slug == 'shirt-alpha')

        self.assertEqual(product.review_count, 2)
        self.assertEqual(int(product.avg_rating), 4)

    def test_suggest_requires_two_characters(self):
        response = self.client.get(reverse('products:suggest'), {'q': 'پ'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['products'], [])

    def test_suggest_returns_products_and_categories(self):
        response = self.client.get(reverse('products:suggest'), {'q': 'پیراهن'})
        payload = response.json()

        self.assertTrue(payload['ok'])
        self.assertTrue(any(row['name'] == 'پیراهن آلفا' for row in payload['products']))
        self.assertTrue(any(row['name'] == 'پیراهن' for row in payload['categories']))
