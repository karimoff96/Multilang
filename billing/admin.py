from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Feature, Tariff, TariffPricing, Subscription, UsageTracking, SubscriptionHistory


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'is_active', 'tariff_count']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['category', 'name']
    
    def tariff_count(self, obj):
        """Show how many tariffs use this feature"""
        count = obj.tariff_set.count()
        if count > 0:
            return format_html(
                '<span style="color: blue;">{} tariff(s)</span>',
                count
            )
        return format_html('<span style="color: gray;">Not used</span>')
    tariff_count.short_description = _('Used in Tariffs')


class TariffPricingInline(admin.TabularInline):
    model = TariffPricing
    extra = 1
    fields = ['duration_months', 'price', 'currency', 'discount_percentage', 'is_active']


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_trial', 'trial_days', 'is_active', 'is_featured', 'feature_count_display', 'limits_summary', 'display_order']
    list_filter = ['is_active', 'is_featured', 'is_trial']
    search_fields = ['title', 'slug', 'description']
    filter_horizontal = ['features']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'slug', 'description', 'is_active', 'is_featured', 'display_order')
        }),
        (_('Trial Settings'), {
            'fields': ('is_trial', 'trial_days'),
            'description': _('Configure free trial period for this tariff')
        }),
        (_('Limits'), {
            'fields': ('max_branches', 'max_staff', 'max_monthly_orders'),
            'description': _('Set usage limits (leave empty for unlimited)')
        }),
        (_('📊 Order Management Features (5)'), {
            'fields': (
                'feature_orders_basic',
                'feature_orders_advanced',
                'feature_order_assignment',
                'feature_bulk_payments',
                'feature_order_templates',
            ),
            'classes': ('collapse',),
            'description': _('Features for creating and managing customer orders')
        }),
        (_('📈 Analytics & Reports Features (6)'), {
            'fields': (
                'feature_analytics_basic',
                'feature_analytics_advanced',
                'feature_financial_reports',
                'feature_staff_performance',
                'feature_custom_reports',
                'feature_export_reports',
            ),
            'classes': ('collapse',),
            'description': _('Analytics dashboards and reporting capabilities')
        }),
        (_('🔗 Integration Features (4)'), {
            'fields': (
                'feature_telegram_bot',
                'feature_webhooks',
                'feature_api_access',
                'feature_integrations',
            ),
            'classes': ('collapse',),
            'description': _('External integrations and API access (some on request)')
        }),
        (_('📢 Marketing Features (2)'), {
            'fields': (
                'feature_marketing_basic',
                'feature_broadcast_messages',
            ),
            'classes': ('collapse',),
            'description': _('Marketing campaigns and broadcast messaging')
        }),
        (_('🏢 Organization & Staff Features (4)'), {
            'fields': (
                'feature_multi_branch',
                'feature_custom_roles',
                'feature_staff_scheduling',
                'feature_branch_settings',
            ),
            'classes': ('collapse',),
            'description': _('Multi-branch management and staff coordination')
        }),
        (_('📦 Storage & Archive Features (3)'), {
            'fields': (
                'feature_archive_access',
                'feature_cloud_backup',
                'feature_extended_storage',
            ),
            'classes': ('collapse',),
            'description': _('File archiving and cloud storage')
        }),
        (_('💰 Financial Management Features (4)'), {
            'fields': (
                'feature_payment_management',
                'feature_multi_currency',
                'feature_invoicing',
                'feature_expense_tracking',
            ),
            'classes': ('collapse',),
            'description': _('Payment processing and financial tracking')
        }),
        (_('🎯 Support & Services Features (2)'), {
            'fields': (
                'feature_support_tickets',
                'feature_knowledge_base',
            ),
            'classes': ('collapse',),
            'description': _('Customer support tools')
        }),
        (_('⚡ Advanced Features (3)'), {
            'fields': (
                'feature_advanced_security',
                'feature_audit_logs',
                'feature_data_retention',
            ),
            'classes': ('collapse',),
            'description': _('Security, compliance, and audit features')
        }),
        (_('🛠️ Services Management Features (4)'), {
            'fields': (
                'feature_products_basic',
                'feature_products_advanced',
                'feature_language_pricing',
                'feature_dynamic_pricing',
            ),
            'classes': ('collapse',),
            'description': _('Product and pricing management')
        }),
        (_('Legacy Features (M2M - Deprecated)'), {
            'fields': ('features',),
            'classes': ('collapse',),
            'description': _('Old M2M feature relationship - will be removed')
        }),
    )
    
    # Temporarily commented out to allow migrations
    # inlines = [TariffPricingInline]
    
    def limits_summary(self, obj):
        return f"Branches: {obj.max_branches or '∞'} | Staff: {obj.max_staff or '∞'} | Orders: {obj.max_monthly_orders or '∞'}"
    limits_summary.short_description = _('Limits')
    
    def feature_count_display(self, obj):
        count = obj.get_feature_count()
        return f"{count}/37 features"
    feature_count_display.short_description = _('Features Enabled')


