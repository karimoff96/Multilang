from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0025_translationcenter_payme_sandbox"),
    ]

    operations = [
        migrations.AlterField(
            model_name="translationcenter",
            name="payme_secret_key",
            field=models.CharField(
                blank=True,
                help_text="Payme secret key for the sandbox/test environment (test.paycom.uz).",
                max_length=200,
                verbose_name="Payme Sandbox Secret Key",
            ),
        ),
        migrations.AddField(
            model_name="translationcenter",
            name="payme_secret_key_prod",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Payme secret key for the production environment (checkout.paycom.uz).",
                max_length=200,
                verbose_name="Payme Production Secret Key",
            ),
            preserve_default=False,
        ),
    ]
