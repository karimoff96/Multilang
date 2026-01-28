# Feature-Based Access Control System

## Overview

This system implements **feature-based permissions** that are decoupled from specific tariff plans. This allows for flexible tariff configurations where any tariff can include any combination of features.

### Key Benefits

✅ **Scalable**: Add new features without modifying code  
✅ **Flexible**: Create custom tariff combinations easily  
✅ **Future-proof**: New tariffs can mix and match existing features  
✅ **UI Integration**: Automatically hides inaccessible menu items  
✅ **View Protection**: Decorators block access at the view level  

---

## Quick Start

### 1. Create Standard Features

Run the management command to create predefined features:

```bash
python manage.py create_features
```

This creates 21 standard features across categories:
- Analytics & Reports (7 features)
- Marketing (2 features)
- Integration (2 features)
- Support (2 features)
- Security & Audit (2 features)
- Customization (2 features)
- Payment (2 features)
- Export (2 features)

### 2. Assign Features to Tariffs

**Option A: Django Admin**
1. Go to Admin → Billing → Tariffs
2. Edit a tariff
3. Select features from the many-to-many field

**Option B: Python Shell**
```python
from billing.models import Tariff, Feature

# Get tariff
starter = Tariff.objects.get(slug='starter')

# Get features
financial_reports = Feature.objects.get(code='FINANCIAL_REPORTS')
basic_analytics = Feature.objects.get(code='ADVANCED_ANALYTICS')

# Assign features
starter.features.add(financial_reports, basic_analytics)

# Or use set() to replace all
starter.features.set([financial_reports, basic_analytics])
```

### 3. Use in Templates

Load the templatetag library:
```django
{% load billing_tags %}
```

**Check if user has a feature:**
```django
{% has_feature 'FINANCIAL_REPORTS' as has_financial %}
{% if has_financial %}
    <a href="{% url 'financial_reports' %}">Financial Reports</a>
{% else %}
    <span class="text-muted">Upgrade to access Financial Reports</span>
{% endif %}
```

**Check multiple features:**
```django
{% has_feature 'ADVANCED_ANALYTICS' as has_analytics %}
{% has_feature 'FINANCIAL_REPORTS' as has_financial %}

{% if has_analytics and has_financial %}
    <!-- Show advanced dashboard -->
{% elif has_analytics %}
    <!-- Show basic analytics -->
{% else %}
    <!-- Show upgrade prompt -->
{% endif %}
```

### 4. Protect Views with Decorators

**Require active subscription:**
```python
from billing.decorators import require_active_subscription

@require_active_subscription
def my_view(request):
    # Only accessible with active subscription
    return render(request, 'my_template.html')
```

**Require specific feature:**
```python
from billing.decorators import require_feature

@require_feature('FINANCIAL_REPORTS')
def financial_reports_view(request):
    # Only accessible if user's tariff includes FINANCIAL_REPORTS
    return render(request, 'reports/financial.html')
```

**Check resource limits:**
```python
from billing.decorators import check_branch_limit

@check_branch_limit
def branch_create(request):
    # Only accessible if user hasn't reached branch limit
    # ...
```

---

## Feature Categories & Codes

### Analytics & Reports
- `ADVANCED_ANALYTICS` - Advanced analytics dashboards
- `FINANCIAL_REPORTS` - Detailed financial reports
- `STAFF_PERFORMANCE` - Staff performance tracking
- `BRANCH_COMPARISON` - Multi-branch comparison
- `CUSTOMER_ANALYTICS` - Customer behavior analysis
- `EXPENSE_ANALYTICS` - Expense tracking and analysis
- `UNIT_ECONOMY` - Unit economics reports

### Marketing
- `MARKETING_BROADCASTS` - Broadcast messaging
- `ADVANCED_MARKETING` - Advanced marketing automation

### Integration
- `API_ACCESS` - REST API access
- `WEBHOOK_INTEGRATION` - Webhook notifications

### Support
- `PRIORITY_SUPPORT` - 24/7 priority support
- `DEDICATED_MANAGER` - Dedicated account manager

### Security & Audit
- `AUDIT_LOGS` - Detailed audit logging
- `ADVANCED_SECURITY` - Enhanced security features

