from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseNotFound, Http404, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from decimal import Decimal
from accounts.models import User
from django.db.models import Sum, Min, Max
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.template.defaultfilters import linebreaksbr
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import sweetify
from django.conf import settings
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DecimalField
from store.decorators import blocked_user_required


def get_common_context():
    return {
        'categories': Category.objects.filter(is_blocked=False),
    }


#=============================================================================== Home =============================================================================================


@blocked_user_required
@never_cache
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    prod_count = products.count()
    featured_products = products.filter(featured=True)
    popular_products = products.filter(popular=True)
    new_added_products = products.filter(latest=True)
    
    # Get the 'Poster' subcategory
    poster_subcategory = Subcategory.objects.filter(sub_name='Posters').first()
    
    # Filter products by the 'Poster' subcategory
    poster_products = products.filter(sub_category=poster_subcategory) if poster_subcategory else Product.objects.none()
    print(poster_products,'poster')

    context = {
        'categories': categories,
        'products': products,
        'prod_count': prod_count,
        'featured_products': featured_products,
        'new_added_products': new_added_products,
        'popular_products': popular_products,
        'poster_products': poster_products,  # Add this to the context
        'title': 'Home',
    }
    return render(request, 'dashboard/home.html', context)


def handler404(request, exception):
    return render(request, '404.html', status=404)


#========================================================================== views related to product =========================================================================================


@blocked_user_required
def list_prod(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    product_attributes = ProductAttribute.objects.all()
    prod_count = Product.objects.count()
    featured_products = Product.objects.filter(featured=True)
    popular_products = Product.objects.filter(popular=True)
    new_added_products = Product.objects.filter(latest=True)


    context = {
        'categories': categories,
        'products': products,
        'product_attributes': product_attributes,
        'prod_count': prod_count,
        'featured_products': featured_products,
        'new_added_products': new_added_products,
        'popular_products': popular_products,
        'title': 'Shop',
    }
    return render(request, 'dashboard/shop.html', context)


@blocked_user_required
def product_list_by_category(request, category_cid):
    category = get_object_or_404(Category, c_id=category_cid)
    search_field = request.GET.get('search_field', '')
    products = Product.objects.filter(category=category, is_blocked=False)

    if search_field:
        products = products.filter(title__icontains=search_field)


    price_filter = request.GET.get('price_filter')
    if price_filter:
        if price_filter == 'below_500':
            products = [p for p in products if p.final_price < 500]
        elif price_filter == '500_1000':
            products = [p for p in products if 500 <= p.final_price < 1000]
        elif price_filter == '1000_1500':
            products = [p for p in products if 1000 <= p.final_price < 1500]
        elif price_filter == '1500_2000':
            products = [p for p in products if 1500 <= p.final_price < 2000]
        elif price_filter == 'above_2000':
            products = [p for p in products if p.final_price >= 2000]

    # Sort by
    sort_by = request.GET.get('sort_by')
    if sort_by:
        if sort_by == 'price_asc':
            products = sorted(products, key=lambda p: p.final_price)
        elif sort_by == 'price_desc':
            products = sorted(products, key=lambda p: p.final_price, reverse=True)
        elif sort_by == 'name_asc':
            products = sorted(products, key=lambda p: p.title)
        elif sort_by == 'name_desc':
            products = sorted(products, key=lambda p: p.title, reverse=True)
        # elif sort_by == 'new_arrivals':
        #     products = sorted(products, key=lambda p: p.updated, reverse=True)
        elif sort_by == 'avg_rating':
            products = sorted(products, key=lambda p: p.avg_rating, reverse=True)

    items_per_page = request.GET.get('items_per_page', 9)
    paginator = Paginator(products, items_per_page)
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'products': page_obj,
        'categories': Category.objects.all(),
        'prod_count': paginator.count,
        'items_per_page': items_per_page,
        'price_filter': price_filter,
        'page_obj': page_obj,
        'search_field': search_field,
        'sort_by': sort_by,
    }
    return render(request, 'dashboard/product_list.html', context)


@blocked_user_required
def product_detailed_view(request, product_pid):
    product = get_object_or_404(Product, p_id=product_pid)
    specifications_lines = product.specifications.split('\n')
    product_images = ProductImages.objects.filter(product=product).order_by('images')
    
    # Filter product attributes where stock is greater than 0
    product_attributes = ProductAttribute.objects.filter(product=product, stock__gt=0)
    title = product.title

    # Apply offers to the product

    # Sort the product_attributes based on price
    sorted_product_attributes = sorted(product_attributes, key=lambda attr: attr.price)

    context = {
        'product': product,
        'title': title,
        'specifications_lines': specifications_lines,
        'product_images': product_images,
        'product_attributes': sorted_product_attributes,
    }
    return render(request, 'dashboard/product_detailed_view.html', context)



