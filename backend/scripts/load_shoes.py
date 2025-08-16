import os
import django
import json
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoe_shopper.settings')
django.setup()

from core.models import Shoe

def load_shoes():
    # Path to backup file (moved to data directory)
    backup_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'shoes_backup.json')
    with open(backup_path, 'r') as f:
        shoes_data = json.load(f)
    
    print(f"Loading {len(shoes_data)} shoes...")
    
    for shoe_data in shoes_data:
        # Remove the 'id' field to let Django auto-assign
        if 'id' in shoe_data:
            del shoe_data['id']
            
        shoe, created = Shoe.objects.get_or_create(
            company=shoe_data['company'],
            model=shoe_data['model'],
            us_size=shoe_data['us_size'],
            defaults=shoe_data
        )
        
        if created:
            print(f"Created: {shoe.company} {shoe.model} ({shoe.us_size})")
        else:
            print(f"Exists: {shoe.company} {shoe.model} ({shoe.us_size})")
    
    print(f"\nTotal shoes in database: {Shoe.objects.count()}")
    print(f"Active shoes: {Shoe.objects.filter(is_active=True).count()}")

if __name__ == "__main__":
    load_shoes()