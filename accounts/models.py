import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _


class BotUser(models.Model):
    """Model for Telegram bot users (customers)"""

    LANGUAGES = (
        ("uz", "Uzbek"),
        ("ru", "Russian"),
        ("en", "English"),
    )

    # Branch relationship - customers are tied to specific branches
    branch = models.ForeignKey(
        'organizations.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_("Branch")
    )

    # Telegram user data
    user_id = models.BigIntegerField(
        unique=True, verbose_name=_("Telegram User ID"), blank=True, null=True
    )
    username = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Username")
    )
    name = models.CharField(max_length=100, verbose_name=_("Full Name"))
    phone = models.CharField(max_length=100, verbose_name=_("Phone Number"))

    # Bot interaction data
    language = models.CharField(
        max_length=100, choices=LANGUAGES, default="uz", verbose_name=_("Language")
    )
    step = models.IntegerField(default=0, verbose_name=_("Registration Step"))
    agency_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        editable=False,
        verbose_name=_("Agency Token"),
    )
    agency_link = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Agency Link")
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name=_("Is Used"),
        help_text=_("Whether this invitation link has been used"),
    )
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"))
    is_agency = models.BooleanField(default=False, verbose_name=_("Is Agency"))
    agency = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agency_users",
        verbose_name=_("Agency"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"@{self.username or self.user_id} - {self.name}"

    @property
    def display_name(self):
        """Get display name for user"""
        return self.name or f"User {self.user_id}"
    
    @property
    def full_name(self):
        """Alias for name field for compatibility"""
        return self.name

    @property
    def is_registered(self):
        """Check if user completed registration"""
        return self.is_active and bool(self.name) and bool(self.phone)

    class Meta:
        verbose_name = _("Telegram User")
        verbose_name_plural = _("Telegram Users")

    def save(self, *args, **kwargs):
        # Generate agency token and link if this is an agency user
        if self.is_agency:
            if not self.agency_token:
                self.agency_token = uuid.uuid4()
            if not self.agency_link:
                self.agency_link = self.get_agency_invite_link()
        super().save(*args, **kwargs)

    def get_agency_invite_link(self):
        """Generate a unique invite link for the agency"""
        if not self.is_agency:
            return None

        # Get bot username from environment variables
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "").strip()
        if not bot_username:
            raise ValueError("TELEGRAM_BOT_USERNAME environment variable is not set")

        # Remove @ if present and ensure it's included in the final URL
        bot_username = bot_username.lstrip("@")
        return f"https://t.me/{bot_username}?start=agency_{self.agency_token}"

    @classmethod
    def get_agency_by_token(cls, token):
        """
        Get agency by invitation token if it exists and hasn't been used yet.
        Marks the token as used if found.
        """
        from django.db import transaction
        import traceback

        try:
            print(f"[DEBUG] Looking for agency with token: {token}")

            # First, let's check if the agency exists at all (regardless of is_used)
            all_agencies = cls.objects.filter(agency_token=token, is_agency=True)
            print(f"[DEBUG] Found {all_agencies.count()} agency(ies) with this token")

            if all_agencies.exists():
                first_agency = all_agencies.first()
                print(
                    f"[DEBUG] Agency found: {first_agency.name}, is_used={first_agency.is_used}"
                )

                if first_agency.is_used:
                    print(f"[WARNING] Agency token already used!")
                    return None

            with transaction.atomic():
                # Use select_for_update to lock the row
                agency = cls.objects.select_for_update().get(
                    agency_token=token,
                    is_agency=True,
                    is_used=False,  # Only get unused tokens
                )
                print(
                    f"[DEBUG] Successfully retrieved unused agency: {agency.name} (ID: {agency.id})"
                )

                # Mark as used
                agency.is_used = True
                agency.save(update_fields=["is_used", "updated_at"])
                print(f"[DEBUG] Marked agency {agency.name} as used")

                return agency
        except cls.DoesNotExist:
            print(f"[WARNING] No unused agency found with token: {token}")
            return None
        except ValueError as e:
            print(f"[ERROR] ValueError in get_agency_by_token: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error in get_agency_by_token: {e}")
            traceback.print_exc()
            return None
