"""
Comprehensive tests for API endpoints
Each test focuses on exactly one behavior
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json
import tempfile
import os
import io
from PIL import Image

from .models import FootImage, Shoe


def create_test_image(width=100, height=100, format='JPEG'):
    """Create a valid test image for upload tests"""
    img = Image.new('RGB', (width, height), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()


class CSRFEndpointTest(TestCase):
    """Test CSRF token endpoint"""
    
    def setUp(self):
        self.client = Client()
        
    def test_csrf_endpoint_returns_200(self):
        """Test CSRF endpoint returns 200 status"""
        response = self.client.get('/api/csrf/')
        self.assertEqual(response.status_code, 200)
        
    def test_csrf_endpoint_returns_json(self):
        """Test CSRF endpoint returns JSON content type"""
        response = self.client.get('/api/csrf/')
        self.assertEqual(response['Content-Type'], 'application/json')
        
    def test_csrf_endpoint_contains_csrf_token(self):
        """Test CSRF endpoint contains csrfToken field"""
        response = self.client.get('/api/csrf/')
        data = response.json()
        self.assertIn('csrfToken', data)
        
    def test_csrf_token_is_string(self):
        """Test CSRF token is a string"""
        response = self.client.get('/api/csrf/')
        data = response.json()
        self.assertIsInstance(data['csrfToken'], str)
        
    def test_csrf_token_is_not_empty(self):
        """Test CSRF token is not empty"""
        response = self.client.get('/api/csrf/')
        data = response.json()
        self.assertGreater(len(data['csrfToken']), 0)


class ShoeListEndpointTest(TestCase):
    """Test shoe list endpoint"""
    
    def setUp(self):
        self.client = Client()
        
    def test_shoe_list_returns_200_when_no_shoes(self):
        """Test shoe list returns 200 even with no shoes"""
        response = self.client.get('/api/shoes/')
        self.assertEqual(response.status_code, 200)
        
    def test_shoe_list_returns_empty_array_when_no_shoes(self):
        """Test shoe list returns empty array when no shoes exist"""
        response = self.client.get('/api/shoes/')
        data = response.json()
        self.assertEqual(data, [])
        
    def test_shoe_list_returns_single_shoe(self):
        """Test shoe list returns single shoe correctly"""
        shoe = Shoe.objects.create(
            company='Nike',
            model='Test Shoe',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://example.com'
        )
        
        response = self.client.get('/api/shoes/')
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['company'], 'Nike')
        self.assertEqual(data[0]['model'], 'Test Shoe')
        
    def test_shoe_list_returns_multiple_shoes(self):
        """Test shoe list returns multiple shoes"""
        Shoe.objects.create(
            company='Nike',
            model='Shoe 1',
            gender='M',
            us_size=Decimal('10.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('100.00'),
            product_url='https://example1.com'
        )
        Shoe.objects.create(
            company='Adidas',
            model='Shoe 2',
            gender='W',
            us_size=Decimal('9.0'),
            width_category='W',
            function='casual',
            price_usd=Decimal('80.00'),
            product_url='https://example2.com'
        )
        
        response = self.client.get('/api/shoes/')
        data = response.json()
        
        self.assertEqual(len(data), 2)
        companies = [shoe['company'] for shoe in data]
        self.assertIn('Nike', companies)
        self.assertIn('Adidas', companies)
        
    def test_shoe_list_only_returns_active_shoes(self):
        """Test shoe list only returns active shoes"""
        Shoe.objects.create(
            company='Nike',
            model='Active Shoe',
            gender='M',
            us_size=Decimal('10.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('100.00'),
            product_url='https://example1.com',
            is_active=True
        )
        Shoe.objects.create(
            company='Adidas',
            model='Inactive Shoe',
            gender='M',
            us_size=Decimal('10.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('100.00'),
            product_url='https://example2.com',
            is_active=False
        )
        
        response = self.client.get('/api/shoes/')
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['model'], 'Active Shoe')
        
    def test_shoe_list_includes_fit_scores_when_available(self):
        """Test shoe list includes fit scores when foot measurement exists"""
        # Create shoe
        Shoe.objects.create(
            company='Nike',
            model='Test Shoe',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://example.com',
            insole_length=10.5,
            insole_width=4.0
        )
        
        # Create guest session with foot measurement
        session = self.client.session
        session['guest_session_id'] = 'test123'
        session.save()
        
        FootImage.objects.create(
            user=None,
            image='test.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            area_sqin=42.0,
            perimeter_inches=28.0,
            error_message='GUEST_SESSION:test123'
        )
        
        response = self.client.get('/api/shoes/')
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertIn('fit_score', data[0])
        self.assertIsInstance(data[0]['fit_score'], (int, float))
        
    def test_shoe_list_without_fit_scores_when_no_measurement(self):
        """Test shoe list doesn't include fit scores when no measurement"""
        Shoe.objects.create(
            company='Nike',
            model='Test Shoe',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://example.com'
        )
        
        response = self.client.get('/api/shoes/')
        data = response.json()
        
        self.assertEqual(len(data), 1)
        # Should not have fit_score when no measurement
        self.assertNotIn('fit_score', data[0])


