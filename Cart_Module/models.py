from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class DiscountCode(models.Model):
    """مدل کد تخفیف - پشتیبانی از تخفیف کل سبد یا محصول خاص"""

    TYPE_PERCENT = 'percent'
    TYPE_FIXED = 'fixed'
    DISCOUNT_TYPE_CHOICES = [
        (TYPE_PERCENT, 'درصدی'),
        (TYPE_FIXED, 'مبلغ ثابت'),
    ]

    SCOPE_CART = 'cart'
    SCOPE_PRODUCT = 'product'
    SCOPE_CHOICES = [
        (SCOPE_CART, 'کل سبد خرید'),
        (SCOPE_PRODUCT, 'محصول خاص'),
    ]

    # ── اطلاعات پایه ──────────────────────────────────────────────────────────
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='کد تخفیف',
        help_text='کد تخفیف را بدون فاصله وارد کنید. سیستم آن را خودکار به حروف بزرگ تبدیل می‌کند.',
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان',
        help_text='یک عنوان توصیفی برای این کد تخفیف وارد کنید. مثال: تخفیف ویژه نوروز',
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات',
        help_text='توضیحات اضافی درباره این کد تخفیف (اختیاری).',
    )

    # ── نوع و محدوده تخفیف ────────────────────────────────────────────────────
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default=TYPE_PERCENT,
        verbose_name='نوع تخفیف',
        help_text='«درصدی»: مثلاً ۱۰٪ از مبلغ. «مبلغ ثابت»: مثلاً ۵۰,۰۰۰ تومان کسر می‌شود.',
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_CART,
        verbose_name='محدوده تخفیف',
        help_text='«کل سبد خرید»: تخفیف روی مجموع سبد اعمال می‌شود. «محصول خاص»: تخفیف فقط روی قیمت یک محصول مشخص اعمال می‌شود.',
    )
    product = models.ForeignKey(
        'Products_Module.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discount_codes',
        verbose_name='محصول مرتبط',
        help_text='فقط در صورتی که محدوده تخفیف «محصول خاص» باشد، این فیلد را پر کنید.',
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(1)],
        verbose_name='مقدار تخفیف',
        help_text='اگر نوع تخفیف «درصدی» است، عدد درصد را وارد کنید (مثلاً ۱۰ برای ۱۰٪). اگر «مبلغ ثابت» است، مبلغ به تومان وارد کنید.',
    )
    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='سقف مبلغ تخفیف (تومان)',
        help_text='فقط برای تخفیف درصدی: حداکثر مبلغی که تخفیف می‌تواند داشته باشد. مثلاً اگر ۱۰٪ تخفیف با سقف ۵۰,۰۰۰ تومان، حتی اگر ۱۰٪ بیشتر شود، بیشتر از ۵۰,۰۰۰ تومان کسر نمی‌شود.',
    )

    # ── شرایط استفاده ─────────────────────────────────────────────────────────
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='حداقل مبلغ سفارش (تومان)',
        help_text='کاربر باید حداقل این مبلغ در سبد خرید داشته باشد تا بتواند از این کد استفاده کند. صفر یعنی بدون محدودیت.',
    )
    starts_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ شروع',
        help_text='از چه تاریخ و ساعتی این کد فعال می‌شود. خالی بگذارید اگر از همین لحظه فعال باشد.',
    )
    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ انقضا',
        help_text='تا چه تاریخ و ساعتی این کد معتبر است. خالی بگذارید اگر بدون تاریخ انقضا باشد.',
    )

    # ── محدودیت استفاده ───────────────────────────────────────────────────────
    usage_limit_total = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='سقف کل استفاده',
        help_text='حداکثر چند بار این کد می‌تواند توسط همه کاربران استفاده شود. خالی بگذارید برای بدون محدودیت.',
    )
    usage_limit_per_user = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='سقف استفاده هر کاربر',
        help_text='هر کاربر حداکثر چند بار می‌تواند از این کد استفاده کند. خالی بگذارید برای بدون محدودیت.',
    )

    # ── آمار و وضعیت ──────────────────────────────────────────────────────────
    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد دفعات استفاده',
        help_text='این فیلد به‌صورت خودکار توسط سیستم به‌روزرسانی می‌شود.',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='اگر غیرفعال باشد، کاربران نمی‌توانند از این کد استفاده کنند.',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'
        ordering = ['-created_at']
        indexes = [
            # Index for active discount codes
            models.Index(fields=['is_active', 'starts_at', 'ends_at'], name='discount_active_idx'),
            # Index for code lookup
            models.Index(fields=['code'], name='discount_code_idx'),
        ]

    def __str__(self):
        scope_label = 'کل سبد' if self.scope == self.SCOPE_CART else f'محصول: {self.product}'
        return f'{self.code} — {self.title} ({scope_label})'

    def clean(self):
        """اعتبارسنجی سطح مدل"""
        errors = {}

        # بررسی تاریخ شروع و پایان
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            errors['ends_at'] = 'تاریخ انقضا باید بعد از تاریخ شروع باشد.'

        # بررسی محصول برای scope=product
        if self.scope == self.SCOPE_PRODUCT and not self.product_id:
            errors['product'] = 'برای تخفیف محصول خاص، باید یک محصول انتخاب کنید.'

        # بررسی درصد معتبر
        if self.discount_type == self.TYPE_PERCENT and self.value and self.value > 100:
            errors['value'] = 'درصد تخفیف نمی‌تواند بیشتر از ۱۰۰ باشد.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # نرمال‌سازی کد: حذف فاصله و تبدیل به حروف بزرگ
        self.code = self.code.strip().upper()
        # اگر scope=cart باشد، product را پاک کن
        if self.scope == self.SCOPE_CART:
            self.product = None
        super().save(*args, **kwargs)

    def has_usage_remaining(self):
        """آیا ظرفیت استفاده باقی مانده؟"""
        if self.usage_limit_total is not None and self.used_count >= self.usage_limit_total:
            return False
        return True

    def user_can_use(self, user):
        """آیا این کاربر می‌تواند از این کد استفاده کند؟"""
        if not user or not user.is_authenticated:
            return True  # کاربر مهمان - بررسی per_user اعمال نمی‌شود
        if self.usage_limit_per_user is not None:
            # سفارش‌های لغوشده نباید سهمیهٔ کاربر را مصرف‌شده نگه دارند.
            user_usage = self.orders.filter(user=user).exclude(status='cancelled').count()
            if user_usage >= self.usage_limit_per_user:
                return False
        return True

    def calculate_discount(self, base_amount):
        """محاسبه مبلغ تخفیف بر اساس مبلغ پایه"""
        if self.discount_type == self.TYPE_PERCENT:
            discount = (base_amount * self.value / Decimal('100')).quantize(Decimal('1'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = min(self.value, base_amount)
        return discount

    def get_discount_for_cart(self, cart_items):
        """
        محاسبه تخفیف برای سبد خرید.
        cart_items: لیست دیکشنری‌های {'product': Product, 'quantity': int, 'price': Decimal, 'total': Decimal}
        برمی‌گرداند: (discount_amount, base_amount, applicable_product_id_or_None)
        """
        if self.scope == self.SCOPE_CART:
            base_amount = sum(item['total'] for item in cart_items)
            return self.calculate_discount(base_amount), base_amount, None
        else:
            # محصول خاص
            for item in cart_items:
                if item['product'].id == self.product_id:
                    base_amount = item['total']
                    return self.calculate_discount(base_amount), base_amount, self.product_id
            return Decimal('0'), Decimal('0'), None


class Order(models.Model):
    """سفارش - برای فاکتور و پرداخت"""

    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='کاربر',
    )
    order_number = models.CharField(max_length=50, unique=True, verbose_name='شماره سفارش')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')

    # اطلاعات تحویل (می‌توان از پروفایل کاربر پر شود)
    full_name = models.CharField(max_length=200, verbose_name='نام مشتری')
    phone = models.CharField(max_length=20, verbose_name='شماره تماس')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    address = models.TextField(verbose_name='آدرس')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='کد پستی')
    city = models.CharField(max_length=100, blank=True, verbose_name='شهر')

    subtotal = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='جمع قبل از تخفیف')
    discount_code = models.ForeignKey(
        DiscountCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='کد تخفیف',
    )
    discount_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='مبلغ تخفیف')
    total = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='مبلغ نهایی')
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='هزینه ارسال')
    tax = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='مالیات')

    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']
        indexes = [
            # Index for user orders
            models.Index(fields=['user', '-created_at'], name='order_user_date_idx'),
            # Index for order status filtering
            models.Index(fields=['status', '-created_at'], name='order_status_idx'),
        ]

    def __str__(self):
        return f'{self.order_number} - {self.full_name}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_part = timezone.now().strftime('%Y%m%d')
            # Use UUID for secure, unpredictable order numbers
            unique_part = uuid.uuid4().hex[:8].upper()
            self.order_number = f'ORD-{date_part}-{unique_part}'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """آیتم سفارش - هر محصول در سفارش"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سفارش',
    )
    product = models.ForeignKey(
        'Products_Module.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name='محصول',
    )
    product_name = models.CharField(max_length=300, verbose_name='نام محصول')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت واحد')
    total = models.DecimalField(max_digits=14, decimal_places=0, verbose_name='مجموع')

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'

    def save(self, *args, **kwargs):
        if self.price is not None and self.quantity is not None:
            self.total = self.price * self.quantity
        super().save(*args, **kwargs)


class CartItem(models.Model):
    """آیتم سبد خرید پایدار برای هر کاربر"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='کاربر',
    )
    product = models.ForeignKey(
        'Products_Module.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='محصول',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'
        unique_together = ('user', 'product')
        indexes = [
            # Index for user cart items lookup
            models.Index(fields=['user', 'created_at'], name='cart_user_date_idx'),
        ]

    def __str__(self):
        return f'{self.user} - {self.product} ({self.quantity})'
