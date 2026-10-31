from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginRegisterView.as_view(), name='login_register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.user_orders_view, name='orders'),
    path('orders/<int:order_id>/', views.user_order_detail_view, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.user_order_cancel_view, name='order_cancel'),
    path('comments/', views.user_comments_view, name='comments'),
    path('forget-password/', views.ForgetPasswordView.as_view(), name='forget_password'),
    path('forget-password/verify/', views.ForgetPasswordVerifyView.as_view(), name='forget_password_verify'),
    path('forget-password/resend/', views.ResendResetCodeView.as_view(), name='resend_reset_code'),
    path('reset/done/', views.ForgetPasswordCompleteView.as_view(), name='password_reset_complete'),
]
