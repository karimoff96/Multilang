from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0013_add_general_expense_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalexpense',
            name='payment_type',
            field=models.CharField(
                choices=[('cash', 'Cash'), ('card', 'Card'), ('nasiya', 'Nasiya (Credit)')],
                default='cash',
                max_length=10,
                verbose_name='Payment Type',
            ),
        ),
        migrations.AddField(
            model_name='generalexpense',
            name='nasiya_deadline',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Nasiya Deadline',
                help_text='Repayment deadline for credit expenses.',
            ),
        ),
        migrations.AddField(
            model_name='generalexpense',
            name='is_paid',
            field=models.BooleanField(
                default=True,
                verbose_name='Paid',
                help_text='Mark as paid once a nasiya (credit) expense is settled.',
            ),
        ),
        migrations.AddField(
            model_name='generalexpense',
            name='vendor',
            field=models.CharField(
                blank=True,
                default='',
                max_length=200,
                verbose_name='Vendor / Supplier',
                help_text='Who was paid — shop, person, company, etc.',
            ),
        ),
    ]
