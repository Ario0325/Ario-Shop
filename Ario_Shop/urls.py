"""
URL configuration for Ario_Shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_control
from Products_Module.sitemaps import ProductSitemap, CategorySitemap


@cache_control(max_age=0, no_cache=True, no_store=True)
def service_worker(request):
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    if not sw_path.exists():
        raise Http404
    with open(sw_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


@cache_control(max_age=86400)
def manifest(request):
    manifest_path = settings.BASE_DIR / 'static' / 'assets' / 'images' / 'icons' / 'site.webmanifest'
    if not manifest_path.exists():
        raise Http404
    with open(manifest_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/manifest+json')
    return response

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('sw.js', service_worker, name='service_worker'),
    path('manifest.json', manifest, name='manifest'),
    path('admin/core/', include('Core_Module.urls')),
    path('admin/', admin.site.urls),
    path('', include('Home_Module.urls')),
    path('Contact_us/', include('Contact_Module.urls')),
    path('About_us/',include('AboutUs_Module.urls')),
    # لیست تمام محصولات
    path('shop/', include('Products_Module.urls')),
    path('accounts/', include('Accounts_Module.urls')),
    path('cart/', include('Cart_Module.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)