from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from accounts.models import User
from cust_auth_admin.views import admin_required
from store.models import *
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from cust_admin.forms import ProductVariantAssignForm
from django.contrib import messages
from decimal import Decimal
import sweetify
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import IntegrityError
from PIL import Image
from django.db.models import Case, CharField, Value, When, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.template.loader import get_template
from xhtml2pdf import pisa
import pandas as pd
from django.urls import reverse
from .utils import paginate_queryset
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import never_cache
from django.utils.timezone import localdate, make_aware
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


#=========================================== admin dashboard ===========================================================================================================================


@admin_required
@never_cache
def dashboard(request):
    product_count = Product.objects.count()
    cat_count = Category.objects.count()
    usr_count = User.objects.count()



    page = request.GET.get('page')
   

    context = {
        'title': 'Admin Dashboard',
        'usr_count': usr_count,
        'product_count': product_count,
        'cat_count': cat_count,
    }
    return render(request, 'cust_admin/index.html', context)


#=========================================== admin list, view, delete user =========================================================================================================


@admin_required
def user_list(request):
    users = User.objects.all().order_by('id')
    page_obj, paginator = paginate_queryset(request, users, items_per_page=20)  # Adjust items_per_page as needed

    context={
        'title':'User List',
         'users': users,
         'page_obj': page_obj,
         'paginator': paginator
         }
    return render(request, 'cust_admin/user/user_list.html', context)


@admin_required
def user_view(request, username):
    user = get_object_or_404(User, username=username)
    context = {
        'title': 'View User',
        'user': user
        }
    return render(request, 'cust_admin/user/user_view.html', context)

User = get_user_model()


@admin_required
def user_block_unblock(request, username):
    user = get_object_or_404(User, username = username)
    user.is_active = not user.is_active
    user.save()
    action = 'blocked' if not user.is_active else 'unblocked'
    sweetify.toast(request, f"The user {user.username} has been {action} successfully.", icon='success', timer=3000)
    return redirect('cust_admin:user_list')


#=========================================== admin add, list, edit, delete category=========================================================================================================


@admin_required
def category_list(request):
    categories = Category.objects.all().order_by('c_id')
    page_obj, paginator = paginate_queryset(request, categories, items_per_page=20)  # Adjust items_per_page as needed

    context = {
        'title':'Category List',
        'categories':categories,
        'page_obj': page_obj,
        'paginator': paginator,

        }
    return render(request, 'cust_admin/category/category_list.html', context)


@admin_required
def add_category(request):
    context = {
        'title': 'Add Category'
    }

    if request.method == 'POST':
        c_name = request.POST.get('cname')
        c_image = request.FILES.get('image')

        # Check if a category with the same name already exists
        existing_category = Category.objects.filter(c_name=c_name).exists()
        if existing_category:
            sweetify.toast(request, f"Category {c_name} with this name already exists.", icon='error', timer=3000)
        else:
            # Create and save the new category
            c_data = Category(c_name=c_name, c_image=c_image)
            c_data.save()
            sweetify.toast(request, "Category added successfully.", icon='success', timer=3000)
            return redirect('cust_admin:category_list')

    return render(request, 'cust_admin/category/add_category.html', context)


@admin_required
def category_list_unlist(request, c_id):
    category = get_object_or_404(Category, c_id = c_id)
    category.is_blocked = not category.is_blocked    
    category.save()
    action = 'unblocked' if not category.is_blocked else 'blocked'
    sweetify.toast(request, f"The category with ID {category.c_id} has been {action} successfully.", icon='success', timer=3000)
    return redirect('cust_admin:category_list')


@admin_required
def edit_category(request, c_id):
    category = get_object_or_404(Category, c_id=c_id)
    
    if request.method == 'POST':
        category.c_name = request.POST.get('cname')
        if request.FILES.get('image'):  # Only update the image if a new one is uploaded
            category.c_image = request.FILES.get('image')
        # Save the updated category
        category.save()
        return redirect('cust_admin:category_list')

    # Pass the category data to the template to prefill the form
    context = {
        'title': 'Edit Category',
        'category': category,
    }
          
    return render(request, 'cust_admin/category/category_edit.html', context)



#=========================================== admin add, list subcategory =========================================================================================================


@admin_required
def subcategory_list(request):
    sub_cat = Subcategory.objects.all()
    context = {
        'title':'Sub Category',
        'sub_cat':sub_cat,
               }
    return render(request,'cust_admin/sub_category/sub_cat_list.html', context)


@admin_required
def add_subcat(request):
    if request.method == 'POST':
        sub_name = request.POST.get('sub_name')
        # c_id = request.POST.get('category')
        # category = Category.objects.get(c_id = c_id)
        Subcategory.objects.create(sub_name = sub_name)
        return redirect('cust_admin:subcategory_list')
    # categories = Category.objects.all()
    return render(request, 'cust_admin/sub_category/add_sub_cat.html', {'title':'Add Sub Category'})


