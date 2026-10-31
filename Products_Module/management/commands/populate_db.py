"""
دستور Django برای پر کردن دیتابیس با داده‌های نمونه
استفاده: python manage.py populate_db
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from Products_Module.models import Category, Brand, Product, ProductImage, ProductColor, ProductSize, ProductReview
from Menu_Module.models import MenuItem
from Contact_Module.models import ContactInfo
from AboutUs_Module.models import AboutPage, Brand as AboutBrand, TeamMember, Testimonial


class Command(BaseCommand):
    help = 'پر کردن دیتابیس با داده‌های نمونه'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('شروع پر کردن دیتابیس...'))

        with transaction.atomic():
            # پاک کردن داده‌های قبلی (به جز کاربران)
            self.stdout.write('پاک کردن داده‌های قبلی...')
            self.stdout.write(self.style.WARNING('توجه: کاربران ادمین حفظ می‌شوند'))
        ProductReview.objects.all().delete()
        ProductSize.objects.all().delete()
        ProductColor.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Brand.objects.all().delete()
        Category.objects.all().delete()
        MenuItem.objects.all().delete()
        ContactInfo.objects.all().delete()
        AboutPage.objects.all().delete()
        AboutBrand.objects.all().delete()
        TeamMember.objects.all().delete()
        Testimonial.objects.all().delete()

        # ایجاد دسته‌بندی‌ها
        self.stdout.write('ایجاد دسته‌بندی‌ها...')
        categories = self.create_categories()

        # ایجاد برندها
        self.stdout.write('ایجاد برندها...')
        brands = self.create_brands()

        # ایجاد محصولات
        self.stdout.write('ایجاد محصولات...')
        products = self.create_products(categories, brands)

        # ایجاد تصاویر محصولات
        self.stdout.write('ایجاد تصاویر محصولات...')
        self.create_product_images(products)

        # ایجاد رنگ‌ها و سایزها
        self.stdout.write('ایجاد رنگ‌ها و سایزها...')
        self.create_colors_and_sizes(products)

        # ایجاد نظرات
        self.stdout.write('ایجاد نظرات...')
        self.create_reviews(products)

        # ایجاد منوها
        self.stdout.write('ایجاد منوها...')
        self.create_menus()

        # ایجاد اطلاعات تماس
        self.stdout.write('ایجاد اطلاعات تماس...')
        self.create_contact_info()

        # ایجاد صفحه درباره ما
        self.stdout.write('ایجاد صفحه درباره ما...')
        self.create_about_page()

        # ایجاد برندهای صفحه درباره ما
        self.stdout.write('ایجاد برندهای صفحه درباره ما...')
        self.create_about_brands()

        # ایجاد اعضای تیم
        self.stdout.write('ایجاد اعضای تیم...')
        self.create_team_members()

        # ایجاد نظرات مشتریان
        self.stdout.write('ایجاد نظرات مشتریان...')
        self.create_testimonials()

        self.stdout.write(self.style.SUCCESS('✓ دیتابیس با موفقیت پر شد!'))
        self.stdout.write(self.style.SUCCESS(f'  - {Category.objects.count()} دسته‌بندی'))
        self.stdout.write(self.style.SUCCESS(f'  - {Brand.objects.count()} برند'))
        self.stdout.write(self.style.SUCCESS(f'  - {Product.objects.count()} محصول'))
        self.stdout.write(self.style.SUCCESS(f'  - {ProductImage.objects.count()} تصویر محصول'))
        self.stdout.write(self.style.SUCCESS(f'  - {ProductReview.objects.count()} نظر'))
        self.stdout.write(self.style.SUCCESS(f'  - {MenuItem.objects.count()} آیتم منو'))
        self.stdout.write(self.style.SUCCESS(f'  - {ContactInfo.objects.count()} اطلاعات تماس'))

    def create_categories(self):
        """ایجاد دسته‌بندی‌ها"""
        categories_data = [
            {'name': 'لباس زنانه', 'slug': 'womens-clothing'},
            {'name': 'لباس مردانه', 'slug': 'mens-clothing'},
            {'name': 'کفش', 'slug': 'shoes'},
            {'name': 'لوازم جانبی', 'slug': 'accessories'},
            {'name': 'کیف و کوله', 'slug': 'bags'},
            {'name': 'ساعت', 'slug': 'watches'},
            {'name': 'عینک', 'slug': 'sunglasses'},
            {'name': 'جواهرات', 'slug': 'jewelry'},
        ]

        categories = {}
        for data in categories_data:
            cat = Category.objects.create(**data)
            categories[data['slug']] = cat

        # ایجاد زیر دسته‌ها
        subcategories = [
            {'name': 'پیراهن زنانه', 'slug': 'womens-shirts', 'parent': categories['womens-clothing']},
            {'name': 'شلوار زنانه', 'slug': 'womens-pants', 'parent': categories['womens-clothing']},
            {'name': 'پیراهن مردانه', 'slug': 'mens-shirts', 'parent': categories['mens-clothing']},
            {'name': 'شلوار مردانه', 'slug': 'mens-pants', 'parent': categories['mens-clothing']},
        ]

        for data in subcategories:
            cat = Category.objects.create(**data)
            categories[data['slug']] = cat

        return categories

    def create_brands(self):
        """ایجاد برندها"""
        brands_data = [
            {'name': 'نایک', 'slug': 'nike'},
            {'name': 'آدیداس', 'slug': 'adidas'},
            {'name': 'پوما', 'slug': 'puma'},
            {'name': 'زارا', 'slug': 'zara'},
            {'name': 'اچ اند ام', 'slug': 'h-and-m'},
            {'name': 'گوچی', 'slug': 'gucci'},
            {'name': 'لویی ویتون', 'slug': 'louis-vuitton'},
            {'name': 'پرادا', 'slug': 'prada'},
        ]

        brands = {}
        for data in brands_data:
            brand = Brand.objects.create(**data)
            brands[data['slug']] = brand

        return brands

    def create_products(self, categories, brands):
        """ایجاد محصولات"""
        products_data = [
            # محصولات مردانه
            {
                'name': 'تی شرت مردانه نایک اسپرت',
                'slug': 'nike-mens-tshirt-sport',
                'category': categories['mens-shirts'],
                'brand': brands['nike'],
                'description': 'تی شرت ورزشی مردانه با کیفیت عالی و جنس نخ پنبه',
                'full_description': 'این تی شرت با استفاده از بهترین مواد اولیه و با طراحی مدرن تولید شده است. مناسب برای ورزش و استفاده روزمره. دارای تکنولوژی Dri-FIT برای جذب عرق.',
                'price': 450000,
                'old_price': 600000,
                'stock': 50,
                'label': 'sale',
            },
            {
                'name': 'پیراهن مردانه آستین بلند زارا',
                'slug': 'zara-mens-long-sleeve-shirt',
                'category': categories['mens-shirts'],
                'brand': brands['zara'],
                'description': 'پیراهن رسمی مردانه با پارچه مرغوب',
                'full_description': 'پیراهن آستین بلند با طراحی کلاسیک و مدرن، مناسب برای محیط کار و مهمانی‌های رسمی.',
                'price': 780000,
                'old_price': 950000,
                'stock': 35,
                'label': 'new',
            },
            {
                'name': 'شلوار جین مردانه آبی تیره',
                'slug': 'mens-dark-blue-jeans',
                'category': categories['mens-pants'],
                'brand': brands['zara'],
                'description': 'شلوار جین با جنس عالی و دوخت مرغوب',
                'full_description': 'شلوار جین مردانه با طراحی مدرن و جنس بادوام، مناسب برای استفاده روزمره. دارای برش Slim Fit.',
                'price': 850000,
                'stock': 40,
                'label': 'hot',
            },
            {
                'name': 'شلوار ورزشی پوما مشکی',
                'slug': 'puma-black-sports-pants',
                'category': categories['mens-pants'],
                'brand': brands['puma'],
                'description': 'شلوار ورزشی با جنس نخ پنبه و پلی استر',
                'full_description': 'شلوار ورزشی راحت و قابل شستشو، مناسب برای ورزش و استفاده روزمره. دارای جیب‌های زیپ دار.',
                'price': 650000,
                'old_price': 800000,
                'stock': 45,
                'label': 'sale',
            },
            
            # محصولات زنانه
            {
                'name': 'پیراهن زنانه گلدار بهاری',
                'slug': 'womens-spring-floral-shirt',
                'category': categories['womens-shirts'],
                'brand': brands['h-and-m'],
                'description': 'پیراهن زنانه با طرح گل‌های زیبا',
                'full_description': 'پیراهن زنانه با پارچه نرم و راحت، مناسب برای فصل بهار و تابستان. طرح گل‌های رنگارنگ.',
                'price': 550000,
                'old_price': 700000,
                'stock': 25,
                'label': 'sale',
            },
            {
                'name': 'بلوز زنانه یقه گرد',
                'slug': 'womens-round-neck-blouse',
                'category': categories['womens-shirts'],
                'brand': brands['zara'],
                'description': 'بلوز زنانه شیک و راحت',
                'full_description': 'بلوز زنانه با طراحی ساده و شیک، مناسب برای استفاده روزمره و محیط کار.',
                'price': 620000,
                'stock': 30,
                'label': 'new',
            },
            {
                'name': 'شلوار جین زنانه آبی روشن',
                'slug': 'womens-light-blue-jeans',
                'category': categories['womens-pants'],
                'brand': brands['h-and-m'],
                'description': 'شلوار جین زنانه با برش مدرن',
                'full_description': 'شلوار جین زنانه با رنگ آبی روشن و برش Skinny Fit، مناسب برای استفاده روزمره.',
                'price': 720000,
                'old_price': 900000,
                'stock': 28,
                'label': 'sale',
            },
            {
                'name': 'شلوار پارچه ای زنانه مشکی',
                'slug': 'womens-black-fabric-pants',
                'category': categories['womens-pants'],
                'brand': brands['zara'],
                'description': 'شلوار پارچه ای رسمی زنانه',
                'full_description': 'شلوار پارچه ای با طراحی رسمی و راحت، مناسب برای محیط کار.',
                'price': 680000,
                'stock': 32,
                'label': 'new',
            },
            
            # کفش‌ها
            {
                'name': 'کفش ورزشی آدیداس اولترا بوست',
                'slug': 'adidas-ultraboost-shoes',
                'category': categories['shoes'],
                'brand': brands['adidas'],
                'description': 'کفش ورزشی با زیره فوق العاده راحت و طراحی زیبا',
                'full_description': 'کفش ورزشی آدیداس با تکنولوژی Boost، مناسب برای دویدن و پیاده روی طولانی مدت. زیره فوق العاده راحت.',
                'price': 2500000,
                'old_price': 3000000,
                'stock': 30,
                'label': 'hot',
            },
            {
                'name': 'کفش کتانی نایک ایر مکس',
                'slug': 'nike-air-max-sneakers',
                'category': categories['shoes'],
                'brand': brands['nike'],
                'description': 'کفش کتانی با طراحی کلاسیک',
                'full_description': 'کفش کتانی نایک با تکنولوژی Air Max، راحتی و سبکی بی‌نظیر برای استفاده روزمره.',
                'price': 2800000,
                'old_price': 3500000,
                'stock': 25,
                'label': 'sale',
            },
            {
                'name': 'کفش رسمی مردانه چرم',
                'slug': 'mens-formal-leather-shoes',
                'category': categories['shoes'],
                'brand': brands['prada'],
                'description': 'کفش رسمی چرم طبیعی',
                'full_description': 'کفش رسمی مردانه با چرم طبیعی و دوخت دستی، مناسب برای مهمانی‌ها و محیط کار.',
                'price': 3200000,
                'stock': 18,
                'label': 'top',
            },
            
            # کیف و کوله
            {
                'name': 'کیف دستی چرم لوکس',
                'slug': 'luxury-leather-handbag',
                'category': categories['bags'],
                'brand': brands['gucci'],
                'description': 'کیف دستی چرم طبیعی با کیفیت بالا',
                'full_description': 'کیف دستی لوکس با چرم طبیعی و دوخت دستی، مناسب برای مهمانی‌ها و رویدادهای رسمی. دارای جیب‌های داخلی متعدد.',
                'price': 5500000,
                'stock': 10,
                'label': 'top',
            },
            {
                'name': 'کوله پشتی ورزشی نایک',
                'slug': 'nike-sports-backpack',
                'category': categories['bags'],
                'brand': brands['nike'],
                'description': 'کوله پشتی با ظرفیت بالا و جیب‌های متعدد',
                'full_description': 'کوله پشتی ورزشی با طراحی ارگونومیک و مناسب برای حمل لپ تاپ. دارای جیب مخصوص بطری آب.',
                'price': 950000,
                'stock': 35,
                'label': 'new',
            },
            {
                'name': 'کیف دوشی زنانه',
                'slug': 'womens-shoulder-bag',
                'category': categories['bags'],
                'brand': brands['louis-vuitton'],
                'description': 'کیف دوشی شیک و کاربردی',
                'full_description': 'کیف دوشی زنانه با طراحی مدرن و جنس چرم مصنوعی با کیفیت، مناسب برای استفاده روزمره.',
                'price': 4200000,
                'old_price': 5000000,
                'stock': 15,
                'label': 'sale',
            },
            
            # ساعت‌ها
            {
                'name': 'ساعت مچی مردانه اسپرت',
                'slug': 'mens-sport-wristwatch',
                'category': categories['watches'],
                'brand': brands['prada'],
                'description': 'ساعت مچی با بدنه استیل و صفحه مشکی',
                'full_description': 'ساعت مچی اسپرت با موتور ژاپنی و ضد آب تا عمق 50 متر. دارای تقویم و کرونومتر.',
                'price': 3200000,
                'old_price': 4000000,
                'stock': 15,
                'label': 'sale',
            },
            {
                'name': 'ساعت هوشمند',
                'slug': 'smart-watch',
                'category': categories['watches'],
                'brand': brands['nike'],
                'description': 'ساعت هوشمند با امکانات ورزشی',
                'full_description': 'ساعت هوشمند با قابلیت اندازه‌گیری ضربان قلب، شمارش قدم و کالری سوزی. مناسب برای ورزشکاران.',
                'price': 2800000,
                'stock': 22,
                'label': 'hot',
            },
            
            # عینک
            {
                'name': 'عینک آفتابی ریبن کلاسیک',
                'slug': 'classic-rayban-sunglasses',
                'category': categories['sunglasses'],
                'brand': brands['prada'],
                'description': 'عینک آفتابی با لنز UV400',
                'full_description': 'عینک آفتابی با فریم فلزی و لنزهای محافظ در برابر اشعه UV. طراحی کلاسیک و همیشه مد.',
                'price': 1200000,
                'stock': 20,
                'label': 'new',
            },
            {
                'name': 'عینک آفتابی اسپرت',
                'slug': 'sport-sunglasses',
                'category': categories['sunglasses'],
                'brand': brands['nike'],
                'description': 'عینک آفتابی ورزشی با لنز پلاریزه',
                'full_description': 'عینک آفتابی ورزشی با فریم سبک و لنزهای پلاریزه، مناسب برای فعالیت‌های ورزشی در فضای باز.',
                'price': 980000,
                'old_price': 1200000,
                'stock': 28,
                'label': 'sale',
            },
            
            # جواهرات
            {
                'name': 'گردنبند طلا با آویز قلب',
                'slug': 'gold-heart-necklace',
                'category': categories['jewelry'],
                'brand': brands['gucci'],
                'description': 'گردنبند طلای 18 عیار با طراحی ظریف',
                'full_description': 'گردنبند طلای اصل با آویز قلب و نگین‌های زیرکونیا، مناسب برای هدیه. وزن: 5 گرم.',
                'price': 8500000,
                'stock': 5,
                'label': 'top',
            },
            {
                'name': 'دستبند نقره زنانه',
                'slug': 'womens-silver-bracelet',
                'category': categories['jewelry'],
                'brand': brands['prada'],
                'description': 'دستبند نقره با طراحی مدرن',
                'full_description': 'دستبند نقره 925 با طراحی مدرن و شیک، مناسب برای استفاده روزمره و مهمانی.',
                'price': 1800000,
                'old_price': 2200000,
                'stock': 12,
                'label': 'sale',
            },
            {
                'name': 'گوشواره طلا',
                'slug': 'gold-earrings',
                'category': categories['jewelry'],
                'brand': brands['gucci'],
                'description': 'گوشواره طلای 18 عیار',
                'full_description': 'گوشواره طلای اصل با طراحی کلاسیک، مناسب برای هر سنی. وزن: 3 گرم.',
                'price': 6200000,
                'stock': 8,
                'label': 'new',
            },
            
            # لوازم جانبی
            {
                'name': 'کمربند چرم مردانه',
                'slug': 'mens-leather-belt',
                'category': categories['accessories'],
                'brand': brands['gucci'],
                'description': 'کمربند چرم طبیعی با سگک فلزی',
                'full_description': 'کمربند چرم طبیعی با دوخت دستی و سگک فلزی، مناسب برای استفاده رسمی و روزمره.',
                'price': 1500000,
                'stock': 25,
                'label': 'new',
            },
            {
                'name': 'کلاه کپ ورزشی',
                'slug': 'sports-cap',
                'category': categories['accessories'],
                'brand': brands['nike'],
                'description': 'کلاه کپ با طراحی اسپرت',
                'full_description': 'کلاه کپ ورزشی با جنس نخ پنبه و قابلیت تنظیم سایز، مناسب برای فعالیت‌های ورزشی.',
                'price': 280000,
                'old_price': 350000,
                'stock': 50,
                'label': 'sale',
            },
            {
                'name': 'شال گردن زنانه',
                'slug': 'womens-scarf',
                'category': categories['accessories'],
                'brand': brands['zara'],
                'description': 'شال گردن با طرح‌های متنوع',
                'full_description': 'شال گردن زنانه با پارچه نرم و طرح‌های زیبا، مناسب برای فصل پاییز و زمستان.',
                'price': 420000,
                'stock': 35,
                'label': 'new',
            },
        ]

        products = []
        for data in products_data:
            product = Product.objects.create(**data)
            products.append(product)

        return products

    def create_product_images(self, products):
        """ایجاد تصاویر محصولات"""
        # تصاویر موجود در پوشه media/products
        available_images = [
            'products/1.jpg',
            'products/2.jpg',
            'products/3.jpg',
            'products/product-1.jpg',
            'products/product-4.jpg',
            'products/product-5.jpg',
            'products/product-6.jpg',
            'products/product-7.jpg',
            'products/product-9.jpg',
        ]
        
        # برای هر محصول، 2-4 تصویر اضافه می‌کنیم
        for idx, product in enumerate(products):
            # تعداد تصاویر برای این محصول (بین 2 تا 4)
            num_images = 2 + (idx % 3)
            
            for i in range(num_images):
                # انتخاب تصویر به صورت چرخشی
                image_path = available_images[(idx + i) % len(available_images)]
                
                ProductImage.objects.create(
                    product=product,
                    image=image_path,
                    alt_text=f'{product.name} - تصویر {i+1}',
                    is_main=(i == 0),  # اولین تصویر به عنوان تصویر اصلی
                    order=i
                )

    def create_colors_and_sizes(self, products):
        """ایجاد رنگ‌ها و سایزها برای محصولات"""
        colors = [
            {'name': 'مشکی', 'code': '#000000'},
            {'name': 'سفید', 'code': '#FFFFFF'},
            {'name': 'قرمز', 'code': '#FF0000'},
            {'name': 'آبی', 'code': '#0000FF'},
            {'name': 'سبز', 'code': '#00FF00'},
            {'name': 'زرد', 'code': '#FFFF00'},
            {'name': 'نقره ای', 'code': '#C0C0C0'},
            {'name': 'طلایی', 'code': '#FFD700'},
        ]

        sizes = ['xs', 's', 'm', 'l', 'xl', 'xxl']

        # برای محصولات لباس (10 محصول اول)
        for product in products[:10]:
            # اضافه کردن رنگ‌ها (3-4 رنگ برای هر محصول)
            num_colors = 3 + (products.index(product) % 2)
            for i in range(num_colors):
                color = colors[i % len(colors)]
                ProductColor.objects.create(
                    product=product,
                    name=color['name'],
                    code=color['code']
                )

            # اضافه کردن سایزها (4-6 سایز برای هر محصول)
            num_sizes = 4 + (products.index(product) % 3)
            for size in sizes[:num_sizes]:
                ProductSize.objects.create(
                    product=product,
                    size=size
                )

    def create_reviews(self, products):
        """ایجاد نظرات برای محصولات"""
        reviews_data = [
            {
                'name': 'علی احمدی',
                'email': 'ali@example.com',
                'rating': 5,
                'title': 'عالی بود',
                'comment': 'محصول بسیار با کیفیت و ارسال سریع. پیشنهاد می‌کنم.',
                'is_approved': True,
            },
            {
                'name': 'سارا محمدی',
                'email': 'sara@example.com',
                'rating': 4,
                'title': 'خوب بود',
                'comment': 'کیفیت خوبی داشت اما قیمت کمی بالا بود.',
                'is_approved': True,
            },
            {
                'name': 'رضا کریمی',
                'email': 'reza@example.com',
                'rating': 5,
                'title': 'فوق العاده',
                'comment': 'بهترین خریدی که تا حالا داشتم. ممنون از فروشگاه.',
                'is_approved': True,
            },
            {
                'name': 'مریم حسینی',
                'email': 'maryam@example.com',
                'rating': 4,
                'title': 'راضی هستم',
                'comment': 'محصول مطابق توضیحات بود. ارسال هم سریع انجام شد.',
                'is_approved': True,
            },
            {
                'name': 'حسین رضایی',
                'email': 'hossein@example.com',
                'rating': 5,
                'title': 'بی نظیر',
                'comment': 'کیفیت عالی و قیمت مناسب. حتما دوباره خرید می‌کنم.',
                'is_approved': True,
            },
            {
                'name': 'زهرا اکبری',
                'email': 'zahra@example.com',
                'rating': 3,
                'title': 'متوسط',
                'comment': 'محصول خوب بود اما انتظار بیشتری داشتم.',
                'is_approved': True,
            },
            {
                'name': 'امیر محمودی',
                'email': 'amir@example.com',
                'rating': 5,
                'title': 'عالی',
                'comment': 'دقیقا همان چیزی بود که می‌خواستم. ممنون.',
                'is_approved': True,
            },
        ]

        # نظر برای همه محصولات
        for product in products:
            # تعداد نظرات برای هر محصول (بین 2 تا 5)
            num_reviews = 2 + (products.index(product) % 4)
            
            for i in range(num_reviews):
                review_data = reviews_data[i % len(reviews_data)]
                ProductReview.objects.create(
                    product=product,
                    **review_data
                )

    def create_menus(self):
        """ایجاد منوها"""
        # منوی اصلی
        main_menus = [
            {'title': 'خانه', 'url': '/', 'order': 1, 'menu_type': 'main'},
            {'title': 'محصولات', 'url': '/products/', 'order': 2, 'menu_type': 'main'},
            {'title': 'درباره ما', 'url': '/about/', 'order': 3, 'menu_type': 'main'},
            {'title': 'تماس با ما', 'url': '/contact/', 'order': 4, 'menu_type': 'main'},
        ]

        main_items = {}
        for menu_data in main_menus:
            item = MenuItem.objects.create(**menu_data)
            main_items[menu_data['title']] = item

        # زیر منوی محصولات
        products_submenus = [
            {'title': 'لباس زنانه', 'url': '/products/category/womens-clothing/', 'parent': main_items['محصولات'], 'order': 1, 'menu_type': 'main'},
            {'title': 'لباس مردانه', 'url': '/products/category/mens-clothing/', 'parent': main_items['محصولات'], 'order': 2, 'menu_type': 'main'},
            {'title': 'کفش', 'url': '/products/category/shoes/', 'parent': main_items['محصولات'], 'order': 3, 'menu_type': 'main'},
            {'title': 'لوازم جانبی', 'url': '/products/category/accessories/', 'parent': main_items['محصولات'], 'order': 4, 'menu_type': 'main'},
        ]

        for menu_data in products_submenus:
            MenuItem.objects.create(**menu_data)

        # منوی فوتر
        footer_menus = [
            {'title': 'حساب کاربری', 'url': '/accounts/login/', 'order': 1, 'menu_type': 'footer'},
            {'title': 'سبد خرید', 'url': '/cart/', 'order': 2, 'menu_type': 'footer'},
            {'title': 'لیست علاقه‌مندی', 'url': '/wishlist/', 'order': 3, 'menu_type': 'footer'},
            {'title': 'پیگیری سفارش', 'url': '/orders/', 'order': 4, 'menu_type': 'footer'},
            {'title': 'قوانین و مقررات', 'url': '/terms/', 'order': 5, 'menu_type': 'footer'},
            {'title': 'حریم خصوصی', 'url': '/privacy/', 'order': 6, 'menu_type': 'footer'},
        ]

        for menu_data in footer_menus:
            MenuItem.objects.create(**menu_data)

    def create_contact_info(self):
        """ایجاد اطلاعات تماس"""
        ContactInfo.objects.create(
            office_address='تهران، خیابان ولیعصر، پلاک 123، طبقه 4',
            email='info@arioshop.com',
            phone1='021-12345678',
            phone2='021-87654321',
            map_embed='<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3239.9999999999995!2d51.42!3d35.7!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMzXCsDQyJzAwLjAiTiA1McKwMjUnMTIuMCJF!5e0!3m2!1sen!2s!4v1234567890123!5m2!1sen!2s" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>',
            instagram_url='https://instagram.com/arioshop',
            twitter_url='https://twitter.com/arioshop',
            facebook_url='https://facebook.com/arioshop',
            is_active=True,
        )

    def create_about_page(self):
        """ایجاد صفحه درباره ما"""
        AboutPage.objects.create(
            vision_title='دید ما',
            vision_description='ما در آریو شاپ تلاش می‌کنیم تا بهترین تجربه خرید آنلاین را برای شما فراهم کنیم. هدف ما ارائه محصولات با کیفیت و خدمات عالی است.',
            mission_title='ماموریت ما',
            mission_description='ماموریت ما ایجاد یک پلتفرم خرید آنلاین قابل اعتماد و راحت است که نیازهای مشتریان را برآورده کند.',
            who_we_are_title='ما چه کسانی هستیم',
            who_we_are_subtitle='فروشگاه آنلاین آریو شاپ',
            who_we_are_description='آریو شاپ یک فروشگاه آنلاین معتبر است که از سال 1400 فعالیت خود را آغاز کرده است. ما با ارائه محصولات اصل و با کیفیت، اعتماد هزاران مشتری را جلب کرده‌ایم.',
            brands_title='برند های معروفی که با ما در حال همکاری هستند',
            brands_description='ما افتخار همکاری با بهترین برندهای جهانی را داریم.',
            team_title='آشنایی با تیم ما',
            testimonials_title='نظرات مشتری های فروشگاه',
        )

    def create_about_brands(self):
        """ایجاد برندهای صفحه درباره ما"""
        brands_data = [
            {'name': 'نایک', 'website': 'https://nike.com', 'order': 1},
            {'name': 'آدیداس', 'website': 'https://adidas.com', 'order': 2},
            {'name': 'پوما', 'website': 'https://puma.com', 'order': 3},
            {'name': 'زارا', 'website': 'https://zara.com', 'order': 4},
        ]

        for brand_data in brands_data:
            AboutBrand.objects.create(**brand_data)

    def create_team_members(self):
        """ایجاد اعضای تیم"""
        team_data = [
            {
                'name': 'محمد رضایی',
                'position': 'مدیر عامل',
                'bio': 'مدیر عامل با 10 سال تجربه در حوزه تجارت الکترونیک',
                'instagram_url': 'https://instagram.com/mohammad',
                'order': 1,
            },
            {
                'name': 'فاطمه احمدی',
                'position': 'مدیر فروش',
                'bio': 'مدیر فروش با تجربه و متخصص در بازاریابی دیجیتال',
                'instagram_url': 'https://instagram.com/fatemeh',
                'order': 2,
            },
            {
                'name': 'علی کریمی',
                'position': 'مدیر فنی',
                'bio': 'توسعه دهنده وب با تخصص در Django و React',
                'instagram_url': 'https://instagram.com/ali',
                'order': 3,
            },
        ]

        for member_data in team_data:
            TeamMember.objects.create(**member_data)

    def create_testimonials(self):
        """ایجاد نظرات مشتریان"""
        testimonials_data = [
            {
                'customer_name': 'سارا محمدی',
                'customer_role': 'مشتری',
                'review': 'تجربه خرید من از آریو شاپ فوق العاده بود. محصولات با کیفیت و ارسال سریع.',
                'order': 1,
            },
            {
                'customer_name': 'رضا احمدی',
                'customer_role': 'مشتری',
                'review': 'پشتیبانی عالی و قیمت‌های مناسب. حتما دوباره خرید می‌کنم.',
                'order': 2,
            },
            {
                'customer_name': 'مریم کریمی',
                'customer_role': 'مشتری',
                'review': 'بهترین فروشگاه آنلاین که تا حالا ازش خرید کردم. ممنون از تیم آریو شاپ.',
                'order': 3,
            },
        ]

        for testimonial_data in testimonials_data:
            Testimonial.objects.create(**testimonial_data)
