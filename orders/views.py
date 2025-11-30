from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderMedia
from organizations.rbac import (
    get_user_orders, get_user_staff, get_user_branches,
    admin_profile_required, role_required, manager_or_owner_required,
    permission_required
)
from organizations.models import AdminUser
from core.audit import log_action, log_order_assign, log_status_change


@login_required(login_url='admin_login')
def ordersList(request):
    """List all orders with search and filter - RBAC aware"""
    # Get orders based on user's role and permissions
    if request.user.is_superuser:
        orders = Order.objects.all()
    else:
        orders = get_user_orders(request.user)
    
    orders = orders.select_related(
        'bot_user', 'product', 'language', 'branch', 'branch__center',
        'assigned_to', 'assigned_to__user'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(bot_user__name__icontains=search_query) |
            Q(bot_user__username__icontains=search_query) |
            Q(bot_user__phone__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Payment type filter
    payment_filter = request.GET.get('payment', '')
    if payment_filter:
        orders = orders.filter(payment_type=payment_filter)
    
    # Center filter (for superusers only)
    center_filter = request.GET.get('center', '')
    if center_filter and request.user.is_superuser:
        orders = orders.filter(branch__center_id=center_filter)
    
    # Branch filter (for owners/superusers who can see multiple branches)
    branch_filter = request.GET.get('branch', '')
    if branch_filter:
        orders = orders.filter(branch_id=branch_filter)
    
    # Assignment filter
    assignment_filter = request.GET.get('assignment', '')
    if assignment_filter == 'unassigned':
        orders = orders.filter(assigned_to__isnull=True)
    elif assignment_filter == 'assigned':
        orders = orders.filter(assigned_to__isnull=False)
    elif assignment_filter == 'mine' and request.admin_profile:
        orders = orders.filter(assigned_to=request.admin_profile)
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    
    paginator = Paginator(orders, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    status_choices = Order.STATUS_CHOICES
    payment_choices = Order.PAYMENT_TYPE
    
    # Get accessible branches for filter dropdown
    branches = get_user_branches(request.user) if not request.user.is_superuser else None
    centers = None
    
    if request.user.is_superuser:
        from organizations.models import Branch, TranslationCenter
        branches = Branch.objects.filter(is_active=True).select_related('center')
        centers = TranslationCenter.objects.filter(is_active=True)
    
    # Get order statistics
    base_orders = get_user_orders(request.user) if not request.user.is_superuser else Order.objects.all()
    stats = {
        'total': base_orders.count(),
        'pending': base_orders.filter(status='pending').count(),
        'in_progress': base_orders.filter(status='in_progress').count(),
        'completed': base_orders.filter(status='completed').count(),
        'unassigned': base_orders.filter(assigned_to__isnull=True).count(),
    }
    
    context = {
        "title": "Orders List",
        "subTitle": "Orders List",
        "orders": page_obj,
        "paginator": paginator,
        "search_query": search_query,
        "status_filter": status_filter,
        "payment_filter": payment_filter,
        "center_filter": center_filter,
        "branch_filter": branch_filter,
        "assignment_filter": assignment_filter,
        "per_page": per_page,
        "total_orders": paginator.count,
        "status_choices": status_choices,
        "payment_choices": payment_choices,
        "centers": centers,
        "branches": branches,
        "stats": stats,
    }
    return render(request, "orders/ordersList.html", context)


@login_required(login_url='admin_login')
def orderDetail(request, order_id):
    """View order details with RBAC check"""
    order = get_object_or_404(
        Order.objects.select_related(
            'bot_user', 'product', 'language', 'branch', 'branch__center',
            'assigned_to', 'assigned_to__user', 'assigned_by', 'assigned_by__user',
            'payment_received_by', 'payment_received_by__user',
            'completed_by', 'completed_by__user'
        ), 
        id=order_id
    )
    
    # Check access permissions
    if not request.user.is_superuser and request.admin_profile:
        accessible_branches = request.admin_profile.get_accessible_branches()
        if order.branch not in accessible_branches:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
        
        # Staff can only see orders assigned to them
        if request.is_staff_member and order.assigned_to != request.admin_profile:
            messages.error(request, "You can only view orders assigned to you.")
            return redirect('ordersList')
    
    # Get available staff for assignment (for owners/managers)
    available_staff = []
    can_assign = False
    can_update_status = False
    can_receive_payment = False
    can_complete = False
    
    if request.user.is_superuser:
        can_assign = True
        can_update_status = True
        can_receive_payment = True
        can_complete = True
        available_staff = AdminUser.objects.filter(
            branch=order.branch,
            is_active=True
        ).select_related('user', 'role')
    elif request.admin_profile:
        # Owners and managers can assign orders
        if request.is_owner or request.is_manager:
            can_assign = True
            can_update_status = True
            can_receive_payment = True
            can_complete = True
            available_staff = AdminUser.objects.filter(
                branch=order.branch,
                is_active=True
            ).select_related('user', 'role')
        elif request.is_staff_member and order.assigned_to == request.admin_profile:
            # Staff can update status of their assigned orders
            can_update_status = True
    
    # Get allowed status transitions based on current status
    allowed_transitions = get_allowed_status_transitions(order.status)
    
    context = {
        "title": f"Order #{order.id}",
        "subTitle": "Order Details",
        "order": order,
        "available_staff": available_staff,
        "can_assign": can_assign,
        "can_update_status": can_update_status,
        "can_receive_payment": can_receive_payment,
        "can_complete": can_complete,
        "allowed_transitions": allowed_transitions,
        "status_choices": Order.STATUS_CHOICES,
    }
    return render(request, "orders/orderDetail.html", context)


def get_allowed_status_transitions(current_status):
    """Get allowed status transitions from current status"""
    transitions = {
        'pending': ['payment_pending', 'cancelled'],
        'payment_pending': ['payment_received', 'cancelled'],
        'payment_received': ['payment_confirmed', 'payment_pending'],
        'payment_confirmed': ['in_progress', 'cancelled'],
        'in_progress': ['ready', 'cancelled'],
        'ready': ['completed', 'in_progress'],
        'completed': [],
        'cancelled': ['pending'],  # Allow reactivation
    }
    return transitions.get(current_status, [])


@login_required(login_url='admin_login')
@require_POST
def updateOrderStatus(request, order_id):
    """Update order status with RBAC check"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check access permissions
    if not request.user.is_superuser and request.admin_profile:
        accessible_branches = request.admin_profile.get_accessible_branches()
        if order.branch not in accessible_branches:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
        
        # Staff can only update orders assigned to them
        if request.is_staff_member and order.assigned_to != request.admin_profile:
            messages.error(request, "You can only update orders assigned to you.")
            return redirect('ordersList')
    
    new_status = request.POST.get('status')
    if new_status not in dict(Order.STATUS_CHOICES):
        messages.error(request, 'Invalid status')
        return redirect('orderDetail', order_id=order_id)
    
    # Validate status transition
    allowed_transitions = get_allowed_status_transitions(order.status)
    if new_status not in allowed_transitions:
        messages.error(request, f'Cannot change status from {order.get_status_display()} to {dict(Order.STATUS_CHOICES).get(new_status)}')
        return redirect('orderDetail', order_id=order_id)
    
    old_status = order.status
    admin_profile = request.admin_profile
    
    # Use helper methods for special status changes
    if new_status == 'payment_confirmed' and admin_profile:
        order.mark_payment_received(admin_profile)
    elif new_status == 'completed' and admin_profile:
        order.mark_completed(admin_profile)
    else:
        order.status = new_status
        order.save()
    
    # Audit log the status change
    log_status_change(
        user=request.user,
        order=order,
        old_status=old_status,
        new_status=new_status,
        request=request
    )
    
    messages.success(request, f'Order status updated from {dict(Order.STATUS_CHOICES).get(old_status)} to {dict(Order.STATUS_CHOICES).get(new_status)}')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'new_status_display': order.get_status_display(),
        })
    
    return redirect('orderDetail', order_id=order_id)


@login_required(login_url='admin_login')
def deleteOrder(request, order_id):
    """Delete an order - only owners/superusers"""
    order = get_object_or_404(Order, id=order_id)
    
    # Only superusers and owners can delete orders
    if not request.user.is_superuser:
        if not request.admin_profile or not request.is_owner:
            messages.error(request, "Only owners can delete orders.")
            return redirect('ordersList')
        
        # Check if owner has access to this order's branch
        if order.branch and order.branch.center.owner != request.user:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
    
    if request.method == 'POST':
        order.delete()
        messages.success(request, f'Order #{order_id} has been deleted')
        return redirect('ordersList')
    
    return redirect('orderDetail', order_id=order_id)


@login_required(login_url='admin_login')
@require_POST
def assignOrder(request, order_id):
    """Assign an order to a staff member - owners/managers only"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not request.user.is_superuser:
        if not request.admin_profile:
            messages.error(request, "You need an admin profile to assign orders.")
            return redirect('ordersList')
        
        if not (request.is_owner or request.is_manager):
            messages.error(request, "Only owners and managers can assign orders.")
            return redirect('orderDetail', order_id=order_id)
        
        # Check branch access
        accessible_branches = request.admin_profile.get_accessible_branches()
        if order.branch not in accessible_branches:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
    
    staff_id = request.POST.get('staff_id')
    if not staff_id:
        messages.error(request, "Please select a staff member.")
        return redirect('orderDetail', order_id=order_id)
    
    try:
        staff_member = AdminUser.objects.get(pk=staff_id, is_active=True)
    except AdminUser.DoesNotExist:
        messages.error(request, "Invalid staff member selected.")
        return redirect('orderDetail', order_id=order_id)
    
    # Verify staff is in the same branch as the order
    if staff_member.branch != order.branch:
        messages.error(request, "Staff member must be in the same branch as the order.")
        return redirect('orderDetail', order_id=order_id)
    
    # Assign the order
    assigner = request.admin_profile if request.admin_profile else None
    order.assign_to_staff(staff_member, assigner)
    
    # Audit log the assignment
    log_order_assign(
        user=request.user,
        order=order,
        staff=staff_member,
        request=request
    )
    
    messages.success(request, f'Order #{order_id} assigned to {staff_member.user.get_full_name() or staff_member.user.username}')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'assigned_to': str(staff_member),
            'assigned_at': order.assigned_at.isoformat() if order.assigned_at else None,
        })
    
    return redirect('orderDetail', order_id=order_id)


@login_required(login_url='admin_login')
@require_POST
def unassignOrder(request, order_id):
    """Unassign an order from a staff member - owners/managers only"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not request.user.is_superuser:
        if not request.admin_profile:
            messages.error(request, "You need an admin profile to unassign orders.")
            return redirect('ordersList')
        
        if not (request.is_owner or request.is_manager):
            messages.error(request, "Only owners and managers can unassign orders.")
            return redirect('orderDetail', order_id=order_id)
        
        # Check branch access
        accessible_branches = request.admin_profile.get_accessible_branches()
        if order.branch not in accessible_branches:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
    
    # Clear assignment
    previous_assignee = order.assigned_to
    previous_assignee_name = str(previous_assignee) if previous_assignee else None
    order.assigned_to = None
    order.assigned_by = None
    order.assigned_at = None
    if order.status == 'in_progress':
        order.status = 'payment_confirmed'
    order.save()
    
    # Audit log the unassignment
    log_action(
        user=request.user,
        action='assign',
        target=order,
        details=f'Order #{order.id} unassigned from {previous_assignee_name}',
        changes={
            'action': 'unassigned',
            'previous_assignee': previous_assignee_name,
        },
        request=request
    )
    
    messages.success(request, f'Order #{order_id} has been unassigned')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('orderDetail', order_id=order_id)


@login_required(login_url='admin_login')
@require_POST
def receivePayment(request, order_id):
    """Mark payment as received - owners/managers only"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not request.user.is_superuser:
        if not request.admin_profile:
            messages.error(request, "You need an admin profile to receive payments.")
            return redirect('ordersList')
        
        if not (request.is_owner or request.is_manager):
            messages.error(request, "Only owners and managers can receive payments.")
            return redirect('orderDetail', order_id=order_id)
        
        # Check branch access
        accessible_branches = request.admin_profile.get_accessible_branches()
        if order.branch not in accessible_branches:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
    
    # Mark payment received
    receiver = request.admin_profile if request.admin_profile else None
    order.mark_payment_received(receiver)
    
    messages.success(request, f'Payment received for Order #{order_id}')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_status': order.status,
            'new_status_display': order.get_status_display(),
        })
    
    return redirect('orderDetail', order_id=order_id)


