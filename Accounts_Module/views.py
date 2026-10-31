"""
ویوهای ماژول کاربران - ورود، ثبت‌نام با OTP، خروج و بازیابی رمز عبور با OTP
"""
import logging

from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from Cart_Module.services import sync_cart_to_db, merge_cart_on_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import View
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
import hmac

from .forms import (
    LoginForm, RegisterForm, ProfileForm,
    VerifyCodeForm, ResetPasswordWithCodeForm, ForgetPasswordEmailForm,
)
from .models import UserProfile, UserVerification, PasswordResetToken
from .services import N8nAuthService

User = get_user_model()
logger = logging.getLogger(__name__)


class LoginRegisterView(View):
    """صفحه ورود و ثبت‌نام با تب‌ها"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')
        return render(request, 'accounts/login_register.html', {
            'login_form': LoginForm(),
            'register_form': RegisterForm(),
        })

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True))
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('index')

        if 'login' in request.POST:
            form = LoginForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                remember_me = form.cleaned_data.get('remember_me', True)
                if not remember_me:
                    request.session.set_expiry(0)
                request.session.cycle_key()
                login(request, user, backend='Accounts_Module.backends.EmailOrUsernameBackend')
                merge_cart_on_login(request)
                messages.success(request, _('با موفقیت وارد شدید.'))
                next_url = request.GET.get('next', reverse_lazy('index'))
                if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    next_url = reverse_lazy('index')
                return redirect(next_url)
            return render(request, 'accounts/login_register.html', {
                'login_form': form,
                'register_form': RegisterForm(),
                'active_tab': 'login',
            })

        if 'register' in request.POST:
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                verification = UserVerification.objects.create(user=user)

                email_sent = N8nAuthService.send_verification_email(
                    email=user.email,
                    username=user.email.split('@')[0],
                    code=verification.code,
                )

                if not email_sent:
                    user.delete()
                    messages.error(request, _('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.'))
                    return render(request, 'accounts/login_register.html', {
                        'login_form': LoginForm(),
                        'register_form': form,
                        'active_tab': 'register',
                    })

                request.session['verify_email'] = user.email
                messages.success(request, _('کد تأیید به ایمیل شما ارسال شد.'))
                return redirect('accounts:verify_email')

            return render(request, 'accounts/login_register.html', {
                'login_form': LoginForm(),
                'register_form': form,
                'active_tab': 'register',
            })

        return redirect('accounts:login_register')


class VerifyEmailView(View):
    """صفحه تأیید ایمیل با کد OTP"""

    def get(self, request):
        email = request.GET.get('email') or request.session.get('verify_email')
        if not email:
            messages.error(request, _('ابتدا ثبت‌نام کنید.'))
            return redirect('accounts:login_register')

        try:
            user = User.objects.get(email=email)
            verification = user.verification
            if verification.is_verified:
                messages.info(request, _('ایمیل شما قبلاً تأیید شده است. لطفاً وارد شوید.'))
                return redirect('accounts:login_register')
        except (User.DoesNotExist, UserVerification.DoesNotExist):
            messages.error(request, _('کاربری با این ایمیل یافت نشد.'))
            return redirect('accounts:login_register')

        return render(request, 'accounts/verify_email.html', {
            'form': VerifyCodeForm(),
            'email': email,
        })

    def post(self, request):
        email = request.session.get('verify_email')
        if not email:
            email = request.GET.get('email')
        if not email:
            messages.error(request, _('ابتدا ثبت‌نام کنید.'))
            return redirect('accounts:login_register')

        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                user = User.objects.get(email=email)
                verification = user.verification
            except (User.DoesNotExist, UserVerification.DoesNotExist):
                messages.error(request, _('کاربری با این ایمیل یافت نشد.'))
                return redirect('accounts:login_register')

            if verification.is_expired():
                messages.error(request, _('کد تأیید منقضی شده است. لطفاً کد جدید دریافت کنید.'))
                return render(request, 'accounts/verify_email.html', {
                    'form': form,
                    'email': email,
                    'expired': True,
                })

            if not hmac.compare_digest(verification.code, code):
                messages.error(request, _('کد تأیید اشتباه است.'))
                return render(request, 'accounts/verify_email.html', {
                    'form': form,
                    'email': email,
                })

            verification.is_verified = True
            verification.save()
            user.is_active = True
            user.save()

            request.session.pop('verify_email', None)
            request.session.cycle_key()
            login(request, user, backend='Accounts_Module.backends.EmailOrUsernameBackend')
            merge_cart_on_login(request)
            messages.success(request, _('حساب شما با موفقیت تأیید شد. خوش آمدید!'))
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('index')

        return render(request, 'accounts/verify_email.html', {
            'form': form,
            'email': email,
        })


class ResendVerificationView(View):
    """ارسال مجدد کد تأیید ثبت‌نام"""

    @method_decorator(ratelimit(key='ip', rate='3/m', block=True))
    def post(self, request):
        email = request.POST.get('email') or request.session.get('verify_email')
        if not email:
            messages.error(request, _('ایمیل یافت نشد.'))
            return redirect('accounts:login_register')

        try:
            user = User.objects.get(email=email)
            verification = user.verification
        except (User.DoesNotExist, UserVerification.DoesNotExist):
            messages.error(request, _('کاربری با این ایمیل یافت نشد.'))
            return redirect('accounts:login_register')

        if verification.is_verified:
            messages.info(request, _('این حساب قبلاً تأیید شده است.'))
            return redirect('accounts:login_register')

        verification.refresh_code()

        email_sent = N8nAuthService.send_verification_email(
            email=email,
            username=email.split('@')[0],
            code=verification.code,
        )

        if email_sent:
            messages.success(request, _('کد جدید به ایمیل شما ارسال شد.'))
        else:
            messages.error(request, _('خطا در ارسال ایمیل. لطفاً دوباره تلاش کنید.'))

        request.session['verify_email'] = email
        return redirect(reverse_lazy('accounts:verify_email'))


class LogoutView(View):
    """خروج از حساب کاربری"""

    def post(self, request):
        sync_cart_to_db(request)
        request.session.pop('_cart_loaded', None)
        logout(request)
        messages.info(request, _('از حساب خود خارج شدید.'))
        return redirect('index')


class ForgetPasswordView(View):
    """درخواست بازیابی رمز عبور - ارسال کد OTP"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')
        return render(request, 'accounts/forget_password.html', {
            'form': ForgetPasswordEmailForm(),
        })

    @method_decorator(ratelimit(key='ip', rate='3/m', block=True))
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('index')

        form = ForgetPasswordEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                messages.success(request, _('اگر این ایمیل در سیستم ثبت باشد، کد بازیابی ارسال می‌شود.'))
                return redirect('accounts:forget_password')

            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            reset_token = PasswordResetToken.objects.create(user=user)

            email_sent = N8nAuthService.send_password_reset_email(
                email=email,
                username=email.split('@')[0],
                code=reset_token.code,
            )

            if not email_sent:
                reset_token.delete()
                messages.error(request, _('خطا در ارسال ایمیل. لطفاً دوباره تلاش کنید.'))
                return render(request, 'accounts/forget_password.html', {'form': form})

            request.session['reset_email'] = email
            messages.success(request, _('کد بازیابی به ایمیل شما ارسال شد.'))
            return redirect('accounts:forget_password_verify')

        return render(request, 'accounts/forget_password.html', {'form': form})


