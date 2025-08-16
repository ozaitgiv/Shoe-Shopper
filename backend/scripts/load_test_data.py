#!/usr/bin/env python
"""
Load test data from shoes_backup.json for testing dynamic categories
"""
import json
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoe_shopper.settings')
django.setup()

from core.models import Shoe
from decimal import Decimal

def load_test_data():
    """Load shoes from backup JSON file"""
    
    # Clear existing shoes
    Shoe.objects.all().delete()
    print("Cleared existing shoes")
    
    # Load JSON data
    with open('shoes_backup.json', 'r') as f:
        shoes_data = json.load(f)
    
    print(f"Loading {len(shoes_data)} shoes...")
    
    created_count = 0
    for shoe_data in shoes_data:
        try:
            shoe = Shoe.objects.create(
                company=shoe_data['company'],
                model=shoe_data['model'],
                gender=shoe_data['gender'],
                us_size=Decimal(str(shoe_data['us_size'])),
                width_category=shoe_data['width_category'],
                function=shoe_data['function'],
                price_usd=Decimal(str(shoe_data['price_usd'])),
                product_url=shoe_data['product_url'],
                is_active=shoe_data.get('is_active', True),
                shoe_image_url=shoe_data.get('shoe_image_url', ''),
                insole_length=shoe_data.get('insole_length'),
                insole_width=shoe_data.get('insole_width'),
                insole_perimeter=shoe_data.get('insole_perimeter'),
                insole_area=shoe_data.get('insole_area'),
            )
            created_count += 1
            print(f"Created: {shoe.company} {shoe.model}")
            
        except Exception as e:
            print(f"Error creating shoe {shoe_data.get('company')} {shoe_data.get('model')}: {e}")
    
    print(f"\n✅ Successfully loaded {created_count} shoes")
    
    # Verify categories
    companies = Shoe.objects.values_list('company', flat=True).distinct().order_by('company')
    genders = Shoe.objects.values_list('gender', flat=True).distinct()
    functions = Shoe.objects.values_list('function', flat=True).distinct()
    widths = Shoe.objects.values_list('width_category', flat=True).distinct()
    
    print(f"\n📊 Categories loaded:")
    print(f"Companies ({len(companies)}): {list(companies)}")
    print(f"Genders: {list(genders)}")
    print(f"Functions: {list(functions)}")
    print(f"Widths: {list(widths)}")

if __name__ == '__main__':
    load_test_data()