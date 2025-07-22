import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Ensure admin user exists (safe to run multiple times)'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@shoeshopper.com'
        password = os.environ.get('ADMIN_PASSWORD', 'shoeshopper123')
        
        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.SUCCESS(f'Admin user "{username}" already exists')
            )
            return
        
        # Create the admin user
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{username}"')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {e}')
            )