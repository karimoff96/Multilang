"""
Views for organization management (Centers, Branches, Staff).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count

from .models import TranslationCenter, Branch, Role, AdminUser
from .rbac import (
    role_required,
    permission_required,
    owner_required,
    get_user_branches,
    get_user_staff,
)
from core.audit import log_create, log_update, log_delete


# ============ Translation Center Views ============


@login_required(login_url="admin_login")
@owner_required
def center_list(request):
    """List translation centers owned by the current owner"""
    if request.user.is_superuser:
        centers = TranslationCenter.objects.all()
    else:
        centers = TranslationCenter.objects.filter(owner=request.user)

    centers = centers.annotate(
        branch_count=Count("branches"),
    ).order_by("-created_at")

    # Pagination - 6 items per page to fit screen nicely
    paginator = Paginator(centers, 6)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Translation Centers",
        "subTitle": "Manage Your Centers",
        "centers": page_obj,
        "paginator": paginator,
        "total_centers": paginator.count,
    }
    return render(request, "organizations/center_list.html", context)


@login_required(login_url="admin_login")
@owner_required
def center_create(request):
    """Create a new translation center"""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        location_url = request.POST.get("location_url", "").strip()

        if not name:
            messages.error(request, "Center name is required.")
        else:
            center = TranslationCenter.objects.create(
                name=name,
                owner=request.user,
                phone=phone or None,
                email=email or None,
                address=address or None,
                location_url=location_url or None,
            )
            messages.success(
                request, f'Translation center "{name}" created successfully!'
            )
            return redirect("center_list")

    context = {
        "title": "Create Center",
        "subTitle": "Add New Translation Center",
    }
    return render(request, "organizations/center_form.html", context)


@login_required(login_url="admin_login")
@owner_required
def center_edit(request, center_id):
    """Edit an existing translation center"""
    if request.user.is_superuser:
        center = get_object_or_404(TranslationCenter, pk=center_id)
    else:
        center = get_object_or_404(TranslationCenter, pk=center_id, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        location_url = request.POST.get("location_url", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(request, "Center name is required.")
        else:
            center.name = name
            center.phone = phone or None
            center.email = email or None
            center.address = address or None
            center.location_url = location_url or None
            center.is_active = is_active
            center.save()
            messages.success(request, f'Center "{name}" updated successfully!')
            return redirect("center_list")

    context = {
        "title": "Edit Center",
        "subTitle": f"Edit {center.name}",
        "center": center,
    }
    return render(request, "organizations/center_form.html", context)


@login_required(login_url="admin_login")
@owner_required
def center_detail(request, center_id):
    """View translation center details with branches, staff, categories, products"""
    from services.models import Category, Product
    from orders.models import Order
    from accounts.models import BotUser

    if request.user.is_superuser:
        center = get_object_or_404(TranslationCenter, pk=center_id)
    else:
        center = get_object_or_404(TranslationCenter, pk=center_id, owner=request.user)

    # Get branches for this center
    branches = (
        Branch.objects.filter(center=center)
        .select_related("region", "district")
        .annotate(
            staff_count=Count("staff"),
            customer_count=Count("customers"),
            order_count=Count("orders"),
        )
        .order_by("-is_main", "name")
    )

    # Get staff for this center
    staff = (
        AdminUser.objects.filter(branch__center=center)
        .select_related("user", "branch", "role")
        .order_by("branch", "user__first_name")
    )

    # Get categories for this center's branches
    categories = (
        Category.objects.filter(branch__center=center)
        .select_related("branch")
        .order_by("branch", "name")
    )

    # Get products for this center
    products = (
        Product.objects.filter(category__branch__center=center)
        .select_related("category", "category__branch")
        .order_by("category__branch", "category", "name")[:10]
    )

    # Get recent orders for this center
    recent_orders = (
        Order.objects.filter(branch__center=center)
        .select_related("bot_user", "branch", "product")
        .order_by("-created_at")[:5]
    )

    # Get customers for this center
    customers = (
        BotUser.objects.filter(branch__center=center)
        .select_related("branch")
        .order_by("-created_at")[:10]
    )

    context = {
        "title": center.name,
        "subTitle": "Center Details",
        "center": center,
        "branches": branches,
        "staff": staff,
        "categories": categories,
        "products": products,
        "recent_orders": recent_orders,
        "customers": customers,
        "total_branches": branches.count(),
        "total_staff": staff.count(),
        "total_categories": categories.count(),
        "total_products": Product.objects.filter(
            category__branch__center=center
        ).count(),
        "total_orders": Order.objects.filter(branch__center=center).count(),
        "total_customers": BotUser.objects.filter(branch__center=center).count(),
    }
    return render(request, "organizations/center_detail.html", context)


# ============ Branch Views ============


@login_required(login_url="admin_login")
def branch_list(request):
    """List branches accessible by the current user"""
    branches = (
        get_user_branches(request.user)
        .select_related("center", "region", "district")
        .annotate(
            staff_count=Count("staff"),
            customer_count=Count("customers"),
        )
        .order_by("center", "name")
    )

    # Filter by center if specified
    center_id = request.GET.get("center")
    if center_id:
        branches = branches.filter(center_id=center_id)

    # Pagination - 6 items per page
    paginator = Paginator(branches, 6)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Get centers for filter dropdown
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
    else:
        centers = TranslationCenter.objects.filter(owner=request.user, is_active=True)

    context = {
        "title": "Branches",
        "subTitle": "Manage Branches",
        "branches": page_obj,
        "paginator": paginator,
        "total_branches": paginator.count,
        "centers": centers,
        "selected_center": center_id,
    }
    return render(request, "organizations/branch_list.html", context)


@login_required(login_url="admin_login")
@permission_required("can_manage_branches")
def branch_create(request, center_id=None):
    """Create a new branch"""
    from core.models import Region, District

    # Get centers the user can manage
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
    else:
        centers = TranslationCenter.objects.filter(owner=request.user, is_active=True)

    if center_id:
        center = get_object_or_404(centers, pk=center_id)
    else:
        center = None

    regions = Region.objects.filter(is_active=True)

    if request.method == "POST":
        center_id = request.POST.get("center")
        name = request.POST.get("name", "").strip()
        region_id = request.POST.get("region")
        district_id = request.POST.get("district")
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        location_url = request.POST.get("location_url", "").strip()

        if not name:
            messages.error(request, "Branch name is required.")
        elif not center_id:
            messages.error(request, "Please select a center.")
        else:
            center = get_object_or_404(centers, pk=center_id)
            branch = Branch.objects.create(
                center=center,
                name=name,
                region_id=region_id or None,
                district_id=district_id or None,
                address=address or None,
                phone=phone or None,
                location_url=location_url or None,
            )
            messages.success(request, f'Branch "{name}" created successfully!')
            return redirect("branch_list")

    context = {
        "title": "Create Branch",
        "subTitle": "Add New Branch",
        "centers": centers,
        "selected_center": center,
        "regions": regions,
    }
    return render(request, "organizations/branch_form.html", context)


@login_required(login_url="admin_login")
def branch_detail(request, branch_id):
    """View branch details with staff, categories, products, orders"""
    from services.models import Category, Product
    from orders.models import Order
    from accounts.models import BotUser

    # Get branch with RBAC check
    accessible_branches = get_user_branches(request.user)
    branch = get_object_or_404(
        accessible_branches.select_related("center", "region", "district"), pk=branch_id
    )

    # Get staff for this branch
    staff = (
        AdminUser.objects.filter(branch=branch)
        .select_related("user", "role")
        .order_by("user__first_name")
    )

    # Get categories for this branch
    categories = (
        Category.objects.filter(branch=branch)
        .annotate(product_count=Count("product"))
        .order_by("name")
    )

    # Get products for this branch
    products = (
        Product.objects.filter(category__branch=branch)
        .select_related("category")
        .order_by("category", "name")[:10]
    )

    # Get recent orders for this branch
    recent_orders = (
        Order.objects.filter(branch=branch)
        .select_related("bot_user", "product", "assigned_to__user")
        .order_by("-created_at")[:10]
    )

    # Get customers for this branch
    customers = BotUser.objects.filter(branch=branch).order_by("-created_at")[:10]

    context = {
        "title": branch.name,
        "subTitle": "Branch Details",
        "branch": branch,
        "staff": staff,
        "categories": categories,
        "products": products,
        "recent_orders": recent_orders,
        "customers": customers,
        "total_staff": staff.count(),
        "total_categories": categories.count(),
        "total_products": Product.objects.filter(category__branch=branch).count(),
        "total_orders": Order.objects.filter(branch=branch).count(),
        "total_customers": BotUser.objects.filter(branch=branch).count(),
    }
    return render(request, "organizations/branch_detail.html", context)


@login_required(login_url="admin_login")
@permission_required("can_manage_branches")
def branch_edit(request, branch_id):
    """Edit an existing branch"""
    from core.models import Region, District

    branch = get_object_or_404(Branch, pk=branch_id)

    # Check access
    if not request.user.is_superuser:
        if branch.center.owner != request.user:
            messages.error(request, "You don't have permission to edit this branch.")
            return redirect("branch_list")

    regions = Region.objects.filter(is_active=True)
    districts = (
        District.objects.filter(region=branch.region)
        if branch.region
        else District.objects.none()
    )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        region_id = request.POST.get("region")
        district_id = request.POST.get("district")
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        location_url = request.POST.get("location_url", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(request, "Branch name is required.")
        else:
            branch.name = name
            branch.region_id = region_id or None
            branch.district_id = district_id or None
            branch.address = address or None
            branch.phone = phone or None
            branch.location_url = location_url or None
            branch.is_active = is_active
            branch.save()
            messages.success(request, f'Branch "{name}" updated successfully!')
            return redirect("branch_list")

    context = {
        "title": "Edit Branch",
        "subTitle": f"Edit {branch.name}",
        "branch": branch,
        "regions": regions,
        "districts": districts,
    }
    return render(request, "organizations/branch_form.html", context)


# ============ Staff Management Views ============


@login_required(login_url="admin_login")
@permission_required("can_manage_staff")
def staff_list(request):
    """List staff members the current user can manage"""
    staff = (
        get_user_staff(request.user)
        .select_related("user", "role", "branch", "branch__center")
        .order_by("-created_at")
    )

    # Center filter for superuser
    centers = None
    center_filter = request.GET.get("center")
    if request.user.is_superuser:
        centers = TranslationCenter.objects.filter(is_active=True)
        if center_filter:
            staff = staff.filter(branch__center_id=center_filter)

    # Filter by role
    role_filter = request.GET.get("role")
    if role_filter:
        staff = staff.filter(role__name=role_filter)

    # Filter by branch
    branch_id = request.GET.get("branch")
    if branch_id:
        staff = staff.filter(branch_id=branch_id)

    # Search
    search = request.GET.get("search", "")
    if search:
        staff = staff.filter(
            Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__username__icontains=search)
            | Q(phone__icontains=search)
        )

    # Get branches for filter
    accessible_branches = get_user_branches(request.user)
    if request.user.is_superuser and center_filter:
        accessible_branches = accessible_branches.filter(center_id=center_filter)
    roles = Role.objects.all()

    # Pagination
    paginator = Paginator(staff, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "title": "Staff Management",
        "subTitle": "Manage Staff Members",
        "staff": page_obj,
        "branches": accessible_branches,
        "roles": roles,
        "role_filter": role_filter,
        "branch_filter": branch_id,
        "search": search,
        "centers": centers,
        "center_filter": center_filter,
    }
    return render(request, "organizations/staff_list.html", context)


@login_required(login_url="admin_login")
@permission_required("can_manage_staff")
def staff_create(request):
    """Create a new staff member"""
    accessible_branches = get_user_branches(request.user)

    # Get all active roles except owner for assignment
    # Managers can only assign staff role, owners/superusers can assign any role except owner
    if request.admin_profile and request.admin_profile.is_manager:
        roles = Role.objects.filter(name="staff", is_active=True)
    else:
        roles = Role.objects.filter(is_active=True).exclude(name="owner")

    if request.method == "POST":
        # User info
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "")

        # Admin profile info
        role_id = request.POST.get("role")
        branch_id = request.POST.get("branch")
        phone = request.POST.get("phone", "").strip()

        # Validation
        errors = []
        if not username:
            errors.append("Username is required.")
        if not first_name:
            errors.append("First name is required.")
        if not password:
            errors.append("Password is required.")
        if not role_id:
            errors.append("Role is required.")
        if not branch_id:
            errors.append("Branch is required.")

        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email or None,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,  # Allow admin access
            )

            # Get role and branch
            role = get_object_or_404(roles, pk=role_id)
            branch = get_object_or_404(accessible_branches, pk=branch_id)

            # Create admin profile
            admin_profile = AdminUser.objects.create(
                user=user,
                role=role,
                branch=branch,
                center=branch.center,
                phone=phone or None,
                created_by=request.user,
            )

            # Audit log the creation
            log_create(
                user=request.user,
                target=admin_profile,
                request=request,
                details=f"Created staff: {first_name} {last_name} ({role.name}) in {branch.name}",
            )

            messages.success(
                request,
                f'Staff member "{first_name} {last_name}" created successfully!',
            )
            return redirect("staff_list")

    context = {
        "title": "Add Staff",
        "subTitle": "Create New Staff Member",
        "branches": accessible_branches,
        "roles": roles,
    }
    return render(request, "organizations/staff_form.html", context)


@login_required(login_url="admin_login")
@permission_required("can_manage_staff")
def staff_edit(request, staff_id):
    """Edit an existing staff member"""
    staff_member = get_object_or_404(AdminUser, pk=staff_id)

    # Check access
    if not request.user.is_superuser:
        accessible_staff = get_user_staff(request.user)
        if not accessible_staff.filter(pk=staff_id).exists():
            messages.error(
                request, "You don't have permission to edit this staff member."
            )
            return redirect("staff_list")

    accessible_branches = get_user_branches(request.user)

    # Owners can manage all roles except owner, managers can only manage staff
    if request.admin_profile and request.admin_profile.is_manager:
        roles = Role.objects.filter(name="staff")
    else:
        roles = Role.objects.exclude(name="owner")

    if request.method == "POST":
        # User info
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "")

        # Admin profile info
        role_id = request.POST.get("role")
        branch_id = request.POST.get("branch")
        phone = request.POST.get("phone", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not first_name:
            messages.error(request, "First name is required.")
        else:
            # Update user
            user = staff_member.user
            user.email = email or None
            user.first_name = first_name
            user.last_name = last_name
            if password:
                user.set_password(password)
            user.save()

            # Update profile
            staff_member.role_id = role_id
            staff_member.branch_id = branch_id
            staff_member.center = (
                Branch.objects.get(pk=branch_id).center if branch_id else None
            )
            staff_member.phone = phone or None
            staff_member.is_active = is_active
            staff_member.save()

            messages.success(
                request,
                f'Staff member "{first_name} {last_name}" updated successfully!',
            )
            return redirect("staff_list")

    context = {
        "title": "Edit Staff",
        "subTitle": f"Edit {staff_member.user.get_full_name()}",
        "staff_member": staff_member,
        "branches": accessible_branches,
        "roles": roles,
    }
    return render(request, "organizations/staff_form.html", context)


@login_required(login_url="admin_login")
@permission_required("can_manage_staff")
def staff_toggle_active(request, staff_id):
    """Toggle staff member active status"""
    if request.method != "POST":
        return redirect("staff_list")

    staff_member = get_object_or_404(AdminUser, pk=staff_id)

    # Check access
    if not request.user.is_superuser:
        accessible_staff = get_user_staff(request.user)
        if not accessible_staff.filter(pk=staff_id).exists():
            messages.error(
                request, "You don't have permission to modify this staff member."
            )
            return redirect("staff_list")

    staff_member.is_active = not staff_member.is_active
    staff_member.save()

    status = "activated" if staff_member.is_active else "deactivated"
    messages.success(
        request, f"Staff member {staff_member.user.get_full_name()} has been {status}."
    )
    return redirect("staff_list")


# ============ API Endpoints ============

from django.http import JsonResponse


@login_required(login_url="admin_login")
def get_districts(request, region_id):
    """AJAX endpoint to get districts for a region"""
    from core.models import District

    districts = District.objects.filter(region_id=region_id, is_active=True).values(
        "id", "name"
    )
    return JsonResponse(list(districts), safe=False)


@login_required(login_url="admin_login")
def get_branch_staff(request, branch_id):
    """AJAX endpoint to get staff for a branch"""
    branch = get_object_or_404(Branch, pk=branch_id)

    # Check access
    if not request.user.is_superuser:
        accessible_branches = get_user_branches(request.user)
        if not accessible_branches.filter(pk=branch_id).exists():
            return JsonResponse({"error": "Access denied"}, status=403)

    staff = (
        AdminUser.objects.filter(branch=branch, is_active=True)
        .select_related("user", "role")
        .values("id", "user__first_name", "user__last_name", "role__name")
    )

    result = [
        {
            "id": s["id"],
            "name": f"{s['user__first_name']} {s['user__last_name']}",
            "role": s["role__name"],
        }
        for s in staff
    ]

    return JsonResponse(result, safe=False)


# ============ Role Management Views (Superuser Only) ============


@login_required(login_url="admin_login")
def role_list(request):
    """List all roles - superuser only"""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can manage roles.")
        return redirect("index")

    roles = Role.objects.annotate(user_count=Count("users")).order_by(
        "-is_system_role", "name"
    )

    context = {
        "title": "Role Management",
        "subTitle": "Manage Roles & Permissions",
        "roles": roles,
        "available_permissions": Role.get_all_permissions(),
    }
    return render(request, "organizations/role_list.html", context)


@login_required(login_url="admin_login")
def role_create(request):
    """Create a new role - superuser only"""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can create roles.")
        return redirect("index")

    available_permissions = Role.get_all_permissions()

    if request.method == "POST":
        name = request.POST.get("name", "").strip().lower().replace(" ", "_")
        display_name = request.POST.get("display_name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(request, "Role name is required.")
        elif Role.objects.filter(name=name).exists():
            messages.error(request, "A role with this name already exists.")
        else:
            role = Role.objects.create(
                name=name,
                display_name=display_name or name.replace("_", " ").title(),
                description=description,
                is_active=is_active,
            )

            # Set permissions from checkboxes
            for perm in available_permissions:
                setattr(role, perm, request.POST.get(perm) == "on")
            role.save()

            log_create(user=request.user, target=role, request=request)
            messages.success(
                request, f'Role "{role.display_name}" created successfully!'
            )
            return redirect("role_list")

    context = {
        "title": "Create Role",
        "subTitle": "Create New Role",
        "available_permissions": available_permissions,
        "permission_labels": {
            "can_manage_center": "Manage Translation Centers",
            "can_manage_branches": "Manage Branches",
            "can_manage_staff": "Manage Staff Members",
            "can_view_all_orders": "View All Orders",
            "can_manage_orders": "Manage Orders",
            "can_assign_orders": "Assign Orders to Staff",
            "can_receive_payments": "Receive Payments",
            "can_view_reports": "View Reports & Analytics",
            "can_manage_products": "Manage Products & Services",
            "can_manage_customers": "Manage Customers",
            "can_export_data": "Export Data",
        },
    }
    return render(request, "organizations/role_form.html", context)


@login_required(login_url="admin_login")
def role_edit(request, role_id):
    """Edit a role - superuser only"""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can edit roles.")
        return redirect("index")

    role = get_object_or_404(Role, pk=role_id)
    available_permissions = Role.get_all_permissions()

    if request.method == "POST":
        display_name = request.POST.get("display_name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        # Don't allow changing system role names
        if not role.is_system_role:
            name = request.POST.get("name", "").strip().lower().replace(" ", "_")
            if name and name != role.name:
                if Role.objects.filter(name=name).exclude(pk=role.pk).exists():
                    messages.error(request, "A role with this name already exists.")
                    return redirect("role_edit", role_id=role_id)
                role.name = name

        role.display_name = display_name or role.name.replace("_", " ").title()
        role.description = description
        role.is_active = is_active

        # Set permissions from checkboxes
        for perm in available_permissions:
            setattr(role, perm, request.POST.get(perm) == "on")

        role.save()

        log_update(
            user=request.user,
            target=role,
            changes={"permissions": "updated"},
            request=request,
        )
        messages.success(request, f'Role "{role.display_name}" updated successfully!')
        return redirect("role_list")

    context = {
        "title": "Edit Role",
        "subTitle": f"Edit Role: {role.display_name}",
        "role": role,
        "available_permissions": available_permissions,
        "permission_labels": {
            "can_manage_center": "Manage Translation Centers",
            "can_manage_branches": "Manage Branches",
            "can_manage_staff": "Manage Staff Members",
            "can_view_all_orders": "View All Orders",
            "can_manage_orders": "Manage Orders",
            "can_assign_orders": "Assign Orders to Staff",
            "can_receive_payments": "Receive Payments",
            "can_view_reports": "View Reports & Analytics",
            "can_manage_products": "Manage Products & Services",
            "can_manage_customers": "Manage Customers",
            "can_export_data": "Export Data",
        },
    }
    return render(request, "organizations/role_form.html", context)


@login_required(login_url="admin_login")
def role_delete(request, role_id):
    """Delete a role - superuser only, cannot delete system roles"""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can delete roles.")
        return redirect("index")

    role = get_object_or_404(Role, pk=role_id)

    if role.is_system_role:
        messages.error(request, "System roles cannot be deleted.")
        return redirect("role_list")

    if role.users.exists():
        messages.error(
            request,
            f'Cannot delete role "{role.display_name}" - it has {role.users.count()} users assigned.',
        )
        return redirect("role_list")

    if request.method == "POST":
        role_name = role.display_name
        log_delete(user=request.user, target=role, request=request)
        role.delete()
        messages.success(request, f'Role "{role_name}" deleted successfully!')
        return redirect("role_list")

    return redirect("role_list")
