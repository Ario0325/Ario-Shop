from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Min, Max, F, Avg, Prefetch
from django.contrib import messages
from django.urls import reverse
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from Core_Module.seo import absolute_url
from Core_Module.templatetags.number_tags import toman as format_toman
from Core_Module.thumbnails import thumb_url
from .models import Product, Category, Brand, ProductColor, ProductImage
from .forms import ProductReviewForm


def _sidebar_categories():
    cache_key = 'all_active_categories_with_count'
    categories = cache.get(cache_key)
    if categories is None:
        categories = list(Category.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ))
        cache.set(cache_key, categories, 60 * 15)
    return categories


def _sidebar_brands(category=None):
    cache_key = 'all_active_brands_with_count' if category is None else f'brands_category_{category.id}'
    brands = cache.get(cache_key)
    if brands is None:
        if category is None:
            brands = list(Brand.objects.filter(is_active=True).annotate(
                product_count=Count('products', filter=Q(products__is_active=True))
            ))
        else:
            brands = list(Brand.objects.filter(is_active=True, products__category=category).distinct().annotate(
                product_count=Count('products', filter=Q(products__is_active=True, products__category=category))
            ))
        cache.set(cache_key, brands, 60 * 15)
    return brands


def _price_range():
    cache_key = 'active_products_price_range'
    price_range = cache.get(cache_key)
    if price_range is None:
        price_range = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        cache.set(cache_key, price_range, 60 * 15)
    return price_range


SIZE_LABELS = {
    'xs': 'XS', 's': 'S', 'm': 'M', 'l': 'L', 'xl': 'XL', 'xxl': 'XXL',
}


def _sidebar_colors():
    """رنگ‌های قابل فیلتر با تعداد محصول."""
    cache_key = 'active_colors_facet_v2'
    colors = cache.get(cache_key)
    if colors is None:
        colors = list(
            ProductColor.objects.filter(product__is_active=True)
            .values('name')
            .annotate(product_count=Count('product', distinct=True), code=Min('code'))
            .order_by('-product_count', 'name')[:14]
        )
        cache.set(cache_key, colors, 60 * 15)
    return colors


FILTER_KEYS = ('brand', 'size', 'color', 'min_price', 'max_price', 'available', 'category')


def _parse_price(value):
    if value in (None, ''):
        return None
    table = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    cleaned = str(value).translate(table).replace(',', '').replace('٬', '').strip()
    try:
        return max(int(cleaned), 0)
    except (TypeError, ValueError):
        return None


def _apply_filters(products, request):
    """اعمال یکسان فیلترها روی همهٔ مسیرهای کاتالوگ."""
    brand_slugs = request.GET.getlist('brand')
    if brand_slugs:
        products = products.filter(brand__slug__in=brand_slugs)

    sizes = request.GET.getlist('size')
    if sizes:
        products = products.filter(sizes__size__in=sizes).distinct()

    colors = request.GET.getlist('color')
    if colors:
        products = products.filter(colors__name__in=colors).distinct()

    min_price = _parse_price(request.GET.get('min_price'))
    if min_price is not None:
        products = products.filter(price__gte=min_price)

    max_price = _parse_price(request.GET.get('max_price'))
    if max_price is not None:
        products = products.filter(price__lte=max_price)

    if request.GET.get('available'):
        products = products.filter(is_available=True, stock__gt=0)

    return products


def _sort_products(products, sort):
    order = {
        'date': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-avg_rating',
        'popularity': '-views_count',
    }.get(sort, '-views_count')
    if sort == 'rating':
        return products.order_by(order, '-views_count')
    return products.order_by(order)


def _query_url(request, key=None, value=None):
    params = request.GET.copy()
    params.pop('page', None)
    if key is not None:
        if value is None:
            params.pop(key, None)
        else:
            remaining = [item for item in params.getlist(key) if item != value]
            if remaining:
                params.setlist(key, remaining)
            else:
                params.pop(key, None)
    encoded = params.urlencode()
    return f'{request.path}?{encoded}' if encoded else request.path