class ForgetPasswordVerifyView(View):
    """تأیید کد OTP و تنظیم رمز جدید"""

    def get(self, request):
        email = request.session.get('reset_email')
        if not email:
            messages.error(request, _('ابتدا درخواست بازیابی رمز دهید.'))
            return redirect('accounts:forget_password')

        return render(request, 'accounts/forget_password_verify.html', {
            'form': ResetPasswordWithCodeForm(),
            'email': email,
        })

    def post(self, request):
        email = request.session.get('reset_email')
        if not email:
            messages.error(request, _('ابتدا درخواست بازیابی رمز دهید.'))
            return redirect('accounts:forget_password')

        form = ResetPasswordWithCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_password = form.cleaned_data['new_password1']

            try:
                user = User.objects.get(email=email, is_active=True)
                reset_token = PasswordResetToken.objects.filter(
                    user=user, is_used=False,
                ).latest('created_at')
            except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
                messages.error(request, _('درخواست بازیابی یافت نشد. لطفاً دوباره تلاش کنید.'))
                return redirect('accounts:forget_password')

            if reset_token.is_expired():
                messages.error(request, _('کد بازیابی منقضی شده است. لطفاً کد جدید دریافت کنید.'))
                return render(request, 'accounts/forget_password_verify.html', {
                    'form': form,
                    'email': email,
                    'expired': True,
                })

            if not hmac.compare_digest(reset_token.code, code):
                messages.error(request, _('کد بازیابی اشتباه است.'))
                return render(request, 'accounts/forget_password_verify.html', {
                    'form': form,
                    'email': email,
                })

            user.set_password(new_password)
            user.save()
            reset_token.is_used = True
            reset_token.save()

            request.session.pop('reset_email', None)
            messages.success(request, _('رمز عبور شما با موفقیت تغییر کرد.'))
            return redirect('accounts:password_reset_complete')

        return render(request, 'accounts/forget_password_verify.html', {
            'form': form,
            'email': email,
        })