@blocked_user_required
def get_price(request, size_id):
    try:
        product_attribute = ProductAttribute.objects.get(pk=size_id)
        price = product_attribute.price
        return JsonResponse({'price': price})
    except ProductAttribute.DoesNotExist:
        return JsonResponse({'error': 'Product attribute not found'}, status=404)


@blocked_user_required
def search_and_filter(request):
    search_field = request.GET.get('search_field', '')
    category_id = request.GET.get('category_id')
    subcategory_id = request.GET.get('subcategory_id', None)
    price_filter = request.GET.get('price_filter', None)
    sort_by = request.GET.get('sort_by', None)
    items_per_page = request.GET.get('items_per_page', '9')

    products = Product.objects.all()
    categories = Category.objects.all()

    # Default search for "posters" if no search term is provided
    if not search_field:
        search_field = 'poster'

    # Filter products based on search_field
    if search_field:
        products = products.filter(title__icontains=search_field)

    if category_id and category_id != 'None':
        products = products.filter(category_id=category_id)

    if subcategory_id:
        products = products.filter(sub_category_id=subcategory_id)

    if price_filter:
        if price_filter == 'below_500':
            products = products.filter(product_attributes__price__lt=500)
        elif price_filter == '500_1000':
            products = products.filter(product_attributes__price__gte=500, product_attributes__price__lte=1000)
        elif price_filter == '1000_1500':
            products = products.filter(product_attributes__price__gte=1000, product_attributes__price__lte=1500)
        elif price_filter == '1500_2000':
            products = products.filter(product_attributes__price__gte=1500, product_attributes__price__lte=2000)
        elif price_filter == 'above_2000':
            products = products.filter(product_attributes__price__gt=2000)

    # Annotate products with min and max price
    products = products.annotate(min_price=Min('product_attributes__price'), max_price=Max('product_attributes__price'))

    # Apply sorting by min_price
    if sort_by == 'price_asc':
        products = products.order_by('min_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-min_price')
    elif sort_by == 'title_asc':
        products = products.order_by('title')
    elif sort_by == 'title_desc':
        products = products.order_by('-title')

    # Remove duplicates
    products = products.distinct()

    # Pagination logic
    if items_per_page != 'all':
        paginator = Paginator(products, int(items_per_page))
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'search_field': search_field,
        'category_id': category_id,
        'subcategory_id': subcategory_id,
        'price_filter': price_filter,
        'sort_by': sort_by,
        'items_per_page': items_per_page,
    }

    return render(request, 'dashboard/search_and_filter.html', context)

#=========================================== views related to shop =================================================================================================================================



@blocked_user_required
def shop(request, category_id=None):
    # Fetch categories that are not blocked
    categories = Category.objects.filter(is_blocked=False)

    selected_category = None
    if category_id:
        selected_category = get_object_or_404(Category, c_id=category_id)

    # Base product query: Only products from unblocked categories
    products = Product.objects.filter(
        is_blocked=False,
        category__is_blocked=False,
        product_attributes__size__isnull=False,  # Ensure the size is present
        product_attributes__stock__gt=0  # Ensure stock is greater than 0
    ).distinct()

    # Filter by selected category if provided
    if selected_category:
        products = products.filter(category=selected_category)

    # Annotate the products with the minimum price of their variants
    products = products.annotate(min_price=Min('product_attributes__price'))

    # Price filter logic
    price_filter = request.GET.get('price_filter', None)
    if price_filter:
        if price_filter == 'below_500':
            products = products.filter(min_price__lt=500)
        elif price_filter == '500_1000':
            products = products.filter(min_price__gte=500, min_price__lte=1000)
        elif price_filter == '1000_1500':
            products = products.filter(min_price__gte=1000, min_price__lte=1500)
        elif price_filter == '1500_2000':
            products = products.filter(min_price__gte=1500, min_price__lte=2000)
        elif price_filter == 'above_2000':
            products = products.filter(min_price__gt=2000)

    # Sort products by price or other criteria
    sort_by = request.GET.get('sort_by', 'featured')
    if sort_by == 'price_asc':
        products = products.order_by('min_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-min_price')
    elif sort_by == 'title_asc':
        products = products.order_by('title')
    elif sort_by == 'title_desc':
        products = products.order_by('-title')

    # Pagination
    items_per_page = request.GET.get('items_per_page', '9')  # Default 9 items per page
    if items_per_page == 'all':
        items_per_page = products.count()
    paginator = Paginator(products, int(items_per_page))
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # Context for template rendering
    context = {
        'categories': categories,       
        'selected_category': selected_category,
        'products': page_obj,
        'total_products': products.count(),
        'price_filter': price_filter,
        'sort_by': sort_by,
        'items_per_page': items_per_page,
        'page_obj': page_obj,
    }

    return render(request, 'dashboard/shop.html', context)


#=========================================== views related to user profile =================================================================================================================================

@blocked_user_required
@login_required
def user_profile(request):
    user = request.user
    address = Address.objects.filter(user=user)