def _filter_clear_url(request):
    params = request.GET.copy()
    for key in FILTER_KEYS:
        params.pop(key, None)
    params.pop('page', None)
    encoded = params.urlencode()
    return f'{request.path}?{encoded}' if encoded else request.path


def _filter_context(request, brands, category_path=None):
    brand_names = {brand.slug: brand.name for brand in brands}
    size_labels = {
        'xs': 'XS', 's': 'S', 'm': 'M', 'l': 'L', 'xl': 'XL', 'xxl': 'XXL',
    }
    filters = []

    if category_path is not None:
        filters.append({'label': category_path.name, 'url': reverse('products:list')})
    else:
        selected_category = request.GET.get('category')
        if selected_category:
            filters.append({
                'label': next(
                    (cat.name for cat in _sidebar_categories() if cat.slug == selected_category),
                    selected_category,
                ),
                'url': _query_url(request, 'category'),
            })

    for slug in request.GET.getlist('brand'):
        filters.append({'label': brand_names.get(slug, slug), 'url': _query_url(request, 'brand', slug)})

    for size in request.GET.getlist('size'):
        filters.append({
            'label': size_labels.get(size.lower(), size.upper()),
            'url': _query_url(request, 'size', size),
        })

    for color in request.GET.getlist('color'):
        filters.append({'label': color, 'url': _query_url(request, 'color', color)})

    min_price = _parse_price(request.GET.get('min_price'))
    if min_price is not None:
        filters.append({
            'label': f'از {format_toman(min_price)}',
            'url': _query_url(request, 'min_price'),
        })
    max_price = _parse_price(request.GET.get('max_price'))
    if max_price is not None:
        filters.append({
            'label': f'تا {format_toman(max_price)}',
            'url': _query_url(request, 'max_price'),
        })

    if request.GET.get('available'):
        filters.append({'label': 'فقط کالاهای موجود', 'url': _query_url(request, 'available')})

    applied_count = sum(len(request.GET.getlist(key)) for key in ('brand', 'size', 'color'))
    applied_count += sum(1 for key in ('min_price', 'max_price', 'available') if request.GET.get(key))
    if category_path is None and request.GET.get('category'):
        applied_count += 1

    return {
        'colors': _sidebar_colors(),
        'selected_brands': request.GET.getlist('brand'),
        'selected_sizes': request.GET.getlist('size'),
        'selected_colors': request.GET.getlist('color'),
        'applied_count': applied_count,
        'active_filters': filters,
        'filter_clear_url': _filter_clear_url(request),
        'hide_category': category_path is not None,
    }


def _catalog_seo(request, *, category=None, search=False, filters_active=False, page_obj=None):
    """Canonical URL and robots policy for listing pages.

    Search and filtered results are thin duplicates, so they are noindexed and
    canonicalized to the clean catalog URL. Unfiltered pagination stays
    indexable with a self-canonical that only keeps the real page number —
    this also absorbs ``?page=1``, ``?page=abc`` and clamped page numbers.
    """
    if search:
        return absolute_url(request, reverse('products:search')), 'noindex, follow'

    clean_path = category.get_absolute_url() if category else reverse('products:list')
    empty = page_obj is not None and page_obj.paginator.count == 0
    if filters_active or empty:
        return absolute_url(request, clean_path), 'noindex, follow'

    params = None
    if page_obj is not None and page_obj.number > 1:
        params = {'page': page_obj.number}
    return absolute_url(request, clean_path, params), 'index, follow'