class UserInfoEndpointTest(TestCase):
    """Test user info endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
    def test_user_info_anonymous_user(self):
        """Test user info for anonymous user requires authentication"""
        response = self.client.get('/api/auth/user/')
        self.assertEqual(response.status_code, 401)  # Requires authentication
        
    def test_user_info_authenticated_user(self):
        """Test user info for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/api/auth/user/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        
    def test_user_info_requires_get_method(self):
        """Test user info endpoint requires GET method"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/user/')
        self.assertEqual(response.status_code, 405)  # Method not allowed


class SignupEndpointTest(TestCase):
    """Test signup endpoint"""
    
    def setUp(self):
        self.client = Client()
        
    def test_signup_successful_with_valid_data(self):
        """Test successful signup with valid data"""
        data = {
            'username': 'newuser',
            'password': 'securepass123',
            'email': 'newuser@example.com'
        }
        
        response = self.client.post('/api/auth/signup/', data)
        self.assertEqual(response.status_code, 201)
        
        # Check user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        
    def test_signup_returns_success_message(self):
        """Test signup returns success message"""
        data = {
            'username': 'newuser',
            'password': 'securepass123',
            'email': 'newuser@example.com'
        }
        
        response = self.client.post('/api/auth/signup/', data)
        response_data = response.json()
        
        self.assertIn('message', response_data)
        self.assertIn('successfully', response_data['message'].lower())
        
    def test_signup_fails_with_existing_username(self):
        """Test signup fails when username already exists"""
        User.objects.create_user(username='existing', password='pass123')
        
        data = {
            'username': 'existing',
            'password': 'newpass123',
            'email': 'new@example.com'
        }
        
        response = self.client.post('/api/auth/signup/', data)
        self.assertEqual(response.status_code, 400)
        
    def test_signup_fails_with_missing_username(self):
        """Test signup fails when username is missing"""
        data = {
            'password': 'securepass123',
            'email': 'test@example.com'
        }
        
        response = self.client.post('/api/auth/signup/', data)
        self.assertEqual(response.status_code, 400)
        
    def test_signup_fails_with_missing_password(self):
        """Test signup fails when password is missing"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com'
        }
        
        response = self.client.post('/api/auth/signup/', data)
        self.assertEqual(response.status_code, 400)
        
    def test_signup_requires_post_method(self):
        """Test signup endpoint requires POST method"""
        response = self.client.get('/api/auth/signup/')
        self.assertEqual(response.status_code, 405)


class LogoutEndpointTest(TestCase):
    """Test logout endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_logout_authenticated_user(self):
        """Test logout for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('message', data)
        
    def test_logout_anonymous_user(self):
        """Test logout for anonymous user still returns 200"""
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        
    def test_logout_requires_post_method(self):
        """Test logout endpoint requires POST method"""
        response = self.client.get('/api/auth/logout/')
        # Should return 405 Method Not Allowed for GET requests
        self.assertEqual(response.status_code, 405)


