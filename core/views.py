from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from core.models import AdminNotification


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    try:
        notification = AdminNotification.objects.get(id=notification_id)
        notification.mark_as_read(request.user)
        return JsonResponse({'success': True})
    except AdminNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    from organizations.models import AdminProfile
    
    try:
        profile = request.user.admin_profile
        if profile.role == 'super_admin' or request.user.is_superuser:
            notifications = AdminNotification.objects.filter(is_read=False)
        elif profile.role == 'center_admin':
            notifications = AdminNotification.objects.filter(
                is_read=False,
                center=profile.translation_center
            )
        else:
            notifications = AdminNotification.objects.filter(
                is_read=False,
                branch=profile.branch
            )
        
        from django.utils import timezone
        count = notifications.update(
            is_read=True,
            read_by=request.user,
            read_at=timezone.now()
        )
        
        return JsonResponse({'success': True, 'count': count})
    except (AttributeError, AdminProfile.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)


@login_required
def get_notifications(request):
    """Get unread notifications for the current user (for AJAX refresh)"""
    notifications = AdminNotification.get_unread_for_user(request.user, limit=10)
    count = AdminNotification.count_unread_for_user(request.user)
    
    data = {
        'count': count,
        'notifications': [
            {
                'id': n.id,
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)
