from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class Feature(models.Model):
    """Individual features that can be included in tariffs"""
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Feature Code"))
    name = models.CharField(max_length=200, verbose_name=_("Feature Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    category = models.CharField(max_length=50, blank=True, verbose_name=_("Category"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Feature")
        verbose_name_plural = _("Features")
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Tariff(models.Model):
    """Tariff plan template/definition"""
    title = models.CharField(max_length=200, verbose_name=_("Tariff Title"))
    slug = models.SlugField(unique=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured"))
    display_order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    
    # Limits
    max_branches = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name=_("Max Branches"),
        help_text=_("Leave empty for unlimited")
    )
    max_staff = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name=_("Max Staff"),
        help_text=_("Leave empty for unlimited")
    )
    max_monthly_orders = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name=_("Max Monthly Orders"),
        help_text=_("Leave empty for unlimited")
    )
    
    # Features
    features = models.ManyToManyField(Feature, blank=True, verbose_name=_("Features"))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Tariff")
        verbose_name_plural = _("Tariffs")
        ordering = ['display_order', 'title']
    
    def __str__(self):
        return self.title
    
    def has_feature(self, feature_code):
        """Check if tariff includes a specific feature"""
        return self.features.filter(code=feature_code, is_active=True).exists()
    
    def get_pricing_options(self):
        """Get all pricing options for this tariff"""
        return self.pricing.filter(is_active=True).order_by('duration_months')


class TariffPricing(models.Model):
    """Pricing for different subscription periods"""
    DURATION_CHOICES = [
        (1, _("1 Month")),
        (3, _("3 Months")),
        (6, _("6 Months")),
        (12, _("1 Year")),
    ]
    
    CURRENCY_CHOICES = [
        ('UZS', _("Uzbek Sum")),
        ('USD', _("US Dollar")),
        ('RUB', _("Russian Ruble")),
    ]
    
    tariff = models.ForeignKey(
        Tariff, 
        on_delete=models.CASCADE, 
        related_name='pricing',
        verbose_name=_("Tariff")
    )
    duration_months = models.IntegerField(
        choices=DURATION_CHOICES,
        verbose_name=_("Duration (Months)")
    )
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Price")
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='UZS',
        verbose_name=_("Currency")
    )
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Discount %"),
        help_text=_("Discount compared to monthly pricing")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Tariff Pricing")
        verbose_name_plural = _("Tariff Pricings")
        unique_together = ['tariff', 'duration_months', 'currency']
        ordering = ['tariff', 'duration_months']
    
    def __str__(self):
        return f"{self.tariff.title} - {self.duration_months} month(s) - {self.price} {self.currency}"
    
    def get_monthly_price(self):
        """Calculate effective monthly price"""
        return self.price / self.duration_months
    
    def get_savings(self):
        """Calculate savings compared to monthly plan"""
        if self.duration_months == 1:
            return 0
        
        monthly_pricing = TariffPricing.objects.filter(
            tariff=self.tariff,
            duration_months=1,
            currency=self.currency,
            is_active=True
        ).first()
        
        if monthly_pricing:
            total_monthly_cost = monthly_pricing.price * self.duration_months
            return total_monthly_cost - self.price
        return 0