@login_required(login_url='admin_login')
@require_POST
def completeOrder(request, order_id):
    """Mark order as completed"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not request.user.is_superuser:
        if not request.admin_profile:
            messages.error(request, "You need an admin profile to complete orders.")
            return redirect('ordersList')
        
        # Check branch access
        accessible_branches = request.admin_profile.get_accessible_branches()
        if order.branch not in accessible_branches:
            messages.error(request, "You don't have access to this order.")
            return redirect('ordersList')
        
        # Staff can only complete orders assigned to them
        if request.is_staff_member and order.assigned_to != request.admin_profile:
            messages.error(request, "You can only complete orders assigned to you.")
            return redirect('orderDetail', order_id=order_id)
    
    # Check if order is ready to be completed
    if order.status not in ['ready', 'in_progress']:
        messages.error(request, "Order must be ready or in progress to complete.")
        return redirect('orderDetail', order_id=order_id)
    
    # Mark completed
    completer = request.admin_profile if request.admin_profile else None
    order.mark_completed(completer)
    
    messages.success(request, f'Order #{order_id} marked as completed')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_status': order.status,
            'new_status_display': order.get_status_display(),
        })
    
    return redirect('orderDetail', order_id=order_id)


# ============ API Endpoints ============

@login_required(login_url='admin_login')
def api_order_stats(request):
    """API endpoint for order statistics"""
    if request.user.is_superuser:
        base_orders = Order.objects.all()
    else:
        base_orders = get_user_orders(request.user)
    
    stats = {
        'total': base_orders.count(),
        'pending': base_orders.filter(status='pending').count(),
        'payment_pending': base_orders.filter(status='payment_pending').count(),
        'payment_received': base_orders.filter(status='payment_received').count(),
        'payment_confirmed': base_orders.filter(status='payment_confirmed').count(),
        'in_progress': base_orders.filter(status='in_progress').count(),
        'ready': base_orders.filter(status='ready').count(),
        'completed': base_orders.filter(status='completed').count(),
        'cancelled': base_orders.filter(status='cancelled').count(),
        'unassigned': base_orders.filter(assigned_to__isnull=True).exclude(
            status__in=['completed', 'cancelled']
        ).count(),
    }
    
    return JsonResponse(stats)


@login_required(login_url='admin_login')
def api_branch_staff(request, branch_id):
    """API endpoint to get staff members for a branch"""
    from organizations.models import Branch
    
    try:
        branch = Branch.objects.get(pk=branch_id, is_active=True)
    except Branch.DoesNotExist:
        return JsonResponse({'error': 'Branch not found'}, status=404)
    
    # Check access
    if not request.user.is_superuser and request.admin_profile:
        accessible_branches = request.admin_profile.get_accessible_branches()
        if branch not in accessible_branches:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    staff = AdminUser.objects.filter(
        branch=branch,
        is_active=True
    ).select_related('user', 'role')
    
    staff_list = [
        {
            'id': s.pk,
            'name': s.user.get_full_name() or s.user.username,
            'role': s.role.get_display_name() if s.role else 'Unknown',
            'assigned_orders': s.assigned_orders.filter(
                status__in=['in_progress', 'ready']
            ).count(),
        }
        for s in staff
    ]
    
    return JsonResponse({'staff': staff_list})


@login_required(login_url='admin_login')
def myOrders(request):
    """List orders assigned to the current user (for staff)"""
    if not request.admin_profile:
        messages.error(request, "You need an admin profile to view your orders.")
        return redirect('index')
    
    orders = Order.objects.filter(
        assigned_to=request.admin_profile
    ).select_related(
        'bot_user', 'product', 'language', 'branch'
    ).order_by('-created_at')
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10
    
    paginator = Paginator(orders, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Stats for my orders
    my_orders = Order.objects.filter(assigned_to=request.admin_profile)
    stats = {
        'total': my_orders.count(),
        'in_progress': my_orders.filter(status='in_progress').count(),
        'ready': my_orders.filter(status='ready').count(),
        'completed': my_orders.filter(status='completed').count(),
    }
    
    context = {
        "title": "My Orders",
        "subTitle": "Orders Assigned to Me",
        "orders": page_obj,
        "paginator": paginator,
        "status_filter": status_filter,
        "per_page": per_page,
        "total_orders": paginator.count,
        "status_choices": Order.STATUS_CHOICES,
        "stats": stats,
    }
    return render(request, "orders/myOrders.html", context)
