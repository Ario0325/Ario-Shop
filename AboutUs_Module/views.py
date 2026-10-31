from django.shortcuts import render
from .models import AboutPage, Brand, TeamMember, Testimonial


def about_us_view(request):
    """
    صفحه درباره ما:
    - اگر رکورد AboutPage وجود نداشته باشد، با مقادیر پیش‌تعیین‌شده (default) نمایش داده می‌شود.
    - تمام مدل‌های فعال واکشی می‌شند.
    """
    # صفحه اصلی (singleton) – اگر نباشد، خودکار با defaults ساخته می‌شود
    about_page, _ = AboutPage.objects.get_or_create(pk=1)

    # برندهای فعال
    brands = Brand.objects.filter(is_active=True)

    # اعضای تیم فعال
    team_members = TeamMember.objects.filter(is_active=True)

    # نظرات فعال
    testimonials = Testimonial.objects.filter(is_active=True)

    context = {
        'about_page': about_page,
        'brands': brands,
        'team_members': team_members,
        'testimonials': testimonials,
        'use_shop_plugins': True,
    }

    return render(request, 'AboutUs_Module/about.html', context)