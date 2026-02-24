# Ensure role table exists (handles DBs where migration state and schema were out of sync).

from django.db import migrations


def ensure_role_table(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE
            )
        """)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_drop_duplicate_otp_columns"),
    ]

    operations = [
        migrations.RunPython(ensure_role_table, noop),
    ]
