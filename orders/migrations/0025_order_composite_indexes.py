"""
Add composite indexes to the orders_order table for the most common
query patterns used throughout the dashboard:

  • (branch_id, status, created_at) — per-branch order list with status filter
  • (status, created_at)           — platform-wide order list with status filter
  • (assigned_to_id, status)        — "my orders" view

Uses CREATE INDEX CONCURRENTLY on PostgreSQL so no full table lock is
acquired during the migration (requires atomic = False).
SQLite does not support CONCURRENTLY; it falls back to a plain
CREATE INDEX statement that is safe because SQLite tests always run on
an empty throw-away database.
"""

from django.db import migrations, connection


def _pg_index(name, cols):
    return f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON orders_order ({cols});"


def _sqlite_index(name, cols):
    return f"CREATE INDEX IF NOT EXISTS {name} ON orders_order ({cols});"


def _index_sql(name, cols):
    vendor = connection.vendor
    if vendor == "postgresql":
        return _pg_index(name, cols)
    return _sqlite_index(name, cols)


def _drop_sql(name):
    return f"DROP INDEX IF EXISTS {name};"


def _apply_indexes(apps, schema_editor):
    indexes = [
        ("orders_order_branch_status_created_idx", "branch_id, status, created_at DESC"),
        ("orders_order_status_created_idx", "status, created_at DESC"),
        ("orders_order_assignedto_status_idx", "assigned_to_id, status"),
    ]
    for name, cols in indexes:
        schema_editor.execute(_index_sql(name, cols))


def _drop_indexes(apps, schema_editor):
    names = [
        "orders_order_branch_status_created_idx",
        "orders_order_status_created_idx",
        "orders_order_assignedto_status_idx",
    ]
    for name in names:
        schema_editor.execute(_drop_sql(name))


class Migration(migrations.Migration):

    # Must be non-atomic so CONCURRENTLY can run outside a transaction on PG
    atomic = False

    dependencies = [
        ("orders", "0024_backfill_payment_source_payme"),
    ]

    operations = [
        migrations.RunPython(_apply_indexes, reverse_code=_drop_indexes),
    ]
