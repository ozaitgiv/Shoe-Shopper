"""
Comprehensive tests for image processing and utility functions
Each test focuses on exactly one behavior
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from unittest.mock import patch, MagicMock, call
import tempfile
import os
import json

from .models import FootImage, Shoe
from .views import (
    parse_predictions,
    process_foot_segmentation_data,
    calculate_hybrid_measurements,
    process_insole_segmentation_data,
    estimate_foot_area_from_dimensions,
    estimate_foot_perimeter_from_dimensions,
    estimate_shoe_area_from_dimensions,
    estimate_shoe_perimeter_from_dimensions,
    get_real_shoe_dimensions,
    get_real_shoe_dimensions_4d,
    estimate_perimeter_score,
    estimate_area_score,
    get_clearances_by_shoe_type,
    cleanup_old_guest_sessions
)


class ParsePredictionsTest(TestCase):
    """Test the parse_predictions function"""
    
    def test_parse_predictions_with_valid_foot_and_paper_data(self):
        """Test parsing when both foot and paper predictions exist"""
        result_json = {
            'predictions': {
                'predictions': [
                    {
                        'class_id': 0,  # foot
                        'width': 10.5,
                        'height': 4.0
                    },
                    {
                        'class_id': 2,  # paper 
                        'width': 8.5,
                        'height': 11.0
                    }
                ]
            }
        }
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        self.assertEqual(foot_dims, (10.5, 4.0))
        self.assertEqual(paper_dims, (8.5, 11.0))
        
    def test_parse_predictions_with_only_foot_data(self):
        """Test parsing when only foot predictions exist"""
        result_json = {
            'predictions': {
                'predictions': [
                    {
                        'class_id': 0,  # foot
                        'width': 10.5,
                        'height': 4.0
                    }
                ]
            }
        }
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        self.assertEqual(foot_dims, (10.5, 4.0))
        self.assertIsNone(paper_dims)
        
    def test_parse_predictions_with_only_paper_data(self):
        """Test parsing when only paper predictions exist"""
        result_json = {
            'predictions': {
                'predictions': [
                    {
                        'class_id': 2,  # paper
                        'width': 8.5,
                        'height': 11.0
                    }
                ]
            }
        }
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        self.assertIsNone(foot_dims)
        self.assertEqual(paper_dims, (8.5, 11.0))
        
    def test_parse_predictions_with_empty_predictions(self):
        """Test parsing when predictions array is empty"""
        result_json = {'predictions': {'predictions': []}}
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        self.assertIsNone(foot_dims)
        self.assertIsNone(paper_dims)
        
    def test_parse_predictions_with_no_predictions_key(self):
        """Test parsing when predictions key doesn't exist"""
        result_json = {}
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        self.assertIsNone(foot_dims)
        self.assertIsNone(paper_dims)
        
    def test_parse_predictions_with_malformed_data(self):
        """Test parsing when data is malformed"""
        result_json = {
            'predictions': {
                'predictions': [
                    {
                        'class_id': 0,  # foot
                        'width': 10.5
                        # Missing height
                    }
                ]
            }
        }
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        # Should handle gracefully - might return partial data
        # In this case it gets width but not height, so returns (10.5, None)
        self.assertIsInstance(foot_dims, tuple)
        self.assertIsNone(paper_dims)
        
    def test_parse_predictions_with_unknown_class_id(self):
        """Test parsing when prediction has unknown class_id"""
        result_json = {
            'predictions': {
                'predictions': [
                    {
                        'class_id': 99,  # unknown
                        'width': 10.0,
                        'height': 4.0
                    }
                ]
            }
        }
        
        paper_dims, foot_dims = parse_predictions(result_json)
        
        self.assertIsNone(foot_dims)
        self.assertIsNone(paper_dims)


