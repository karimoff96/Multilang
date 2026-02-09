from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_short_filenames'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders_created', to='organizations.adminuser', verbose_name='Created By'),
        ),
    ]
