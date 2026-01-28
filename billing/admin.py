from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Feature, Tariff, TariffPricing, Subscription, UsageTracking, SubscriptionHistory


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['category', 'name']


class TariffPricingInline(admin.TabularInline):
    model = TariffPricing
    extra = 1
    fields = ['duration_months', 'price', 'currency', 'discount_percentage', 'is_active']


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_trial', 'trial_days', 'is_active', 'is_featured', 'limits_summary', 'display_order']
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
            'fields': ('max_branches', 'max_staff', 'max_monthly_orders')
        }),
        (_('Features'), {
            'fields': ('features',)
        }),
    )
    
    # Temporarily commented out to allow migrations
    # inlines = [TariffPricingInline]
    
    def limits_summary(self, obj):
        return f"Branches: {obj.max_branches or '∞'} | Staff: {obj.max_staff or '∞'} | Orders: {obj.max_monthly_orders or '∞'}"
    limits_summary.short_description = _('Limits')


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
        return False
