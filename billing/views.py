from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from .models import Tariff, TariffPricing, Subscription, Feature, UsageTracking, SubscriptionHistory
from organizations.models import TranslationCenter


@login_required
def subscription_list(request):
    """List all subscriptions - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    # Filters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    subscriptions = Subscription.objects.select_related(
        'organization', 'tariff', 'pricing', 'created_by'
    ).all()
    
    # Apply filters
    if status_filter != 'all':
        subscriptions = subscriptions.filter(status=status_filter)
    
    if search_query:
        subscriptions = subscriptions.filter(
            Q(organization__name__icontains=search_query) |
            Q(organization__subdomain__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )
    
    # Statistics
    total_subscriptions = Subscription.objects.count()
    active_count = Subscription.objects.filter(status=Subscription.STATUS_ACTIVE).count()
    expired_count = Subscription.objects.filter(status=Subscription.STATUS_EXPIRED).count()
    pending_count = Subscription.objects.filter(status=Subscription.STATUS_PENDING).count()
    
    # Expiring soon (within 7 days)
    expiring_soon = Subscription.objects.filter(
        status=Subscription.STATUS_ACTIVE,
        end_date__lte=date.today() + timedelta(days=7),
        end_date__gte=date.today()
    ).count()
    
    # Pagination
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    subscriptions_page = paginator.get_page(page_number)
    
    context = {
        'subscriptions': subscriptions_page,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_subscriptions': total_subscriptions,
        'active_count': active_count,
        'expired_count': expired_count,
        'pending_count': pending_count,
        'expiring_soon': expiring_soon,
    }
    
    return render(request, 'billing/subscription_list.html', context)


@login_required
def subscription_create(request, center_id):
    """Create subscription for a center - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    center = get_object_or_404(TranslationCenter, pk=center_id)
    
    if request.method == 'POST':
        tariff_id = request.POST.get('tariff')
        pricing_id = request.POST.get('pricing')
        start_date_str = request.POST.get('start_date')
        status = request.POST.get('status', Subscription.STATUS_PENDING)
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id')
        notes = request.POST.get('notes', '')
        auto_renew = request.POST.get('auto_renew') == 'on'
        
        try:
            tariff = Tariff.objects.get(pk=tariff_id)
            pricing = TariffPricing.objects.get(pk=pricing_id)
            
            # Convert string date to date object
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            
            # Check if center already has subscription
            if hasattr(center, 'subscription'):
                # Cancel old subscription
                old_sub = center.subscription
                old_sub.status = Subscription.STATUS_CANCELLED
                old_sub.save()
                
                SubscriptionHistory.objects.create(
                    subscription=old_sub,
                    action='cancelled',
                    description=_('Cancelled to create new subscription'),
                    performed_by=request.user
                )
            
            # Create new subscription
            subscription = Subscription.objects.create(
                organization=center,
                tariff=tariff,
                pricing=pricing,
                start_date=start_date,
                status=status,
                amount_paid=amount_paid if amount_paid else None,
                payment_method=payment_method,
                transaction_id=transaction_id,
                notes=notes,
                auto_renew=auto_renew,
                created_by=request.user
            )
            
            if status == Subscription.STATUS_ACTIVE:
                subscription.payment_date = date.today()
                subscription.save()
            
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='created',
                description=_('Subscription created by superuser'),
                performed_by=request.user
            )
            
            messages.success(request, _("Subscription created successfully!"))
            return redirect('billing:subscription_list')
            
        except Exception as e:
            messages.error(request, f"Error creating subscription: {str(e)}")
    
    tariffs = Tariff.objects.filter(is_active=True).prefetch_related('pricing')
    
    context = {
        'center': center,
        'tariffs': tariffs,
    }
    
    return render(request, 'billing/subscription_create.html', context)


