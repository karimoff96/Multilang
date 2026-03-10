from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0024_translationcenter_payme_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="translationcenter",
            name="payme_sandbox",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Use Payme test environment (test.paycom.uz). "
                    "Enable while testing; disable when going live with production credentials."
                ),
                verbose_name="Payme Sandbox Mode",
            ),
        ),
    ]
