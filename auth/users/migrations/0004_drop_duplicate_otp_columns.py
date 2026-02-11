# Drop duplicate lowercase otp/otp_only columns added by 0003.
# The table already had "OTP" and "OTP_only" from 0001; the model now uses db_column
# to target those, so we remove the duplicate lowercase columns to avoid NOT NULL on "OTP".

from django.db import migrations


def drop_duplicate_columns(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        for sql in [
            'ALTER TABLE users DROP COLUMN IF EXISTS otp',
            'ALTER TABLE users DROP COLUMN IF EXISTS otp_only',
        ]:
            cursor.execute(sql)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_add_missing_user_columns"),
    ]

    operations = [
        migrations.RunPython(drop_duplicate_columns, noop),
    ]
