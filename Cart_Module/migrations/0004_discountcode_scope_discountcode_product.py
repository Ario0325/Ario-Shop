# Generated manually - اضافه کردن فیلدهای scope و product به DiscountCode

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Cart_Module', '0003_discountcode_order_discount_amount_order_subtotal_and_more'),
        ('Products_Module', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountcode',
            name='scope',
            field=models.CharField(
                choices=[('cart', 'کل سبد خرید'), ('product', 'محصول خاص')],
                default='cart',
                max_length=20,
                verbose_name='محدوده تخفیف',
                help_text='«کل سبد خرید»: تخفیف روی مجموع سبد اعمال می‌شود. «محصول خاص»: تخفیف فقط روی قیمت یک محصول مشخص اعمال می‌شود.',
            ),
        ),
        migrations.AddField(
            model_name='discountcode',
            name='product',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='discount_codes',
                to='Products_Module.product',
                verbose_name='محصول مرتبط',
                help_text='فقط در صورتی که محدوده تخفیف «محصول خاص» باشد، این فیلد را پر کنید.',
            ),
        ),
        # به‌روزرسانی verbose_name فیلدهای موجود به فارسی
        migrations.AlterField(
            model_name='discountcode',
            name='code',
            field=models.CharField(
                max_length=50,
                unique=True,
                verbose_name='کد تخفیف',
                help_text='کد تخفیف را بدون فاصله وارد کنید. سیستم آن را خودکار به حروف بزرگ تبدیل می‌کند.',
            ),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='title',
            field=models.CharField(
                max_length=200,
                verbose_name='عنوان',
                help_text='یک عنوان توصیفی برای این کد تخفیف وارد کنید.',
            ),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='description',
            field=models.TextField(
                blank=True,
                verbose_name='توضیحات',
                help_text='توضیحات اضافی درباره این کد تخفیف (اختیاری).',
            ),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='discount_type',
            field=models.CharField(
                choices=[('percent', 'درصدی'), ('fixed', 'مبلغ ثابت')],
                default='percent',
                max_length=20,
                verbose_name='نوع تخفیف',
            ),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='is_active',
            field=models.BooleanField(
                default=True,
                verbose_name='فعال',
                help_text='اگر غیرفعال باشد، کاربران نمی‌توانند از این کد استفاده کنند.',
            ),
        ),
        migrations.AlterModelOptions(
            name='discountcode',
            options={
                'verbose_name': 'کد تخفیف',
                'verbose_name_plural': 'کدهای تخفیف',
                'ordering': ['-created_at'],
            },
        ),
    ]
