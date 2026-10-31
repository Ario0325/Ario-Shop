from django.urls import path
from .admin_views import dashboard_stats_api

urlpatterns = [
    path('dashboard-stats/', dashboard_stats_api, name='admin-dashboard-stats'),
]
