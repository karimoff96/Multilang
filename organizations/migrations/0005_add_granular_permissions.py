# Generated migration for granular order permissions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_role_rbac_permissions'),
    ]

    operations = [
        # New Order-related permissions
        migrations.AddField(
            model_name='role',
            name='can_view_own_orders',
            field=models.BooleanField(default=True, verbose_name='Can view own orders'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_edit_orders',
            field=models.BooleanField(default=False, verbose_name='Can edit orders'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_delete_orders',
            field=models.BooleanField(default=False, verbose_name='Can delete orders'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_update_order_status',
            field=models.BooleanField(default=False, verbose_name='Can update order status'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_complete_orders',
            field=models.BooleanField(default=False, verbose_name='Can complete orders'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_cancel_orders',
            field=models.BooleanField(default=False, verbose_name='Can cancel orders'),
        ),
        # New Financial permissions
        migrations.AddField(
            model_name='role',
            name='can_view_financial_reports',
            field=models.BooleanField(default=False, verbose_name='Can view financial reports'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_apply_discounts',
            field=models.BooleanField(default=False, verbose_name='Can apply discounts'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_refund_orders',
            field=models.BooleanField(default=False, verbose_name='Can refund orders'),
        ),
        # New Reports & Analytics permissions
        migrations.AddField(
            model_name='role',
            name='can_view_analytics',
            field=models.BooleanField(default=False, verbose_name='Can view analytics'),
        ),
        # New Customer permissions
        migrations.AddField(
            model_name='role',
            name='can_view_customer_details',
            field=models.BooleanField(default=False, verbose_name='Can view customer details'),
        ),
        # Update can_manage_orders help_text
        migrations.AlterField(
            model_name='role',
            name='can_manage_orders',
            field=models.BooleanField(default=False, help_text='Full order management - overrides other order permissions', verbose_name='Can manage orders (full access)'),
        ),
    ]
