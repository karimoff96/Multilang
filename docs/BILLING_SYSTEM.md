# Comprehensive Billing & Tariff System

## Overview

This is an advanced, flexible billing system designed for long-term scalability. It supports:
- Multiple tariff plans with customizable features
- Flexible pricing (monthly, quarterly, semi-annual, annual)
- Subscription period tracking with start/end dates
- Usage monitoring and limits enforcement
- Feature-based access control
- Automatic pricing discounts for longer periods

---

## Database Structure

### 1. **Feature Model**
Individual features that can be included in tariffs.

**Fields:**
- `code`: Unique identifier (e.g., 'advanced_analytics')
- `name`: Display name
- `description`: Feature description
- `category`: Feature category for grouping
- `is_active`: Enable/disable feature

**Purpose:** Modular feature management - add/remove features from tariffs without code changes.

---

### 2. **Tariff Model**
Tariff plan template/definition.

**Fields:**
- `title`: Plan name (adjustable, e.g., "Starter", "Professional")
- `slug`: URL-friendly identifier
- `description`: Plan description
- `is_active`: Enable/disable tariff
- `is_featured`: Mark as "Popular" or "Recommended"
- `display_order`: Control display order on pricing page
- **Limits:**
  - `max_branches`: Branch limit (NULL = unlimited)
  - `max_staff`: Staff limit (NULL = unlimited)
  - `max_monthly_orders`: Monthly order limit (NULL = unlimited)
- `features`: ManyToMany relationship with Feature model

**Methods:**
- `has_feature(feature_code)`: Check if tariff includes specific feature
- `get_pricing_options()`: Get all pricing options

---

### 3. **TariffPricing Model**
Pricing for different subscription periods.

**Fields:**
- `tariff`: Foreign key to Tariff
- `duration_months`: 1, 3, 6, or 12 months
- `price`: Price amount
- `currency`: UZS, USD, RUB
- `discount_percentage`: Discount compared to monthly pricing
- `is_active`: Enable/disable pricing option

**Methods:**
- `get_monthly_price()`: Calculate effective monthly price
- `get_savings()`: Calculate savings vs monthly plan

**Example:**
```python
# Starter - 1 month: 299,000 UZS (no discount)
# Starter - 3 months: 807,300 UZS (10% discount)
# Starter - 6 months: 1,553,400 UZS (13% discount)
# Starter - 12 months: 2,990,000 UZS (17% discount)
```

---

### 4. **Subscription Model**
Organization's active subscription to a tariff.

**Fields:**
- `organization`: OneToOne with TranslationCenter
- `tariff`: Current tariff plan
- `pricing`: Selected pricing option
- **Period:**
  - `start_date`: Subscription start date
  - `end_date`: Subscription end date (auto-calculated)
- **Status:**
  - `status`: active, expired, cancelled, pending
  - `auto_renew`: Auto-renew on expiration
- **Payment:**
  - `amount_paid`: Actual amount paid
  - `payment_date`: When payment was received
  - `payment_method`: Payment method used
  - `transaction_id`: Payment gateway transaction ID
- `notes`: Admin notes
- `created_by`: Who created the subscription

**Methods:**
- `is_active()`: Check if subscription is currently active
- `days_remaining()`: Calculate days until expiration
- `can_add_branch()`: Check branch limit
- `can_add_staff()`: Check staff limit
- `can_create_order()`: Check monthly order limit
- `renew()`: Create renewal subscription

**Automatic Behavior:**
- `end_date` auto-calculated from `start_date` + `pricing.duration_months`
- Status auto-updated based on dates
- Payment status tracked

---

### 5. **UsageTracking Model**
Track monthly usage statistics.

**Fields:**
- `organization`: Foreign key to center
- `year`, `month`: Usage period
- **Counters:**
  - `orders_created`: Total orders
  - `bot_orders`: Orders from bot
  - `manual_orders`: Orders from dashboard
  - `branches_count`: Snapshot of branch count
  - `staff_count`: Snapshot of staff count
  - `total_revenue`: Revenue for the month