class DimensionEstimationTest(TestCase):
    """Test dimension estimation functions"""
    
    def test_estimate_foot_area_from_dimensions_normal_foot(self):
        """Test foot area estimation for normal-sized foot"""
        area = estimate_foot_area_from_dimensions(10.5, 4.0)
        
        # Should be reasonable foot area (using foot shape factor)
        expected_approx = 10.5 * 4.0 * 0.7  # 29.4 square inches
        self.assertAlmostEqual(area, expected_approx, places=1)
        
    def test_estimate_foot_area_from_dimensions_small_foot(self):
        """Test foot area estimation for small foot"""
        area = estimate_foot_area_from_dimensions(8.0, 3.0)
        
        expected_approx = 8.0 * 3.0 * 0.7  # 16.8 square inches
        self.assertAlmostEqual(area, expected_approx, places=1)
        
    def test_estimate_foot_area_from_dimensions_large_foot(self):
        """Test foot area estimation for large foot"""
        area = estimate_foot_area_from_dimensions(12.0, 5.0)
        
        expected_approx = 12.0 * 5.0 * 0.7  # 42.0 square inches
        self.assertAlmostEqual(area, expected_approx, places=1)
        
    def test_estimate_foot_perimeter_from_dimensions_normal_foot(self):
        """Test foot perimeter estimation for normal-sized foot"""
        perimeter = estimate_foot_perimeter_from_dimensions(10.5, 4.0)
        
        # Should be reasonable - foot perimeter is complex shape
        self.assertGreater(perimeter, 0)
        self.assertLess(perimeter, 100)  # Sanity check
        
    def test_estimate_foot_perimeter_uses_ellipse_formula(self):
        """Test that foot perimeter uses elliptical approximation"""
        length = 10.0
        width = 4.0
        perimeter = estimate_foot_perimeter_from_dimensions(length, width)
        
        # Should be significantly more than simple rectangle
        rectangle_perimeter = 2 * (length + width)
        self.assertGreater(perimeter, rectangle_perimeter)
        
    def test_estimate_shoe_area_from_dimensions(self):
        """Test shoe area estimation"""
        area = estimate_shoe_area_from_dimensions(10.5, 4.0)
        
        # Shoe area should be slightly larger than foot area
        foot_area = estimate_foot_area_from_dimensions(10.5, 4.0)
        self.assertGreater(area, foot_area)
        
    def test_estimate_shoe_perimeter_from_dimensions(self):
        """Test shoe perimeter estimation"""
        perimeter = estimate_shoe_perimeter_from_dimensions(10.5, 4.0)
        
        # Shoe perimeter should be reasonable
        self.assertGreater(perimeter, 0)
        self.assertLess(perimeter, 100)


class GetShoeDimensionsTest(TestCase):
    """Test get_real_shoe_dimensions functions"""
    
    def setUp(self):
        self.shoe_with_measurements = Shoe.objects.create(
            company='Nike',
            model='Measured Shoe',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://example.com',
            insole_length=10.8,
            insole_width=4.2,
            insole_area=45.0,
            insole_perimeter=30.0
        )
        
        self.shoe_without_measurements = Shoe.objects.create(
            company='Adidas',
            model='Unmeasured Shoe',
            gender='M',
            us_size=Decimal('11.0'),
            width_category='W',
            function='casual',
            price_usd=Decimal('100.00'),
            product_url='https://example.com'
        )
        
    def test_get_real_shoe_dimensions_with_measurements(self):
        """Test getting dimensions when shoe has real measurements"""
        length, width = get_real_shoe_dimensions(self.shoe_with_measurements)
        
        self.assertEqual(length, 10.8)
        self.assertEqual(width, 4.2)
        
    def test_get_real_shoe_dimensions_without_measurements(self):
        """Test getting dimensions when shoe lacks measurements"""
        length, width = get_real_shoe_dimensions(self.shoe_without_measurements)
        
        # Should fall back to size-based estimates
        self.assertIsInstance(length, float)
        self.assertIsInstance(width, float)
        self.assertGreater(length, 0)
        self.assertGreater(width, 0)
        
    def test_get_real_shoe_dimensions_4d_with_all_measurements(self):
        """Test 4D dimensions when shoe has all measurements"""
        length, width, area, perimeter = get_real_shoe_dimensions_4d(self.shoe_with_measurements)
        
        self.assertEqual(length, 10.8)
        self.assertEqual(width, 4.2)
        self.assertEqual(area, 45.0)
        self.assertEqual(perimeter, 30.0)
        
    def test_get_real_shoe_dimensions_4d_with_partial_measurements(self):
        """Test 4D dimensions when shoe has only length/width"""
        # Shoe with only length and width
        shoe = Shoe.objects.create(
            company='Partial',
            model='Partial Shoe',
            gender='M',
            us_size=Decimal('10.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('80.00'),
            product_url='https://example.com',
            insole_length=10.0,
            insole_width=4.0
            # No area or perimeter
        )
        
        length, width, area, perimeter = get_real_shoe_dimensions_4d(shoe)
        
        self.assertEqual(length, 10.0)
        self.assertEqual(width, 4.0)
        # Area and perimeter should be estimated
        self.assertIsInstance(area, float)
        self.assertIsInstance(perimeter, float)
        self.assertGreater(area, 0)
        self.assertGreater(perimeter, 0)
        
    def test_get_real_shoe_dimensions_4d_without_measurements(self):
        """Test 4D dimensions when shoe has no measurements"""
        length, width, area, perimeter = get_real_shoe_dimensions_4d(self.shoe_without_measurements)
        
        # All should be estimated based on size
        self.assertIsInstance(length, float)
        self.assertIsInstance(width, float)
        self.assertIsInstance(area, float)
        self.assertIsInstance(perimeter, float)
        self.assertGreater(length, 0)
        self.assertGreater(width, 0)
        self.assertGreater(area, 0)
        self.assertGreater(perimeter, 0)


class ScoringFunctionsTest(TestCase):
    """Test scoring calculation functions"""
    
    def test_estimate_perimeter_score_perfect_match(self):
        """Test perimeter scoring with perfect match"""
        score = estimate_perimeter_score(10.5, 4.0, 10.5, 4.0)
        
        # Perfect match should give high score
        self.assertGreaterEqual(score, 90)
        
    def test_estimate_perimeter_score_close_match(self):
        """Test perimeter scoring with close match"""
        score = estimate_perimeter_score(10.5, 4.0, 10.7, 4.1)
        
        # Close match should give excellent score (improved algorithm has extended perfect zones)
        self.assertGreaterEqual(score, 90)
        self.assertLessEqual(score, 100)
        
    def test_estimate_perimeter_score_poor_match(self):
        """Test perimeter scoring with poor match"""
        score = estimate_perimeter_score(10.5, 4.0, 12.0, 5.0)
        
        # Poor match should give lower score than perfect match
        perfect_score = estimate_perimeter_score(10.5, 4.0, 10.5, 4.0)
        self.assertLess(score, perfect_score)
        
    def test_estimate_area_score_perfect_match(self):
        """Test area scoring with perfect match"""
        score = estimate_area_score(10.5, 4.0, 10.5, 4.0)
        
        # Perfect match should give high score
        self.assertGreaterEqual(score, 90)
        
    def test_estimate_area_score_close_match(self):
        """Test area scoring with close match"""
        score = estimate_area_score(10.5, 4.0, 10.7, 4.1)
        
        # Close match should give excellent score (improved algorithm has extended perfect zones)
        self.assertGreaterEqual(score, 90)
        self.assertLessEqual(score, 100)
        
    def test_estimate_area_score_poor_match(self):
        """Test area scoring with poor match"""
        score = estimate_area_score(10.5, 4.0, 12.0, 5.0)
        
        # Poor match should give lower score than perfect match
        perfect_score = estimate_area_score(10.5, 4.0, 10.5, 4.0)
        self.assertLess(score, perfect_score)


class GetClearancesTest(TestCase):
    """Test get_clearances_by_shoe_type function"""
    
    def test_get_clearances_running_shoes(self):
        """Test clearances for running shoes"""
        clearances = get_clearances_by_shoe_type('running')
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)
        self.assertIsInstance(clearances['length'], (int, float))
        self.assertIsInstance(clearances['width'], (int, float))
        
    def test_get_clearances_hiking_shoes(self):
        """Test clearances for hiking shoes"""
        clearances = get_clearances_by_shoe_type('hiking')
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)
        # Hiking shoes typically need more clearance
        running_clearances = get_clearances_by_shoe_type('running')
        self.assertGreaterEqual(clearances['length'], running_clearances['length'])
        
    def test_get_clearances_work_shoes(self):
        """Test clearances for work shoes"""
        clearances = get_clearances_by_shoe_type('work')
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)
        
    def test_get_clearances_casual_shoes(self):
        """Test clearances for casual shoes"""
        clearances = get_clearances_by_shoe_type('casual')
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)
        
    def test_get_clearances_unknown_shoe_type(self):
        """Test clearances for unknown shoe type returns default"""
        clearances = get_clearances_by_shoe_type('unknown_type')
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)
        # Should return reasonable default values
        self.assertGreater(clearances['length'], 0)
        self.assertGreater(clearances['width'], 0)
        
    def test_get_clearances_empty_shoe_type(self):
        """Test clearances for empty shoe type"""
        clearances = get_clearances_by_shoe_type('')
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)
        
    def test_get_clearances_none_shoe_type(self):
        """Test clearances for None shoe type"""
        clearances = get_clearances_by_shoe_type(None)
        
        self.assertIn('length', clearances)
        self.assertIn('width', clearances)


