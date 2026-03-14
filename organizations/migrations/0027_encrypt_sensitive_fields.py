"""
Change bot_token, payme_secret_key, and payme_secret_key_prod to
core.fields.EncryptedCharField (backed by TextField).

SAFETY:
  • Existing plain-text values remain readable — EncryptedCharField
    detects non-encrypted values and returns them as-is.
  • Values are encrypted automatically next time each record is saved.
  • To encrypt all existing values in one shot, run:
        python manage.py encrypt_credentials
  • No data is modified by this migration itself.
"""

import core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0026_translationcenter_payme_secret_key_prod"),
    ]

    operations = [
        migrations.AlterField(
            model_name="translationcenter",
            name="bot_token",
            field=core.fields.EncryptedCharField(
                blank=True,
                max_length=500,
                null=True,
                unique=True,
                verbose_name="Bot Token",
                help_text="Telegram Bot Token for this center (unique, superuser only)",
            ),
        ),
        migrations.AlterField(
            model_name="translationcenter",
            name="payme_secret_key",
            field=core.fields.EncryptedCharField(
                blank=True,
                max_length=500,
                verbose_name="Payme Sandbox Secret Key",
                help_text="Payme secret key for the sandbox/test environment (test.paycom.uz).",
            ),
        ),
        migrations.AlterField(
            model_name="translationcenter",
            name="payme_secret_key_prod",
            field=core.fields.EncryptedCharField(
                blank=True,
                max_length=500,
                verbose_name="Payme Production Secret Key",
                help_text="Payme secret key for the production environment (checkout.paycom.uz).",
            ),
        ),
    ]
