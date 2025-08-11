# Force make user_id nullable using raw SQL

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_make_user_nullable'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_footimage ALTER COLUMN user_id DROP NOT NULL;",
            reverse_sql="ALTER TABLE core_footimage ALTER COLUMN user_id SET NOT NULL;",
        ),
    ]