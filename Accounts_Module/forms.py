"""
فرم‌های ماژول کاربران - ورود، ثبت‌نام و بازیابی رمز عبور
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()


class LoginForm(AuthenticationForm):
    """فرم ورود با پشتیبانی از مرا به خاطر بسپار"""

    username = forms.CharField(
        label='نام کاربری یا آدرس ایمیل',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'singin-email-2',
            'placeholder': ' ',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'singin-password-2',
            'placeholder': ' ',
            'autocomplete': 'current-password',
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'custom-control-input', 'id': 'signin-remember-2'}),
    )


class RegisterForm(UserCreationForm):
    """فرم ثبت‌نام با ایمیل و رمز عبور"""

    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'register-email-2',
            'placeholder': ' ',
            'autocomplete': 'email',
        }),
    )
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'register-password-2',
            'placeholder': ' ',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label='تکرار رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'register-password2-2',
            'placeholder': ' ',
            'autocomplete': 'new-password',
        }),
    )
    accept_terms = forms.BooleanField(
        label='قوانین و مقررات',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'custom-control-input', 'id': 'register-policy-2'}),
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email


class ProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل در داشبورد"""

    class Meta:
        model = UserProfile
        fields = ('full_name', 'phone', 'address', 'postal_code', 'city')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام و نام خانوادگی'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '۰۹۱۲۳۴۵۶۷۸۹'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'آدرس کامل پستی'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی ۱۰ رقمی'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهر'}),
        }
        labels = {
            'full_name': 'نام و نام خانوادگی',
            'phone': 'شماره تماس',
            'address': 'آدرس',
            'postal_code': 'کد پستی',
            'city': 'شهر',
        }


class VerifyCodeForm(forms.Form):
    """فرم ورود کد تأیید ۶ رقمی"""

    code = forms.CharField(
        max_length=6,
        min_length=6,
        label='کد تأیید',
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '------',
            'autocomplete': 'one-time-code',
            'dir': 'ltr',
            'style': 'font-size: 24px; letter-spacing: 12px; font-weight: bold;',
        }),
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '')
        if not code.isdigit():
            raise forms.ValidationError('کد تأیید باید فقط شامل اعداد باشد.')
        return code


class ResetPasswordWithCodeForm(forms.Form):
    """فرم بازیابی رمز عبور با کد OTP"""

    code = forms.CharField(
        max_length=6,
        min_length=6,
        label='کد تأیید',
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '------',
            'dir': 'ltr',
            'style': 'font-size: 20px; letter-spacing: 10px; font-weight: bold;',
        }),
    )
    new_password1 = forms.CharField(
        label='رمز عبور جدید',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': ' ',
            'autocomplete': 'new-password',
        }),
    )
    new_password2 = forms.CharField(
        label='تکرار رمز عبور جدید',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': ' ',
            'autocomplete': 'new-password',
        }),
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '')
        if not code.isdigit():
            raise forms.ValidationError('کد تأیید باید فقط شامل اعداد باشد.')
        return code

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'رمزهای عبور مطابقت ندارند.')
        return cleaned_data


class ForgetPasswordEmailForm(forms.Form):
    """فرم ورود ایمیل برای بازیابی رمز عبور"""

    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': ' ',
            'autocomplete': 'email',
        }),
    )
