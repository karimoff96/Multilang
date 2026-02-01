from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Prefetch
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from .models import Tariff, TariffPricing, Subscription, Feature, UsageTracking, SubscriptionHistory, SubscriptionAnalytics
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
        'title': _('Subscription Management'),
        'subTitle': _('Subscriptions'),
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
            if not tariff_id:
                messages.error(request, _("Please select a tariff."))
                tariffs = Tariff.objects.filter(is_active=True).prefetch_related('pricing')
                return render(request, 'billing/subscription_create.html', {'center': center, 'tariffs': tariffs})
            
            tariff = Tariff.objects.get(pk=tariff_id)
            
            # For trial subscriptions, pricing is not required
            if tariff.is_trial:
                pricing = None
            else:
                if not pricing_id or pricing_id == 'trial':
                    messages.error(request, _("Please select a pricing option for non-trial tariffs."))
                    tariffs = Tariff.objects.filter(is_active=True).prefetch_related('pricing')
                    return render(request, 'billing/subscription_create.html', {'center': center, 'tariffs': tariffs})
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
                status=status if not tariff.is_trial else Subscription.STATUS_ACTIVE,
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
            'organization', 'tariff', 'pricing'
        ),
        pk=pk
    )
    
    # Get comprehensive analytics for this center
    org = subscription.organization
    analytics = SubscriptionAnalytics.get_center_analytics(org)
    
    # Get usage statistics
    current_usage = {}
    if subscription.organization:
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
    
    # Get subscription history
    history_entries = subscription.history.all()[:20]  # Last 20 entries
    
    context = {
        'title': _('Billing'),
        'subTitle': _('Subscription Detail'),
        'subscription': subscription,
        'current_usage': current_usage,
        'analytics': analytics,
        'history_entries': history_entries,
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
        'title': _('Tariff Plans'),
        'subTitle': _('Tariffs'),
        'tariffs': tariffs,
    }
    
    return render(request, 'billing/tariff_list.html', context)


