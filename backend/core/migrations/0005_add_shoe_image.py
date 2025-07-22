from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_enhance_shoe_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoe',
            name='shoe_image',
            field=models.ImageField(
                blank=True, 
                help_text='Upload product image of the shoe', 
                null=True, 
                upload_to='shoe_images/'
            ),
        ),
    ]