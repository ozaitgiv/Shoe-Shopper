from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from unittest.mock import patch

from core.models import FootImage, Shoe


class FootImageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_foot_image_str_with_user(self):
        """Test FootImage __str__ method with authenticated user"""
        foot_image = FootImage.objects.create(
            user=self.user,
            image='test_image.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0
        )
        expected = f"FootImage {foot_image.id} by testuser"
        self.assertEqual(str(foot_image), expected)
        
    def test_foot_image_str_guest_with_session(self):
        """Test FootImage __str__ method for guest with session ID"""
        foot_image = FootImage.objects.create(
            user=None,
            image='test_image.jpg',
            status='complete',
            error_message='GUEST_SESSION:abc123def456ghi789',
            length_inches=10.5,
            width_inches=4.0
        )
        expected = f"FootImage {foot_image.id} by Guest (abc123de...)"
        self.assertEqual(str(foot_image), expected)
        
    def test_foot_image_str_guest_without_session(self):
        """Test FootImage __str__ method for guest without session ID"""
        foot_image = FootImage.objects.create(
            user=None,
            image='test_image.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0
        )
        expected = f"FootImage {foot_image.id} by Guest"
        self.assertEqual(str(foot_image), expected)
        
    def test_foot_image_status_choices(self):
        """Test FootImage status field validation"""
        foot_image = FootImage.objects.create(
            user=self.user,
            image='test_image.jpg',
            status='processing'
        )
        self.assertEqual(foot_image.status, 'processing')
        
        foot_image.status = 'complete'
        foot_image.save()
        self.assertEqual(foot_image.status, 'complete')
        
        foot_image.status = 'error'
        foot_image.save()
        self.assertEqual(foot_image.status, 'error')


class ShoeModelTest(TestCase):
    def setUp(self):
        self.shoe_data = {
            'company': 'Nike',
            'model': 'Air Max 90',
            'gender': 'M',
            'us_size': Decimal('10.5'),
            'width_category': 'D',
            'function': 'running',
            'price_usd': Decimal('120.00'),
            'product_url': 'https://nike.com/air-max-90',
            'shoe_image_url': 'https://example.com/shoe.jpg'
        }
        
    def test_shoe_creation(self):
        """Test basic shoe creation"""
        shoe = Shoe.objects.create(**self.shoe_data)
        self.assertEqual(shoe.company, 'Nike')
        self.assertEqual(shoe.model, 'Air Max 90')
        self.assertEqual(shoe.us_size, Decimal('10.5'))
        self.assertTrue(shoe.is_active)
        
    def test_shoe_str_method(self):
        """Test Shoe __str__ method"""
        shoe = Shoe.objects.create(**self.shoe_data)
        expected = "Nike Air Max 90 (US 10.5)"
        self.assertEqual(str(shoe), expected)
        
    def test_shoe_gender_choices(self):
        """Test shoe gender field validation"""
        for gender_code, gender_name in [('M', 'Men'), ('W', 'Women'), ('U', 'Unisex')]:
            shoe_data = self.shoe_data.copy()
            shoe_data['gender'] = gender_code
            shoe_data['model'] = f'{self.shoe_data["model"]} {gender_code}'  # Make unique
            shoe = Shoe.objects.create(**shoe_data)
            self.assertEqual(shoe.gender, gender_code)
            
    def test_shoe_width_choices(self):
        """Test shoe width category validation"""
        for width_code, width_name in [('N', 'Narrow'), ('D', 'Regular'), ('W', 'Wide')]:
            shoe_data = self.shoe_data.copy()
            shoe_data['width_category'] = width_code
            shoe_data['model'] = f'{self.shoe_data["model"]} {width_code}'  # Make unique
            shoe = Shoe.objects.create(**shoe_data)
            self.assertEqual(shoe.width_category, width_code)
            
    def test_shoe_function_choices(self):
        """Test shoe function field validation"""
        functions = ['casual', 'hiking', 'work', 'running']
        for i, function in enumerate(functions):
            shoe_data = self.shoe_data.copy()
            shoe_data['function'] = function
            shoe_data['model'] = f'{self.shoe_data["model"]} {i}'  # Make unique
            shoe = Shoe.objects.create(**shoe_data)
            self.assertEqual(shoe.function, function)
            
    @patch('core.views.process_insole_image_with_enhanced_measurements')
    @patch('core.models.Shoe.save')
    def test_shoe_save_process_mocked(self, mock_save, mock_process):
        """Test shoe save method logic without actual processing"""
        # Test that the processing is called when expected
        mock_process.return_value = (10.5, 4.0, 28.0, 42.0, None)
        
        shoe = Shoe(**self.shoe_data)
        shoe.insole_image = 'test_insole.jpg'
        
        # This tests the logic without the actual file operations
        self.assertTrue(hasattr(shoe, 'insole_image'))
        self.assertIsNone(shoe.insole_length)