# 🚨 PRODUCTION MIGRATION FIX - NUCLEAR OPTION

## Problem
Multiple conflicting Django migrations causing deployment failures:
```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph
```

## Solution
**Nuclear reset** to clean migration state and apply correct migration.

## ⚠️ CRITICAL PREREQUISITES

### 🛡️ MANDATORY DATABASE BACKUP
**DO NOT PROCEED WITHOUT BACKUP!** This operation modifies migration records.

1. **BACKUP DATABASE** using multiple methods
2. **VERIFY BACKUP** can be restored
3. **DOWNLOAD BACKUP** to local machine
4. Ensure you have the latest development branch code
5. Have database access to production environment

## 🔥 EXECUTION STEPS

### Step 1: MANDATORY Database Backup (Multiple Methods)

#### Option A: Platform Backup (Recommended)
```bash
# Railway: Use dashboard backup feature
# Render: Use dashboard backup feature
# Or your platform's native backup
```

#### Option B: Direct PostgreSQL Backup
```bash
# Full database backup with timestamp
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file exists and has content
ls -lh backup_*.sql
head -20 backup_*.sql
```

#### Option C: Django Data Backup
```bash
# Export data as JSON fixtures (safer for Django)
python manage.py dumpdata --natural-foreign --natural-primary > full_backup_$(date +%Y%m%d_%H%M%S).json

# Backup just the core app data
python manage.py dumpdata core > core_backup_$(date +%Y%m%d_%H%M%S).json
```

### Step 1.5: VERIFY BACKUP
```bash
# Check backup file size (should not be 0 bytes)
ls -lh backup_*.sql
ls -lh *_backup_*.json

# Test JSON backup validity
python -m json.tool core_backup_*.json > /dev/null && echo "JSON backup valid" || echo "JSON backup INVALID"
```

### Step 2: Deploy Latest Code
```bash
# Pull latest development branch
git pull origin development
```

### Step 3: Run Nuclear Reset Script
```bash
# In production environment
cd /app
python reset_migrations.py
```

### Step 4: Verify Success
```bash
# Check migration status
python manage.py showmigrations core

# Should show:
# [X] 0001_initial
# [X] 0002_footimage_error_message_footimage_length_inches_and_more
# [X] 0003_shoe
# [X] 0004_enhance_shoe_model
# [X] 0005_add_shoe_image
# [X] 0004_footimage_user
# [X] 0006_merge_0004_footimage_user_0005_add_shoe_image
# [X] 0007_replace_shoe_image_with_url
# [X] 0008_footimage_area_sqin_footimage_perimeter_inches_and_more
```

### Step 5: Test Application
```bash
# Test basic functionality
python manage.py check
python manage.py shell -c "
from core.models import FootImage, Shoe
print('Models working:', FootImage.objects.count(), Shoe.objects.count())
"
```

## 🎯 ALTERNATIVE: Manual Reset (if script fails)

If the reset script fails, run these Django commands manually:

```bash
# Reset migration records
python manage.py shell -c "
from django.db.migrations.recorder import MigrationRecorder
from django.db import connection

recorder = MigrationRecorder(connection)

# Remove bad migration records
bad_migrations = [
    ('core', '0007_add_missing_fields'),
    ('core', '0008_merge_migration_branches'), 
    ('core', '0009_make_user_nullable'),
    ('core', '0010_make_user_nullable_sql'),
    ('core', '0011_footimage_area_sqin_footimage_perimeter_inches_and_more'),
    ('core', '0012_merge_20250812_0201'),
    ('core', '0012_merge_20250812_0241'),
]

for app, migration in bad_migrations:
    try:
        recorder.record_unapplied(app, migration)
        print(f'Removed: {migration}')
    except:
        print(f'Not found: {migration}')
"

# Apply clean migrations
python manage.py migrate core
```

## ✅ Expected Final State

After successful reset:
- **FootImage model**: Has `area_sqin` and `perimeter_inches` fields
- **Shoe model**: Has `shoe_image_url` field (NOT `image_url`)
- **Enhanced Algorithm**: 4D scoring works with area/perimeter measurements
- **Guest Support**: FootImage.user is nullable
- **No Migration Conflicts**: Clean migration tree

## 🔍 Verification Commands

```bash
# Test enhanced algorithm
python manage.py shell -c "
from core.views import enhanced_score_shoe_4d
score = enhanced_score_shoe_4d(10.5, 4.2, 35.5, 28.3, 11.125, 4.2, 38.0, 30.0)
print(f'Enhanced algorithm score: {score}')
"

# Test model fields
python manage.py shell -c "
from core.models import FootImage, Shoe
foot = FootImage.objects.create(image='test.jpg', area_sqin=35.5, perimeter_inches=28.3)
shoe = Shoe.objects.create(company='Test', model='Test', gender='M', us_size=10, width_category='D', function='casual', price_usd=99.99, product_url='http://test.com', shoe_image_url='http://test.com/img.jpg')
print(f'FootImage area: {foot.area_sqin}')
print(f'Shoe image URL: {shoe.shoe_image_url}')
foot.delete()
shoe.delete()
"
```

## 🆘 DISASTER RECOVERY

### If Migration Reset Fails:

#### Option 1: Restore from PostgreSQL Backup
```bash
# Drop and recreate database (DANGEROUS!)
# dropdb $DATABASE_NAME  # Only if absolutely necessary
# createdb $DATABASE_NAME
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

#### Option 2: Restore from Django JSON Backup
```bash
# Reset database to clean state
python manage.py flush --noinput

# Restore from JSON backup
python manage.py loaddata full_backup_YYYYMMDD_HHMMSS.json
```

#### Option 3: Partial Data Recovery
```bash
# If only core app data needed
python manage.py loaddata core_backup_YYYYMMDD_HHMMSS.json
```

### Emergency Contacts
1. **Contact development team immediately**
2. **Do not attempt further fixes without backup restoration**
3. **Document exactly what happened for debugging**

## 📋 Post-Deployment Checklist

- [ ] Database backup completed
- [ ] Migration reset script executed successfully  
- [ ] All migrations showing as applied
- [ ] Enhanced algorithm functional
- [ ] Application starts without errors
- [ ] User uploads working
- [ ] Recommendations API working