# Ensure users table has Telegram linkage columns.

from django.db import migrations


def ensure_telegram_columns(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for sql in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(255) NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS users_telegram_id_unique_idx ON users (telegram_id) WHERE telegram_id IS NOT NULL",
        ]:
            cursor.execute(sql)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_ensure_users_otp_columns"),
    ]

    operations = [
        migrations.RunPython(ensure_telegram_columns, noop),
    ]
