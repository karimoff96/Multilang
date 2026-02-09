from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0010_populate_language_translations"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="written_verification_required",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "If enabled, the bot will ask users to type full names from their documents to avoid misspelling handwritten names."
                ),
                verbose_name="Written Verification Required",
            ),
        ),
    ]
