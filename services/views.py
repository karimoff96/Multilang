from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Category, Product, Language
from organizations.rbac import get_user_categories, get_user_products, get_user_branches
from organizations.models import TranslationCenter


# ============ Category Views ============

@login_required(login_url='admin_login')
def categoryList(request):
    """List all categories with search and filter"""
    # Use RBAC-filtered categories
    categories = get_user_categories(request.user).select_related(
        'branch', 'branch__center'
    ).annotate(
        product_count=Count('product')
    ).order_by('-created_at')
    
    # Get accessible branches for filter dropdown
    branches = get_user_branches(request.user).select_related('center')
    
    # Center filter (superuser only)
    centers = None
    center_filter = request.GET.get('center', '')
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_filter:
            categories = categories.filter(branch__center_id=center_filter)
            branches = branches.filter(center_id=center_filter)
    
    # Branch filter
    branch_filter = request.GET.get('branch', '')
    if branch_filter:
        categories = categories.filter(branch_id=branch_filter)
    
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
        "branches": branches,
        "branch_filter": branch_filter,
        "centers": centers,
        "center_filter": center_filter,
        "search_query": search_query,
        "status_filter": status_filter,
        "per_page": per_page,
        "total_categories": paginator.count,
    }
    return render(request, "services/categoryList.html", context)