@login_required
def tariff_create(request):
    """Create new tariff - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            slug = request.POST.get('slug')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            is_trial = request.POST.get('is_trial') == 'on'
            trial_days = request.POST.get('trial_days') or None
            display_order = request.POST.get('display_order', 0)
            
            # Limits
            max_branches = request.POST.get('max_branches') or None
            max_staff = request.POST.get('max_staff') or None
            max_monthly_orders = request.POST.get('max_monthly_orders') or None
            
            tariff = Tariff.objects.create(
                title=title,
                slug=slug,
                description=description,
                is_active=is_active,
                is_featured=is_featured,
                is_trial=is_trial,
                trial_days=trial_days,
                display_order=display_order,
                max_branches=max_branches,
                max_staff=max_staff,
                max_monthly_orders=max_monthly_orders,
            )
            
            # Set feature flags (37 boolean fields)
            feature_fields = [
                # Orders (5)
                'feature_orders_basic', 'feature_orders_advanced', 'feature_orders_bulk',
                'feature_orders_archive', 'feature_bulk_payment_collection',
                # Analytics (6)
                'feature_analytics_basic', 'feature_analytics_advanced', 'feature_sales_reports',
                'feature_finance_reports', 'feature_custom_reports', 'feature_export_data',
                # Integration (4)
                'feature_webhooks', 'feature_api_access', 'feature_third_party_integrations',
                'feature_telegram_bot',
                # Marketing (2)
                'feature_marketing_campaigns', 'feature_broadcasts',
                # Organization (4)
                'feature_multi_branch', 'feature_staff_management', 'feature_rbac', 'feature_audit_logs',
                # Storage (3)
                'feature_file_uploads', 'feature_storage_basic', 'feature_storage_advanced',
                # Financial (4)
                'feature_payment_tracking', 'feature_expense_management', 'feature_payment_reminders',
                'feature_invoicing',
                # Support (2)
                'feature_priority_support', 'feature_onboarding',
                # Advanced (3)
                'feature_white_label', 'feature_data_backup', 'feature_advanced_security',
                # Services (4)
                'feature_services_basic', 'feature_services_advanced', 'feature_service_tracking',
                'feature_service_analytics',
            ]
            
            for field in feature_fields:
                setattr(tariff, field, request.POST.get(field) == 'on')
            
            tariff.save()
            
            messages.success(request, _("Tariff created successfully!"))
            return redirect('billing:tariff_list')
            
        except Exception as e:
            messages.error(request, f"Error creating tariff: {str(e)}")
    
    
    return render(request, 'billing/tariff_create.html')


@login_required
def tariff_edit(request, pk):
    """Edit tariff - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    tariff = get_object_or_404(Tariff, pk=pk)
    
    if request.method == 'POST':
        try:
            # Set all language variants
            tariff.title_uz = request.POST.get('title_uz', '')
            tariff.title_ru = request.POST.get('title_ru', '')
            tariff.title_en = request.POST.get('title_en', '')
            
            # Also set base title to default language (Uzbek)
            tariff.title = request.POST.get('title_uz', '')
            
            tariff.slug = request.POST.get('slug')
            
            tariff.description_uz = request.POST.get('description_uz', '')
            tariff.description_ru = request.POST.get('description_ru', '')
            tariff.description_en = request.POST.get('description_en', '')
            
            # Also set base description to default language (Uzbek)
            tariff.description = request.POST.get('description_uz', '')
            
            tariff.is_active = request.POST.get('is_active') == 'on'
            tariff.is_featured = request.POST.get('is_featured') == 'on'
            tariff.is_trial = request.POST.get('is_trial') == 'on'
            tariff.trial_days = request.POST.get('trial_days') or None
            tariff.display_order = request.POST.get('display_order', 0)
            
            # Limits
            max_branches = request.POST.get('max_branches')
            max_staff = request.POST.get('max_staff')
            max_monthly_orders = request.POST.get('max_monthly_orders')
            
            tariff.max_branches = int(max_branches) if max_branches else None
            tariff.max_staff = int(max_staff) if max_staff else None
            tariff.max_monthly_orders = int(max_monthly_orders) if max_monthly_orders else None
            
            tariff.save()
            
            # Update boolean feature flags (37 features)
            feature_fields = [
                # Orders (5)
                'feature_orders_basic', 'feature_orders_advanced', 'feature_order_assignment',
                'feature_bulk_payments', 'feature_order_templates',
                # Analytics (6)
                'feature_analytics_basic', 'feature_analytics_advanced', 'feature_financial_reports',
                'feature_staff_performance', 'feature_custom_reports', 'feature_export_reports',
                # Integration (4)
                'feature_telegram_bot', 'feature_webhooks', 'feature_api_access', 'feature_integrations',
                # Marketing (2)
                'feature_marketing_basic', 'feature_broadcast_messages',
                # Organization (4)
                'feature_multi_branch', 'feature_custom_roles', 'feature_staff_scheduling', 'feature_branch_settings',
                # Storage (3)
                'feature_archive_access', 'feature_cloud_backup', 'feature_extended_storage',
                # Financial (4)
                'feature_payment_management', 'feature_multi_currency', 'feature_invoicing', 'feature_expense_tracking',
                # Support (2)
                'feature_support_tickets', 'feature_knowledge_base',
                # Advanced (3)
                'feature_advanced_security', 'feature_audit_logs', 'feature_data_retention',
                # Services (4)
                'feature_products_basic', 'feature_products_advanced', 'feature_language_pricing', 'feature_dynamic_pricing',
            ]
            
            for field in feature_fields:
                setattr(tariff, field, request.POST.get(field) == 'on')
            
            tariff.save()
            
            # Update pricing
            pricing_ids = request.POST.getlist('pricing_id[]')
            pricing_durations = request.POST.getlist('pricing_duration[]')
            pricing_monthly = request.POST.getlist('pricing_monthly[]')
            pricing_total = request.POST.getlist('pricing_total[]')
            pricing_currency = request.POST.getlist('pricing_currency[]')
            
            # Track existing pricing IDs to know which to delete
            existing_ids = set()
            
            for i in range(len(pricing_durations)):
                pricing_id = pricing_ids[i] if i < len(pricing_ids) else ''
                duration = int(pricing_durations[i]) if pricing_durations[i] else 1
                monthly = float(pricing_monthly[i]) if pricing_monthly[i] else 0
                total = float(pricing_total[i]) if pricing_total[i] else 0
                currency = pricing_currency[i] if i < len(pricing_currency) else 'UZS'
                
                # Skip if no valid pricing data
                if duration <= 0 or total <= 0:
                    continue
                
                if pricing_id:
                    # Update existing pricing
                    pricing_obj = TariffPricing.objects.get(id=pricing_id, tariff=tariff)
                    pricing_obj.duration_months = duration
                    pricing_obj.monthly_price = monthly
                    pricing_obj.price = total
                    pricing_obj.currency = currency
                    pricing_obj.save()
                    existing_ids.add(int(pricing_id))
                else:
                    # Create new pricing
                    new_pricing = TariffPricing.objects.create(
                        tariff=tariff,
                        duration_months=duration,
                        monthly_price=monthly,
                        price=total,
                        currency=currency
                    )
                    existing_ids.add(new_pricing.id)
            
            # Delete pricing options that were removed
            tariff.pricing.exclude(id__in=existing_ids).delete()
            
            messages.success(request, _("Tariff updated successfully!"))
            return redirect('billing:tariff_list')
            
        except Exception as e:
            messages.error(request, f"Error updating tariff: {str(e)}")
    
    context = {
        'tariff': tariff,
    }
    
    return render(request, 'billing/tariff_edit.html', context)


