from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0023_add_can_edit_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="translationcenter",
            name="payme_enabled",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Enable Payme card payment integration for this center. "
                    "When enabled, bot users are redirected to Payme checkout "
                    "instead of uploading a receipt."
                ),
                verbose_name="Payme Enabled",
            ),
        ),
        migrations.AddField(
            model_name="translationcenter",
            name="payme_merchant_id",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Per-center Payme merchant ID. Leave blank to use the "
                    "global PAYME_MERCHANT_ID setting."
                ),
                max_length=100,
                verbose_name="Payme Merchant ID",
            ),
        ),
        migrations.AddField(
            model_name="translationcenter",
            name="payme_secret_key",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Per-center Payme secret key. Leave blank to use the "
                    "global PAYME_SECRET_KEY setting."
                ),
                max_length=200,
                verbose_name="Payme Secret Key",
            ),
        ),
    ]
