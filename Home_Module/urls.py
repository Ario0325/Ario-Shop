from django.urls import path
from .views import index, robots_txt


urlpatterns = [
    path('', index, name='index'),
    path('robots.txt', robots_txt, name='robots_txt'),
]
