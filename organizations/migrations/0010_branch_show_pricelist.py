# Generated manually on 2025-12-04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0009_add_branch_settings_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="branch",
            name="show_pricelist",
            field=models.BooleanField(
                default=False,
                help_text="Show price list button in Telegram bot for this branch",
                verbose_name="Show Price List",
            ),
        ),
    ]
