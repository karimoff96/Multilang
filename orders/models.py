from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import BotUser
from organizations.models import Branch, AdminUser
from services.models import Language, Product

# Create your models here.


class OrderMedia(models.Model):
    file = models.FileField(upload_to="order_media/", verbose_name=_("File"))
    pages = models.PositiveIntegerField(default=1, verbose_name=_("Pages"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"{self.file.name} ({self.pages} pages)"

    class Meta:
        verbose_name = _("Order file")
        verbose_name_plural = _("Order media")


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", _("Pending")),  # Order created, awaiting payment
        ("payment_pending", _("Payment Pending")),  # Card payment, waiting for receipt
        ("payment_received", _("Payment Received")),  # Receipt uploaded
        ("payment_confirmed", _("Payment Confirmed")),  # Payment verified by admin
        ("in_progress", _("In Progress")),  # Order being processed
        ("ready", _("Ready")),  # Order completed, ready for pickup
        ("completed", _("Completed")),  # Order delivered
        ("cancelled", _("Cancelled")),  # Order cancelled
    )

    PAYMENT_TYPE = (
        ("cash", _("Cash")),
        ("card", _("Card")),
    )

    # Branch relationship - orders belong to specific branches
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Branch"),
        null=True,
        blank=True,
    )

    bot_user = models.ForeignKey(
        BotUser, on_delete=models.CASCADE, verbose_name=_("Telegram User")
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name=_("Document Type")
    )
    total_pages = models.PositiveIntegerField(default=1, verbose_name=_("Total Pages"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
    )
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"))
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)
    language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Translation Language"),
        help_text=_(
            "The target language selected by user from category's available languages"
        ),
    )
    payment_type = models.CharField(
        max_length=100,
        choices=PAYMENT_TYPE,
        default="cash",
        verbose_name=_("Payment Type"),
    )
    recipt = models.FileField(
        upload_to="recipts/", blank=True, null=True, verbose_name=_("Receipt")
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Total Price")
    )
    copy_number = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Number of Copies"),
        help_text=_("Additional copies needed (0 means only original)"),
    )
    files = models.ManyToManyField(OrderMedia, verbose_name=_("Files"))

    # Staff assignment fields
    assigned_to = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
        verbose_name=_("Assigned To"),
        limit_choices_to={"role__name": "staff"},
    )
    assigned_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_assigned",
        verbose_name=_("Assigned By"),
        limit_choices_to={"role__name__in": ["owner", "manager"]},
    )
    assigned_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Assigned At")
    )

    # Payment tracking
    payment_received_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_received",
        verbose_name=_("Payment Received By"),
    )
    payment_received_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Payment Received At")
    )

    # Order completion tracking
    completed_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_orders",
        verbose_name=_("Completed By"),
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Completed At")
    )

    def __str__(self):
        return f"Order {self.id} - {self.bot_user.display_name} - {self.product} ({self.total_pages} pages)"

    @property
    def calculated_price(self):
        """Calculate price based on user type, total pages, and copy number"""
        base_price = self.product.get_price_for_user_type(
            is_agency=self.bot_user.is_agency, pages=self.total_pages
        )

        # Add copy charges if copy_number > 0
        if self.copy_number > 0:
            copy_percentage = (
                self.product.agency_copy_price_percentage
                if self.bot_user.is_agency
                else self.product.user_copy_price_percentage
            )
            copy_charge = (base_price * copy_percentage * self.copy_number) / 100
            return base_price + copy_charge

        return base_price

    @property
    def category(self):
        """Get main service from document type"""
        return self.product.category

    @property
    def available_languages(self):
        """Get available languages from product's category"""
        if self.product and self.product.category:
            return self.product.category.languages.all()
        return Language.objects.none()

    def is_valid_language(self, language):
        """Check if the given language is valid for this order's category"""
        if not language:
            return True  # Allow null
        return self.available_languages.filter(pk=language.pk).exists()

    @property
    def complexity_level(self):
        """Get complexity level from document type"""
        return self.product.complexity_level

    @property
    def service_category(self):
        """Get service category from document type"""
        return self.product.service_category

    @property
    def estimated_days(self):
        """Get estimated days from document type"""
        return self.product.estimated_days

    def update_total_pages(self):
        """Update total pages from all files"""
        self.total_pages = self.files.aggregate(total=models.Sum("pages"))["total"] or 0
        return self.total_pages

    def assign_to_staff(self, staff_member, assigned_by):
        """Assign this order to a staff member"""
        self.assigned_to = staff_member
        self.assigned_by = assigned_by
        self.assigned_at = timezone.now()
        self.status = "in_progress"
        self.save(
            update_fields=[
                "assigned_to",
                "assigned_by",
                "assigned_at",
                "status",
                "updated_at",
            ]
        )

    def mark_payment_received(self, received_by):
        """Mark payment as received"""
        self.payment_received_by = received_by
        self.payment_received_at = timezone.now()
        self.status = "payment_confirmed"
        self.save(
            update_fields=[
                "payment_received_by",
                "payment_received_at",
                "status",
                "updated_at",
            ]
        )

    def mark_completed(self, completed_by):
        """Mark order as completed"""
        self.completed_by = completed_by
        self.completed_at = timezone.now()
        self.status = "completed"
        self.save(
            update_fields=["completed_by", "completed_at", "status", "updated_at"]
        )

    def save(self, *args, **kwargs):
        # Auto-set branch from bot_user if not set
        if not self.branch and self.bot_user and self.bot_user.branch:
            self.branch = self.bot_user.branch

        # Validate that the selected language is available in the product's category
        if self.language and self.product and self.product.category:
            available_languages = self.product.category.languages.all()
            if (
                available_languages.exists()
                and not available_languages.filter(pk=self.language.pk).exists()
            ):
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {
                        "language": _(
                            "Selected language is not available for this product's category."
                        )
                    }
                )

        # Update total pages before calculating price
        if hasattr(self, "_update_pages") and self._update_pages:
            self.update_total_pages()

        # Auto-calculate total price based on pages and user type
        if not self.total_price or self.total_pages:
            self.total_price = self.calculated_price

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]


@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    """Track status changes before save"""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def send_status_notification(sender, instance, created, **kwargs):
    """Send notification after status change"""
    if not created and hasattr(instance, "_old_status"):
        old_status = instance._old_status
        new_status = instance.status

        if old_status != new_status:
            # Import here to avoid circular imports
            try:
                from bot.main import send_order_status_notification

                send_order_status_notification(instance, old_status, new_status)
            except Exception as e:
                print(f"[ERROR] Failed to send status notification: {e}")
                import traceback

                traceback.print_exc()