class ResendResetCodeView(View):
    """ارسال مجدد کد بازیابی رمز عبور"""

    @method_decorator(ratelimit(key='ip', rate='3/m', block=True))
    def post(self, request):
        email = request.session.get('reset_email')
        if not email:
            messages.error(request, _('ابتدا درخواست بازیابی رمز دهید.'))
            return redirect('accounts:forget_password')

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            messages.error(request, _('کاربری با این ایمیل یافت نشد.'))
            return redirect('accounts:forget_password')

        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        reset_token = PasswordResetToken.objects.create(user=user)

        email_sent = N8nAuthService.send_password_reset_email(
            email=email,
            username=email.split('@')[0],
            code=reset_token.code,
        )

        if email_sent:
            messages.success(request, _('کد جدید به ایمیل شما ارسال شد.'))
        else:
            messages.error(request, _('خطا در ارسال ایمیل. لطفاً دوباره تلاش کنید.'))

        return redirect('accounts:forget_password_verify')


class ForgetPasswordCompleteView(View):
    """صفحه اتمام بازیابی رمز"""

    def get(self, request):
        return render(request, 'accounts/forget_password_complete.html')


@login_required
def dashboard_view(request):
    """داشبورد کاربر - ویرایش اطلاعات پروفایل"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, _('اطلاعات با موفقیت ذخیره شد.'))
            return redirect('accounts:dashboard')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/dashboard.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def user_orders_view(request):
    """لیست سفارشات کاربر"""
    from Cart_Module.models import Order
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product__images'
    ).order_by('-created_at')
    page_obj = Paginator(orders, 20).get_page(request.GET.get('page'))
    return render(request, 'accounts/orders.html', {
        'orders': page_obj.object_list,
        'page_obj': page_obj,
    })


@login_required
def user_order_detail_view(request, order_id):
    """جزئیات یک سفارش"""
    from Cart_Module.models import Order
    from django.http import Http404
    try:
        order = Order.objects.prefetch_related('items__product__images').get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        raise Http404("سفارش یافت نشد")
    return render(request, 'accounts/order_detail.html', {
        'order': order,
    })


@login_required
@require_POST
def user_order_cancel_view(request, order_id):
    """لغو سفارش - فقط برای سفارشاتی که ارسال نشده‌اند"""
    from Cart_Module.models import Order
    from django.http import Http404, HttpResponseForbidden

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        raise Http404("سفارش یافت نشد")

    cancellable_statuses = ['pending', 'paid', 'processing']

    if order.status not in cancellable_statuses:
        messages.error(request, _('این سفارش قابل لغو نیست.'))
        return redirect('accounts:order_detail', order_id=order.id)

    if request.method == 'POST':
        from django.db import transaction
        with transaction.atomic():
            order = type(order).objects.select_for_update().get(pk=order.pk)
            if order.status not in cancellable_statuses:
                messages.error(request, _('این سفارش قابل لغو نیست.'))
                return redirect('accounts:order_detail', order_id=order.id)
            for item in order.items.select_related('product').all():
                if item.product:
                    item.product.stock += item.quantity
                    if item.product.stock > 0:
                        item.product.is_available = True
                    item.product.save(update_fields=['stock', 'is_available'])
            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])
        messages.success(request, _('سفارش با موفقیت لغو شد.'))
        return redirect('accounts:orders')


@login_required
def user_comments_view(request):
    """لیست نظرات کاربر"""
    from Products_Module.models import ProductReview
    reviews = ProductReview.objects.filter(user=request.user).select_related('product').prefetch_related(
        'product__images'
    ).order_by('-created_at')
    page_obj = Paginator(reviews, 20).get_page(request.GET.get('page'))
    return render(request, 'accounts/comments.html', {
        'reviews': page_obj.object_list,
        'page_obj': page_obj,
    })