### Customization
- `CUSTOM_BRANDING` - Custom logo and branding
- `WHITE_LABEL` - Complete white-label solution

### Payment
- `BULK_PAYMENTS` - Bulk payment processing
- `PAYMENT_GATEWAY_INTEGRATION` - Payment gateway integration

### Export
- `DATA_EXPORT` - Export to Excel/CSV/PDF
- `AUTOMATED_REPORTS` - Scheduled report generation

---

## Example Tariff Configurations

### Starter Plan
```python
starter = Tariff.objects.create(
    title='Starter',
    slug='starter',
    max_branches=3,
    max_staff=5,
    max_monthly_orders=100,
)

# Basic features only
starter.features.set([
    Feature.objects.get(code='FINANCIAL_REPORTS'),
    Feature.objects.get(code='DATA_EXPORT'),
])
```

### Professional Plan
```python
professional = Tariff.objects.create(
    title='Professional',
    slug='professional',
    max_branches=10,
    max_staff=20,
    max_monthly_orders=500,
)

# Advanced analytics + integrations
professional.features.set([
    Feature.objects.get(code='ADVANCED_ANALYTICS'),
    Feature.objects.get(code='FINANCIAL_REPORTS'),
    Feature.objects.get(code='STAFF_PERFORMANCE'),
    Feature.objects.get(code='EXPENSE_ANALYTICS'),
    Feature.objects.get(code='MARKETING_BROADCASTS'),
    Feature.objects.get(code='API_ACCESS'),
    Feature.objects.get(code='PRIORITY_SUPPORT'),
    Feature.objects.get(code='DATA_EXPORT'),
])
```

### Enterprise Plan
```python
enterprise = Tariff.objects.create(
    title='Enterprise',
    slug='enterprise',
    max_branches=None,  # Unlimited
    max_staff=None,
    max_monthly_orders=None,
)

# All features
enterprise.features.set(Feature.objects.filter(is_active=True))
```

---

## Sidebar Integration

The sidebar automatically hides menu items based on features:

```django
{% load billing_tags %}

<!-- Financial Reports - Requires FINANCIAL_REPORTS feature -->
{% can_do 'reports.financial' as can_financial %}
{% has_feature 'FINANCIAL_REPORTS' as has_financial_feature %}
{% if can_financial and has_financial_feature %}
<li>
    <a href="{% url 'financial_reports' %}">
        <i class="ri-circle-fill"></i>
        <span>{% trans "Financial Reports" %}</span>
    </a>
</li>
{% endif %}

<!-- Staff Performance - Requires STAFF_PERFORMANCE feature -->
{% has_feature 'STAFF_PERFORMANCE' as has_staff_perf %}
{% if can_order_reports and has_staff_perf %}
<li>
    <a href="{% url 'staff_performance' %}">
        <i class="ri-circle-fill"></i>
        <span>{% trans "Staff Performance" %}</span>
    </a>
</li>
{% endif %}
```

---

## Context Variables

Available in all templates via context processor:

```django
{{ has_active_subscription }}  <!-- Boolean -->
{{ user_tariff }}              <!-- Tariff object or None -->
{{ subscription_status }}      <!-- Dict with subscription details -->
```

**subscription_status dict:**
```python
{
    'has_subscription': True,
    'is_active': True,
    'tariff_name': 'Professional',
    'days_remaining': 25,
    'is_trial': False,
    'end_date': datetime.date(2026, 02, 22)
}
```

---

## Adding New Features

### Step 1: Create Feature in Database

```python
from billing.models import Feature

Feature.objects.create(
    code='MY_NEW_FEATURE',
    name='My New Feature',
    description='Description of what this feature does',
    category='analytics',  # or 'marketing', 'integration', etc.
    is_active=True
)
```

### Step 2: Protect Views

```python
from billing.decorators import require_feature

@require_feature('MY_NEW_FEATURE')
def my_new_feature_view(request):
    return render(request, 'my_feature.html')
```

### Step 3: Update Templates

```django
{% has_feature 'MY_NEW_FEATURE' as has_my_feature %}
{% if has_my_feature %}
    <a href="{% url 'my_new_feature' %}">My New Feature</a>
{% endif %}
```

### Step 4: Assign to Tariffs

