# Generated to merge conflicting migration branches

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_replace_shoe_image_with_url'),
        ('core', '0007_remove_shoe_shoe_image_shoe_image_url'),
    ]

    operations = [
        # No operations needed, this just merges the branches
    ]