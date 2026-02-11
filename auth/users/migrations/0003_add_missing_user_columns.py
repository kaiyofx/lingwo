from django.db import migrations


def add_columns(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        for sql in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_only BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS lockout_time TIMESTAMP WITH TIME ZONE NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_username_change TIMESTAMP WITH TIME ZONE NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS requested_username VARCHAR(150) NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS requested_email VARCHAR(254) NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_email_change TIMESTAMP WITH TIME ZONE NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id BIGINT NULL DEFAULT 2",
        ]:
            try:
                cursor.execute(sql)
            except Exception:
                pass


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_role_alter_absuser_managed"),
    ]

    operations = [
        migrations.RunPython(add_columns, noop),
    ]