```python
# Add to specific tariffs
professional = Tariff.objects.get(slug='professional')
my_feature = Feature.objects.get(code='MY_NEW_FEATURE')
professional.features.add(my_feature)
```

---

## Access Control Flow

```
User → Request Page
    ↓
1. Check Authentication (Django)
    ↓
2. Check RBAC Permission (organizations.rbac)
    ↓
3. Check Active Subscription (billing.decorators)
    ↓
4. Check Feature Access (billing.decorators)
    ↓
5. Check Resource Limits (billing.decorators)
    ↓
Allow or Deny Access
```

---

## Best Practices

### ✅ DO:
- Use feature codes (not tariff slugs) in templates and views
- Create descriptive feature codes: `FINANCIAL_REPORTS` not `FEATURE_1`
- Group related features by category
- Document what each feature unlocks
- Test access control in staging before production
- Combine RBAC permissions with feature checks

### ❌ DON'T:
- Hardcode tariff names in code
- Skip view-level protection (always use decorators)
- Forget to check features in templates (UI should match backend)
- Create too many granular features (keep it manageable)
- Change feature codes after deployment (breaks existing tariffs)

---

## Troubleshooting

### Menu item not showing for user with correct tariff?

1. **Check feature is active:**
   ```python
   Feature.objects.filter(code='FINANCIAL_REPORTS', is_active=True)
   ```

2. **Check tariff includes feature:**
   ```python
   tariff = user.organization.subscription.tariff
   tariff.has_feature('FINANCIAL_REPORTS')
   ```

3. **Check subscription is active:**
   ```python
   user.organization.subscription.is_active()
   ```

### User can see menu but can't access page?

- Add decorator to view:
  ```python
  @require_feature('FINANCIAL_REPORTS')
  ```

### Superuser sees "feature not available"?

- Superusers should bypass feature checks in decorators and templatetags (already implemented)

---

## Migration Path for Existing Installations

If you have existing tariffs without features:

```python
from billing.models import Tariff, Feature

# Create features first
# ... (use create_features management command)

# Assign features to existing tariffs
starter = Tariff.objects.get(slug='starter')
starter.features.set([
    Feature.objects.get(code='FINANCIAL_REPORTS'),
    Feature.objects.get(code='DATA_EXPORT'),
])

professional = Tariff.objects.get(slug='professional')
professional.features.set([
    Feature.objects.get(code='ADVANCED_ANALYTICS'),
    Feature.objects.get(code='FINANCIAL_REPORTS'),
    Feature.objects.get(code='STAFF_PERFORMANCE'),
    Feature.objects.get(code='MARKETING_BROADCASTS'),
    Feature.objects.get(code='API_ACCESS'),
    Feature.objects.get(code='PRIORITY_SUPPORT'),
])

enterprise = Tariff.objects.get(slug='enterprise')
enterprise.features.set(Feature.objects.filter(is_active=True))
```

---

## Testing Feature Access

Use the test script to verify feature permissions:

```bash
python test_tariff_permissions.py
```

Or create custom tests:

```python
from django.test import TestCase
from billing.models import Tariff, Feature, Subscription
from organizations.models import TranslationCenter

class FeatureAccessTest(TestCase):
    def test_starter_cannot_access_advanced_analytics(self):
        # Create tariff without feature
        starter = Tariff.objects.create(slug='starter')
        
        # Create subscription
        center = TranslationCenter.objects.create(...)
        sub = Subscription.objects.create(
            organization=center,
            tariff=starter,
            ...
        )
        
        # Test feature access
        self.assertFalse(starter.has_feature('ADVANCED_ANALYTICS'))
```

---

## Future Enhancements

Potential additions to the system:

1. **Feature Usage Tracking**: Track which features are actually used
2. **Feature Trials**: Allow temporary access to premium features
3. **Feature Bundles**: Group features into packages
4. **Dynamic Pricing**: Price calculation based on selected features
5. **Feature Recommendations**: Suggest features based on usage patterns
6. **Usage Analytics**: Dashboard showing feature adoption rates
7. **A/B Testing**: Test feature availability impact on conversions

---

## Support

For questions or issues with the feature-based access control system, contact the development team or refer to the main billing documentation.
