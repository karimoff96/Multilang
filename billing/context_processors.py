"""
Context processor to make billing/subscription info available in all templates.
"""

def billing_context(request):
    """
    Add billing and subscription information to template context.
    
    Available in all templates:
    - has_active_subscription: Boolean
    - user_tariff: Tariff object or None
    - subscription_status: Dict with subscription details
    """
    context = {}
    
    if request.user.is_authenticated:
        # Superusers always have access
        if request.user.is_superuser:
            context['has_active_subscription'] = True
            context['user_tariff'] = None
            context['subscription_status'] = {
                'is_superuser': True,
                'has_subscription': True,
                'is_active': True
            }
            return context
        
        # Check organization subscription
        if hasattr(request.user, 'organization'):
            org = request.user.organization
            
            if hasattr(org, 'subscription'):
                subscription = org.subscription
                
                context['has_active_subscription'] = subscription.is_active()
                context['user_tariff'] = subscription.tariff
                context['subscription_status'] = {
                    'has_subscription': True,
                    'is_active': subscription.is_active(),
                    'tariff_name': subscription.tariff.title,
                    'days_remaining': subscription.days_remaining(),
                    'is_trial': subscription.is_trial,
                    'end_date': subscription.end_date,
                }
            else:
                context['has_active_subscription'] = False
                context['user_tariff'] = None
                context['subscription_status'] = {
                    'has_subscription': False,
                    'is_active': False
                }
        else:
            context['has_active_subscription'] = False
            context['user_tariff'] = None
            context['subscription_status'] = {
                'has_subscription': False,
                'is_active': False
            }
    else:
        context['has_active_subscription'] = False
        context['user_tariff'] = None
        context['subscription_status'] = {
            'has_subscription': False,
            'is_active': False
        }
    
    return context
