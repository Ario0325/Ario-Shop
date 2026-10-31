from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

from . import admin_stats


@staff_member_required
def dashboard_stats_api(request):
    days = admin_stats.normalize_days(request.GET.get('days', 30))

    return JsonResponse({
        'kpi': admin_stats.period_stats(days),
        'sales': admin_stats.sales_series(days),
        'statuses': admin_stats.status_breakdown(),
        'top_products': admin_stats.top_products(days),
    })
