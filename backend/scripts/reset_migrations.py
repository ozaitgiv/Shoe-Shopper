#!/usr/bin/env python
"""
NUCLEAR MIGRATION RESET SCRIPT
This script resets Django migrations to a clean state and applies the correct migration.

IMPORTANT: Only run this on production after backing up the database!
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

def main():
    """Reset migrations to clean state"""
    
    print("🚨 MIGRATION NUCLEAR RESET SCRIPT")
    print("=" * 50)
    print("⚠️  WARNING: This will modify migration records!")
    print("⚠️  Ensure you have backed up the database!")
    print("")
    
    # Safety check
    confirm = input("Have you backed up the database? (type 'YES' to continue): ")
    if confirm != 'YES':
        print("❌ Aborting. Please backup database first!")
        return False
    
    print("📋 Checking data before reset...")
    from core.models import FootImage, Shoe
    
    try:
        foot_count = FootImage.objects.count()
        shoe_count = Shoe.objects.count()
        print(f"   Current data: {foot_count} FootImages, {shoe_count} Shoes")
        
        if foot_count > 0 or shoe_count > 0:
            confirm2 = input(f"Found {foot_count + shoe_count} records. Continue? (type 'YES'): ")
            if confirm2 != 'YES':
                print("❌ Aborting for data safety!")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not check data counts: {e}")
        confirm3 = input("Continue anyway? (type 'YES'): ")
        if confirm3 != 'YES':
            print("❌ Aborting!")
            return False
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoe_shopper.settings')
    django.setup()
    
    from django.core.management.commands.migrate import Command as MigrateCommand
    from django.db.migrations.recorder import MigrationRecorder
    
    print("\n1. Current migration state:")
    execute_from_command_line(['manage.py', 'showmigrations', 'core'])
    
    print("\n2. Resetting migration history to 0006...")
    
    # Get migration recorder
    recorder = MigrationRecorder(connection)
    
    # Delete problematic migration records
    problematic_migrations = [
        ('core', '0007_add_missing_fields'),
        ('core', '0007_remove_shoe_shoe_image_shoe_image_url'), 
        ('core', '0008_footimage_area_sqin_footimage_perimeter_inches_and_more'),
        ('core', '0008_merge_migration_branches'),
        ('core', '0009_make_user_nullable'),
        ('core', '0010_make_user_nullable_sql'),
        ('core', '0011_footimage_area_sqin_footimage_perimeter_inches_and_more'),
        ('core', '0012_merge_20250812_0201'),
        ('core', '0012_merge_20250812_0241'),
    ]
    
    for app_label, migration_name in problematic_migrations:
        try:
            recorder.record_unapplied(app_label, migration_name)
            print(f"   ✓ Removed: {migration_name}")
        except Exception as e:
            print(f"   - Not found: {migration_name}")
    
    print("\n3. After reset migration state:")
    execute_from_command_line(['manage.py', 'showmigrations', 'core'])
    
    print("\n4. Applying clean migration...")
    try:
        execute_from_command_line(['manage.py', 'migrate', 'core'])
        print("   ✅ Migration successful!")
    except Exception as e:
        print(f"   ❌ Migration failed: {e}")
        return False
    
    print("\n5. Final migration state:")
    execute_from_command_line(['manage.py', 'showmigrations', 'core'])
    
    print("\n🎉 MIGRATION RESET COMPLETE!")
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)