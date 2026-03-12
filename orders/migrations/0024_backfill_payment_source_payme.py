from django.db import migrations


def backfill_payme_payment_source(apps, schema_editor):
    """
    Set payment_source='payme' on all orders that have a completed
    PaymeTransaction (state=2 = STATE_PERFORMED).
    """
    Order = apps.get_model("orders", "Order")
    PaymeTransaction = apps.get_model("orders", "PaymeTransaction")

    payme_order_ids = PaymeTransaction.objects.filter(
        state=2  # STATE_PERFORMED
    ).values_list("order_id", flat=True).distinct()

    Order.objects.filter(id__in=list(payme_order_ids)).update(payment_source="payme")


def reverse_backfill(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(payment_source="payme").update(payment_source="manual")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0023_add_payment_source_to_order"),
    ]

    operations = [
        migrations.RunPython(backfill_payme_payment_source, reverse_backfill),
    ]