def product_list(request):
    """نمایش لیست محصولات با فیلترینگ - بهینه شده"""

    products = Product.objects.filter(is_active=True).for_cards()

    # فیلتر دسته‌بندی
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    products = _apply_filters(products, request)

    # مرتب‌سازی
    sort = request.GET.get('sort', 'popularity')
    products = _sort_products(products, sort)

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = _sidebar_categories()
    brands = _sidebar_brands()
    price_range = _price_range()

    # حفظ پارامترهای GET برای pagination و sort
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    query_string = get_params.urlencode()

    filters = _filter_context(request, brands)
    # ?category= is a duplicate of /shop/category/<slug>/ and is counted as a
    # filter by _filter_context; do not let it trigger noindex on its own.
    category_bonus = 1 if selected_category and request.GET.get('category') else 0
    filters_active = filters['applied_count'] - category_bonus > 0
    seo_canonical, seo_robots = _catalog_seo(
        request, category=selected_category, filters_active=filters_active, page_obj=page_obj
    )

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'brands': brands,
        'selected_category': selected_category,
        'price_range': price_range,
        'current_sort': sort,
        'total_products': paginator.count,
        'query_string': query_string,
        'seo_canonical': seo_canonical,
        'seo_robots': seo_robots,
        **filters,
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    """نمایش جزئیات محصول و ثبت نظر"""

    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('order', 'created_at')),
            'colors',
            'sizes',
        ).annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True), distinct=True),
        ),
        slug=slug,
        is_active=True
    )

    # شمارش بازدید حداکثر یک‌بار در ساعت برای هر بازدیدکننده
    viewer_key = request.session.session_key or request.META.get('REMOTE_ADDR', '')
    if cache.add(f'pdp_view_{product.pk}_{viewer_key}', True, 60 * 60):
        Product.objects.filter(pk=product.pk).update(views_count=F('views_count') + 1)
        product.views_count += 1

    # دریافت نظرات تایید شده - با کشینگ
    reviews_cache_key = f'product_{product.id}_approved_reviews'
    reviews = cache.get(reviews_cache_key)
    if reviews is None:
        reviews = list(product.reviews.filter(is_approved=True).order_by('-created_at'))
        cache.set(reviews_cache_key, reviews, 60 * 5)  # Cache for 5 minutes

    # فرم نظر و پردازش POST
    initial = {}
    if request.user.is_authenticated:
        initial['name'] = request.user.get_full_name() or request.user.get_username()
        initial['email'] = getattr(request.user, 'email', '') or ''
    review_form = ProductReviewForm(initial=initial)
    
    if request.method == 'POST' and request.POST.get('submit_review'):
        # Rate limit review submissions
        if request.user.is_authenticated:
            # Check if user recently submitted a review
            recent_review_key = f'last_review_{request.user.id}'
            last_review_time = cache.get(recent_review_key)
            if last_review_time:
                messages.error(request, 'لطفاً چند دقیقه صبر کنید قبل از ثبت نظر بعدی.')
                return redirect(reverse('products:detail', kwargs={'slug': slug}) + '?review_submitted=1#product-review-tab')
            
            review_form = ProductReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.name = review.name or request.user.get_full_name() or request.user.get_username()
                review.email = review.email or getattr(request.user, 'email', '') or review.email
                review.is_approved = False
                review.save()

                # پاک کردن کش نظرات این محصول
                cache.delete(f'product_{product.id}_approved_reviews')
                
                # Set rate limit cache
                cache.set(recent_review_key, True, 60 * 5)  # 5 minute cooldown
                
                messages.success(request, 'نظر شما با موفقیت ثبت شد و پس از تأیید نمایش داده می‌شود.')
                return redirect(reverse('products:detail', kwargs={'slug': slug}) + '?review_submitted=1#product-review-tab')

    # محصولات مشابه
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        is_available=True
    ).exclude(id=product.id).for_cards()[:8]

    # محصول قبلی و بعدی در همان دسته‌بندی (بر اساس تاریخ ایجاد)
    prev_product = Product.objects.filter(
        category=product.category,
        is_active=True,
        created_at__lt=product.created_at
    ).order_by('-created_at').first()

    next_product = Product.objects.filter(
        category=product.category,
        is_active=True,
        created_at__gt=product.created_at
    ).order_by('created_at').first()

    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'related_products': related_products,
        'product_images': product.images.all(),
        'product_colors': sorted(product.colors.all(), key=lambda color: not color.is_available),
        'product_sizes': sorted(product.sizes.all(), key=lambda size: not size.is_available),
        'prev_product': prev_product,
        'next_product': next_product,
        'use_shop_plugins': True,
    }

    return render(request, 'products/product_detail.html', context)


