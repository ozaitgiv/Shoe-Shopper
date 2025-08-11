from django.db import migrations, models

def log_migration_info(apps, schema_editor):
    """Log what's happening during migration"""
    Shoe = apps.get_model('core', 'Shoe')
    
    total_shoes = Shoe.objects.count()
    shoes_with_images = Shoe.objects.exclude(shoe_image='').count()
    
    print(f"\n=== SHOE IMAGE MIGRATION ===")
    print(f"Total shoes in database: {total_shoes}")
    print(f"Shoes with image files: {shoes_with_images}")
    print(f"Image files will be removed (not working without S3)")
    print(f"All other shoe data will be preserved")
    print(f"New shoe_image_url field will be added for future use")
    print(f"================================\n")

def reverse_log_migration_info(apps, schema_editor):
    """Reverse function - no action needed"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_merge_20250721_2035'),
    ]

    operations = [
        # Log what we're doing
        migrations.RunPython(
            log_migration_info,
            reverse_log_migration_info,
        ),
        
        # Add the new URL field
        migrations.AddField(
            model_name='shoe',
            name='shoe_image_url',
            field=models.URLField(
                blank=True, 
                help_text='URL to the shoe product image (e.g., from manufacturer website or CDN)', 
                null=True
            ),
        ),
        
        # Remove the old ImageField (this will delete the image files)
        migrations.RemoveField(
            model_name='shoe',
            name='shoe_image',
        ),
    ]