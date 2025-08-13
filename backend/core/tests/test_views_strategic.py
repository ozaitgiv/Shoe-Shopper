"""
Strategic views.py testing - targeting specific uncovered lines for maximum coverage boost
Current coverage: 66% (191 missed lines) -> Target: 85%+ 

Uncovered line ranges to target:
- 109, 124-150: Image processing fallback logic
- 692-753: FootImageUploadView success/error paths  
- 760-764: FootImageUploadView error handling
- 797-818, 825-830: Deprecated endpoints
- 843-863: Legacy shoe recommendations
- 906-911: Shoe list guest handling
- 1025-1030, 1044-1045: Guest session edge cases
"""
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.backends.db import SessionStore
from decimal import Decimal
from unittest.mock import patch, MagicMock, call
import json
import io
from PIL import Image


import tempfile
import random

from core.models import FootImage, Shoe


def create_test_image(width=100, height=100, format='JPEG'):
    """Create a valid test image for upload tests"""
    img = Image.new('RGB', (width, height), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()


class ViewsStrategicImageProcessingTest(TestCase):
    """Target lines 109, 124-150 - Image processing fallback branches"""
    
    @patch('core.views.InferenceHTTPClient')
    def test_process_foot_image_enhanced_complete_fallback_success(self, mock_client_class):
        """Test complete fallback from workflow to bounding box (lines 109, 124-150)"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate workflow failure but successful bounding box detection  
        mock_client.run_workflow.side_effect = [
            Exception("Workflow service unavailable"),  # First workflow fails
            [{'predictions': {'predictions': [
                {'x': 100, 'y': 50, 'width': 200, 'height': 300, 'class_id': 2, 'confidence': 0.9},  # paper
                {'x': 120, 'y': 70, 'width': 160, 'height': 260, 'class_id': 0, 'confidence': 0.8}   # foot
            ]}}],  # Second workflow succeeds with correct format
            Exception("Workflow service unavailable"),  # Third workflow fails (A4 test)
            [{'predictions': {'predictions': [
                {'x': 100, 'y': 50, 'width': 200, 'height': 300, 'class_id': 2, 'confidence': 0.9},  # paper
                {'x': 120, 'y': 70, 'width': 160, 'height': 260, 'class_id': 0, 'confidence': 0.8}   # foot
            ]}}]  # Fourth workflow succeeds with correct format (A4 test)
        ]
        
        from core.views import process_foot_image_enhanced
        
        # Test letter paper size
        result = process_foot_image_enhanced('/fake/path.jpg', 'letter')
        self.assertEqual(len(result), 5)
        self.assertIsNotNone(result[0])  # length should be calculated
        self.assertIsNotNone(result[1])  # width should be calculated
        self.assertIsNotNone(result[2])  # area should be estimated
        self.assertIsNotNone(result[3])  # perimeter should be estimated
        self.assertIsNone(result[4])     # no error
        
        # Test A4 paper size (different calculation path)
        result_a4 = process_foot_image_enhanced('/fake/path.jpg', 'a4')
        self.assertEqual(len(result_a4), 5)
        self.assertIsNotNone(result_a4[0])
        self.assertNotEqual(result[0], result_a4[0])  # Should be different due to paper size
    
    @patch('core.views.InferenceHTTPClient')
    def test_process_foot_image_enhanced_paper_not_detected(self, mock_client_class):
        """Test paper not detected branch (line 128)"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock the first workflow to fail, then the second to succeed but without paper
        mock_client.run_workflow.side_effect = [
            Exception("Workflow failed"),  # First workflow fails
            [{'predictions': {'predictions': [
                {'x': 120, 'y': 70, 'width': 160, 'height': 260, 'class_id': 0, 'confidence': 0.8}
                # No paper prediction (class_id 2)
            ]}}]  # Second workflow succeeds but missing paper
        ]
        
        from core.views import process_foot_image_enhanced
        result = process_foot_image_enhanced('/fake/path.jpg')
        
        self.assertEqual(len(result), 5)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        self.assertIsNone(result[2])
        self.assertIsNone(result[3])
        self.assertEqual(result[4], "Paper not detected in the image")
    
    @patch('core.views.InferenceHTTPClient')
    def test_process_foot_image_enhanced_foot_not_detected(self, mock_client_class):
        """Test foot not detected branch (line 130)"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock the first workflow to fail, then the second to succeed but without foot
        mock_client.run_workflow.side_effect = [
            Exception("Workflow failed"),  # First workflow fails
            [{'predictions': {'predictions': [
                {'x': 100, 'y': 50, 'width': 200, 'height': 300, 'class_id': 2, 'confidence': 0.9}
                # No foot prediction (class_id 0)
            ]}}]  # Second workflow succeeds but missing foot
        ]
        
        from core.views import process_foot_image_enhanced
        result = process_foot_image_enhanced('/fake/path.jpg')
        
        self.assertEqual(len(result), 5)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        self.assertIsNone(result[2])
        self.assertIsNone(result[3])
        self.assertEqual(result[4], "Foot not detected in the image")


class ViewsStrategicUploadTest(TestCase):
    """Target lines 692-753, 760-764 - FootImageUploadView complete paths"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    @patch('core.views.process_foot_image_enhanced')
    @patch('core.views.cleanup_old_guest_sessions')
    @patch('random.random')
    def test_foot_image_upload_guest_with_cleanup_trigger(self, mock_random, mock_cleanup, mock_process):
        """Test guest upload with cleanup trigger (lines 702-704)"""
        # Mock successful processing
        mock_process.return_value = (10.5, 4.0, 42.0, 28.0, None)
        # Force cleanup to trigger (10% chance)
        mock_random.return_value = 0.05  # Less than 0.1, should trigger cleanup
        
        test_image = SimpleUploadedFile('test.jpg', create_test_image(), content_type='image/jpeg')
        
        response = self.client.post('/api/measurements/upload/', {'image': test_image})
        
        self.assertEqual(response.status_code, 201)
        # Cleanup should have been called
        mock_cleanup.assert_called_once()
        
        # Verify guest session was stored (new UUID-based system)
        foot_image = FootImage.objects.get(id=response.json()['measurement_id'])
        self.assertIsNotNone(foot_image.guest_session)
        # Verify response includes guest session ID
        response_data = response.json()
        self.assertIn('guest_session_id', response_data)
        self.assertEqual(str(foot_image.guest_session.id), response_data['guest_session_id'])
    
    @patch('core.views.process_foot_image_enhanced')
    @patch('random.random')
    def test_foot_image_upload_guest_no_cleanup(self, mock_random, mock_process):
        """Test guest upload without cleanup trigger (line 703)"""
        mock_process.return_value = (10.5, 4.0, 42.0, 28.0, None)
        # Prevent cleanup from triggering
        mock_random.return_value = 0.5  # Greater than 0.1
        
        test_image = SimpleUploadedFile('test.jpg', create_test_image(), content_type='image/jpeg')
        
        with patch('core.views.cleanup_old_guest_sessions') as mock_cleanup:
            response = self.client.post('/api/measurements/upload/', {'image': test_image})
            
            self.assertEqual(response.status_code, 201)
            # Cleanup should NOT have been called
            mock_cleanup.assert_not_called()
    
    @patch('core.views.process_foot_image_enhanced')
    def test_foot_image_upload_processing_error_path(self, mock_process):
        """Test processing error path (lines 723-730)"""
        # Mock processing error
        mock_process.return_value = (None, None, None, None, "AI service temporarily unavailable")
        
        test_image = SimpleUploadedFile('test.jpg', create_test_image(), content_type='image/jpeg')
        
        response = self.client.post('/api/measurements/upload/', {'image': test_image})
        
        self.assertEqual(response.status_code, 201)
        
        foot_image = FootImage.objects.get(id=response.json()['measurement_id'])
        self.assertEqual(foot_image.status, 'error')
        self.assertEqual(foot_image.error_message, "AI service temporarily unavailable")
    
    @patch('core.views.process_foot_image_enhanced')
    def test_foot_image_upload_success_path(self, mock_process):
        """Test successful processing path (lines 730-743)"""
        # Mock successful processing
        mock_process.return_value = (11.2, 4.3, 44.5, 29.1, None)
        
        test_image = SimpleUploadedFile('test.jpg', create_test_image(), content_type='image/jpeg')
        
        response = self.client.post('/api/measurements/upload/', {'image': test_image})
        
        self.assertEqual(response.status_code, 201)
        
        foot_image = FootImage.objects.get(id=response.json()['measurement_id'])
        self.assertEqual(foot_image.status, 'complete')
        self.assertEqual(foot_image.length_inches, 11.2)
        self.assertEqual(foot_image.width_inches, 4.3)
        self.assertEqual(foot_image.area_sqin, 44.5)
        self.assertEqual(foot_image.perimeter_inches, 29.1)
    
    @patch('core.views.process_foot_image_enhanced')
    def test_foot_image_upload_paper_size_parameter(self, mock_process):
        """Test paper_size parameter handling (lines 715-720)"""
        mock_process.return_value = (10.0, 4.0, 40.0, 26.0, None)
        
        test_image = SimpleUploadedFile('test.jpg', create_test_image(), content_type='image/jpeg')
        
        # Test with custom paper size
        response = self.client.post('/api/measurements/upload/', {
            'image': test_image,
            'paper_size': 'a4'
        })
        
        self.assertEqual(response.status_code, 201)
        # Verify process_foot_image_enhanced was called with correct paper size
        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        # paper_size is passed as the second positional argument
        self.assertEqual(args[1], 'a4')
    
    def test_foot_image_upload_exception_handling(self):
        """Test exception handling during processing (lines 744-752)"""
        test_image = SimpleUploadedFile('test.jpg', create_test_image(), content_type='image/jpeg')
        
        # Force an exception by mocking image.path to raise an error
        with patch.object(FootImage, 'save') as mock_save:
            def side_effect(*args, **kwargs):
                if mock_save.call_count == 1:
                    # Let the first save succeed (instance creation)
                    return
                else:
                    # Make the second save fail
                    raise Exception("Database connection lost")
            
            mock_save.side_effect = side_effect
            
            response = self.client.post('/api/measurements/upload/', {'image': test_image})
            
            # Should return 500 due to database error during processing
            self.assertEqual(response.status_code, 500)


class ViewsStrategicAPIEndpointsTest(TestCase):
    """Target lines 797-818, 825-830, 843-863, 906-911 - Legacy/deprecated endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create test shoes
        self.shoe = Shoe.objects.create(
            company='Nike', model='Test', gender='M', us_size=Decimal('10.5'),
            width_category='D', function='running', price_usd=Decimal('120'),
            product_url='https://example.com', insole_length=10.5, insole_width=4.0
        )
    
    def test_shoe_list_deprecated_endpoint(self):
        """Test deprecated shoe_list function (lines 797-818)"""
        from core.views import shoe_list
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.method = 'GET'
        
        response = shoe_list(request)
        
        # Should return some response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
    
    def test_shoe_detail_deprecated_endpoint(self):
        """Test deprecated shoe_detail function (lines 825-830)"""
        from core.views import shoe_detail
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.method = 'GET'
        
        response = shoe_detail(request, pk=self.shoe.id)
        
        # Should return shoe details
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
    
    def test_shoe_recommendations_legacy_endpoint(self):
        """Test legacy shoe_recommendations function (lines 843-863)"""
        self.client.login(username='testuser', password='testpass')
        
        # Create user measurement
        FootImage.objects.create(
            user=self.user, image='test.jpg', status='complete',
            length_inches=10.5, width_inches=4.0
        )
        
        from core.views import shoe_recommendations
        from django.http import HttpRequest
        from django.http import QueryDict
        
        request = HttpRequest()
        request.user = self.user
        request.method = 'GET'
        request.GET = QueryDict('length=10.5&width=4.0')
        
        response = shoe_recommendations(request)
        
        # Should return recommendations
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
    
    def test_shoe_list_with_scores_guest_user_path(self):
        """Test shoe list guest user handling (lines 906-911)"""
        # Test as guest (not logged in)
        response = self.client.get('/api/shoes/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Should not include fit scores for guest users
        if len(data) > 0:
            self.assertNotIn('fit_score', data[0])


class ViewsStrategicGuestSessionTest(TestCase):
    """Target lines 1025-1030, 1044-1045, 1081 - Guest session edge cases"""
    
    def setUp(self):
        self.client = Client()
    
    def test_recommendations_guest_no_session_key(self):
        """Test recommendations for guest without session key (lines 1025-1030)"""
        # Ensure no session exists
        response = self.client.get('/api/recommendations/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('measurement', data['error'].lower())
    
    def test_recommendations_guest_with_session_no_measurement(self):
        """Test guest with session but no measurements (lines 1044-1045)"""
        # Set up session but don't create any measurements
        session = self.client.session
        session['guest_session_id'] = 'empty_session_123'
        session.save()
        
        response = self.client.get('/api/recommendations/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_get_latest_measurement_guest_edge_case(self):
        """Test get_latest_measurement guest session edge case (line 1081)"""
        # Create a session and get the session key
        session = self.client.session
        session['dummy'] = 'value'  # Force session creation
        session.save()
        session_key = session.session_key
        
        # Create guest measurement with session
        FootImage.objects.create(
            user=None, image='guest.jpg', status='complete',
            length_inches=10.5, width_inches=4.0,
            error_message=f'GUEST_SESSION:{session_key}'
        )
        
        response = self.client.get('/api/measurements/latest/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['length_inches'], 10.5)
        self.assertEqual(data['width_inches'], 4.0)


class ViewsStrategicParametrizedTest(TestCase):
    """Use parametrized testing for comprehensive edge case coverage"""
    
    def test_parse_predictions_various_formats(self):
        """Test parse_predictions with multiple input formats"""
        from core.views import parse_predictions
        
        test_cases = [
            # Empty predictions
            ({'predictions': []}, (None, None)),
            # Missing predictions key
            ({}, (None, None)),
            # Invalid prediction format
            ({'predictions': [{'invalid': 'data'}]}, (None, None)),
            # Valid bounding box format with correct class_id
            ({
                'predictions': {
                    'predictions': [
                        {'x': 100, 'y': 50, 'width': 200, 'height': 300, 'class_id': 2},  # paper
                        {'x': 120, 'y': 70, 'width': 160, 'height': 260, 'class_id': 0}   # foot
                    ]
                }
            }, lambda result: result != (None, None)),
        ]
        
        for input_data, expected in test_cases:
            with self.subTest(input_data=input_data):
                result = parse_predictions(input_data)
                if callable(expected):
                    self.assertTrue(expected(result))
                else:
                    self.assertEqual(result, expected)
    
    def test_enhanced_scoring_edge_cases(self):
        """Test enhanced scoring functions with edge cases"""
        from core.views import enhanced_score_shoe, enhanced_score_shoe_4d
        
        edge_cases = [
            # Zero values
            (0, 0, 10, 4),
            # Negative values (should be handled gracefully)
            (-1, -1, 10, 4),
            # Very large values
            (1000, 1000, 10, 4),
            # Equal values (perfect fit)
            (10.5, 4.0, 10.5, 4.0),
        ]
        
        for user_l, user_w, shoe_l, shoe_w in edge_cases:
            with self.subTest(user_l=user_l, user_w=user_w, shoe_l=shoe_l, shoe_w=shoe_w):
                # 2D scoring
                score_2d = enhanced_score_shoe(user_l, user_w, shoe_l, shoe_w)
                self.assertGreaterEqual(score_2d, 0)
                self.assertLessEqual(score_2d, 100)
                
                # 4D scoring (with estimated area/perimeter)
                score_4d = enhanced_score_shoe_4d(
                    user_l, user_w, abs(user_l * user_w * 0.7), abs((user_l + user_w) * 2.2),
                    shoe_l, shoe_w, abs(shoe_l * shoe_w * 0.75), abs((shoe_l + shoe_w) * 2.3)
                )
                self.assertGreaterEqual(score_4d, 0)
                self.assertLessEqual(score_4d, 100)


class ViewsStrategicAuthenticationTest(TestCase):
    """Test authentication-related edge cases and branches"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_delete_account_comprehensive_validation(self):
        """Test all delete account validation branches"""
        self.client.login(username='testuser', password='testpass')
        
        # Test missing username
        response = self.client.delete('/api/auth/account/',
                                    data=json.dumps({'password': 'testpass'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing password
        response = self.client.delete('/api/auth/account/',
                                    data=json.dumps({'username': 'testuser'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test wrong username
        response = self.client.delete('/api/auth/account/',
                                    data=json.dumps({'username': 'wronguser', 'password': 'testpass'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username confirmation failed', response.json()['error'])
        
        # Test wrong password
        response = self.client.delete('/api/auth/account/',
                                    data=json.dumps({'username': 'testuser', 'password': 'wrongpass'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid password', response.json()['error'])
        
        # Test successful deletion
        response = self.client.delete('/api/auth/account/',
                                    data=json.dumps({'username': 'testuser', 'password': 'testpass'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # User should be deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())