class Subscription(models.Model):
    """Organization's subscription to a tariff"""
    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PENDING = 'pending'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, _("Active")),
        (STATUS_EXPIRED, _("Expired")),
        (STATUS_CANCELLED, _("Cancelled")),
        (STATUS_PENDING, _("Pending Payment")),
    ]
    
    organization = models.OneToOneField(
        'organizations.TranslationCenter',
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_("Organization")
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_("Tariff")
    )
    pricing = models.ForeignKey(
        TariffPricing,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_("Pricing Plan")
    )
    
    # Subscription Period
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_("Status")
    )
    auto_renew = models.BooleanField(default=True, verbose_name=_("Auto Renew"))
    
    # Payment tracking
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Amount Paid")
    )
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Payment Date"))
    payment_method = models.CharField(max_length=50, blank=True, verbose_name=_("Payment Method"))
    transaction_id = models.CharField(max_length=200, blank=True, verbose_name=_("Transaction ID"))
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_subscriptions',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['end_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.tariff.title} ({self.start_date} - {self.end_date})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate end_date based on pricing duration
        if not self.end_date and self.start_date and self.pricing:
            self.end_date = self.start_date + relativedelta(months=self.pricing.duration_months)
        
        # Auto-update status based on dates
        if self.status != self.STATUS_CANCELLED:
            today = date.today()
            if self.end_date < today:
                self.status = self.STATUS_EXPIRED
            elif self.start_date <= today <= self.end_date:
                if self.status == self.STATUS_PENDING and self.payment_date:
                    self.status = self.STATUS_ACTIVE
        
        super().save(*args, **kwargs)
    
    def is_active(self):
        """Check if subscription is currently active"""
        today = date.today()
        return (
            self.status == self.STATUS_ACTIVE and
            self.start_date <= today <= self.end_date
        )
    
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if not self.is_active():
            return 0
        return (self.end_date - date.today()).days
    
    def get_usage_percentage(self, usage_type='orders'):
        """Get current usage percentage for orders/staff/branches"""
        if usage_type == 'orders':
            limit = self.tariff.max_monthly_orders
            if limit is None:
                return 0  # Unlimited
            
            current_usage = self.organization.get_current_month_orders_count()
            return (current_usage / limit * 100) if limit > 0 else 0
        
        elif usage_type == 'branches':
            limit = self.tariff.max_branches
            if limit is None:
                return 0
            
            current_usage = self.organization.branches.count()
            return (current_usage / limit * 100) if limit > 0 else 0
        
        elif usage_type == 'staff':
            limit = self.tariff.max_staff
            if limit is None:
                return 0
            
            from accounts.models import User
            current_usage = User.objects.filter(organization=self.organization).count()
            return (current_usage / limit * 100) if limit > 0 else 0
        
        return 0
    
    def can_add_branch(self):
        """Check if organization can add more branches"""
        if not self.is_active():
            return False
        
        limit = self.tariff.max_branches
        if limit is None:  # Unlimited
            return True
        
        current_count = self.organization.branches.count()
        return current_count < limit
    
    def can_add_staff(self):
        """Check if organization can add more staff"""
        if not self.is_active():
            return False
        
        limit = self.tariff.max_staff
        if limit is None:
            return True
        
        from accounts.models import User
        current_count = User.objects.filter(organization=self.organization).count()
        return current_count < limit
    
    def can_create_order(self):
        """Check if organization can create more orders this month"""
        if not self.is_active():
            return False
        
        limit = self.tariff.max_monthly_orders
        if limit is None:
            return True
        
        current_count = self.organization.get_current_month_orders_count()
        return current_count < limit    
    def get_usage_percentage(self, resource_type):
        """Get usage percentage for a specific resource (branches, staff, orders)."""
        if resource_type == 'branches':
            current = self.organization.branches.count()
            limit = self.tariff.max_branches
        elif resource_type == 'staff':
            current = self.organization.get_staff_count()
            limit = self.tariff.max_staff
        elif resource_type == 'orders':
            current = self.organization.get_current_month_orders_count()
            limit = self.tariff.max_monthly_orders
        else:
            return 0
        
        if limit is None or limit == 0:
            return 0
        
        return int((current / limit) * 100)    
    def renew(self, new_pricing=None):
        """Create a new subscription for renewal"""
        if new_pricing is None:
            new_pricing = self.pricing
        
        new_subscription = Subscription.objects.create(
            organization=self.organization,
            tariff=new_pricing.tariff,
            pricing=new_pricing,
            start_date=self.end_date + timedelta(days=1),
            status=self.STATUS_PENDING,
            auto_renew=self.auto_renew,
        )
        
        return new_subscription


class UsageTracking(models.Model):
    """Track monthly usage statistics"""
    organization = models.ForeignKey(
        'organizations.TranslationCenter',
        on_delete=models.CASCADE,
        related_name='usage_tracking',
        verbose_name=_("Organization")
    )
    year = models.IntegerField(verbose_name=_("Year"))
    month = models.IntegerField(verbose_name=_("Month"))
    
    # Usage counters
    orders_created = models.IntegerField(default=0, verbose_name=_("Orders Created"))
    branches_count = models.IntegerField(default=0, verbose_name=_("Branches Count"))
    staff_count = models.IntegerField(default=0, verbose_name=_("Staff Count"))
    
    # Additional metrics
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total Revenue")
    )
    bot_orders = models.IntegerField(default=0, verbose_name=_("Bot Orders"))
    manual_orders = models.IntegerField(default=0, verbose_name=_("Manual Orders"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Usage Tracking")
        verbose_name_plural = _("Usage Tracking")
        unique_together = ['organization', 'year', 'month']
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['organization', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.year}/{self.month}"
    
    @classmethod
    def get_or_create_current_month(cls, organization):
        """Get or create usage tracking for current month"""
        today = date.today()
        tracking, created = cls.objects.get_or_create(
            organization=organization,
            year=today.year,
            month=today.month,
            defaults={
                'branches_count': organization.branches.count(),
                'staff_count': organization.get_staff_count(),
            }
        )
        return tracking
    
    def increment_orders(self, is_bot_order=False):
        """Increment order counter"""
        self.orders_created += 1
        if is_bot_order:
            self.bot_orders += 1
        else:
            self.manual_orders += 1
        self.save()


class SubscriptionHistory(models.Model):
    """Historical record of subscription changes"""
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_("Subscription")
    )
    action = models.CharField(max_length=50, verbose_name=_("Action"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Performed By")
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Subscription History")
        verbose_name_plural = _("Subscription History")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.subscription.organization.name} - {self.action} - {self.timestamp}"
