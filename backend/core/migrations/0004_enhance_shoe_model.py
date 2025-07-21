from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_shoe'),
    ]

    operations = [
        # Update function field to use choices
        migrations.AlterField(
            model_name='shoe',
            name='function',
            field=models.CharField(
                choices=[('casual', 'Casual'), ('hiking', 'Hiking'), ('work', 'Work'), ('running', 'Running')], 
                max_length=20
            ),
        ),
        
        # Add insole processing fields
        migrations.AddField(
            model_name='shoe',
            name='insole_image',
            field=models.ImageField(
                blank=True, 
                help_text='Upload insole photo to automatically calculate measurements', 
                null=True, 
                upload_to='insole_images/'
            ),
        ),
        migrations.AddField(
            model_name='shoe',
            name='insole_length',
            field=models.FloatField(blank=True, help_text='Length in inches', null=True),
        ),
        migrations.AddField(
            model_name='shoe',
            name='insole_width',
            field=models.FloatField(blank=True, help_text='Width in inches', null=True),
        ),
        migrations.AddField(
            model_name='shoe',
            name='insole_perimeter',
            field=models.FloatField(blank=True, help_text='Perimeter in inches', null=True),
        ),
        migrations.AddField(
            model_name='shoe',
            name='insole_area',
            field=models.FloatField(blank=True, help_text='Area in square inches', null=True),
        ),
    ]