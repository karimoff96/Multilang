from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0020_additional_files"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymeTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payme_transaction_id", models.CharField(max_length=64, unique=True, verbose_name="Payme Transaction ID")),
                ("amount_tiyin", models.BigIntegerField(default=0, verbose_name="Amount (tiyin)")),
                ("account", models.JSONField(blank=True, default=dict, verbose_name="Account Payload")),
                ("state", models.IntegerField(db_index=True, default=0, help_text="Payme transaction state: 1=created, 2=performed, -1/-2 canceled", verbose_name="State")),
                ("create_time_ms", models.BigIntegerField(blank=True, null=True, verbose_name="Create Time (ms)")),
                ("perform_time_ms", models.BigIntegerField(blank=True, null=True, verbose_name="Perform Time (ms)")),
                ("cancel_time_ms", models.BigIntegerField(blank=True, null=True, verbose_name="Cancel Time (ms)")),
                ("cancel_reason", models.IntegerField(blank=True, null=True, verbose_name="Cancel Reason")),
                ("checkout_url", models.CharField(blank=True, max_length=500, verbose_name="Checkout URL")),
                ("detail", models.JSONField(blank=True, null=True, verbose_name="Receipt Detail Payload")),
                ("raw_request", models.JSONField(blank=True, null=True, verbose_name="Last Request Payload")),
                ("raw_response", models.JSONField(blank=True, null=True, verbose_name="Last Response Payload")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="payme_transactions", to="orders.order", verbose_name="Order")),
            ],
            options={
                "verbose_name": "Payme Transaction",
                "verbose_name_plural": "Payme Transactions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="paymetransaction",
            index=models.Index(fields=["payme_transaction_id"], name="orders_paym_payme_tr_7e8f90_idx"),
        ),
        migrations.AddIndex(
            model_name="paymetransaction",
            index=models.Index(fields=["state"], name="orders_paym_state_aa5929_idx"),
        ),
        migrations.AddIndex(
            model_name="paymetransaction",
            index=models.Index(fields=["created_at"], name="orders_paym_created__15244a_idx"),
        ),
    ]