@login_required
def subscription_detail(request, pk):
    """View subscription details - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    subscription = get_object_or_404(
        Subscription.objects.select_related(
            'organization', 'tariff', 'pricing', 'created_by'
        ).prefetch_related('history'),
        pk=pk
    )
    
    # Get usage statistics
    current_usage = {}
    if subscription.organization:
        org = subscription.organization
        current_usage = {
            'branches': org.branches.count(),
            'branches_limit': subscription.tariff.max_branches,
            'branches_percent': subscription.get_usage_percentage('branches'),
            'staff': org.get_staff_count(),
            'staff_limit': subscription.tariff.max_staff,
            'staff_percent': subscription.get_usage_percentage('staff'),
            'orders': org.get_current_month_orders_count(),
            'orders_limit': subscription.tariff.max_monthly_orders,
            'orders_percent': subscription.get_usage_percentage('orders'),
        }
    
    context = {
        'subscription': subscription,
        'current_usage': current_usage,
    }
    
    return render(request, 'billing/subscription_detail.html', context)


@login_required
def subscription_update_status(request, pk):
    """Update subscription status - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied."))
        return redirect('dashboard')
    
    if request.method == 'POST':
        subscription = get_object_or_404(Subscription, pk=pk)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        old_status = subscription.status
        subscription.status = new_status
        
        if new_status == Subscription.STATUS_ACTIVE and not subscription.payment_date:
            subscription.payment_date = date.today()
        
        subscription.save()
        
        SubscriptionHistory.objects.create(
            subscription=subscription,
            action='status_changed',
            description=f'Status changed from {old_status} to {new_status}. {notes}',
            performed_by=request.user
        )
        
        messages.success(request, _("Subscription status updated successfully!"))
    
    return redirect('billing:subscription_detail', pk=pk)


@login_required
def tariff_list(request):
    """List all tariffs - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    tariffs = Tariff.objects.prefetch_related('pricing', 'features').all()
    
    context = {
        'tariffs': tariffs,
    }
    
    return render(request, 'billing/tariff_list.html', context)


@login_required
def usage_tracking_list(request):
    """View usage tracking statistics - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    # Filters
    center_id = request.GET.get('center')
    year = request.GET.get('year', date.today().year)
    month = request.GET.get('month', date.today().month)
    
    usage_data = UsageTracking.objects.select_related('organization').all()
    
    if center_id:
        usage_data = usage_data.filter(organization_id=center_id)
    
    if year:
        usage_data = usage_data.filter(year=year)
    
    if month:
        usage_data = usage_data.filter(month=month)
    
    usage_data = usage_data.order_by('-year', '-month')
    
    # Pagination
    paginator = Paginator(usage_data, 20)
    page_number = request.GET.get('page')
    usage_page = paginator.get_page(page_number)
    
    # Get all centers for filter
    centers = TranslationCenter.objects.all().order_by('name')
    
    # Generate year and month ranges for filters
    current_year = date.today().year
    years = list(range(2024, current_year + 2))  # 2024 to current year + 1
    months = list(range(1, 13))  # 1 to 12
    
    context = {
        'usage_data': usage_page,
        'centers': centers,
        'selected_center': center_id,
        'selected_year': year,
        'selected_month': month,
        'years': years,
        'months': months,
    }
    
    return render(request, 'billing/usage_tracking.html', context)


@login_required
def centers_list(request):
    """List all translation centers with subscription status - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    search_query = request.GET.get('search', '')
    
    centers = TranslationCenter.objects.select_related('owner').prefetch_related('subscription').all()
    
    if search_query:
        centers = centers.filter(
            Q(name__icontains=search_query) |
            Q(subdomain__icontains=search_query) |
            Q(owner__username__icontains=search_query)
        )
    
    # Add subscription status to each center
    for center in centers:
        if hasattr(center, 'subscription'):
            center.sub_status = center.subscription.status
            center.sub_tariff = center.subscription.tariff.title
            center.sub_end_date = center.subscription.end_date
        else:
            center.sub_status = None
            center.sub_tariff = None
            center.sub_end_date = None
    
    # Pagination
    paginator = Paginator(centers, 20)
    page_number = request.GET.get('page')
    centers_page = paginator.get_page(page_number)
    
    # Statistics
    total_centers = TranslationCenter.objects.count()
    with_subscription = TranslationCenter.objects.filter(subscription__isnull=False).count()
    without_subscription = total_centers - with_subscription
    
    context = {
        'centers': centers_page,
        'search_query': search_query,
        'total_centers': total_centers,
        'with_subscription': with_subscription,
        'without_subscription': without_subscription,
    }
    
    return render(request, 'billing/centers_list.html', context)