#=========================================== admin add, list, edit, delete variant =========================================================================================================


@admin_required
def list_variant(request):
    # Define the custom ordering based on the size values
    custom_ordering = Case(
        When(size='S', then=Value(0)),
        When(size='M', then=Value(1)),
        When(size='L', then=Value(2)),
        When(size='XL', then=Value(3)),
        When(size='XXL', then=Value(4)),
        When(size='XXXL', then=Value(5)),
        default=Value(5),
        output_field=CharField(),
    )

    # Fetch the Size objects ordered according to the custom ordering
    data = Size.objects.all().order_by(custom_ordering)

    context = {
        'data': data,
        'title': 'Variant List',
    }
    return render(request, 'cust_admin/variant/variant_list.html', context)


@admin_required
def add_variant(request):
    if request.method == 'POST':
        size = request.POST.get('size')

        try:
            existing_size = Size.objects.filter(size__iexact=size)
            if existing_size:
                sweetify.toast(request, "The size already exists", timer=3000, icon='warning')
            else:
                new_size = Size(size=size)
                new_size.save()
                sweetify.toast(request, f'The size {size} added successfully', icon='success', timer=3000)
        except IntegrityError as e:
            error_message = str(e)
            sweetify.toast(request, f'An error occurred while adding the size: {error_message}', icon='alert', timer=3000)
        
        return redirect('cust_admin:list_variant')
    context = {
            'title': 'Variant Add',
        }
    return render(request, 'cust_admin/variant/variant_add.html', context)


@admin_required
def edit_variant(request, id):
    if request.method == 'POST':
        size = request.POST.get('size')
        price_increment = request.POST.get('price_inc')
        edit=Size.objects.get(id=id)
        edit.size = size
        edit.price_increment = price_increment
        edit.save()
        return redirect('cust_admin:list_variant')
    obj = Size.objects.get(id=id)
    context = {
        "obj":obj,
        'title': 'Variant Edit',
    }
    
    return render(request, 'cust_admin/variant/variant_edit.html', context)


#=========================================== admin add, list, edit, delete product =========================================================================================================


@admin_required
def prod_list(request):
    products = Product.objects.all().order_by('-p_id')
    page_obj, paginator = paginate_queryset(request, products, items_per_page=20)
    
    context = {
        'products': products,
        'title': 'Product Lobby',
        'paginator': paginator,
        'page_obj': page_obj
    }
    return render(request, 'cust_admin/product/product_list.html', context)


@admin_required
def add_product(request):
    if request.method == 'POST':
        # Maximum file size in bytes (2MB = 2097152 bytes)
        max_file_size = 2097152

        # Extract data from the form
        title = request.POST.get('title')
        description = request.POST.get('description')
        specifications = request.POST.get('specifications')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        featured = request.POST.get('featured') == 'on'
        popular = request.POST.get('popular') == 'on'
        latest = request.POST.get('latest') == 'on'
        availability = request.POST.get('availability') == 'on'

        # Main product image validation
        image = request.FILES.get('image')
        if image and image.size > max_file_size:
            sweetify.error(request, 'Main product image exceeds the 2MB size limit.')
            return redirect('cust_admin:add_product')

        # Validate additional images size
        images = request.FILES.getlist('images')
        for img in images:
            if img.size > max_file_size:
                sweetify.error(request, 'One or more additional images exceed the 2MB size limit.')
                return redirect('cust_admin:add_product')

        # Get the category and subcategory objects
        category = Category.objects.get(c_id=category_id)
        subcategory = Subcategory.objects.get(sid=subcategory_id)

        # Create the product
        product = Product.objects.create(
            title=title,
            description=description,
            specifications=specifications,
            category=category,
            featured=featured,
            popular=popular,
            latest=latest,
            sub_category=subcategory,
            availability=availability,
            image=image  # Assign the main product image
        )

        # Save additional images
        for img in images:
            ProductImages.objects.create(product=product, images=img)

        sweetify.toast(request, 'Product added successfully!', icon='success', timer=3000)
        return redirect('cust_admin:prod_list')

    # If request method is GET, render the form
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    context = {
        'categories': categories,
        'subcategories': subcategories,
    }

    return render(request, 'cust_admin/product/product_add.html', context)



