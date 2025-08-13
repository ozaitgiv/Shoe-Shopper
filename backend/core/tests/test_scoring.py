from django.test import TestCase
from decimal import Decimal

from core.views import (
    enhanced_score_shoe, enhanced_score_shoe_4d, 
    estimate_foot_area_from_dimensions, estimate_foot_perimeter_from_dimensions,
    get_real_shoe_dimensions_4d
)
from core.models import Shoe


class ScoringAlgorithmTest(TestCase):
    def test_enhanced_score_shoe_perfect_fit(self):
        """Test scoring algorithm with perfect fit"""
        user_length = 10.5
        user_width = 4.0
        shoe_length = 10.5
        shoe_width = 4.0
        
        score = enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width)
        self.assertGreaterEqual(score, 85)  # Should be excellent fit
        
    def test_enhanced_score_shoe_too_small(self):
        """Test scoring algorithm with too small shoe"""
        user_length = 10.5
        user_width = 4.0
        shoe_length = 9.0  # Much too small
        shoe_width = 3.5
        
        score = enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width)
        self.assertLess(score, 60)  # Should be poor fit
        
    def test_enhanced_score_shoe_too_big(self):
        """Test scoring algorithm with oversized shoe"""
        user_length = 10.5
        user_width = 4.0
        shoe_length = 12.0  # Much too big
        shoe_width = 5.0
        
        score = enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width)
        self.assertLess(score, 75)  # Should be fair to poor fit
        
    def test_enhanced_score_shoe_4d_perfect_fit(self):
        """Test 4D scoring algorithm with perfect fit"""
        user_length = 10.5
        user_width = 4.0
        user_area = 42.0
        user_perimeter = 28.0
        
        shoe_length = 10.5
        shoe_width = 4.0
        shoe_area = 42.0
        shoe_perimeter = 28.0
        
        score = enhanced_score_shoe_4d(
            user_length, user_width, user_area, user_perimeter,
            shoe_length, shoe_width, shoe_area, shoe_perimeter
        )
        self.assertGreaterEqual(score, 75)
        
    def test_estimate_foot_area_from_dimensions(self):
        """Test foot area estimation function"""
        length = 10.5
        width = 4.0
        area = estimate_foot_area_from_dimensions(length, width)
        
        # Area should be reasonable (less than length * width but more than 0)
        self.assertGreater(area, 0)
        self.assertLess(area, length * width)
        
    def test_estimate_foot_perimeter_from_dimensions(self):
        """Test foot perimeter estimation function"""
        length = 10.5
        width = 4.0
        perimeter = estimate_foot_perimeter_from_dimensions(length, width)
        
        # Perimeter should be reasonable
        self.assertGreater(perimeter, 0)
        # Should be more than a simple rectangle perimeter due to foot shape
        self.assertGreater(perimeter, 2 * (length + width))


class ShoeRecommendationTest(TestCase):
    def setUp(self):
        # Create test shoes
        self.shoe1 = Shoe.objects.create(
            company='Nike',
            model='Air Max 90',
            gender='M',
            us_size=Decimal('10.5'),
            width_category='D',
            function='running',
            price_usd=Decimal('120.00'),
            product_url='https://nike.com/air-max-90',
            insole_length=10.5,
            insole_width=4.0
        )
        
        self.shoe2 = Shoe.objects.create(
            company='Adidas',
            model='Ultraboost',
            gender='M',
            us_size=Decimal('11.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('180.00'),
            product_url='https://adidas.com/ultraboost',
            insole_length=11.0,
            insole_width=4.2
        )
        
    def test_get_real_shoe_dimensions_4d_with_measurements(self):
        """Test getting real shoe dimensions when measurements exist"""
        length, width, area, perimeter = get_real_shoe_dimensions_4d(self.shoe1)
        
        self.assertEqual(length, 10.5)
        self.assertEqual(width, 4.0)
        self.assertGreater(area, 0)
        self.assertGreater(perimeter, 0)
        
    def test_get_real_shoe_dimensions_4d_without_measurements(self):
        """Test getting shoe dimensions when no measurements exist"""
        # Create shoe without measurements
        shoe_no_measurements = Shoe.objects.create(
            company='Puma',
            model='Runner',
            gender='M',
            us_size=Decimal('10.0'),
            width_category='D',
            function='running',
            price_usd=Decimal('100.00'),
            product_url='https://puma.com/runner'
        )
        
        length, width, area, perimeter = get_real_shoe_dimensions_4d(shoe_no_measurements)
        
        # Should fall back to size-based estimates
        self.assertGreater(length, 0)
        self.assertGreater(width, 0)
        self.assertGreater(area, 0)
        self.assertGreater(perimeter, 0)