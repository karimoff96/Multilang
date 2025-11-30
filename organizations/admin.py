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
    list_display = ['name', 'center', 'region', 'is_main', 'is_active']
    list_filter = ['center', 'region', 'is_main', 'is_active']
    search_fields = ['name', 'center__name', 'region__name']
    ordering = ['center', '-is_main', 'name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_manage_center', 'can_manage_branches', 'can_manage_staff', 
                    'can_view_all_orders', 'can_manage_orders', 'can_receive_payments']
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Permissions', {
            'fields': (
                'can_manage_center',
                'can_manage_branches',
                'can_manage_staff',
                'can_view_all_orders',
                'can_manage_orders',
                'can_receive_payments',
                'can_view_reports',
                'can_manage_products',
            )
        }),
    )


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'center', 'branch', 'phone', 'is_active', 'created_at']
    list_filter = ['role', 'center', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    raw_id_fields = ['user', 'created_by']
    ordering = ['-created_at']
