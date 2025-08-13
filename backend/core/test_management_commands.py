"""
Comprehensive tests for management commands
Each test focuses on exactly one behavior
"""
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connection
from unittest.mock import patch, MagicMock
import io
import sys
import os

from core.management.commands.ensure_admin import Command as EnsureAdminCommand
from core.management.commands.fix_guest_uploads import Command as FixGuestUploadsCommand


class EnsureAdminCommandTest(TestCase):
    """Test the ensure_admin management command"""
    
    def test_ensure_admin_creates_admin_when_none_exists(self):
        """Test command creates admin user when none exists"""
        # Ensure no admin user exists
        User.objects.filter(username='admin').delete()
        
        # Capture output
        out = io.StringIO()
        
        # Run command
        call_command('ensure_admin', stdout=out)
        
        # Check admin user was created
        admin_user = User.objects.get(username='admin')
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.email, 'admin@shoeshopper.com')
        
        # Check output message
        output = out.getvalue()
        self.assertIn('Successfully created admin user "admin"', output)
        
    def test_ensure_admin_skips_when_admin_exists(self):
        """Test command skips creation when admin already exists"""
        # Create existing admin user
        User.objects.create_superuser(
            username='admin',
            email='existing@example.com',
            password='existing123'
        )
        
        out = io.StringIO()
        call_command('ensure_admin', stdout=out)
        
        # Should have only one admin user
        admin_users = User.objects.filter(username='admin')
        self.assertEqual(admin_users.count(), 1)
        
        # Check output message
        output = out.getvalue()
        self.assertIn('Admin user "admin" already exists', output)
        
    @patch.dict(os.environ, {'ADMIN_PASSWORD': 'custom_password'})
    def test_ensure_admin_uses_environment_password(self):
        """Test command uses password from environment variable"""
        User.objects.filter(username='admin').delete()
        
        out = io.StringIO()
        call_command('ensure_admin', stdout=out)
        
        admin_user = User.objects.get(username='admin')
        # Check that user was created (password validation would be complex)
        self.assertTrue(admin_user.check_password('custom_password'))
        
    def test_ensure_admin_uses_default_password_when_no_env(self):
        """Test command uses default password when no environment variable"""
        User.objects.filter(username='admin').delete()
        
        # Remove environment variable if it exists
        with patch.dict(os.environ, {}, clear=True):
            out = io.StringIO()
            call_command('ensure_admin', stdout=out)
            
            admin_user = User.objects.get(username='admin')
            self.assertTrue(admin_user.check_password('shoeshopper123'))
            
    @patch('core.management.commands.ensure_admin.User.objects.create_superuser')
    def test_ensure_admin_handles_creation_error(self, mock_create):
        """Test command handles errors during user creation"""
        User.objects.filter(username='admin').delete()
        mock_create.side_effect = Exception("Database error")
        
        out = io.StringIO()
        call_command('ensure_admin', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Error creating admin user: Database error', output)
        
    def test_ensure_admin_command_help_text(self):
        """Test command has proper help text"""
        command = EnsureAdminCommand()
        self.assertEqual(command.help, 'Ensure admin user exists (safe to run multiple times)')


class FixGuestUploadsCommandTest(TestCase):
    """Test the fix_guest_uploads management command"""
    
    @patch('core.management.commands.fix_guest_uploads.connection.cursor')
    def test_fix_guest_uploads_makes_column_nullable(self, mock_cursor):
        """Test command makes user_id column nullable when it's not"""
        # Mock cursor and database responses
        mock_cursor_obj = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_obj
        
        # Simulate column is currently NOT NULL
        mock_cursor_obj.fetchone.return_value = ('user_id', 'NO')
        
        out = io.StringIO()
        call_command('fix_guest_uploads', stdout=out)
        
        # Check that ALTER TABLE command was called
        mock_cursor_obj.execute.assert_any_call(
            'ALTER TABLE core_footimage ALTER COLUMN user_id DROP NOT NULL;'
        )
        
        output = out.getvalue()
        self.assertIn('Making user_id column nullable', output)
        self.assertIn('user_id column is now nullable!', output)
        
    @patch('core.management.commands.fix_guest_uploads.connection.cursor')
    def test_fix_guest_uploads_skips_when_already_nullable(self, mock_cursor):
        """Test command skips when column is already nullable"""
        mock_cursor_obj = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_obj
        
        # Simulate column is already nullable
        mock_cursor_obj.fetchone.return_value = ('user_id', 'YES')
        
        out = io.StringIO()
        call_command('fix_guest_uploads', stdout=out)
        
        # Check that ALTER TABLE command was NOT called
        alter_calls = [call for call in mock_cursor_obj.execute.call_args_list 
                      if 'ALTER TABLE' in str(call)]
        self.assertEqual(len(alter_calls), 0)
        
        output = out.getvalue()
        self.assertIn('user_id column is already nullable!', output)
        
    @patch('core.management.commands.fix_guest_uploads.connection.cursor')
    def test_fix_guest_uploads_handles_missing_column(self, mock_cursor):
        """Test command handles case when column doesn't exist"""
        mock_cursor_obj = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_obj
        
        # Simulate column not found
        mock_cursor_obj.fetchone.return_value = None
        
        out = io.StringIO()
        call_command('fix_guest_uploads', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Could not find user_id column', output)
        
    @patch('core.management.commands.fix_guest_uploads.connection.cursor')
    def test_fix_guest_uploads_handles_database_error(self, mock_cursor):
        """Test command handles database errors gracefully"""
        mock_cursor_obj = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_obj
        
        # Simulate database error
        mock_cursor_obj.fetchone.side_effect = Exception("Connection failed")
        
        out = io.StringIO()
        call_command('fix_guest_uploads', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Error: Connection failed', output)
        
    def test_fix_guest_uploads_command_help_text(self):
        """Test command has proper help text"""
        command = FixGuestUploadsCommand()
        expected_help = 'Fix guest uploads by making user_id nullable - bypasses migration system'
        self.assertEqual(command.help, expected_help)
        
    @patch('core.management.commands.fix_guest_uploads.connection.cursor')
    def test_fix_guest_uploads_checks_current_schema_first(self, mock_cursor):
        """Test command checks current schema before making changes"""
        mock_cursor_obj = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_obj
        mock_cursor_obj.fetchone.return_value = ('user_id', 'NO')
        
        out = io.StringIO()
        call_command('fix_guest_uploads', stdout=out)
        
        # Check that the information_schema query was executed
        info_schema_calls = [call for call in mock_cursor_obj.execute.call_args_list 
                           if 'information_schema' in str(call)]
        self.assertGreater(len(info_schema_calls), 0)
        
        output = out.getvalue()
        self.assertIn('Current user_id column: nullable = NO', output)
        
    @patch('core.management.commands.fix_guest_uploads.connection.cursor')
    def test_fix_guest_uploads_completes_successfully(self, mock_cursor):
        """Test command completes and shows completion message"""
        mock_cursor_obj = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_obj
        mock_cursor_obj.fetchone.return_value = ('user_id', 'YES')
        
        out = io.StringIO()
        call_command('fix_guest_uploads', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Done!', output)


class ManagementCommandIntegrationTest(TestCase):
    """Integration tests for management commands"""
    
    def test_both_commands_can_run_without_errors(self):
        """Test that both commands can be executed without throwing exceptions"""
        # This tests the basic command structure and imports
        try:
            # Just test that commands can be instantiated
            ensure_admin_cmd = EnsureAdminCommand()
            fix_uploads_cmd = FixGuestUploadsCommand()
            
            # Basic attribute checks
            self.assertTrue(hasattr(ensure_admin_cmd, 'handle'))
            self.assertTrue(hasattr(fix_uploads_cmd, 'handle'))
            self.assertTrue(hasattr(ensure_admin_cmd, 'help'))
            self.assertTrue(hasattr(fix_uploads_cmd, 'help'))
            
        except Exception as e:
            self.fail(f"Management commands failed to instantiate: {e}")
            
    def test_ensure_admin_command_available_via_django(self):
        """Test that ensure_admin command is properly registered with Django"""
        from django.core.management import get_commands
        commands = get_commands()
        self.assertIn('ensure_admin', commands)
        
    def test_fix_guest_uploads_command_available_via_django(self):
        """Test that fix_guest_uploads command is properly registered with Django"""
        from django.core.management import get_commands
        commands = get_commands()
        self.assertIn('fix_guest_uploads', commands)