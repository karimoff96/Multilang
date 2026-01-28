from django.core.management.base import BaseCommand
from billing.models import Feature


class Command(BaseCommand):
    help = 'Create standard features for tariff plans'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating standard features...'))

        features_data = [
            # Analytics & Reports Features
            {
                'code': 'ADVANCED_ANALYTICS',
                'name': 'Advanced Analytics',
                'description': 'Access to advanced analytics dashboards and detailed reports',
                'category': 'analytics'
            },
            {
                'code': 'FINANCIAL_REPORTS',
                'name': 'Financial Reports',
                'description': 'Detailed financial reports and payment analytics',
                'category': 'analytics'
            },
            {
                'code': 'STAFF_PERFORMANCE',
                'name': 'Staff Performance Reports',
                'description': 'Track and analyze staff performance metrics',
                'category': 'analytics'
            },
            {
                'code': 'BRANCH_COMPARISON',
                'name': 'Branch Comparison',
                'description': 'Compare performance across multiple branches',
                'category': 'analytics'
            },
            {
                'code': 'CUSTOMER_ANALYTICS',
                'name': 'Customer Analytics',
                'description': 'Customer behavior analysis and insights',
                'category': 'analytics'
            },
            {
                'code': 'EXPENSE_ANALYTICS',
                'name': 'Expense Analytics',
                'description': 'Detailed expense tracking and analysis',
                'category': 'analytics'
            },
            {
                'code': 'UNIT_ECONOMY',
                'name': 'Unit Economy Reports',
                'description': 'Unit economics and profitability analysis',
                'category': 'analytics'
            },
            
            # Marketing Features
            {
                'code': 'MARKETING_BROADCASTS',
                'name': 'Marketing Broadcasts',
                'description': 'Send broadcast messages to customers',
                'category': 'marketing'
            },
            {
                'code': 'ADVANCED_MARKETING',
                'name': 'Advanced Marketing Tools',
                'description': 'Advanced marketing campaigns and automation',
                'category': 'marketing'
            },
            
            # Integration Features
            {
                'code': 'API_ACCESS',
                'name': 'API Access',
                'description': 'REST API access for third-party integrations',
                'category': 'integration'
            },
            {
                'code': 'WEBHOOK_INTEGRATION',
                'name': 'Webhook Integration',
                'description': 'Webhook support for real-time event notifications',
                'category': 'integration'
            },
            
            # Support Features
            {
                'code': 'PRIORITY_SUPPORT',
                'name': 'Priority Support',
                'description': '24/7 priority customer support',
                'category': 'support'
            },
            {
                'code': 'DEDICATED_MANAGER',
                'name': 'Dedicated Account Manager',
                'description': 'Personal account manager for business support',
                'category': 'support'
            },
            
            # Security & Audit Features
            {
                'code': 'AUDIT_LOGS',
                'name': 'Audit Logs',
                'description': 'Detailed audit logs and activity tracking',
                'category': 'security'
            },
            {
                'code': 'ADVANCED_SECURITY',
                'name': 'Advanced Security',
                'description': 'Enhanced security features and access controls',
                'category': 'security'
            },
            
            # Customization Features
            {
                'code': 'CUSTOM_BRANDING',
                'name': 'Custom Branding',
                'description': 'Custom logo, colors, and branding',
                'category': 'customization'
            },
            {
                'code': 'WHITE_LABEL',
                'name': 'White Label',
                'description': 'Complete white-label solution',
                'category': 'customization'
            },
            
            # Payment Features
            {
                'code': 'BULK_PAYMENTS',
                'name': 'Bulk Payments',
                'description': 'Process multiple payments at once',
                'category': 'payment'
            },
            {
                'code': 'PAYMENT_GATEWAY_INTEGRATION',
                'name': 'Payment Gateway Integration',
                'description': 'Integration with payment gateways',
                'category': 'payment'
            },
            
            # Export Features
            {
                'code': 'DATA_EXPORT',
                'name': 'Data Export',
                'description': 'Export data to Excel, CSV, PDF formats',
                'category': 'export'
            },
            {
                'code': 'AUTOMATED_REPORTS',
                'name': 'Automated Reports',
                'description': 'Schedule and automate report generation',
                'category': 'export'
            },
        ]

        created_count = 0
        updated_count = 0

        for feature_data in features_data:
            feature, created = Feature.objects.update_or_create(
                code=feature_data['code'],
                defaults={
                    'name': feature_data['name'],
                    'description': feature_data['description'],
                    'category': feature_data['category'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {feature.name} ({feature.code})'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'  ↻ Updated: {feature.name} ({feature.code})'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Complete! Created {created_count} new features, updated {updated_count} existing features.'))
        self.stdout.write(self.style.SUCCESS(f'Total features: {Feature.objects.count()}'))