@login_required
def tariff_delete(request, pk):
    """Delete tariff - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    tariff = get_object_or_404(Tariff, pk=pk)
    
    # Check if tariff has any subscriptions
    subscription_count = tariff.subscriptions.count()
    if subscription_count > 0:
        messages.error(request, _(f"Cannot delete tariff '{tariff.title}'. It has {subscription_count} subscription(s) associated with it."))
        return redirect('billing:tariff_list')
    
    if request.method == 'POST':
        tariff_name = tariff.title
        tariff.delete()
        messages.success(request, _(f"Tariff '{tariff_name}' deleted successfully!"))
        return redirect('billing:tariff_list')
    
    return redirect('billing:tariff_list')


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
    min_orders = request.GET.get('min_orders')
    min_revenue = request.GET.get('min_revenue')
    sort_by = request.GET.get('sort', '-total_revenue')  # Default: highest revenue first
    
    usage_data = UsageTracking.objects.select_related('organization').all()
    
    if center_id:
        usage_data = usage_data.filter(organization_id=center_id)
    
    if year:
        usage_data = usage_data.filter(year=year)
    
    if month:
        usage_data = usage_data.filter(month=month)
    
    if min_orders:
        try:
            usage_data = usage_data.filter(orders_created__gte=int(min_orders))
        except ValueError:
            pass
    
    if min_revenue:
        try:
            usage_data = usage_data.filter(total_revenue__gte=float(min_revenue))
        except ValueError:
            pass
    
    # Apply sorting
    valid_sorts = ['organization__name', '-organization__name', 'orders_created', '-orders_created', 
                   'total_revenue', '-total_revenue', 'year', '-year', 'month', '-month']
    if sort_by in valid_sorts:
        usage_data = usage_data.order_by(sort_by, '-year', '-month')
    else:
        usage_data = usage_data.order_by('-total_revenue', '-year', '-month')
    
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
    
    # Calculate summary statistics
    total_orders = usage_data.aggregate(total=Sum('orders_created'))['total'] or 0
    total_revenue = usage_data.aggregate(total=Sum('total_revenue'))['total'] or 0
    total_centers = usage_data.values('organization').distinct().count()
    
    context = {
        'title': _('Usage Tracking'),
        'subTitle': _('Usage Tracking'),
        'usage_data': usage_page,
        'centers': centers,
        'selected_center': center_id,
        'selected_year': year,
        'selected_month': month,
        'min_orders': min_orders,
        'min_revenue': min_revenue,
        'sort_by': sort_by,
        'years': years,
        'months': months,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_centers': total_centers,
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
        'title': _('All Translation Centers'),
        'subTitle': _('Centers'),
        'centers': centers_page,
        'search_query': search_query,
        'total_centers': total_centers,
        'with_subscription': with_subscription,
        'without_subscription': without_subscription,
    }
    
    return render(request, 'billing/centers_list.html', context)


@login_required
def convert_trial_to_paid(request, pk):
    """Convert trial subscription to paid subscription - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    subscription = get_object_or_404(Subscription, pk=pk)
    
    if not subscription.is_trial:
        messages.error(request, _("This subscription is not a trial subscription."))
        return redirect('billing:subscription_detail', pk=pk)
    
    if request.method == 'POST':
        tariff_id = request.POST.get('tariff')
        pricing_id = request.POST.get('pricing')
        
        try:
            if not tariff_id or not pricing_id:
                messages.error(request, _("Please select both tariff and pricing option."))
                tariffs = Tariff.objects.filter(is_active=True, is_trial=False).prefetch_related('pricing')
                return render(request, 'billing/convert_trial.html', {'subscription': subscription, 'tariffs': tariffs})
            
            tariff = Tariff.objects.get(pk=tariff_id, is_trial=False)
            pricing = TariffPricing.objects.get(pk=pricing_id)
            
            if subscription.convert_trial_to_paid(tariff, pricing):
                messages.success(request, _("Trial subscription converted to paid subscription successfully!"))
                return redirect('billing:subscription_detail', pk=pk)
            else:
                messages.error(request, _("Failed to convert trial subscription."))
        except Exception as e:
            messages.error(request, f"Error converting subscription: {str(e)}")
    
    # Get non-trial tariffs for conversion
    tariffs = Tariff.objects.filter(is_active=True, is_trial=False).prefetch_related('pricing')
    
    context = {
        'subscription': subscription,
        'tariffs': tariffs,
    }
    
    return render(request, 'billing/convert_trial.html', context)