def category_products(request, slug):
    """نمایش محصولات یک دسته‌بندی"""

    category = get_object_or_404(Category, slug=slug, is_active=True)

    products = Product.objects.filter(
        category=category,
        is_active=True
    ).for_cards()

    products = _apply_filters(products, request)

    # مرتب‌سازی
    sort = request.GET.get('sort', 'popularity')
    products = _sort_products(products, sort)

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = _sidebar_categories()
    brands = _sidebar_brands(category)

    # حفظ پارامترهای GET برای pagination و sort
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    query_string = get_params.urlencode()

    filters = _filter_context(request, brands, category_path=category)
    seo_canonical, seo_robots = _catalog_seo(
        request, category=category, filters_active=filters['applied_count'] > 0, page_obj=page_obj
    )

    context = {
        'category': category,
        'selected_category': category,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'brands': brands,
        'current_sort': sort,
        'total_products': paginator.count,
        'query_string': query_string,
        'seo_canonical': seo_canonical,
        'seo_robots': seo_robots,
        **filters,
    }

    return render(request, 'products/product_list.html', context)


def search_products(request):
    """جستجوی محصولات"""

    query = request.GET.get('q', '')

    products = Product.objects.filter(is_active=True).for_cards()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).distinct()

    products = _apply_filters(products, request)

    # مرتب‌سازی
    sort = request.GET.get('sort', 'popularity')
    products = _sort_products(products, sort)

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = _sidebar_categories()
    brands = _sidebar_brands()

    # حفظ پارامترهای GET برای pagination و sort
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    query_string = get_params.urlencode()

    filters = _filter_context(request, brands)
    seo_canonical, seo_robots = _catalog_seo(request, search=True, page_obj=page_obj)

    context = {
        'query': query,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'brands': brands,
        'selected_category': None,
        'current_sort': sort,
        'total_products': paginator.count,
        'query_string': query_string,
        'seo_canonical': seo_canonical,
        'seo_robots': seo_robots,
        **filters,
    }

    return render(request, 'products/product_list.html', context)


@ratelimit(key='ip', rate='60/m', block=True)
def suggest_products(request):
    """پیشنهاد زندهٔ جستجو (محصول + دسته) برای فیلدهای جستجو."""
    query = ' '.join(request.GET.get('q', '').split())[:60]
    empty = {'ok': True, 'query': query, 'products': [], 'categories': []}
    if len(query) < 2:
        return JsonResponse(empty)

    cache_key = f'suggest_v1_{query.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'ok': True, 'query': query, **cached})

    products = Product.objects.filter(is_active=True).filter(
        Q(name__icontains=query) |
        Q(brand__name__icontains=query) |
        Q(category__name__icontains=query)
    ).for_cards().order_by('-views_count')[:6]

    product_rows = []
    for product in products:
        image_url = ''
        images = list(product.images.all())
        if images:
            image_url = thumb_url(images[0].image, 96)
        product_rows.append({
            'name': product.name,
            'url': product.get_absolute_url(),
            'image': image_url,
            'price': str(product.price),
            'price_display': format_toman(product.price),
            'rating': round(float(product.avg_rating or 0), 1),
            'review_count': product.review_count,
            'is_available': bool(product.is_available and product.stock > 0),
        })

    categories = Category.objects.filter(
        is_active=True, name__icontains=query
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('-product_count')[:4]

    payload = {
        'products': product_rows,
        'categories': [
            {
                'name': category.name,
                'url': category.get_absolute_url(),
                'product_count': category.product_count,
            }
            for category in categories
        ],
        'search_url': f"{reverse('products:search')}?q={query}",
    }
    cache.set(cache_key, payload, 60 * 2)
    return JsonResponse({'ok': True, 'query': query, **payload})