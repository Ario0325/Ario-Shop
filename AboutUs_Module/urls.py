from django.urls import path
from . import views

app_name = 'AboutUs_Module'

urlpatterns = [
    path('', views.about_us_view, name='about'),
]