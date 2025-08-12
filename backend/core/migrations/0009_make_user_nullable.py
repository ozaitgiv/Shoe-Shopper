# Generated manually for guest support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_shoe_shoe_image_shoe_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='footimage',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='foot_images', to='auth.user'),
        ),
    ]