**Methods:**
- `get_or_create_current_month()`: Get/create tracking for current month
- `increment_orders()`: Increment order counter

**Purpose:** Historical usage tracking and analytics.

---

### 6. **SubscriptionHistory Model**
Audit log of subscription changes.

**Fields:**
- `subscription`: Related subscription
- `action`: Type of action (created, renewed, cancelled, etc.)
- `description`: Details of the change
- `performed_by`: User who made the change
- `timestamp`: When the change occurred

**Purpose:** Audit trail and compliance.

---

## Tariff Plans

### **Starter - 299,000 UZS/month**
**Target:** Small translation centers (1-3 people)
- 1 Translation Center
- 1 Branch
- 3 Staff Members
- 150 Orders/month
- ✓ Telegram Bot
- ✓ Basic Reports
- ✓ Excel Export
- ✗ Advanced Analytics
- ✗ Marketing Tools

### **Professional - 499,000 UZS/month** (POPULAR)
**Target:** Growing centers (3-10 people)
- 1 Translation Center
- 3 Branches
- 10 Staff Members
- 500 Orders/month
- ✓ All Starter features
- ✓ Advanced Analytics
- ✓ Marketing Tools
- ✓ Auto Archiving
- ✓ Staff Performance Tracking

### **Enterprise - 1,999,000 UZS/month**
**Target:** Large multi-branch operations
- Unlimited Centers
- Unlimited Branches
- Unlimited Staff
- Unlimited Orders
- ✓ All Professional features
- ✓ API Access
- ✓ 24/7 Technical Support
- ✓ Dedicated Account Manager

---

## Pricing Periods & Discounts

All plans offer these duration options:
- **1 Month**: No discount (base price)
- **3 Months**: 10% discount
- **6 Months**: 13% discount
- **12 Months**: 17% discount

Example for Starter (299,000 UZS/month):
- 1 month: 299,000 UZS
- 3 months: 807,300 UZS (saves 89,700 UZS)
- 6 months: 1,553,400 UZS (saves 240,600 UZS)
- 12 months: 2,990,000 UZS (saves 598,000 UZS)

---

## Implementation Guide

### Step 1: Create Migrations

```bash
python manage.py makemigrations billing
python manage.py migrate billing
```

### Step 2: Seed Initial Data

```bash
python manage.py seed_tariffs
```

This creates:
- 13 features
- 3 tariff plans
- 12 pricing options (4 per tariff)

### Step 3: Apply Decorators to Views

```python
# organizations/views.py
from billing.decorators import check_branch_limit

@login_required
@check_branch_limit
def branchCreate(request):
    # Branch creation logic
    pass

# accounts/views.py
from billing.decorators import check_staff_limit

@login_required
@check_staff_limit
def userCreate(request):
    # User creation logic
    pass

# orders/views.py
from billing.decorators import check_order_limit

@login_required
@check_order_limit
def orderCreate(request):
    org = request.user.organization
    
    # Order creation logic...
    
    # Track usage
    from billing.models import UsageTracking
    tracking = UsageTracking.get_or_create_current_month(org)
    tracking.increment_orders(is_bot_order=False)
    
    pass
```

### Step 4: Feature-Based Access Control

```python
# marketing/views.py
from billing.decorators import require_feature

@login_required
@require_feature('marketing_tools')
def broadcast_campaign_create(request):
    # Marketing logic
    pass

# WowDash/reports_views.py
@login_required
@require_feature('advanced_analytics')
def advanced_analytics_view(request):
    # Analytics logic
    pass
```

### Step 5: Template Restrictions

```django
<!-- templates/partials/sidebar.html -->
{% if user.organization.subscription.tariff.has_feature 'marketing_tools' %}
<li class="sidebar-menu-item">
    <a href="{% url 'marketing:campaign_list' %}">
        {% trans "Marketing" %}
    </a>
</li>
{% endif %}

<!-- templates/organizations/branch_list.html -->
{% if user.organization.subscription.can_add_branch %}
    <a href="{% url 'organizations:branch_create' %}" class="btn btn-primary">
        {% trans "Add Branch" %}
    </a>
{% else %}
    <button class="btn btn-secondary" disabled>
        {% trans "Add Branch" %} ({% trans "Limit Reached - Upgrade Plan" %})
    </button>
{% endif %}
```

