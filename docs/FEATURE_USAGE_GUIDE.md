# Feature System Usage Guide

## Overview
This guide shows how to use the new feature system in views, templates, and decorators.

---

## 🔍 Checking Features in Views

### Method 1: Direct Tariff Check
```python
from billing.models import Tariff

def my_view(request):
    tariff = Tariff.objects.get(slug='professional')
    
    # Check single feature
    if tariff.has_feature('marketing_basic'):
        # Enable marketing features
        show_marketing_tools = True
    
    # Get all enabled features
    enabled_features = tariff.get_enabled_features()
    # Returns: ['orders_basic', 'marketing_basic', ...]
    
    # Get features by category
    marketing_features = tariff.get_features_by_category('marketing')
    # Returns: {'marketing_basic': True, 'broadcast_messages': True}
    
    # Get all categories
    all_features = tariff.get_features_by_category()
    # Returns: {'orders': {...}, 'analytics': {...}, ...}
    
    # Count enabled features
    feature_count = tariff.get_feature_count()
    # Returns: 29
```

### Method 2: Through Organization Subscription
```python
def dashboard_view(request):
    org = request.user.organization
    subscription = org.active_subscription
    
    if not subscription:
        # No active subscription
        return redirect('billing:choose_plan')
    
    # Check feature through subscription
    if subscription.has_feature('broadcast_messages'):
        # Allow broadcast messaging
        context['can_broadcast'] = True
    
    # Get enabled features
    features = subscription.get_features()
    context['enabled_features'] = features
    
    # Get features by category
    marketing_features = subscription.get_features_by_category('marketing')
    context['marketing_features'] = marketing_features
```

### Method 3: Helper Function (Recommended)
```python
# Create in billing/utils.py
def get_subscription_features(user):
    """Get features for user's organization subscription"""
    if not hasattr(user, 'organization'):
        return []
    
    subscription = user.organization.active_subscription
    if not subscription or not subscription.is_active():
        return []
    
    return subscription.get_features()

def user_has_feature(user, feature_name):
    """Check if user's organization has a specific feature"""
    if not hasattr(user, 'organization'):
        return False
    
    subscription = user.organization.active_subscription
    if not subscription or not subscription.is_active():
        return False
    
    return subscription.has_feature(feature_name)

# Usage in views
from billing.utils import user_has_feature

def marketing_campaign_view(request):
    if not user_has_feature(request.user, 'marketing_basic'):
        messages.error(request, "Your plan doesn't include marketing features. Upgrade to Professional or Enterprise.")
        return redirect('billing:upgrade')
    
    # Marketing campaign logic
    ...
```

---

## 🎨 Using Features in Templates

### Display Enabled Features
```django
{% load i18n %}

{# Show all enabled features #}
<div class="features-list">
    <h3>{% trans "Your Plan Features" %}</h3>
    <ul>
    {% for feature in subscription.get_features %}
        <li>
            <i class="fas fa-check-circle text-success"></i>
            {{ feature|title|replace:'_':' ' }}
        </li>
    {% endfor %}
    </ul>
</div>
```

### Display Features by Category
```django
{% with features=subscription.get_features_by_category %}
    {% for category, feature_dict in features.items %}
        <div class="feature-category">
            <h4>
                {% if category == 'orders' %}📊{% endif %}
                {% if category == 'analytics' %}📈{% endif %}
                {% if category == 'marketing' %}📢{% endif %}
                {{ category|title }}
            </h4>
            <ul>
            {% for feature_name, is_enabled in feature_dict.items %}
                {% if is_enabled %}
                    <li class="text-success">
                        <i class="fas fa-check"></i>
                        {{ feature_name|replace:'_':' '|title }}
                    </li>
                {% else %}
                    <li class="text-muted">
                        <i class="fas fa-times"></i>
                        {{ feature_name|replace:'_':' '|title }}
                        <span class="badge badge-warning">Upgrade Required</span>
                    </li>
                {% endif %}
            {% endfor %}
            </ul>
        </div>
    {% endfor %}
{% endwith %}
```