@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, p_id=product_id)
    additional_images = ProductImages.objects.filter(product=product)
    
    if request.method == 'POST':
        max_file_size = 2097152
        title = request.POST.get('title')
        description = request.POST.get('description')
        specifications = request.POST.get('specifications')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        featured = request.POST.get('featured') == 'on'
        popular = request.POST.get('popular') == 'on'
        latest = request.POST.get('latest') == 'on'
        availability = request.POST.get('availability') == 'on'

        main_image = request.FILES.get('image')
        if main_image and main_image.size > max_file_size:
            sweetify.error(request, 'Main product image exceeds the 2MB size limit.')
            return redirect('cust_admin:edit_product', product_id=product_id)

        additional_images_files = request.FILES.getlist('images')
        for img in additional_images_files:
            if img.size > max_file_size:
                sweetify.error(request, 'One or more additional images exceed the 2MB size limit.')
                return redirect('cust_admin:edit_product', product_id=product_id)

        product.title = title
        product.description = description
        product.specifications = specifications
        product.featured = featured
        product.popular = popular
        product.latest = latest
        product.availability = availability

        product.category = get_object_or_404(Category, c_id=category_id)
        product.sub_category = get_object_or_404(Subcategory, sid=subcategory_id)
        
        if main_image:
            product.image = main_image

        product.save()
        ProductImages.objects.filter(product=product).delete()
        for img in additional_images_files:
            ProductImages.objects.create(product=product, images=img)

        sweetify.toast(request, 'Product updated successfully!', icon='success', timer=3000)
        return redirect('cust_admin:prod_list')

    context = {
        'product': product,
        'additional_images': additional_images,
        'categories': Category.objects.all(),
        'subcategories': Subcategory.objects.all(),
    }
    return render(request, 'cust_admin/product/product_edit.html', context)


@admin_required
def product_list_unlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)  # Use product_id here
    product.is_blocked = not product.is_blocked
    product.save()
    action = 'unblocked' if not product.is_blocked else 'blocked'
    sweetify.toast(request, f"The product with ID {product_id} has been {action} successfully.", icon='success', timer=3000)
    return redirect('cust_admin:prod_list')


@admin_required
def prod_catalogue_list(request):    
    products = ProductAttribute.objects.all().order_by('-id')
    page_obj, paginator = paginate_queryset(request, products, items_per_page=20)
    prods = Product.objects.all()
    
    context = {
        'prods': prods,
        'products': products,
        'title': 'Product Catalogue',
        'page_obj': page_obj,
        'paginator': paginator
    }
    return render(request, 'cust_admin/product/product_catalogue.html', context)


@admin_required
def catalogue_list_unlist(request, pk):
    product = get_object_or_404(ProductAttribute, pk=pk)
    product.is_blocked = not product.is_blocked
    product.save()
    action = 'unblocked' if not product.is_blocked else 'blocked'
    sweetify.toast(request, f"The product variant with ID {product.pk} has been {action} successfully.", timer=3000, icon='success')
    return redirect('cust_admin:prod_catalogue')


#=========================================== admin product variant assign, edit =========================================================================================================


@admin_required
def prod_variant_assign(request):
    form = ProductVariantAssignForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Process form data
        product = form.cleaned_data['product']
        size = form.cleaned_data['size']
        price = form.cleaned_data['price']
        old_price = form.cleaned_data['old_price']
        stock = form.cleaned_data['stock']
        in_stock = form.cleaned_data['in_stock']
        status = form.cleaned_data['status']
        
        # Check if size already exists for the product
        existing_size = ProductAttribute.objects.filter(product=product, size=size).exists()
        if existing_size:
            sweetify.toast(request, f"The size {size} already added", icon='warning')
        else:
            # Save the form data to the database
            product_attribute = ProductAttribute.objects.create(
                product=product,
                size=size,
                price=price,
                old_price=old_price,
                stock=stock,
                in_stock=in_stock,
                status=status
            )
            sweetify.toast(request, 'Successfully added Product with variant!', timer=3000, icon='success')
            return redirect('cust_admin:prod_catalogue')

    context = {
        'title': 'Add New Product',
        'form': form,
    }
    return render(request, 'cust_admin/product/prod_variant_assign.html', context)


@admin_required
def prod_variant_edit(request, pk):
    product_attribute = get_object_or_404(ProductAttribute, pk=pk)

    if request.method == 'POST':
        form = ProductVariantAssignForm(request.POST)
        if form.is_valid():
            product_attribute.product = form.cleaned_data['product']
            product_attribute.size = form.cleaned_data['size']
            product_attribute.price = form.cleaned_data['price']
            product_attribute.old_price = form.cleaned_data['old_price']
            product_attribute.stock = form.cleaned_data['stock']
            product_attribute.in_stock = form.cleaned_data['in_stock']
            product_attribute.status = form.cleaned_data['status']
            product_attribute.save()
            
            sweetify.toast(request, 'Product attribute details updated successfully!', icon='success', timer=3000)
            return redirect('cust_admin:prod_catalogue')
    else:
        initial_data = {
            'product': product_attribute.product,
            'size': product_attribute.size,
            'price': product_attribute.price,
            'old_price': product_attribute.old_price,
            'stock': product_attribute.stock,
            'in_stock': product_attribute.in_stock,
            'status': product_attribute.status
        }
        form = ProductVariantAssignForm(initial_data=initial_data)

    context = {
        'form': form,
        'title': 'Product Variant Edit',
    }

    return render(request, 'cust_admin/product/prod_variant_edit.html', context)