class CleanupFunctionTest(TestCase):
    """Test cleanup_old_guest_sessions function"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test123')
        
    def test_cleanup_old_guest_sessions_runs_without_error(self):
        """Test cleanup function can run without throwing errors"""
        try:
            cleanup_old_guest_sessions()
        except Exception as e:
            self.fail(f"cleanup_old_guest_sessions raised {e}")
            
    def test_cleanup_old_guest_sessions_preserves_user_images(self):
        """Test cleanup doesn't affect images with real users"""
        # Create user image
        user_image = FootImage.objects.create(
            user=self.user,
            image='user_image.jpg',
            status='complete'
        )
        
        cleanup_old_guest_sessions()
        
        # User image should still exist
        self.assertTrue(FootImage.objects.filter(id=user_image.id).exists())
        
    def test_cleanup_old_guest_sessions_preserves_recent_guest_images(self):
        """Test cleanup preserves recent guest images"""
        # Create recent guest image (will have recent timestamp)
        guest_image = FootImage.objects.create(
            user=None,
            image='recent_guest.jpg',
            status='complete',
            error_message='GUEST_SESSION:recent123'
        )
        
        cleanup_old_guest_sessions()
        
        # Recent guest image should still exist
        self.assertTrue(FootImage.objects.filter(id=guest_image.id).exists())
        
    def test_cleanup_old_guest_sessions_preserves_non_guest_session_images(self):
        """Test cleanup preserves images without guest session markers"""
        # Create image without guest session marker
        image = FootImage.objects.create(
            user=None,
            image='no_session.jpg',
            status='complete'
        )
        
        cleanup_old_guest_sessions()
        
        # Image should still exist (no guest session marker)
        self.assertTrue(FootImage.objects.filter(id=image.id).exists())