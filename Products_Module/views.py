from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count, Min, Max, F, Avg, Prefetch
from django.contrib import messages
from django.urls import reverse
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .models import Product, Category, Brand, ProductImage
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


def product_list(request):
    """نمایش لیست محصولات با فیلترینگ - بهینه شده"""

    products = Product.objects.filter(is_active=True).for_cards()

    # فیلتر دسته‌بندی
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    # فیلتر برند
    brand_slugs = request.GET.getlist('brand')
    if brand_slugs:
        products = products.filter(brand__slug__in=brand_slugs)

    # فیلتر سایز
    sizes = request.GET.getlist('size')
    if sizes:
        products = products.filter(sizes__size__in=sizes).distinct()

    # فیلتر رنگ
    colors = request.GET.getlist('color')
    if colors:
        products = products.filter(colors__code__in=colors).distinct()

    # فیلتر قیمت
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # فیلتر موجودی
    only_available = request.GET.get('available')
    if only_available:
        products = products.filter(is_available=True, stock__gt=0)

    # مرتب‌سازی
    sort = request.GET.get('sort', 'popularity')
    if sort == 'popularity':
        products = products.order_by('-views_count')
    elif sort == 'date':
        products = products.order_by('-created_at')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.order_by('-avg_rating', '-views_count')

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
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
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
        'product_colors': [color for color in product.colors.all() if color.is_available],
        'product_sizes': [size for size in product.sizes.all() if size.is_available],
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

    # مرتب‌سازی
    sort = request.GET.get('sort', 'popularity')
    if sort == 'popularity':
        products = products.order_by('-views_count')
    elif sort == 'date':
        products = products.order_by('-created_at')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')

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

    # مرتب‌سازی
    sort = request.GET.get('sort', 'popularity')
    if sort == 'popularity':
        products = products.order_by('-views_count')
    elif sort == 'date':
        products = products.order_by('-created_at')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')

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
    }

    return render(request, 'products/product_list.html', context)