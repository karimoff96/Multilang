"""
Management command to encrypt plain-text credentials stored in
TranslationCenter.bot_token, payme_secret_key, and payme_secret_key_prod.

Run this ONCE after setting FIELD_ENCRYPTION_KEY in .env and applying
the 0027_encrypt_sensitive_fields migration.

    python manage.py encrypt_credentials [--dry-run]

Options:
    --dry-run   Print what would be changed without writing to the database.

The command is idempotent: already-encrypted values are left unchanged.
"""

from django.core.management.base import BaseCommand
from core.fields import _FERNET_PREFIX, encrypt_value


class Command(BaseCommand):
    help = "Encrypt plain-text credentials in TranslationCenter (run once after migration 0027)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Show what would be encrypted without writing to the database.",
        )

    def handle(self, *args, **options):
        from django.conf import settings
        from organizations.models import TranslationCenter

        dry_run = options["dry_run"]

        key = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or ""
        if not key:
            self.stderr.write(
                self.style.ERROR(
                    "FIELD_ENCRYPTION_KEY is not set in settings / .env. "
                    "Generate one with:\n"
                    "  python -c \"from cryptography.fernet import Fernet; "
                    "print(Fernet.generate_key().decode())\""
                )
            )
            return

        FIELDS = ["bot_token", "payme_secret_key", "payme_secret_key_prod"]
        centers = TranslationCenter.objects.all()
        encrypted_count = 0
        skipped_count = 0

        for center in centers:
            changed_fields = []
            for field_name in FIELDS:
                value = getattr(center, field_name, None)
                if not value:
                    continue
                if value.startswith(_FERNET_PREFIX):
                    skipped_count += 1
                    continue  # Already encrypted
                encrypted = encrypt_value(value)
                if not dry_run:
                    setattr(center, field_name, encrypted)
                changed_fields.append(field_name)
                encrypted_count += 1

            if changed_fields and not dry_run:
                # Save only the changed fields plus updated_at
                center.save(update_fields=changed_fields + ["updated_at"])
                self.stdout.write(
                    f"  Encrypted center #{center.pk} [{center.name}]: {', '.join(changed_fields)}"
                )
            elif changed_fields and dry_run:
                self.stdout.write(
                    f"  [DRY-RUN] Would encrypt center #{center.pk} [{center.name}]: "
                    f"{', '.join(changed_fields)}"
                )

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{prefix}Done. "
                f"Encrypted: {encrypted_count} field(s). "
                f"Already encrypted / empty: {skipped_count} field(s)."
            )
        )
        if dry_run:
            self.stdout.write(
                "Re-run without --dry-run to apply changes."
            )
