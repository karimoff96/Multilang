# Generated migration for RBAC permission updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_role_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='can_create_orders',
            field=models.BooleanField(default=False, verbose_name='Can create orders'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_view_staff',
            field=models.BooleanField(default=False, verbose_name='Can view staff details'),
        ),
    ]
