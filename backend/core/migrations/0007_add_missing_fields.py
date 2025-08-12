# Generated manually to fix migration conflicts
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def check_and_add_shoe_image_url(apps, schema_editor):
    """Safely add shoe_image_url field if it doesn't exist"""
    cursor = schema_editor.connection.cursor()
    
    try:
        # Check if shoe_image_url field exists
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='core_shoe'
        """)
        table_sql = cursor.fetchone()[0]
        
        if 'shoe_image_url' not in table_sql:
            print("Adding shoe_image_url field...")
            cursor.execute("""
                ALTER TABLE core_shoe 
                ADD COLUMN shoe_image_url varchar(200) NULL
            """)
        else:
            print("shoe_image_url field already exists, skipping...")
            
    except Exception as e:
        print(f"Error checking/adding shoe_image_url: {e}")


def reverse_check_and_add_shoe_image_url(apps, schema_editor):
    """Reverse operation - no action needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_merge_0004_footimage_user_0005_add_shoe_image'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Safely add shoe_image_url field if needed
        migrations.RunPython(
            check_and_add_shoe_image_url,
            reverse_check_and_add_shoe_image_url,
        ),
        
        # Add FootImage fields
        migrations.AddField(
            model_name='footimage',
            name='area_sqin',
            field=models.FloatField(blank=True, help_text='Foot area in square inches', null=True),
        ),
        migrations.AddField(
            model_name='footimage',
            name='perimeter_inches',
            field=models.FloatField(blank=True, help_text='Foot perimeter in inches', null=True),
        ),
        
        # Update FootImage user field to allow null
        migrations.AlterField(
            model_name='footimage',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='foot_images', to=settings.AUTH_USER_MODEL),
        ),
    ]