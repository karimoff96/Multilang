from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class TranslationCenter(models.Model):
    """Translation center owned by an owner"""
    name = models.CharField(_("Name"), max_length=200)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_centers',
        verbose_name=_("Owner")
    )
    logo = models.ImageField(_("Logo"), upload_to='centers/logos/', blank=True, null=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    location_url = models.URLField(_("Location URL"), blank=True, null=True, help_text=_("Google Maps or Yandex Maps URL"))
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Translation Center")
        verbose_name_plural = _("Translation Centers")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Auto-create default branch for new centers
        if is_new:
            Branch.objects.create(
                center=self,
                name=f"{self.name} - Main Branch",
                is_main=True
            )


class Branch(models.Model):
    """Physical branch location of a translation center"""
    center = models.ForeignKey(
        TranslationCenter,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name=_("Translation Center")
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='branches',
        verbose_name=_("Region")
    )
    district = models.ForeignKey(
        'core.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='branches',
        verbose_name=_("District")
    )
    name = models.CharField(_("Name"), max_length=200)
    address = models.TextField(_("Address"), blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True, null=True)
    location_url = models.URLField(_("Location URL"), blank=True, null=True, help_text=_("Google Maps or Yandex Maps URL"))
    is_main = models.BooleanField(_("Main Branch"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        ordering = ['center', '-is_main', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.center.name})"


class Role(models.Model):
    """Roles with customizable permissions - can be created by superusers"""
    # System role identifiers (used for special logic)
    OWNER = 'owner'
    MANAGER = 'manager'
    STAFF = 'staff'
    
    # These are just defaults/system roles - custom roles can be created
    SYSTEM_ROLES = [OWNER, MANAGER, STAFF]
    
    name = models.CharField(_("Name"), max_length=50, unique=True)
    display_name = models.CharField(_("Display Name"), max_length=100, blank=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    is_system_role = models.BooleanField(_("System Role"), default=False, 
        help_text=_("System roles cannot be deleted"))
    
    # Permissions
    can_manage_center = models.BooleanField(_("Can manage center"), default=False)
    can_manage_branches = models.BooleanField(_("Can manage branches"), default=False)
    can_manage_staff = models.BooleanField(_("Can manage staff"), default=False)
    can_view_all_orders = models.BooleanField(_("Can view all orders"), default=False)
    can_manage_orders = models.BooleanField(_("Can manage orders"), default=False)
    can_assign_orders = models.BooleanField(_("Can assign orders"), default=False)
    can_receive_payments = models.BooleanField(_("Can receive payments"), default=False)
    can_view_reports = models.BooleanField(_("Can view reports"), default=False)
    can_manage_products = models.BooleanField(_("Can manage products"), default=False)
    can_manage_customers = models.BooleanField(_("Can manage customers"), default=False)
    can_export_data = models.BooleanField(_("Can export data"), default=False)
    
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True, null=True)
    
    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ['name']
    
    def __str__(self):
        return self.display_name or self.name.title()
    
    def save(self, *args, **kwargs):
        # Auto-set display name if not provided
        if not self.display_name:
            self.display_name = self.name.replace('_', ' ').title()
        # Mark system roles
        if self.name in self.SYSTEM_ROLES:
            self.is_system_role = True
        super().save(*args, **kwargs)
    
    @classmethod
    def get_all_permissions(cls):
        """Return list of all permission field names"""
        return [
            'can_manage_center',
            'can_manage_branches', 
            'can_manage_staff',
            'can_view_all_orders',
            'can_manage_orders',
            'can_assign_orders',
            'can_receive_payments',
            'can_view_reports',
            'can_manage_products',
            'can_manage_customers',
            'can_export_data',
        ]


class AdminUser(models.Model):
    """Extended user profile for staff/managers with role-based access"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile',
        verbose_name=_("User")
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='users',
        verbose_name=_("Role")
    )
    center = models.ForeignKey(
        TranslationCenter,
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name=_("Translation Center"),
        null=True,
        blank=True,
        help_text=_("For owners, this is their primary center")
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name=_("Branch"),
        help_text=_("Specific branch assignment for managers/staff")
    )
    phone = models.CharField(_("Phone"), max_length=20, blank=True, null=True)
    avatar = models.ImageField(_("Avatar"), upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_staff',
        verbose_name=_("Created by")
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Admin User")
        verbose_name_plural = _("Admin Users")
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"
    
    @property
    def is_owner(self):
        return self.role.name == Role.OWNER
    
    @property
    def is_manager(self):
        return self.role.name == Role.MANAGER
    
    @property
    def is_staff_role(self):
        return self.role.name == Role.STAFF
    
    def has_permission(self, permission):
        """Check if user has a specific permission"""
        return getattr(self.role, permission, False)
    
    def get_accessible_branches(self):
        """Get branches this user can access"""
        if self.is_owner:
            # Owners can access all branches of their centers
            return Branch.objects.filter(center__owner=self.user)
        elif self.is_manager:
            # Managers can access their assigned branch
            if self.branch:
                return Branch.objects.filter(pk=self.branch.pk)
            return Branch.objects.none()
        else:
            # Staff can only access their branch
            if self.branch:
                return Branch.objects.filter(pk=self.branch.pk)
            return Branch.objects.none()
    
    def can_access_branch(self, branch):
        """Check if user can access a specific branch"""
        return self.get_accessible_branches().filter(pk=branch.pk).exists()
