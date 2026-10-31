from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('empty/', views.cart_empty, name='empty'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('remove/<int:product_id>/', views.cart_remove, name='remove'),
    path('update/', views.cart_update, name='update'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/<int:order_id>/', views.payment_view, name='payment'),
    path('invoice/<int:order_id>/', views.invoice_view, name='invoice'),
    # کد تخفیف
    path('discount/apply/', views.discount_apply, name='discount_apply'),
    path('discount/remove/', views.discount_remove, name='discount_remove'),
    # API برای اعلان‌های سفارش
    path('api/new-orders/', views.api_new_orders, name='api_new_orders'),
]
