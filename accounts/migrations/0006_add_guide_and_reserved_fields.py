# Generated manually on 2025-12-04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_add_center_to_botuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="additionalinfo",
            name="guide",
            field=models.URLField(
                blank=True,
                help_text="URL to a guide (Telegram message, YouTube video, documentation, etc.)",
                max_length=500,
                null=True,
                verbose_name="Guide Link",
            ),
        ),
        migrations.AddField(
            model_name="additionalinfo",
            name="reserved_field_1",
            field=models.CharField(
                blank=True,
                help_text="Reserved for future use",
                max_length=500,
                null=True,
                verbose_name="Reserved Field 1",
            ),
        ),
        migrations.AddField(
            model_name="additionalinfo",
            name="reserved_field_2",
            field=models.CharField(
                blank=True,
                help_text="Reserved for future use",
                max_length=500,
                null=True,
                verbose_name="Reserved Field 2",
            ),
        ),
        migrations.AddField(
            model_name="additionalinfo",
            name="reserved_field_3",
            field=models.CharField(
                blank=True,
                help_text="Reserved for future use",
                max_length=500,
                null=True,
                verbose_name="Reserved Field 3",
            ),
        ),
    ]