---

## Admin Interface

### Superuser Tasks:

**1. Create Subscription for New Center:**
```
Admin Panel → Subscriptions → Add Subscription
- Select organization
- Select tariff
- Select pricing (duration)
- Set start date
- Mark as "Pending" initially
- After payment received:
  - Set amount_paid
  - Set payment_date
  - Change status to "Active"
```

**2. Monitor Usage:**
```
Admin Panel → Usage Tracking
- View monthly statistics per organization
- Track orders (bot vs manual)
- Monitor revenue
```

**3. Manage Tariffs:**
```
Admin Panel → Tariffs
- Edit tariff limits
- Enable/disable features
- Adjust pricing
- Create new tariffs
```

**4. Handle Renewals:**
```
Admin Panel → Subscriptions
- Filter by "end_date" approaching
- Create new subscription for renewal
- Or let auto_renew handle it
```

---

## Usage Examples

### Check Subscription Status
```python
center = TranslationCenter.objects.get(subdomain='mycenter')

# Check if has active subscription
if center.has_active_subscription():
    status = center.get_subscription_status()
    print(f"Tariff: {status['tariff']}")
    print(f"Days remaining: {status['days_remaining']}")
else:
    print("No active subscription")
```

### Check Limits
```python
subscription = center.subscription

# Check if can add branch
if subscription.can_add_branch():
    Branch.objects.create(center=center, name="New Branch")
else:
    print("Branch limit reached")

# Check usage percentage
orders_usage = subscription.get_usage_percentage('orders')
print(f"Used {orders_usage}% of monthly order limit")
```

### Track Usage
```python
from billing.models import UsageTracking

# Increment order count
tracking = UsageTracking.get_or_create_current_month(center)
tracking.increment_orders(is_bot_order=True)
```

---

## Future Enhancements

1. **Payment Gateway Integration:**
   - Click, Payme, PayPal
   - Automatic payment processing
   - Invoice generation

2. **Billing Dashboard:**
   - Usage charts and graphs
   - Upgrade/downgrade flows
   - Invoice history

3. **Email Notifications:**
   - Subscription expiring (7 days before)
   - Subscription expired
   - Limit warnings (80% usage)
   - Payment receipts

4. **Promo Codes:**
   - Discount codes
   - Trial periods
   - Referral bonuses

5. **Custom Tariffs:**
   - Create custom tariffs for specific clients
   - Negotiated pricing
   - Special features

---

## Benefits of This Design

✅ **Flexible:** Easy to add new tariffs, features, or pricing tiers
✅ **Scalable:** Supports growth from 1 to 1000+ organizations
✅ **Transparent:** Clear usage tracking and limits
✅ **Professional:** Proper billing with audit trails
✅ **Maintainable:** Clean separation of concerns
✅ **Future-Proof:** Designed with long-term growth in mind

---

## Migration Path for Existing Centers

1. Create "Free Trial" tariff (30 days)
2. Assign all existing centers to Free Trial
3. Before expiration, contact centers for subscription
4. Convert to paid subscription

```bash
python manage.py shell

from organizations.models import TranslationCenter
from billing.models import Tariff, TariffPricing, Subscription
from datetime import date, timedelta

# Get starter tariff
starter = Tariff.objects.get(slug='starter')
starter_monthly = TariffPricing.objects.get(tariff=starter, duration_months=1)

# Assign to all centers
for center in TranslationCenter.objects.all():
    if not hasattr(center, 'subscription'):
        Subscription.objects.create(
            organization=center,
            tariff=starter,
            pricing=starter_monthly,
            start_date=date.today(),
            status='active',
            notes='Migrated from legacy system'
        )
        print(f"Created subscription for {center.name}")
```

---

This billing system provides a solid foundation for your SaaS business with room for growth and customization!
