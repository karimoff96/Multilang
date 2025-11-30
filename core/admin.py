from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Region, District, AdditionalInfo, AuditLog


@admin.register(Region)
class RegionAdmin(TranslationAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(District)
class DistrictAdmin(TranslationAdmin):
    list_display = ['name', 'region', 'is_active']
    list_filter = ['region', 'is_active']
    search_fields = ['name', 'region__name']
    ordering = ['region', 'name']


@admin.register(AdditionalInfo)
class AdditionalInfoAdmin(admin.ModelAdmin):
    list_display = ['bot_user', 'branch', 'title', 'created_at']
    list_filter = ['branch', 'created_at']
    search_fields = ['title', 'bot_user__name']
    ordering = ['-created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'target_repr', 'branch', 'ip_address']
    list_filter = ['action', 'created_at', 'branch', 'center']
    search_fields = ['user__username', 'user__first_name', 'target_repr', 'details']
    readonly_fields = ['user', 'action', 'content_type', 'object_id', 'target_repr', 
                       'details', 'changes', 'ip_address', 'user_agent', 'branch', 
                       'center', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
