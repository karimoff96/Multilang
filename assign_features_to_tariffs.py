#!/usr/bin/env python
"""
Assign features to existing tariffs based on plan tiers.

This script demonstrates how to configure your production tariffs with appropriate features.
Customize the feature assignments based on your business model.

Run with: python manage.py shell < assign_features_to_tariffs.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WowDash.settings')
django.setup()

from billing.models import Tariff, Feature

print("="*80)
print(" ASSIGNING FEATURES TO TARIFFS ".center(80))
print("="*80)
print()

# Get all features
try:
    # Basic features (for all paid plans)
    financial_reports = Feature.objects.get(code='FINANCIAL_REPORTS')
    data_export = Feature.objects.get(code='DATA_EXPORT')
    
    # Advanced analytics features
    advanced_analytics = Feature.objects.get(code='ADVANCED_ANALYTICS')
    staff_performance = Feature.objects.get(code='STAFF_PERFORMANCE')
    expense_analytics = Feature.objects.get(code='EXPENSE_ANALYTICS')
    customer_analytics = Feature.objects.get(code='CUSTOMER_ANALYTICS')
    unit_economy = Feature.objects.get(code='UNIT_ECONOMY')
    branch_comparison = Feature.objects.get(code='BRANCH_COMPARISON')
    
    # Marketing features
    marketing_broadcasts = Feature.objects.get(code='MARKETING_BROADCASTS')
    advanced_marketing = Feature.objects.get(code='ADVANCED_MARKETING')
    
    # Integration features
    api_access = Feature.objects.get(code='API_ACCESS')
    webhook_integration = Feature.objects.get(code='WEBHOOK_INTEGRATION')
    
    # Support features
    priority_support = Feature.objects.get(code='PRIORITY_SUPPORT')
    dedicated_manager = Feature.objects.get(code='DEDICATED_MANAGER')
    
    # Security features
    audit_logs = Feature.objects.get(code='AUDIT_LOGS')
    advanced_security = Feature.objects.get(code='ADVANCED_SECURITY')
    
    # Customization features
    custom_branding = Feature.objects.get(code='CUSTOM_BRANDING')
    white_label = Feature.objects.get(code='WHITE_LABEL')
    
    # Payment features
    bulk_payments = Feature.objects.get(code='BULK_PAYMENTS')
    payment_gateway = Feature.objects.get(code='PAYMENT_GATEWAY_INTEGRATION')
    
    # Report features
    automated_reports = Feature.objects.get(code='AUTOMATED_REPORTS')
    
    print("✓ Loaded 21 features successfully")
    print()
    
except Feature.DoesNotExist as e:
    print(f"✗ Error: Feature not found: {e}")
    print("  Please run: python manage.py create_features")
    exit(1)

# ============================================================================
# CONFIGURE YOUR TARIFFS HERE
# ============================================================================

tariff_configs = {
    # Free Trial - Very limited (no features, just trial period)
    'free-trial': {
        'features': [],
        'description': '10-day free trial with basic functionality'
    },
    
    # Starter - Small businesses
    'starter': {
        'features': [
            financial_reports,      # Basic financial reports
            data_export,           # Export data to Excel/CSV
        ],
        'description': 'Perfect for small translation centers'
    },
    
    # Professional - Growing businesses
    'professional': {
        'features': [
            # All starter features +
            financial_reports,
            data_export,
            
            # Advanced analytics
            advanced_analytics,
            staff_performance,
            expense_analytics,
            
            # Marketing
            marketing_broadcasts,
            
            # Integration
            api_access,
            
            # Support
            priority_support,
            
            # Payment
            bulk_payments,
        ],
        'description': 'For growing translation businesses'
    },
    
    # Enterprise - Large organizations
    'enterprise': {
        'features': 'ALL',  # Special case: all features
        'description': 'Unlimited resources for large enterprises'
    },
}

# ============================================================================
# APPLY CONFIGURATIONS
# ============================================================================

print("Assigning features to tariffs...")
print("-" * 80)

for slug, config in tariff_configs.items():
    try:
        tariff = Tariff.objects.get(slug=slug)
        
        if config['features'] == 'ALL':
            # Assign all active features
            all_features = Feature.objects.filter(is_active=True)
            tariff.features.set(all_features)
            feature_count = all_features.count()
            print(f"\n✓ {tariff.title} ({slug})")
            print(f"  Description: {config['description']}")
            print(f"  Features: ALL ({feature_count} features)")
        else:
            # Assign specific features
            tariff.features.set(config['features'])
            print(f"\n✓ {tariff.title} ({slug})")
            print(f"  Description: {config['description']}")
            print(f"  Features ({len(config['features'])}):")
            for feature in config['features']:
                print(f"    - {feature.name}")
        
    except Tariff.DoesNotExist:
        print(f"\n⚠ Warning: Tariff '{slug}' not found - skipping")
        continue

print()
print("-" * 80)
print("✓ Feature assignment complete!")
print()

# ============================================================================
# VERIFICATION
# ============================================================================

print("=" * 80)
print(" VERIFICATION - Current Tariff Configurations ".center(80))
print("=" * 80)
print()

all_tariffs = Tariff.objects.filter(is_active=True).prefetch_related('features')

for tariff in all_tariffs:
    features = tariff.features.filter(is_active=True)
    feature_count = features.count()
    
    print(f"\n{tariff.title} ({tariff.slug})")
    print(f"  Limits: {tariff.max_branches or '∞'} branches, "
          f"{tariff.max_staff or '∞'} staff, "
          f"{tariff.max_monthly_orders or '∞'} monthly orders")
    
    if feature_count > 0:
        print(f"  Features ({feature_count}):")
        for feature in features:
            print(f"    • {feature.name} ({feature.category})")
    else:
        print(f"  Features: None (basic trial only)")

print()
print("=" * 80)
print()

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

print("EXAMPLE: Checking feature access")
print("-" * 80)
print()

for tariff in all_tariffs[:3]:  # Show first 3 tariffs
    print(f"{tariff.title}:")
    print(f"  Has FINANCIAL_REPORTS: {tariff.has_feature('FINANCIAL_REPORTS')}")
    print(f"  Has ADVANCED_ANALYTICS: {tariff.has_feature('ADVANCED_ANALYTICS')}")
    print(f"  Has API_ACCESS: {tariff.has_feature('API_ACCESS')}")
    print()

print("=" * 80)
print("✓ All done! Your tariffs are now configured with features.")
print()
print("Next steps:")
print("  1. Test with different user accounts")
print("  2. Verify menu items show/hide correctly")
print("  3. Test view access with decorators")
print("  4. Customize feature assignments as needed")
print()
