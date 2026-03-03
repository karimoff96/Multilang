import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0018_bulkpayment_receipt_file'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderPriceChange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Old Price')),
                ('new_price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='New Price')),
                ('reason', models.TextField(help_text='Why was the price changed?', verbose_name='Reason')),
                ('changed_at', models.DateTimeField(auto_now_add=True, verbose_name='Changed At')),
                ('changed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='price_changes_made',
                    to='organizations.adminuser',
                    verbose_name='Changed By',
                )),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='price_changes',
                    to='orders.order',
                    verbose_name='Order',
                )),
            ],
            options={
                'verbose_name': 'Order Price Change',
                'verbose_name_plural': 'Order Price Changes',
                'ordering': ['-changed_at'],
            },
        ),
    ]
