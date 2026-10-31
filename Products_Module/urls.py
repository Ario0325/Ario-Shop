from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('search/', views.search_products, name='search'),
    path('category/<slug:slug>/', views.category_products, name='category'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]