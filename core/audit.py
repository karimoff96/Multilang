"""
Audit Logging System for tracking user actions.

This module provides:
- Helper functions for audit logging
- Utility to detect model changes
"""

from django.contrib.contenttypes.models import ContentType


def get_audit_log_model():
    """Get the AuditLog model (lazy import to avoid circular imports)"""
    from .models import AuditLog
    return AuditLog


def log_action(user, action, target=None, details=None, changes=None, request=None, branch=None, center=None):
    """
    Create an audit log entry.
    
    Args:
        user: The user performing the action
        action: One of ACTION_* constants from AuditLog
        target: The object being acted upon (optional)
        details: Human-readable description (optional)
        changes: Dict of field changes for updates (optional)
        request: HTTP request for IP/user agent (optional)
        branch: Branch context (optional)
        center: Center context (optional)
    """
    AuditLog = get_audit_log_model()
    
    log_entry = AuditLog(
        user=user,
        action=action,
        details=details,
        changes=changes or {},
    )
    
    # Set target object
    if target:
        log_entry.content_type = ContentType.objects.get_for_model(target)
        log_entry.object_id = target.pk
        log_entry.target_repr = str(target)[:255]
        
        # Auto-detect branch/center from target
        if not branch and hasattr(target, 'branch'):
            branch = target.branch
        if not center and hasattr(target, 'center'):
            center = target.center
        if not center and branch:
            center = branch.center
    
    log_entry.branch = branch
    log_entry.center = center
    
    # Extract request info
    if request:
        log_entry.ip_address = _get_client_ip(request)
        log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    log_entry.save()
    return log_entry


def _get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_create(user, target, request=None, details=None):
    """Log object creation"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_CREATE,
        target=target,
        details=details or f"Created {target._meta.verbose_name}: {target}",
        request=request
    )


def log_update(user, target, changes, request=None, details=None):
    """Log object update with field changes"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_UPDATE,
        target=target,
        changes=changes,
        details=details or f"Updated {target._meta.verbose_name}: {target}",
        request=request
    )


def log_delete(user, target, request=None, details=None):
    """Log object deletion"""
    AuditLog = get_audit_log_model()
    target_repr = str(target)
    target_type = target._meta.verbose_name
    
    log_entry = AuditLog(
        user=user,
        action=AuditLog.ACTION_DELETE,
        content_type=ContentType.objects.get_for_model(target),
        object_id=target.pk,
        target_repr=target_repr[:255],
        details=details or f"Deleted {target_type}: {target_repr}",
    )
    
    if hasattr(target, 'branch') and target.branch:
        log_entry.branch = target.branch
        log_entry.center = target.branch.center
    elif hasattr(target, 'center') and target.center:
        log_entry.center = target.center
    
    if request:
        log_entry.ip_address = _get_client_ip(request)
        log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    log_entry.save()
    return log_entry


def log_login(user, request=None):
    """Log user login"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_LOGIN,
        details=f"User logged in",
        request=request
    )


def log_logout(user, request=None):
    """Log user logout"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_LOGOUT,
        details=f"User logged out",
        request=request
    )


def log_order_assign(user, order, staff, request=None):
    """Log order assignment"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_ASSIGN,
        target=order,
        details=f"Assigned order #{order.id} to {staff}",
        request=request,
        branch=order.branch
    )


def log_status_change(user, order, old_status, new_status, request=None):
    """Log order status change"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_STATUS_CHANGE,
        target=order,
        changes={'status': {'old': old_status, 'new': new_status}},
        details=f"Changed order #{order.id} status from {old_status} to {new_status}",
        request=request,
        branch=order.branch
    )


def log_payment(user, order, request=None):
    """Log payment received"""
    AuditLog = get_audit_log_model()
    return log_action(
        user=user,
        action=AuditLog.ACTION_PAYMENT,
        target=order,
        details=f"Received payment for order #{order.id} - {order.total_price} UZS",
        request=request,
        branch=order.branch
    )


def get_model_changes(instance, old_instance):
    """
    Compare two model instances and return dict of changed fields.
    
    Returns:
        dict: {field_name: {'old': old_value, 'new': new_value}}
    """
    changes = {}
    
    for field in instance._meta.fields:
        field_name = field.name
        
        # Skip auto fields
        if field_name in ('id', 'pk', 'created_at', 'updated_at'):
            continue
        
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)
        
        # Handle foreign keys
        if hasattr(old_value, 'pk'):
            old_value = old_value.pk
        if hasattr(new_value, 'pk'):
            new_value = new_value.pk
        
        # Convert to string for comparison
        old_str = str(old_value) if old_value is not None else None
        new_str = str(new_value) if new_value is not None else None
        
        if old_str != new_str:
            changes[field_name] = {
                'old': old_str,
                'new': new_str
            }
    
    return changes