@login_required(login_url='admin_login')
def categoryDetail(request, category_id):
    """View category details with its products"""
    # Get category with RBAC check
    accessible_categories = get_user_categories(request.user)
    category = get_object_or_404(accessible_categories.select_related('branch', 'branch__center'), id=category_id)
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
    branches = get_user_branches(request.user).select_related('center')
    
    if request.method == 'POST':
        # Get translated fields
        name_uz = request.POST.get('name_uz', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        name_en = request.POST.get('name_en', '').strip()
        description_uz = request.POST.get('description_uz', '').strip()
        description_ru = request.POST.get('description_ru', '').strip()
        description_en = request.POST.get('description_en', '').strip()
        
        branch_id = request.POST.get('branch', '')
        charging = request.POST.get('charging', 'dynamic')
        is_active = request.POST.get('is_active') == 'on'
        selected_languages = request.POST.getlist('languages')
        
        # Use Uzbek name as primary (fallback to any available)
        name = name_uz or name_ru or name_en
        
        if not name:
            messages.error(request, 'Category name is required in at least one language.')
        elif not branch_id:
            messages.error(request, 'Branch is required.')
        elif Category.objects.filter(name_uz__iexact=name_uz, branch_id=branch_id).exists():
            messages.error(request, 'A category with this name already exists for this branch.')
        else:
            try:
                # Verify branch access
                branch = get_object_or_404(branches, id=branch_id)
                category = Category.objects.create(
                    name=name,
                    name_uz=name_uz or None,
                    name_ru=name_ru or None,
                    name_en=name_en or None,
                    description=description_uz or description_ru or description_en,
                    description_uz=description_uz or None,
                    description_ru=description_ru or None,
                    description_en=description_en or None,
                    branch=branch,
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
        "branches": branches,
        "charge_types": Category.CHARGE_TYPE,
    }
    return render(request, "services/addCategory.html", context)


@login_required(login_url='admin_login')
def editCategory(request, category_id):
    """Edit an existing category"""
    # Get category with RBAC check
    accessible_categories = get_user_categories(request.user)
    category = get_object_or_404(accessible_categories.select_related('branch', 'branch__center'), id=category_id)
    languages = Language.objects.all()
    branches = get_user_branches(request.user).select_related('center')
    
    if request.method == 'POST':
        # Get translated fields
        name_uz = request.POST.get('name_uz', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        name_en = request.POST.get('name_en', '').strip()
        description_uz = request.POST.get('description_uz', '').strip()
        description_ru = request.POST.get('description_ru', '').strip()
        description_en = request.POST.get('description_en', '').strip()
        
        branch_id = request.POST.get('branch', '')
        charging = request.POST.get('charging', 'dynamic')
        is_active = request.POST.get('is_active') == 'on'
        selected_languages = request.POST.getlist('languages')
        
        # Use Uzbek name as primary (fallback to any available)
        name = name_uz or name_ru or name_en
        
        if not name:
            messages.error(request, 'Category name is required in at least one language.')
        elif not branch_id:
            messages.error(request, 'Branch is required.')
        elif Category.objects.filter(name_uz__iexact=name_uz, branch_id=branch_id).exclude(id=category_id).exists():
            messages.error(request, 'A category with this name already exists for this branch.')
        else:
            try:
                # Verify branch access
                branch = get_object_or_404(branches, id=branch_id)
                category.name = name
                category.name_uz = name_uz or None
                category.name_ru = name_ru or None
                category.name_en = name_en or None
                category.description = description_uz or description_ru or description_en
                category.description_uz = description_uz or None
                category.description_ru = description_ru or None
                category.description_en = description_en or None
                category.branch = branch
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
        "branches": branches,
        "charge_types": Category.CHARGE_TYPE,
    }
    return render(request, "services/editCategory.html", context)


@login_required(login_url='admin_login')
def deleteCategory(request, category_id):
    """Delete a category"""
    # Get category with RBAC check
    accessible_categories = get_user_categories(request.user)
    category = get_object_or_404(accessible_categories, id=category_id)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" has been deleted successfully.')
    
    return redirect('categoryList')


# ============ Product Views ============

@login_required(login_url='admin_login')
def productList(request):
    """List all products with search and filter"""
    # Use RBAC-filtered products
    products = get_user_products(request.user).select_related(
        'category', 'category__branch', 'category__branch__center'
    ).order_by('-created_at')
    
    # Get accessible branches for filter dropdown
    branches = get_user_branches(request.user).select_related('center')
    
    # Center filter (superuser only)
    centers = None
    center_filter = request.GET.get('center', '')
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_filter:
            products = products.filter(category__branch__center_id=center_filter)
            branches = branches.filter(center_id=center_filter)
    
    # Branch filter
    branch_filter = request.GET.get('branch', '')
    if branch_filter:
        products = products.filter(category__branch_id=branch_filter)
    
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
    
    # Get RBAC-filtered categories for filter dropdown
    categories = get_user_categories(request.user).filter(is_active=True).order_by('name')
    
    context = {
        "title": "Products",
        "subTitle": "Products",
        "products": page_obj,
        "categories": categories,
        "branches": branches,
        "branch_filter": branch_filter,
        "centers": centers,
        "center_filter": center_filter,
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
    # Get product with RBAC check
    accessible_products = get_user_products(request.user)
    product = get_object_or_404(
        accessible_products.select_related('category', 'category__branch', 'category__branch__center'),
        id=product_id
    )
    
    context = {
        "title": f"Product: {product.name}",
        "subTitle": "Product Details",
        "product": product,
    }
    return render(request, "services/productDetail.html", context)


@login_required(login_url='admin_login')
def addProduct(request):
    """Add a new product"""
    # Get RBAC-filtered categories
    categories = get_user_categories(request.user).filter(is_active=True).select_related(
        'branch', 'branch__center'
    ).order_by('name')
    
    if request.method == 'POST':
        # Get translated fields
        name_uz = request.POST.get('name_uz', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        name_en = request.POST.get('name_en', '').strip()
        description_uz = request.POST.get('description_uz', '').strip()
        description_ru = request.POST.get('description_ru', '').strip()
        description_en = request.POST.get('description_en', '').strip()
        
        category_id = request.POST.get('category', '')
        
        # Use Uzbek name as primary (fallback to any available)
        name = name_uz or name_ru or name_en
        description = description_uz or description_ru or description_en
        
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
            messages.error(request, 'Product name is required in at least one language.')
        elif not category_id:
            messages.error(request, 'Please select a category.')
        else:
            try:
                product = Product.objects.create(
                    name=name,
                    name_uz=name_uz or None,
                    name_ru=name_ru or None,
                    name_en=name_en or None,
                    category_id=category_id,
                    description=description,
                    description_uz=description_uz or None,
                    description_ru=description_ru or None,
                    description_en=description_en or None,
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
    # Get product with RBAC check
    accessible_products = get_user_products(request.user)
    product = get_object_or_404(
        accessible_products.select_related('category', 'category__branch', 'category__branch__center'),
        id=product_id
    )
    # Get RBAC-filtered categories
    categories = get_user_categories(request.user).filter(is_active=True).select_related(
        'branch', 'branch__center'
    ).order_by('name')
    
    if request.method == 'POST':
        # Get translated fields
        name_uz = request.POST.get('name_uz', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        name_en = request.POST.get('name_en', '').strip()
        description_uz = request.POST.get('description_uz', '').strip()
        description_ru = request.POST.get('description_ru', '').strip()
        description_en = request.POST.get('description_en', '').strip()
        
        category_id = request.POST.get('category', '')
        
        # Use Uzbek name as primary (fallback to any available)
        name = name_uz or name_ru or name_en
        description = description_uz or description_ru or description_en
        
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
            messages.error(request, 'Product name is required in at least one language.')
        elif not category_id:
            messages.error(request, 'Please select a category.')
        else:
            try:
                product.name = name
                product.name_uz = name_uz or None
                product.name_ru = name_ru or None
                product.name_en = name_en or None
                product.category_id = category_id
                product.description = description
                product.description_uz = description_uz or None
                product.description_ru = description_ru or None
                product.description_en = description_en or None
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
    # Get product with RBAC check
    accessible_products = get_user_products(request.user)
    product = get_object_or_404(accessible_products, id=product_id)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" has been deleted successfully.')
    
    return redirect('productList')