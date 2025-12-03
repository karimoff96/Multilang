# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0006_allow_null_role'),
    ]

    operations = [
        # Add bot fields to TranslationCenter
        migrations.AddField(
            model_name='translationcenter',
            name='bot_token',
            field=models.CharField(
                blank=True,
                help_text='Telegram Bot Token for this center (unique, superuser only)',
                max_length=100,
                null=True,
                unique=True,
                verbose_name='Bot Token',
            ),
        ),
        migrations.AddField(
            model_name='translationcenter',
            name='company_orders_channel_id',
            field=models.CharField(
                blank=True,
                help_text='Telegram channel ID for all company orders',
                max_length=50,
                null=True,
                verbose_name='Company Orders Channel ID',
            ),
        ),
        # Add channel fields to Branch
        migrations.AddField(
            model_name='branch',
            name='b2c_orders_channel_id',
            field=models.CharField(
                blank=True,
                help_text='Telegram channel ID for B2C (individual customer) orders',
                max_length=50,
                null=True,
                verbose_name='B2C Orders Channel ID',
            ),
        ),
        migrations.AddField(
            model_name='branch',
            name='b2b_orders_channel_id',
            field=models.CharField(
                blank=True,
                help_text='Telegram channel ID for B2B (agency/business) orders',
                max_length=50,
                null=True,
                verbose_name='B2B Orders Channel ID',
            ),
        ),
    ]