@admin.register(TariffPricing)
class TariffPricingAdmin(admin.ModelAdmin):
    list_display = ['tariff', 'duration_months', 'price', 'currency', 'discount_percentage', 'monthly_price_display', 'is_active']
    list_filter = ['tariff', 'duration_months', 'currency', 'is_active']
    search_fields = ['tariff__title']
    
    def monthly_price_display(self, obj):
        monthly = obj.get_monthly_price()
        return f"{monthly:.2f} {obj.currency}/month"
    monthly_price_display.short_description = _('Monthly Price')


class SubscriptionHistoryInline(admin.TabularInline):
    model = SubscriptionHistory
    extra = 0
    readonly_fields = ['action', 'description', 'performed_by', 'timestamp']
    can_delete = False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 
        'tariff', 
        'status_badge',
        'start_date', 
        'end_date', 
        'days_left',
        'payment_status',
        'auto_renew'
    ]
    list_filter = ['status', 'tariff', 'auto_renew', 'start_date', 'end_date']
    search_fields = ['organization__name', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Organization'), {
            'fields': ('organization',)
        }),
        (_('Tariff Details'), {
            'fields': ('tariff', 'pricing')
        }),
        (_('Subscription Period'), {
            'fields': ('start_date', 'end_date', 'status', 'auto_renew')
        }),
        (_('Trial Period'), {
            'fields': ('is_trial', 'trial_end_date'),
            'description': _('Trial subscription information')
        }),
        (_('Payment Information'), {
            'fields': ('amount_paid', 'payment_date', 'payment_method', 'transaction_id')
        }),
        (_('Additional Info'), {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Temporarily commented out to allow migrations
    # inlines = [SubscriptionHistoryInline]
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'expired': 'red',
            'cancelled': 'gray',
            'pending': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def days_left(self, obj):
        if obj.is_active():
            days = obj.days_remaining()
            if days <= 7:
                return format_html('<span style="color: red; font-weight: bold;">{} days</span>', days)
            return f"{days} days"
        return '-'
    days_left.short_description = _('Days Left')
    
    def payment_status(self, obj):
        if obj.payment_date:
            return format_html('<span style="color: green;">✓ Paid</span>')
        return format_html('<span style="color: red;">✗ Unpaid</span>')
    payment_status.short_description = _('Payment')
    
    actions = ['activate_subscriptions', 'cancel_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(status=Subscription.STATUS_ACTIVE)
        self.message_user(request, f'{updated} subscription(s) activated.')
    activate_subscriptions.short_description = _('Activate selected subscriptions')
    
    def cancel_subscriptions(self, request, queryset):
        updated = queryset.update(status=Subscription.STATUS_CANCELLED)
        self.message_user(request, f'{updated} subscription(s) cancelled.')
    cancel_subscriptions.short_description = _('Cancel selected subscriptions')


@admin.register(UsageTracking)
class UsageTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'organization',
        'year_month',
        'orders_created',
        'bot_orders',
        'manual_orders',
        'branches_count',
        'staff_count',
        'total_revenue'
    ]
    list_filter = ['year', 'month', 'organization']
    search_fields = ['organization__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def year_month(self, obj):
        return f"{obj.year}-{obj.month:02d}"
    year_month.short_description = _('Period')


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['subscription__organization__name', 'description']
    readonly_fields = ['subscription', 'action', 'description', 'performed_by', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow superusers to delete (enables cascade delete from Subscription)
        return request.user.is_superuser