### Conditional Feature Display
```django
{# Show marketing tools only if feature is enabled #}
{% if subscription.has_feature.marketing_basic %}
    <div class="marketing-tools">
        <h3>{% trans "Marketing Campaign Manager" %}</h3>
        <a href="{% url 'marketing:create_campaign' %}" class="btn btn-primary">
            {% trans "Create Campaign" %}
        </a>
    </div>
{% else %}
    <div class="upgrade-prompt">
        <p>{% trans "Marketing features are available in Professional and Enterprise plans." %}</p>
        <a href="{% url 'billing:upgrade' %}" class="btn btn-warning">
            {% trans "Upgrade Now" %}
        </a>
    </div>
{% endif %}
```

### Tariff Comparison Table
```django
<table class="table table-comparison">
    <thead>
        <tr>
            <th>Feature</th>
            {% for tariff in tariffs %}
                <th>{{ tariff.title }}</th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
        {# Orders #}
        <tr>
            <td>Basic Order Management</td>
            {% for tariff in tariffs %}
                <td>
                    {% if tariff.feature_orders_basic %}
                        <i class="fas fa-check text-success"></i>
                    {% else %}
                        <i class="fas fa-times text-muted"></i>
                    {% endif %}
                </td>
            {% endfor %}
        </tr>
        <tr>
            <td>Advanced Order Management</td>
            {% for tariff in tariffs %}
                <td>
                    {% if tariff.feature_orders_advanced %}
                        <i class="fas fa-check text-success"></i>
                    {% else %}
                        <i class="fas fa-times text-muted"></i>
                    {% endif %}
                </td>
            {% endfor %}
        </tr>
        {# Add more features... #}
    </tbody>
</table>
```

---

## 🛡️ Using Feature Decorators

### Existing Decorator (Already Compatible)
```python
# In organizations/rbac.py (already exists)
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _

def subscription_feature_required(feature_code):
    """
    Decorator to check if user's organization subscription has a feature
    Works with both old M2M and new boolean fields
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'organization'):
                messages.error(request, _("You must belong to an organization."))
                return redirect('accounts:profile')
            
            subscription = request.user.organization.active_subscription
            if not subscription:
                messages.error(request, _("Your organization doesn't have an active subscription."))
                return redirect('billing:choose_plan')
            
            # This works with boolean fields via has_feature() method
            if not subscription.has_feature(feature_code):
                messages.error(
                    request, 
                    _("Your subscription plan doesn't include this feature. Please upgrade.")
                )
                return redirect('billing:upgrade')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage in views
from organizations.rbac import subscription_feature_required

@subscription_feature_required('marketing_basic')
def marketing_dashboard(request):
    # Only accessible if subscription has marketing_basic feature
    return render(request, 'marketing/dashboard.html')

@subscription_feature_required('broadcast_messages')
def send_broadcast(request):
    # Only accessible with broadcast_messages feature
    if request.method == 'POST':
        # Send broadcast logic
        ...
    return render(request, 'marketing/broadcast.html')
```

### Combined Permission and Feature Check
```python
def permission_and_feature_required(permissions=None, features=None):
    """
    Check both RBAC permissions AND subscription features
    
    Usage:
        @permission_and_feature_required(
            permissions=['can_view_marketing'],
            features=['marketing_basic']
        )
        def marketing_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Check permissions
            if permissions:
                for perm in permissions:
                    if not user.organization_role or not user.organization_role.has_permission(perm):
                        messages.error(request, _("You don't have permission to access this page."))
                        return redirect('dashboard')
            
            # Check features
            if features:
                subscription = user.organization.active_subscription
                if not subscription:
                    messages.error(request, _("No active subscription."))
                    return redirect('billing:choose_plan')
                
                for feature in features:
                    if not subscription.has_feature(feature):
                        messages.error(
                            request,
                            _("Your plan doesn't include %(feature)s. Upgrade required.") % {'feature': feature}
                        )
                        return redirect('billing:upgrade')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@permission_and_feature_required(
    permissions=['can_view_marketing', 'can_create_campaigns'],
    features=['marketing_basic', 'broadcast_messages']
)
def create_broadcast_campaign(request):
    # User must have BOTH permissions AND features
    ...
```