class LatestMeasurementEndpointTest(TestCase):
    """Test latest measurement endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_latest_measurement_no_measurements(self):
        """Test latest measurement when no measurements exist"""
        response = self.client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn('error', data)
        
    def test_latest_measurement_guest_with_session(self):
        """Test latest measurement for guest with session"""
        # Set up guest session and get actual session key
        session = self.client.session
        session.save()  # This creates the session and generates session_key
        session_key = session.session_key
        
        # Create measurement for guest using actual session key
        FootImage.objects.create(
            user=None,
            image='guest.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            area_sqin=42.0,
            perimeter_inches=28.0,
            error_message=f'GUEST_SESSION:{session_key}'
        )
        
        response = self.client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['length_inches'], 10.5)
        self.assertEqual(data['width_inches'], 4.0)
        
    def test_latest_measurement_authenticated_user(self):
        """Test latest measurement for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        
        FootImage.objects.create(
            user=self.user,
            image='user.jpg',
            status='complete',
            length_inches=11.0,
            width_inches=4.5,
            area_sqin=49.5,
            perimeter_inches=31.0
        )
        
        response = self.client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['length_inches'], 11.0)
        self.assertEqual(data['width_inches'], 4.5)
        
    def test_latest_measurement_ignores_processing_status(self):
        """Test latest measurement ignores processing/error status"""
        session = self.client.session
        session['guest_session_id'] = 'guest123'
        session.save()
        
        # Create processing measurement (should be ignored)
        FootImage.objects.create(
            user=None,
            image='processing.jpg',
            status='processing',
            error_message='GUEST_SESSION:guest123'
        )
        
        response = self.client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 404)
        
    def test_latest_measurement_returns_most_recent(self):
        """Test latest measurement returns most recent when multiple exist"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create older measurement with explicit timestamp
        older_time = timezone.now() - timedelta(minutes=1)
        older = FootImage.objects.create(
            user=self.user,
            image='old.jpg',
            status='complete',
            length_inches=10.0,
            width_inches=3.5
        )
        older.uploaded_at = older_time
        older.save()
        
        # Create newer measurement  
        newer = FootImage.objects.create(
            user=self.user,
            image='new.jpg',
            status='complete',
            length_inches=11.0,
            width_inches=4.5
        )
        
        response = self.client.get('/api/measurements/latest/')
        data = response.json()
        
        # Should return the newer measurement
        self.assertEqual(data['length_inches'], 11.0)


class RecommendationsEndpointTest(TestCase):
    """Test recommendations endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test shoes
        self.shoe1 = Shoe.objects.create(
            company='Nike',
            model='Perfect Fit',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://example1.com',
            insole_length=10.5,
            insole_width=4.0
        )
        
        self.shoe2 = Shoe.objects.create(
            company='Adidas',
            model='Close Fit',
            gender='M',
            us_size=Decimal('11.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('140.00'),
            product_url='https://example2.com',
            insole_length=11.0,
            insole_width=4.2
        )
        
    def test_recommendations_no_measurement(self):
        """Test recommendations when no measurement exists"""
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        
    def test_recommendations_with_guest_measurement(self):
        """Test recommendations with guest measurement"""
        # Set up guest session
        session = self.client.session
        session['guest_session_id'] = 'guest123'
        session.save()
        
        # Create guest measurement
        FootImage.objects.create(
            user=None,
            image='guest.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            area_sqin=42.0,
            perimeter_inches=28.0,
            error_message='GUEST_SESSION:guest123'
        )
        
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('recommendations', data)
        self.assertIn('user_measurements', data)
        self.assertGreater(len(data['recommendations']), 0)
        
    def test_recommendations_with_user_measurement(self):
        """Test recommendations with authenticated user measurement"""
        self.client.login(username='testuser', password='testpass123')
        
        FootImage.objects.create(
            user=self.user,
            image='user.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            area_sqin=42.0,
            perimeter_inches=28.0
        )
        
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('recommendations', data)
        self.assertIn('user_measurements', data)
        
    def test_recommendations_sorted_by_score(self):
        """Test recommendations are sorted by fit score"""
        session = self.client.session
        session['guest_session_id'] = 'guest123'
        session.save()
        
        FootImage.objects.create(
            user=None,
            image='guest.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            area_sqin=42.0,
            perimeter_inches=28.0,
            error_message='GUEST_SESSION:guest123'
        )
        
        response = self.client.get('/api/recommendations/')
        data = response.json()
        
        recommendations = data['recommendations']
        self.assertGreaterEqual(len(recommendations), 2)
        
        # Check that scores are in descending order
        for i in range(len(recommendations) - 1):
            current_score = recommendations[i]['fit_score']
            next_score = recommendations[i + 1]['fit_score']
            self.assertGreaterEqual(current_score, next_score)
            
    def test_recommendations_includes_user_measurements(self):
        """Test recommendations response includes user measurements"""
        session = self.client.session
        session['guest_session_id'] = 'guest123'
        session.save()
        
        FootImage.objects.create(
            user=None,
            image='guest.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            area_sqin=42.0,
            perimeter_inches=28.0,
            error_message='GUEST_SESSION:guest123'
        )
        
        response = self.client.get('/api/recommendations/')
        data = response.json()
        
        measurements = data['user_measurements']
        self.assertEqual(measurements['length_inches'], 10.5)
        self.assertEqual(measurements['width_inches'], 4.0)
        self.assertEqual(measurements['area_sqin'], 42.0)
        self.assertEqual(measurements['perimeter_inches'], 28.0)


class FootImageUploadEndpointTest(TestCase):
    """Test foot image upload endpoint"""
    
    def setUp(self):
        self.client = Client()
        
    @patch('core.views.process_foot_image_enhanced')
    def test_foot_image_upload_successful(self, mock_process):
        """Test successful foot image upload"""
        mock_process.return_value = (10.5, 4.0, 42.0, 28.0, None)
        
        # Create test image
        test_image = SimpleUploadedFile(
            'test_foot.jpg',
            create_test_image(),
            content_type='image/jpeg'
        )
        
        response = self.client.post('/api/measurements/upload/', {
            'image': test_image
        })
        
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertIn('measurement_id', data)
        self.assertIsInstance(data['measurement_id'], int)
        
    def test_foot_image_upload_missing_image(self):
        """Test foot image upload fails when image is missing"""
        response = self.client.post('/api/measurements/upload/', {})
        self.assertEqual(response.status_code, 400)
        
    @patch('core.views.process_foot_image_enhanced')
    def test_foot_image_upload_processing_error(self, mock_process):
        """Test foot image upload handles processing errors"""
        mock_process.return_value = (None, None, None, None, "Processing failed")
        
        test_image = SimpleUploadedFile(
            'test_foot.jpg',
            create_test_image(),
            content_type='image/jpeg'
        )
        
        response = self.client.post('/api/measurements/upload/', {
            'image': test_image
        })
        
        self.assertEqual(response.status_code, 201)  # Still creates record
        
        data = response.json()
        self.assertIn('measurement_id', data)
        
    def test_foot_image_upload_requires_post(self):
        """Test foot image upload requires POST method"""
        response = self.client.get('/api/measurements/upload/')
        self.assertEqual(response.status_code, 405)


class FootImageDetailEndpointTest(TestCase):
    """Test foot image detail endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_foot_image_detail_authenticated_user(self):
        """Test foot image detail for authenticated user's image"""
        self.client.login(username='testuser', password='testpass123')
        
        foot_image = FootImage.objects.create(
            user=self.user,
            image='test.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0
        )
        
        response = self.client.get(f'/api/measurements/{foot_image.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['id'], foot_image.id)
        self.assertEqual(data['status'], 'complete')
        
    def test_foot_image_detail_guest_with_session(self):
        """Test foot image detail for guest with matching session"""
        session = self.client.session
        session['guest_session_id'] = 'guest123'
        session.save()
        
        foot_image = FootImage.objects.create(
            user=None,
            image='guest.jpg',
            status='complete',
            length_inches=10.5,
            width_inches=4.0,
            error_message='GUEST_SESSION:guest123'
        )
        
        response = self.client.get(f'/api/measurements/{foot_image.id}/')
        self.assertEqual(response.status_code, 200)
        
    def test_foot_image_detail_unauthorized_access(self):
        """Test foot image detail denies unauthorized access"""
        other_user = User.objects.create_user(username='other', password='pass123')
        
        foot_image = FootImage.objects.create(
            user=other_user,
            image='other.jpg',
            status='complete'
        )
        
        response = self.client.get(f'/api/measurements/{foot_image.id}/')
        self.assertEqual(response.status_code, 403)
        
    def test_foot_image_detail_not_found(self):
        """Test foot image detail returns 404 for non-existent image"""
        response = self.client.get('/api/measurements/999/')
        self.assertEqual(response.status_code, 404)