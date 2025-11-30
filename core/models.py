from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    """Region/Oblast of Uzbekistan"""
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=10, unique=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class District(models.Model):
    """District/Tuman within a Region"""
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='districts',
        verbose_name=_("Region")
    )
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")
        ordering = ['region', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.region.name}"


class AdditionalInfo(models.Model):
    """Additional user info for flexible data storage"""
    bot_user = models.ForeignKey(
        'accounts.BotUser',
        on_delete=models.CASCADE,
        related_name='additional_info'
    )
    branch = models.ForeignKey(
        'organizations.Branch',
        on_delete=models.CASCADE,
        related_name='customer_additional_info',
        verbose_name=_("Branch"),
        null=True,
        blank=True
    )
    title = models.CharField(_("Title"), max_length=100)
    body = models.TextField(_("Body"), blank=True, null=True)
    file = models.FileField(_("File"), upload_to='additional_info/', blank=True, null=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Additional Info")
        verbose_name_plural = _("Additional Info")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.bot_user.full_name}"


class AuditLog(models.Model):
    """Model to store audit trail of user actions"""
    
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_VIEW = 'view'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_ASSIGN = 'assign'
    ACTION_STATUS_CHANGE = 'status_change'
    ACTION_PAYMENT = 'payment'
    ACTION_OTHER = 'other'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, _('Create')),
        (ACTION_UPDATE, _('Update')),
        (ACTION_DELETE, _('Delete')),
        (ACTION_VIEW, _('View')),
        (ACTION_LOGIN, _('Login')),
        (ACTION_LOGOUT, _('Logout')),
        (ACTION_ASSIGN, _('Assign')),
        (ACTION_STATUS_CHANGE, _('Status Change')),
        (ACTION_PAYMENT, _('Payment')),
        (ACTION_OTHER, _('Other')),
    ]
    
    # Who performed the action
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_("User")
    )
    
    # What action was performed
    action = models.CharField(
        _("Action"),
        max_length=20,
        choices=ACTION_CHOICES
    )
    
    # Target object (generic relation)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Content Type")
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Object ID"))
    
    # Human-readable target description
    target_repr = models.CharField(_("Target"), max_length=255, blank=True)
    
    # Additional details
    details = models.TextField(_("Details"), blank=True, null=True)
    changes = models.JSONField(_("Changes"), default=dict, blank=True)
    
    # Context
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True, null=True)
    
    # Branch/Center context for filtering
    branch = models.ForeignKey(
        'organizations.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_("Branch")
    )
    center = models.ForeignKey(
        'organizations.TranslationCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_("Translation Center")
    )
    
    # Timestamp
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['branch', 'created_at']),
            models.Index(fields=['center', 'created_at']),
        ]
    
    def __str__(self):
        user_name = self.user.get_full_name() or self.user.username if self.user else 'System'
        return f"{user_name} - {self.get_action_display()} - {self.target_repr}"