@login_required
def subscription_renew(request, pk):
    """Renew subscription - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    subscription = get_object_or_404(Subscription, pk=pk)
    
    if request.method == 'POST':
        pricing_id = request.GET.get('pricing_id') or request.POST.get('pricing')
        payment_method = request.POST.get('payment_method', '')
        transaction_id = request.POST.get('transaction_id', '')
        amount_paid = request.POST.get('amount_paid')
        notes = request.POST.get('notes', '')
        
        try:
            # Get pricing (can be same or different)
            if pricing_id:
                pricing = TariffPricing.objects.get(pk=pricing_id)
                tariff = pricing.tariff
            else:
                # Keep same pricing
                pricing = subscription.pricing
                tariff = subscription.tariff
            
            # Extend subscription
            old_end_date = subscription.end_date
            subscription.tariff = tariff
            subscription.pricing = pricing
            subscription.end_date = old_end_date + relativedelta(months=pricing.duration_months)
            subscription.status = Subscription.STATUS_PENDING
            subscription.payment_method = payment_method
            subscription.transaction_id = transaction_id
            subscription.notes = notes
            
            if amount_paid:
                subscription.amount_paid = amount_paid
                subscription.payment_date = datetime.now()
                subscription.status = Subscription.STATUS_ACTIVE
            
            subscription.save()
            
            # Log renewal
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='renewed',
                description=f'Subscription renewed for {pricing.duration_months} month(s). Extended from {old_end_date} to {subscription.end_date}',
                performed_by=request.user
            )
            
            messages.success(request, _("Subscription renewed successfully!"))
            return redirect('billing:subscription_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f"Error renewing subscription: {str(e)}")
    
    # Get available pricing options for current or other tariffs
    # Get all active tariffs
    tariffs = Tariff.objects.filter(is_active=True, is_trial=False).prefetch_related('pricing')
    
    # Filter pricing in template or here
    # Since we're passing to template, let's create a list with filtered pricing
    tariffs_with_pricing = []
    for tariff in tariffs:
        # Convert to list so template can iterate properly
        tariff.active_pricing = list(tariff.pricing.filter(is_active=True))
        tariffs_with_pricing.append(tariff)
    
    context = {
        'subscription': subscription,
        'tariffs': tariffs_with_pricing,
    }
    
    return render(request, 'billing/subscription_renew.html', context)


@login_required
def subscription_analytics(request, center_id):
    """Detailed subscription analytics for a specific center - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    center = get_object_or_404(TranslationCenter, pk=center_id)
    
    # Get comprehensive analytics
    analytics = SubscriptionAnalytics.get_center_analytics(center)
    
    # Get payment history with details
    payment_history = Subscription.objects.filter(
        organization=center
    ).exclude(
        amount_paid__isnull=True
    ).exclude(
        amount_paid=0
    ).order_by('-payment_date')
    
    # Calculate monthly breakdown
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth
    
    monthly_payments = Subscription.objects.filter(
        organization=center,
        payment_date__isnull=False
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    ).order_by('-month')[:12]
    
    context = {
        'center': center,
        'analytics': analytics,
        'payment_history': payment_history,
        'monthly_payments': monthly_payments,
    }
    
    return render(request, 'billing/subscription_analytics.html', context)


