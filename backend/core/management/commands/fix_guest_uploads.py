from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix guest uploads by making user_id nullable - bypasses migration system'

    def handle(self, *args, **options):
        self.stdout.write('Fixing guest uploads by making user_id nullable...')
        
        try:
            with connection.cursor() as cursor:
                # Check current schema
                cursor.execute("""
                    SELECT column_name, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'core_footimage' AND column_name = 'user_id';
                """)
                
                result = cursor.fetchone()
                if result:
                    column_name, is_nullable = result
                    self.stdout.write(f'Current user_id column: nullable = {is_nullable}')
                    
                    if is_nullable == 'NO':
                        self.stdout.write('Making user_id column nullable...')
                        cursor.execute('ALTER TABLE core_footimage ALTER COLUMN user_id DROP NOT NULL;')
                        self.stdout.write(self.style.SUCCESS('✅ user_id column is now nullable!'))
                    else:
                        self.stdout.write(self.style.SUCCESS('✅ user_id column is already nullable!'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Could not find user_id column'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            
        self.stdout.write('Done!')