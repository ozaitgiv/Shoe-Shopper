"""
End-to-End Testing Suite
Tests complete user workflows from frontend to backend
"""
from django.test import LiveServerTestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from unittest.mock import patch, MagicMock
import tempfile
import os
import time
import json
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


class E2EUserWorkflowTest(TransactionTestCase):
    """Test complete user workflows without browser automation"""
    
    def setUp(self):
        """Set up test data"""
        # Create test shoes
        self.shoe1 = Shoe.objects.create(
            company='Nike',
            model='Perfect Fit Shoe',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://nike.com/perfect-fit',
            insole_length=10.5,
            insole_width=4.0,
            insole_area=42.0,
            insole_perimeter=28.0,
            shoe_image_url='https://example.com/nike-shoe.jpg'
        )
        
        self.shoe2 = Shoe.objects.create(
            company='Adidas',
            model='Close Fit Shoe',
            gender='M',
            us_size=Decimal('11.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('140.00'),
            product_url='https://adidas.com/close-fit',
            insole_length=11.0,
            insole_width=4.2,
            insole_area=46.2,
            insole_perimeter=30.0,
            shoe_image_url='https://example.com/adidas-shoe.jpg'
        )
        
    @patch('core.views.process_foot_image_enhanced')
    def test_complete_guest_workflow(self, mock_process):
        """Test complete guest user workflow: upload -> measure -> recommend"""
        # Mock successful foot processing
        mock_process.return_value = (10.5, 4.0, 42.0, 28.0, None)
        
        # Step 1: Guest accesses the site and gets CSRF token
        response = self.client.get('/api/csrf/')
        self.assertEqual(response.status_code, 200)
        csrf_token = response.json()['csrfToken']
        
        # Step 2: Guest uploads foot image
        test_image = SimpleUploadedFile(
            'guest_foot.jpg',
            create_test_image(),
            content_type='image/jpeg'
        )
        
        response = self.client.post('/api/measurements/upload/', {
            'image': test_image
        }, HTTP_X_CSRFTOKEN=csrf_token)
        
        self.assertEqual(response.status_code, 201)
        upload_data = response.json()
        foot_image_id = upload_data['measurement_id']
        
        # Verify foot image was created with guest session
        foot_image = FootImage.objects.get(id=foot_image_id)
        self.assertIsNone(foot_image.user)
        self.assertEqual(foot_image.status, 'complete')
        self.assertEqual(foot_image.length_inches, 10.5)
        self.assertEqual(foot_image.width_inches, 4.0)
        
        # Step 3: Guest retrieves their latest measurement
        response = self.client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 200)
        
        measurement_data = response.json()
        self.assertEqual(measurement_data['length_inches'], 10.5)
        self.assertEqual(measurement_data['width_inches'], 4.0)
        
        # Step 4: Guest gets shoe recommendations
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)
        
        recommendations_data = response.json()
        self.assertIn('recommendations', recommendations_data)
        self.assertIn('user_measurements', recommendations_data)
        
        recommendations = recommendations_data['recommendations']
        self.assertGreater(len(recommendations), 0)
        
        # Verify recommendations are sorted by fit score
        for i in range(len(recommendations) - 1):
            current_score = recommendations[i]['fit_score']
            next_score = recommendations[i + 1]['fit_score']
            self.assertGreaterEqual(current_score, next_score)
            
        # Step 5: Guest views detailed shoe information
        best_shoe = recommendations[0]
        response = self.client.get('/api/shoes/')
        self.assertEqual(response.status_code, 200)
        
        shoes_data = response.json()
        self.assertGreater(len(shoes_data), 0)
        
        # Verify the workflow produced meaningful results
        self.assertGreater(best_shoe['fit_score'], 50)  # Should be reasonable fit
        
    def test_complete_authenticated_user_workflow(self):
        """Test complete authenticated user workflow"""
        # Step 1: User signs up
        signup_data = {
            'username': 'testuser',
            'password': 'securepass123',
            'email': 'test@example.com'
        }
        
        response = self.client.post('/api/auth/signup/', signup_data)
        self.assertEqual(response.status_code, 201)
        
        # Verify user was created
        user = User.objects.get(username='testuser')
        self.assertEqual(user.username, 'testuser')
        
        # Step 2: User logs in
        self.client.login(username='testuser', password='securepass123')
        
        # Step 3: User checks their info
        response = self.client.get('/api/auth/user/')
        self.assertEqual(response.status_code, 200)
        
        user_data = response.json()
        self.assertEqual(user_data['username'], 'testuser')
        
        # Step 4: User uploads foot image
        with patch('core.views.process_foot_image_enhanced') as mock_process:
            mock_process.return_value = (10.8, 4.1, 44.28, 29.0, None)
            
            test_image = SimpleUploadedFile(
                'user_foot.jpg',
                create_test_image(),
                content_type='image/jpeg'
            )
            
            response = self.client.post('/api/measurements/upload/', {
                'image': test_image
            })
            
            self.assertEqual(response.status_code, 201)
            foot_image_id = response.json()['measurement_id']
            
        # Verify foot image was associated with user
        foot_image = FootImage.objects.get(id=foot_image_id)
        self.assertEqual(foot_image.user, user)
        self.assertEqual(foot_image.status, 'complete')
        
        # Step 5: User gets personalized recommendations
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)
        
        recommendations_data = response.json()
        recommendations = recommendations_data['recommendations']
        user_measurements = recommendations_data['user_measurements']
        
        # Verify personalized data
        self.assertEqual(user_measurements['length_inches'], 10.8)
        self.assertEqual(user_measurements['width_inches'], 4.1)
        self.assertGreater(len(recommendations), 0)
        
        # Step 6: User logs out
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        
    @patch('core.views.process_foot_image_enhanced')
    def test_error_handling_workflow(self, mock_process):
        """Test workflow when image processing fails"""
        # Mock failed processing
        mock_process.return_value = (None, None, None, None, "Processing failed: Invalid image")
        
        # Step 1: Guest uploads problematic image
        test_image = SimpleUploadedFile(
            'bad_image.jpg',
            create_test_image(),
            content_type='image/jpeg'
        )
        
        response = self.client.post('/api/measurements/upload/', {
            'image': test_image
        })
        
        # Should still create record but with error status
        self.assertEqual(response.status_code, 201)
        upload_data = response.json()
        foot_image_id = upload_data['measurement_id']
        
        # Verify the database record has error status
        foot_image = FootImage.objects.get(id=foot_image_id)
        self.assertEqual(foot_image.status, 'error')
        
        # Step 2: Verify no measurement available
        response = self.client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 404)
        
        # Step 3: Verify no recommendations available
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 400)
        
        error_data = response.json()
        self.assertIn('error', error_data)
        
    def test_multiple_sessions_isolation(self):
        """Test that guest sessions are properly isolated"""
        # Create first guest session
        with patch('core.views.process_foot_image_enhanced') as mock_process:
            mock_process.return_value = (10.0, 3.8, 38.0, 26.0, None)
            
            # First client (guest 1)
            client1 = self.client
            
            test_image1 = SimpleUploadedFile(
                'guest1_foot.jpg',
                create_test_image(),
                content_type='image/jpeg'
            )
            
            response1 = client1.post('/api/measurements/upload/', {
                'image': test_image1
            })
            self.assertEqual(response1.status_code, 201)
            
            # Get guest 1's measurement
            response1 = client1.get('/api/measurements/latest/')
            self.assertEqual(response1.status_code, 200)
            guest1_measurement = response1.json()
            
        # Create second guest session
        with patch('core.views.process_foot_image_enhanced') as mock_process:
            mock_process.return_value = (11.0, 4.5, 49.5, 31.0, None)
            
            # Second client (guest 2) - new session
            from django.test import Client
            client2 = Client()
            
            test_image2 = SimpleUploadedFile(
                'guest2_foot.jpg',
                create_test_image(),
                content_type='image/jpeg'
            )
            
            response2 = client2.post('/api/measurements/upload/', {
                'image': test_image2
            })
            self.assertEqual(response2.status_code, 201)
            
            # Get guest 2's measurement
            response2 = client2.get('/api/measurements/latest/')
            self.assertEqual(response2.status_code, 200)
            guest2_measurement = response2.json()
            
        # Verify sessions are isolated
        self.assertNotEqual(
            guest1_measurement['length_inches'], 
            guest2_measurement['length_inches']
        )
        
        # Verify guest 1 still has their own data
        response1_check = client1.get('/api/measurements/latest/')
        self.assertEqual(response1_check.status_code, 200)
        guest1_check = response1_check.json()
        self.assertEqual(guest1_check['length_inches'], 10.0)
        
    def test_data_persistence_workflow(self):
        """Test that user data persists across sessions"""
        # Step 1: Create authenticated user and upload measurement
        user = User.objects.create_user(
            username='persistent_user',
            password='persist123'
        )
        
        self.client.login(username='persistent_user', password='persist123')
        
        with patch('core.views.process_foot_image_enhanced') as mock_process:
            mock_process.return_value = (10.7, 4.2, 44.94, 29.5, None)
            
            test_image = SimpleUploadedFile(
                'persistent_foot.jpg',
                create_test_image(),
                content_type='image/jpeg'
            )
            
            response = self.client.post('/api/measurements/upload/', {
                'image': test_image
            })
            self.assertEqual(response.status_code, 201)
            
        # Step 2: Log out
        self.client.post('/api/auth/logout/')
        
        # Step 3: Log back in with new client (simulating new session)
        from django.test import Client
        new_client = Client()
        new_client.login(username='persistent_user', password='persist123')
        
        # Step 4: Verify data is still available
        response = new_client.get('/api/measurements/latest/')
        self.assertEqual(response.status_code, 200)
        
        measurement = response.json()
        self.assertEqual(measurement['length_inches'], 10.7)
        self.assertEqual(measurement['width_inches'], 4.2)
        
        # Step 5: Get recommendations with persisted data
        response = new_client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)
        
        recommendations_data = response.json()
        self.assertIn('recommendations', recommendations_data)
        self.assertGreater(len(recommendations_data['recommendations']), 0)


