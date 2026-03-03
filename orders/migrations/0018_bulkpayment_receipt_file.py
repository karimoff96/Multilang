from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0017_order_deadline'),
    ]

    operations = [
        migrations.AddField(
            model_name='bulkpayment',
            name='receipt_file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='bulk_payment_receipts/',
                verbose_name='Receipt File',
                help_text='Uploaded receipt image/PDF for card payments',
            ),
        ),
    ]
