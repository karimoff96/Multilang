from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Category, Product, Language


# ============ Category Views ============

@login_required(login_url='admin_login')
def categoryList(request):
    """List all categories with search and filter"""
    categories = Category.objects.all().annotate(
        product_count=Count('product')
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        categories = categories.filter(is_active=True)
    elif status_filter == 'inactive':
        categories = categories.filter(is_active=False)
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    
    paginator = Paginator(categories, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        "title": "Categories",
        "subTitle": "Categories",
        "categories": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "per_page": per_page,
        "total_categories": paginator.count,
    }
    return render(request, "services/categoryList.html", context)


@login_required(login_url='admin_login')
def categoryDetail(request, category_id):
    """View category details with its products"""
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by('-created_at')
    
    context = {
        "title": f"Category: {category.name}",
        "subTitle": "Category Details",
        "category": category,
        "products": products,
        "product_count": products.count(),
    }
    return render(request, "services/categoryDetail.html", context)


@login_required(login_url='admin_login')
def addCategory(request):
    """Add a new category"""
    languages = Language.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        charging = request.POST.get('charging', 'dynamic')
        is_active = request.POST.get('is_active') == 'on'
        selected_languages = request.POST.getlist('languages')
        
        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A category with this name already exists.')
        else:
            try:
                category = Category.objects.create(
                    name=name,
                    description=description,
                    charging=charging,
                    is_active=is_active,
                )
                # Add selected languages
                if selected_languages:
                    category.languages.set(selected_languages)
                
                messages.success(request, f'Category "{name}" has been created successfully.')
                return redirect('categoryList')
            except Exception as e:
                messages.error(request, f'Error creating category: {str(e)}')
    
    context = {
        "title": "Add Category",
        "subTitle": "Add Category",
        "languages": languages,
        "charge_types": Category.CHARGE_TYPE,
    }
    return render(request, "services/addCategory.html", context)


@login_required(login_url='admin_login')
def editCategory(request, category_id):
    """Edit an existing category"""
    category = get_object_or_404(Category, id=category_id)
    languages = Language.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        charging = request.POST.get('charging', 'dynamic')
        is_active = request.POST.get('is_active') == 'on'
        selected_languages = request.POST.getlist('languages')
        
        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
            messages.error(request, 'A category with this name already exists.')
        else:
            try:
                category.name = name
                category.description = description
                category.charging = charging
                category.is_active = is_active
                category.save()
                
                # Update languages
                category.languages.set(selected_languages)
                
                messages.success(request, f'Category "{name}" has been updated successfully.')
                return redirect('categoryList')
            except Exception as e:
                messages.error(request, f'Error updating category: {str(e)}')
    
    context = {
        "title": "Edit Category",
        "subTitle": "Edit Category",
        "category": category,
        "languages": languages,
        "charge_types": Category.CHARGE_TYPE,
    }
    return render(request, "services/editCategory.html", context)


@login_required(login_url='admin_login')
def deleteCategory(request, category_id):
    """Delete a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" has been deleted successfully.')
    
    return redirect('categoryList')


# ============ Product Views ============

@login_required(login_url='admin_login')
def productList(request):
    """List all products with search and filter"""
    products = Product.objects.select_related('category').all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    
    paginator = Paginator(products, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        "title": "Products",
        "subTitle": "Products",
        "products": page_obj,
        "categories": categories,
        "search_query": search_query,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "per_page": per_page,
        "total_products": paginator.count,
    }
    return render(request, "services/productList.html", context)


@login_required(login_url='admin_login')
def productDetail(request, product_id):
    """View product details"""
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    
    context = {
        "title": f"Product: {product.name}",
        "subTitle": "Product Details",
        "product": product,
    }
    return render(request, "services/productDetail.html", context)


@login_required(login_url='admin_login')
def addProduct(request):
    """Add a new product"""
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category', '')
        description = request.POST.get('description', '').strip()
        
        # Pricing
        ordinary_first_page_price = request.POST.get('ordinary_first_page_price', '0')
        ordinary_other_page_price = request.POST.get('ordinary_other_page_price', '0')
        agency_first_page_price = request.POST.get('agency_first_page_price', '0')
        agency_other_page_price = request.POST.get('agency_other_page_price', '0')
        user_copy_price_percentage = request.POST.get('user_copy_price_percentage', '100')
        agency_copy_price_percentage = request.POST.get('agency_copy_price_percentage', '100')
        
        # Other fields
        min_pages = request.POST.get('min_pages', '1')
        estimated_days = request.POST.get('estimated_days', '1')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, 'Product name is required.')
        elif not category_id:
            messages.error(request, 'Please select a category.')
        else:
            try:
                product = Product.objects.create(
                    name=name,
                    category_id=category_id,
                    description=description,
                    ordinary_first_page_price=ordinary_first_page_price or 0,
                    ordinary_other_page_price=ordinary_other_page_price or 0,
                    agency_first_page_price=agency_first_page_price or 0,
                    agency_other_page_price=agency_other_page_price or 0,
                    user_copy_price_percentage=user_copy_price_percentage or 100,
                    agency_copy_price_percentage=agency_copy_price_percentage or 100,
                    min_pages=min_pages or 1,
                    estimated_days=estimated_days or 1,
                    is_active=is_active,
                )
                messages.success(request, f'Product "{name}" has been created successfully.')
                return redirect('productList')
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
    
    context = {
        "title": "Add Product",
        "subTitle": "Add Product",
        "categories": categories,
    }
    return render(request, "services/addProduct.html", context)


@login_required(login_url='admin_login')
def editProduct(request, product_id):
    """Edit an existing product"""
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category', '')
        description = request.POST.get('description', '').strip()
        
        # Pricing
        ordinary_first_page_price = request.POST.get('ordinary_first_page_price', '0')
        ordinary_other_page_price = request.POST.get('ordinary_other_page_price', '0')
        agency_first_page_price = request.POST.get('agency_first_page_price', '0')
        agency_other_page_price = request.POST.get('agency_other_page_price', '0')
        user_copy_price_percentage = request.POST.get('user_copy_price_percentage', '100')
        agency_copy_price_percentage = request.POST.get('agency_copy_price_percentage', '100')
        
        # Other fields
        min_pages = request.POST.get('min_pages', '1')
        estimated_days = request.POST.get('estimated_days', '1')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, 'Product name is required.')
        elif not category_id:
            messages.error(request, 'Please select a category.')
        else:
            try:
                product.name = name
                product.category_id = category_id
                product.description = description
                product.ordinary_first_page_price = ordinary_first_page_price or 0
                product.ordinary_other_page_price = ordinary_other_page_price or 0
                product.agency_first_page_price = agency_first_page_price or 0
                product.agency_other_page_price = agency_other_page_price or 0
                product.user_copy_price_percentage = user_copy_price_percentage or 100
                product.agency_copy_price_percentage = agency_copy_price_percentage or 100
                product.min_pages = min_pages or 1
                product.estimated_days = estimated_days or 1
                product.is_active = is_active
                product.save()
                
                messages.success(request, f'Product "{name}" has been updated successfully.')
                return redirect('productList')
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
    
    context = {
        "title": "Edit Product",
        "subTitle": "Edit Product",
        "product": product,
        "categories": categories,
    }
    return render(request, "services/editProduct.html", context)


@login_required(login_url='admin_login')
def deleteProduct(request, product_id):
    """Delete a product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" has been deleted successfully.')
    
    return redirect('productList')