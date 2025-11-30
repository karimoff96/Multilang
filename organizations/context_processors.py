"""
Context processors for the translation center management system.
Provides role and permission info to all templates.
"""

from organizations.rbac import get_admin_profile


def rbac_context(request):
    """
    Add RBAC-related variables to template context.
    
    Available in templates:
    - admin_profile: The AdminUser instance
    - user_role: Role name ('owner', 'manager', 'staff')
    - is_owner: Boolean
    - is_manager: Boolean  
    - is_staff_member: Boolean
    - current_center: TranslationCenter instance
    - current_branch: Branch instance
    - permissions: Dict of all permissions
    """
    context = {
        'admin_profile': None,
        'user_role': None,
        'user_role_display': None,
        'is_owner': False,
        'is_manager': False,
        'is_staff_member': False,
        'current_center': None,
        'current_branch': None,
        'permissions': {},
    }
    
    if not request.user.is_authenticated:
        return context
    
    # Superuser has all permissions
    if request.user.is_superuser:
        context.update({
            'user_role': 'superuser',
            'user_role_display': 'Super Admin',
            'is_owner': True,
            'is_manager': True,
            'is_staff_member': False,  # Superuser is not a staff member - they see aggregated data
            'permissions': {
                'can_manage_center': True,
                'can_manage_branches': True,
                'can_manage_staff': True,
                'can_view_all_orders': True,
                'can_manage_orders': True,
                'can_receive_payments': True,
                'can_view_reports': True,
                'can_manage_products': True,
            }
        })
        return context
    
    admin_profile = get_admin_profile(request.user)
    
    if admin_profile:
        role = admin_profile.role
        context.update({
            'admin_profile': admin_profile,
            'user_role': role.name,
            'user_role_display': role.get_name_display(),
            'is_owner': admin_profile.is_owner,
            'is_manager': admin_profile.is_manager,
            'is_staff_member': admin_profile.is_staff_role,
            'current_center': admin_profile.center,
            'current_branch': admin_profile.branch,
            'permissions': {
                'can_manage_center': role.can_manage_center,
                'can_manage_branches': role.can_manage_branches,
                'can_manage_staff': role.can_manage_staff,
                'can_view_all_orders': role.can_view_all_orders,
                'can_manage_orders': role.can_manage_orders,
                'can_receive_payments': role.can_receive_payments,
                'can_view_reports': role.can_view_reports,
                'can_manage_products': role.can_manage_products,
            }
        })
    
    return context