class E2EAdminWorkflowTest(TransactionTestCase):
    """Test admin-specific workflows"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
    def test_admin_shoe_management_workflow(self):
        """Test admin workflow for managing shoes"""
        # Step 1: Admin logs in
        self.client.login(username='admin', password='admin123')
        
        # Step 2: Admin creates new shoe (via Django admin or API)
        shoe_data = {
            'company': 'New Brand',
            'model': 'Test Shoe',
            'gender': 'M',
            'us_size': Decimal('9.5'),
            'width_category': 'W',
            'function': 'casual',
            'price_usd': Decimal('99.99'),
            'product_url': 'https://newbrand.com/test-shoe',
            'shoe_image_url': 'https://newbrand.com/test-shoe.jpg',
            'is_active': True
        }
        
        new_shoe = Shoe.objects.create(**shoe_data)
        
        # Step 3: Verify shoe appears in API
        response = self.client.get('/api/shoes/')
        self.assertEqual(response.status_code, 200)
        
        shoes = response.json()
        shoe_names = [shoe['model'] for shoe in shoes]
        self.assertIn('Test Shoe', shoe_names)
        
        # Step 4: Admin deactivates shoe
        new_shoe.is_active = False
        new_shoe.save()
        
        # Step 5: Verify shoe no longer appears in public API
        response = self.client.get('/api/shoes/')
        shoes = response.json()
        active_shoe_names = [shoe['model'] for shoe in shoes]
        self.assertNotIn('Test Shoe', active_shoe_names)


class E2EPerformanceTest(TransactionTestCase):
    """Test system performance under realistic conditions"""
    
    def setUp(self):
        # Create many shoes for performance testing
        self.shoes = []
        for i in range(50):
            shoe = Shoe.objects.create(
                company=f'Brand{i % 10}',
                model=f'Model{i}',
                gender='M' if i % 2 == 0 else 'W',
                us_size=Decimal(str(8.0 + (i % 6) * 0.5)),
                width_category=['N', 'D', 'W'][i % 3],
                function=['casual', 'running', 'hiking', 'work'][i % 4],
                price_usd=Decimal(str(80.0 + i * 2)),
                product_url=f'https://brand{i % 10}.com/model{i}',
                insole_length=9.0 + (i % 6) * 0.5,
                insole_width=3.5 + (i % 3) * 0.3,
                is_active=True
            )
            self.shoes.append(shoe)
            
    @patch('core.views.process_foot_image_enhanced')
    def test_recommendation_performance_with_many_shoes(self, mock_process):
        """Test recommendation performance with large shoe database"""
        mock_process.return_value = (10.5, 4.0, 42.0, 28.0, None)
        
        # Upload foot measurement
        test_image = SimpleUploadedFile(
            'perf_test_foot.jpg',
            create_test_image(),
            content_type='image/jpeg'
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/measurements/upload/', {
            'image': test_image
        })
        
        upload_time = time.time() - start_time
        self.assertEqual(response.status_code, 201)
        
        # Get recommendations
        start_time = time.time()
        
        response = self.client.get('/api/recommendations/')
        
        recommendation_time = time.time() - start_time
        self.assertEqual(response.status_code, 200)
        
        recommendations = response.json()['recommendations']
        
        # Performance assertions
        self.assertLess(upload_time, 5.0)  # Upload should be fast (mocked processing)
        self.assertLess(recommendation_time, 2.0)  # Recommendations should be fast
        self.assertEqual(len(recommendations), 50)  # Should return all shoes
        
        # Verify recommendations are properly scored and sorted
        for i in range(len(recommendations) - 1):
            current_score = recommendations[i]['fit_score']
            next_score = recommendations[i + 1]['fit_score']
            self.assertGreaterEqual(current_score, next_score)
            
    def test_concurrent_user_simulation(self):
        """Test system behavior with multiple concurrent operations"""
        # Simulate multiple users uploading simultaneously
        responses = []
        
        with patch('core.views.process_foot_image_enhanced') as mock_process:
            mock_process.return_value = (10.5, 4.0, 42.0, 28.0, None)
            
            # Create multiple clients (simulating concurrent users)
            clients = [self.client]  # Start with existing client
            for i in range(4):  # Add 4 more clients
                from django.test import Client
                clients.append(Client())
                
            # Each client uploads a foot image
            for i, client in enumerate(clients):
                test_image = SimpleUploadedFile(
                    f'concurrent_foot_{i}.jpg',
                    f'concurrent test foot image {i}'.encode(),
                    content_type='image/jpeg'
                )
                
                response = client.post('/api/measurements/upload/', {
                    'image': test_image
                })
                
                responses.append(response)
                
        # Verify all uploads succeeded
        for response in responses:
            self.assertEqual(response.status_code, 201)
            
        # Verify each client can get their own recommendations
        for client in clients:
            response = client.get('/api/recommendations/')
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('recommendations', data)
            self.assertGreater(len(data['recommendations']), 0)