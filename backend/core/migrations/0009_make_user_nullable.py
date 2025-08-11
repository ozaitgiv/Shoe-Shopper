# Generated manually for guest support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_merge_migration_branches'),
    ]

    operations = [
        migrations.AlterField(
            model_name='footimage',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='foot_images', to='auth.user'),
        ),
    ]