# Соответствие моделям: managed=False (таблицы уже созданы миграцией 0001)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ABSUser",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="Role",
            options={"managed": False},
        ),
    ]
