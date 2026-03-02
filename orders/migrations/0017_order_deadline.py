from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0016_order_name_clarifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='deadline',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Deadline',
                help_text='Optional date by which the order should be completed',
            ),
        ),
    ]
