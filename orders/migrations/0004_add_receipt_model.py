# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('organizations', '0001_initial'),
        ('orders', '0003_partial_payment_support'),
    ]

    operations = [
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, help_text='Receipt image or document', null=True, upload_to='receipts/%Y/%m/', verbose_name='Receipt File')),
                ('telegram_file_id', models.CharField(blank=True, help_text='File ID from Telegram for quick access', max_length=255, null=True, verbose_name='Telegram File ID')),
                ('amount', models.DecimalField(decimal_places=2, default=0, help_text='Amount claimed in this receipt', max_digits=12, verbose_name='Amount')),
                ('verified_amount', models.DecimalField(decimal_places=2, default=0, help_text='Amount verified by admin', max_digits=12, verbose_name='Verified Amount')),
                ('source', models.CharField(choices=[('bot', 'Bot (User Upload)'), ('admin', 'Admin Upload'), ('phone', 'Phone Confirmation')], default='bot', max_length=20, verbose_name='Source')),
                ('status', models.CharField(choices=[('pending', 'Pending Verification'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending', max_length=20, verbose_name='Status')),
                ('comment', models.TextField(blank=True, help_text='Admin notes or rejection reason', null=True, verbose_name='Comment')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('verified_at', models.DateTimeField(blank=True, null=True, verbose_name='Verified At')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='orders.order', verbose_name='Order')),
                ('uploaded_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_receipts', to='accounts.botuser', verbose_name='Uploaded By (User)')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_receipts', to='organizations.adminuser', verbose_name='Verified By')),
            ],
            options={
                'verbose_name': 'Receipt',
                'verbose_name_plural': 'Receipts',
                'ordering': ['-created_at'],
            },
        ),
    ]
