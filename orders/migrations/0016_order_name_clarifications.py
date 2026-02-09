from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0015_order_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="name_clarifications",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Full names typed by the user to avoid misreading handwriting",
                verbose_name="Name Clarifications",
            ),
        ),
    ]
