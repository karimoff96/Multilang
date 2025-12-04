from django.contrib import admin
from .models import TranslationCenter, Branch, Role, AdminUser


class BranchInline(admin.TabularInline):
    model = Branch
    extra = 0
    fields = ['name', 'region', 'district', 'phone', 'is_main', 'is_active']
    readonly_fields = []


@admin.register(TranslationCenter)
class TranslationCenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'owner__username', 'owner__first_name', 'owner__last_name']
    inlines = [BranchInline]
    ordering = ['-created_at']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'center', 'region', 'is_main', 'show_pricelist', 'is_active']
    list_filter = ['center', 'region', 'is_main', 'show_pricelist', 'is_active']
    search_fields = ['name', 'center__name', 'region__name']
    ordering = ['center', '-is_main', 'name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'is_system_role', 'is_active',
                    'can_manage_center', 'can_manage_branches', 'can_manage_staff', 
                    'can_create_orders', 'can_assign_orders', 'can_receive_payments']
    list_filter = ['is_system_role', 'is_active']
    search_fields = ['name', 'display_name']
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description', 'is_active', 'is_system_role')
        }),
        ('Center & Branch Management', {
            'fields': (
                'can_manage_center',
                'can_manage_branches',
            ),
            'classes': ('collapse',),
        }),
        ('Staff Management', {
            'fields': (
                'can_manage_staff',
                'can_view_staff',
            ),
            'classes': ('collapse',),
        }),
        ('Order Management', {
            'fields': (
                'can_view_all_orders',
                'can_manage_orders',
                'can_create_orders',
                'can_assign_orders',
            ),
            'classes': ('collapse',),
        }),
        ('Financial Permissions', {
            'fields': (
                'can_receive_payments',
            ),
            'classes': ('collapse',),
        }),
        ('Products & Customers', {
            'fields': (
                'can_manage_products',
                'can_manage_customers',
            ),
            'classes': ('collapse',),
        }),
        ('Reports & Data', {
            'fields': (
                'can_view_reports',
                'can_export_data',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'center', 'branch', 'phone', 'is_active', 'created_at']
    list_filter = ['role', 'center', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    raw_id_fields = ['user', 'created_by']
    ordering = ['-created_at']
    
    def get_readonly_fields(self, request, obj=None):
        """Prevent non-superusers from changing role to owner"""
        if obj and obj.is_owner and not request.user.is_superuser:
            return ['role']
        return []
    
    def save_model(self, request, obj, form, change):
        """Validate role assignment before saving"""
        if not request.user.is_superuser and obj.role.name == Role.OWNER:
            from django.contrib import messages
            messages.error(request, "Only superusers can assign the Owner role.")
            return
        super().save_model(request, obj, form, change)
