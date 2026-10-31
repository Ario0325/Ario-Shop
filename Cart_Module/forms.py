"""
فرم‌های ماژول سبد خرید - اطلاعات ارسال در مرحله چک‌اوت
"""
import re

from django import forms

_PERSIAN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def _normalize_digits(value):
    """ارقام فارسی/عربی را به لاتین تبدیل می‌کند تا اعتبارسنجی ساده بماند."""
    if not value:
        return value
    return str(value).translate(_PERSIAN_DIGITS).strip()


class CheckoutAddressForm(forms.Form):
    """اطلاعات ارسال سفارش؛ با پروفایل کاربر پیش‌پر می‌شود."""

    full_name = forms.CharField(
        label='نام و نام خانوادگی',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام و نام خانوادگی',
            'autocomplete': 'name',
        }),
    )
    phone = forms.CharField(
        label='شماره تماس',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '۰۹۱۲۳۴۵۶۷۸۹',
            'inputmode': 'tel',
            'autocomplete': 'tel',
            'dir': 'ltr',
        }),
    )
    city = forms.CharField(
        label='شهر',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شهر',
            'autocomplete': 'address-level2',
        }),
    )
    address = forms.CharField(
        label='آدرس',
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'آدرس کامل پستی',
            'autocomplete': 'street-address',
        }),
    )
    postal_code = forms.CharField(
        label='کد پستی',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد پستی ۱۰ رقمی (اختیاری)',
            'inputmode': 'numeric',
            'autocomplete': 'postal-code',
            'dir': 'ltr',
        }),
    )

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if profile is not None and not self.is_bound:
            self.initial.update({
                'full_name': profile.full_name or '',
                'phone': profile.phone or '',
                'city': profile.city or '',
                'address': profile.address or '',
                'postal_code': profile.postal_code or '',
            })

    def clean_phone(self):
        phone = _normalize_digits(self.cleaned_data.get('phone'))
        digits = re.sub(r'[\s\-()]', '', phone or '')
        if digits.startswith('+98'):
            digits = '0' + digits[3:]
        elif digits.startswith('0098'):
            digits = '0' + digits[4:]
        elif digits.startswith('98') and len(digits) == 12:
            digits = '0' + digits[2:]
        if not re.fullmatch(r'0?\d{10}', digits):
            raise forms.ValidationError('شماره تماس را به صورت ۱۱ رقمی و با ۰۹ وارد کنید.')
        return digits

    def clean_postal_code(self):
        postal_code = _normalize_digits(self.cleaned_data.get('postal_code'))
        postal_code = re.sub(r'[\s\-]', '', postal_code or '')
        if postal_code and not re.fullmatch(r'\d{10}', postal_code):
            raise forms.ValidationError('کد پستی باید ۱۰ رقم باشد.')
        return postal_code
