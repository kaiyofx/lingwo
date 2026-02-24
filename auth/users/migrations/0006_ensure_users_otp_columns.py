# Ensure users table has OTP and OTP_only columns (model uses db_column="OTP" / "OTP_only").
# Handles DBs where 0001 never created the table or 0003/0004 left no OTP columns.

from django.db import migrations


def ensure_otp_columns(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for sql in [
            'ALTER TABLE users ADD COLUMN IF NOT EXISTS "OTP" BOOLEAN NOT NULL DEFAULT FALSE',
            'ALTER TABLE users ADD COLUMN IF NOT EXISTS "OTP_only" BOOLEAN NOT NULL DEFAULT FALSE',
        ]:
            cursor.execute(sql)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_ensure_role_table"),
    ]

    operations = [
        migrations.RunPython(ensure_otp_columns, noop),
    ]