@login_required
def centers_monitoring(request):
    """Monitor all centers' subscription status - Superuser only"""
    if not request.user.is_superuser:
        messages.error(request, _("Access denied. This feature is only available to superusers."))
        return redirect('dashboard')
    
    # Get sorting parameters
    sort_by = request.GET.get('sort', 'payments')  # payments, age, subscriptions
    search_query = request.GET.get('search', '')
    
    # Get all centers analytics
    centers_data = SubscriptionAnalytics.get_all_centers_analytics()
    
    # Apply search filter
    if search_query:
        centers_data = [
            item for item in centers_data 
            if search_query.lower() in item['center'].name.lower() or 
               search_query.lower() in item['center'].subdomain.lower()
        ]
    
    # Apply sorting
    if sort_by == 'age':
        centers_data.sort(key=lambda x: x['account_age_days'], reverse=True)
    elif sort_by == 'subscriptions':
        centers_data.sort(key=lambda x: x['total_subscriptions'], reverse=True)
    elif sort_by == 'name':
        centers_data.sort(key=lambda x: x['center'].name)
    # Default is already sorted by total_payments
    
    # Calculate totals
    total_revenue = sum(item['total_payments'] for item in centers_data)
    total_centers = len(centers_data)
    active_centers = sum(1 for item in centers_data if item['current_subscription'] and item['current_subscription'].is_active())
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(centers_data, 25)
    page_number = request.GET.get('page')
    centers_page = paginator.get_page(page_number)
    
    context = {
        'title': _('Centers Subscription Monitoring'),
        'subTitle': _('Monitoring'),
        'centers_data': centers_page,
        'sort_by': sort_by,
        'search_query': search_query,
        'total_revenue': total_revenue,
        'total_centers': total_centers,
        'active_centers': active_centers,
    }
    
    return render(request, 'billing/centers_monitoring.html', context)


@login_required
def request_renewal(request):
    """Request subscription renewal - Regular user view"""
    if not hasattr(request.user, 'admin_profile') or not request.user.admin_profile:
        messages.error(request, _("You don't have an admin profile associated with your account."))
        return redirect('dashboard')
    
    center = request.user.admin_profile.center
    
    # Check if center has subscription
    if not center or not hasattr(center, 'subscription'):
        messages.error(request, _("Your center doesn't have an active subscription."))
        return redirect('dashboard')
    
    subscription = center.subscription
    
    if request.method == 'POST':
        # Handle renewal request submission
        tariff_id = request.POST.get('tariff')
        pricing_id = request.POST.get('pricing')
        message = request.POST.get('message', '')
        
        try:
            if not tariff_id or not pricing_id:
                messages.error(request, _("Please select both tariff and pricing option."))
                tariffs = Tariff.objects.filter(is_active=True, is_trial=False).prefetch_related('pricing')
                return render(request, 'billing/request_renewal.html', {'subscription': subscription, 'tariffs': tariffs})
            
            tariff = Tariff.objects.get(pk=tariff_id, is_active=True)
            pricing = TariffPricing.objects.get(pk=pricing_id, tariff=tariff)
            
            # Create note for admins
            renewal_request_note = f"""
Renewal Request from {org.name}
User: {request.user.get_full_name()} ({request.user.email})
Current Subscription: {subscription.tariff.title} (ends {subscription.end_date})
Requested Tariff: {tariff.title}
Requested Duration: {pricing.duration_months} months
Requested Price: {pricing.price:,} {pricing.currency}
User Message: {message}
Request Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """.strip()
            
            # Log the request in subscription history
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='renewal_requested',
                description=renewal_request_note,
                performed_by=request.user
            )
            
            # Send success message
            messages.success(
                request, 
                _("Your renewal request has been submitted successfully! Our team will contact you shortly to process the payment.")
            )
            
            # TODO: Send email/telegram notification to admins
            
            return redirect('billing:request_renewal')
            
        except Exception as e:
            messages.error(request, f"Error submitting renewal request: {str(e)}")
    
    # Get available tariffs for selection
    tariffs = Tariff.objects.filter(is_active=True, is_trial=False).prefetch_related('pricing')
    
    # Get current usage stats
    current_usage = {
        'branches': org.branches.count(),
        'staff': org.get_staff_count(),
        'orders': org.get_current_month_orders_count(),
    }
    
    context = {
        'title': _('Renew Subscription'),
        'subTitle': _('Billing'),
        'subscription': subscription,
        'tariffs': tariffs,
        'current_usage': current_usage,
    }
    
    return render(request, 'billing/request_renewal.html', context)