---

## 🔄 Context Processor (Global Template Access)

### Create billing/context_processors.py
```python
def subscription_features(request):
    """
    Add subscription features to all template contexts
    Usage in templates: {{ subscription_features.marketing_basic }}
    """
    if not request.user.is_authenticated:
        return {'subscription_features': {}}
    
    if not hasattr(request.user, 'organization'):
        return {'subscription_features': {}}
    
    subscription = request.user.organization.active_subscription
    if not subscription or not subscription.is_active():
        return {'subscription_features': {}}
    
    # Build dictionary of feature states
    features = {}
    for feature_name in subscription.get_features():
        features[feature_name] = True
    
    return {
        'subscription_features': features,
        'subscription_feature_count': len(features),
        'subscription_tariff': subscription.tariff,
    }
```

### Register in settings.py
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... other context processors
                'billing.context_processors.subscription_features',
            ],
        },
    },
]
```

### Use in templates
```django
{# Available in ALL templates #}
{% if subscription_features.marketing_basic %}
    <li class="nav-item">
        <a href="{% url 'marketing:dashboard' %}">Marketing</a>
    </li>
{% endif %}

{% if subscription_features.broadcast_messages %}
    <button class="btn btn-primary" data-toggle="modal" data-target="#broadcastModal">
        Send Broadcast
    </button>
{% endif %}

{# Show feature count #}
<span class="badge badge-info">
    {{ subscription_feature_count }} features enabled
</span>

{# Show tariff name #}
<div class="subscription-info">
    Current Plan: {{ subscription_tariff.title }}
</div>
```

---

## 📊 Analytics & Reporting

### Track Feature Usage
```python
from django.db.models import Count, Q
from billing.models import Subscription

def get_feature_usage_stats():
    """Get statistics on feature adoption"""
    
    # Count subscriptions by tariff
    tariff_distribution = Subscription.objects.filter(
        status='active'
    ).values('tariff__title').annotate(
        count=Count('id')
    )
    
    # Find most popular features
    feature_usage = {}
    for tariff in Tariff.objects.all():
        features = tariff.get_enabled_features()
        for feature in features:
            feature_usage[feature] = feature_usage.get(feature, 0) + 1
    
    return {
        'tariff_distribution': tariff_distribution,
        'feature_usage': feature_usage,
        'total_active_subscriptions': Subscription.objects.filter(status='active').count()
    }

# Usage in admin dashboard
def admin_dashboard(request):
    stats = get_feature_usage_stats()
    return render(request, 'admin/dashboard.html', {'stats': stats})
```

---

## ✅ Best Practices

### 1. Always Check Subscription Status
```python
# BAD: Direct feature check without subscription check
if tariff.has_feature('marketing_basic'):
    # What if subscription expired?
    ...

# GOOD: Check subscription status first
subscription = org.active_subscription
if subscription and subscription.is_active() and subscription.has_feature('marketing_basic'):
    # Safe to proceed
    ...
```

### 2. Provide Upgrade Prompts
```python
def marketing_view(request):
    subscription = request.user.organization.active_subscription
    
    if not subscription.has_feature('marketing_basic'):
        context = {
            'feature_name': 'Marketing Tools',
            'available_in': ['Professional', 'Enterprise'],
            'upgrade_url': reverse('billing:upgrade')
        }
        return render(request, 'billing/upgrade_required.html', context)
    
    # Feature logic
    ...
```

### 3. Use Feature Categories
```python
# Get all marketing features at once
marketing_features = subscription.get_features_by_category('marketing')

# Check multiple features
has_basic = marketing_features.get('marketing_basic', False)
has_broadcast = marketing_features.get('broadcast_messages', False)

if has_basic and has_broadcast:
    # Full marketing suite available
    ...
```

### 4. Cache Feature Checks
```python
from django.core.cache import cache

def get_user_features_cached(user_id):
    """Cache feature list for 5 minutes"""
    cache_key = f'user_features_{user_id}'
    features = cache.get(cache_key)
    
    if features is None:
        user = User.objects.get(id=user_id)
        subscription = user.organization.active_subscription
        features = subscription.get_features() if subscription else []
        cache.set(cache_key, features, 300)  # 5 minutes
    
    return features
```

---

## 🚀 Complete Example: Marketing Module

### views.py
```python
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from organizations.rbac import subscription_feature_required

@login_required
@subscription_feature_required('marketing_basic')
def marketing_dashboard(request):
    """Marketing dashboard - requires marketing_basic feature"""
    subscription = request.user.organization.active_subscription
    marketing_features = subscription.get_features_by_category('marketing')
    
    context = {
        'can_broadcast': marketing_features.get('broadcast_messages', False),
        'campaigns': Campaign.objects.filter(organization=request.user.organization)
    }
    return render(request, 'marketing/dashboard.html', context)

@login_required
@subscription_feature_required('broadcast_messages')
def send_broadcast(request):
    """Send broadcast - requires broadcast_messages feature"""
    if request.method == 'POST':
        # Broadcast logic
        messages.success(request, "Broadcast sent successfully!")
        return redirect('marketing:dashboard')
    
    return render(request, 'marketing/broadcast_form.html')
```

### dashboard.html
```django
{% extends 'base.html' %}
{% load i18n %}

{% block content %}
<div class="marketing-dashboard">
    <h1>{% trans "Marketing Dashboard" %}</h1>
    
    {# Show available features #}
    <div class="feature-status mb-4">
        <span class="badge badge-success">
            <i class="fas fa-check"></i> {% trans "Marketing Tools Enabled" %}
        </span>
        
        {% if can_broadcast %}
            <span class="badge badge-success">
                <i class="fas fa-check"></i> {% trans "Broadcast Messaging" %}
            </span>
        {% else %}
            <span class="badge badge-warning">
                <i class="fas fa-lock"></i> {% trans "Broadcast (Upgrade Required)" %}
            </span>
        {% endif %}
    </div>
    
    {# Campaign management #}
    <div class="row">
        <div class="col-md-8">
            <h2>{% trans "Campaigns" %}</h2>
            {# Campaign list #}
        </div>
        
        <div class="col-md-4">
            {# Broadcast section - conditional #}
            {% if can_broadcast %}
                <div class="card">
                    <div class="card-body">
                        <h3>{% trans "Send Broadcast" %}</h3>
                        <a href="{% url 'marketing:broadcast' %}" class="btn btn-primary">
                            {% trans "Create Broadcast" %}
                        </a>
                    </div>
                </div>
            {% else %}
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <i class="fas fa-lock fa-3x text-muted mb-3"></i>
                        <h4>{% trans "Unlock Broadcast Messaging" %}</h4>
                        <p>{% trans "Upgrade to Professional or Enterprise" %}</p>
                        <a href="{% url 'billing:upgrade' %}" class="btn btn-warning">
                            {% trans "View Plans" %}
                        </a>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

---

## 📝 Summary

The feature system provides multiple ways to check and enforce features:

1. **Model Methods:** `tariff.has_feature()`, `subscription.has_feature()`
2. **Category Access:** `get_features_by_category()`
3. **Decorators:** `@subscription_feature_required('feature_name')`
4. **Templates:** Direct access via subscription object
5. **Context Processors:** Global template access

Choose the method that best fits your use case! 🎯
