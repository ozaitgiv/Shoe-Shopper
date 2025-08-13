#!/usr/bin/env python3
"""
Comprehensive unit tests for improved penalty functions
"""
import unittest
import os
import django
import sys

# Setup Django environment for testing
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoe_shopper.settings')
django.setup()

from core.views import (
    enhanced_score_shoe_4d,
    enhanced_score_shoe,
    estimate_perimeter_score,
    estimate_area_score,
    get_clearances_by_shoe_type,
    FIT_THRESHOLDS,
    # Constants for validation
    PERIMETER_PERFECT_MIN, PERIMETER_PERFECT_MAX, PERIMETER_TIGHT_THRESHOLD, PERIMETER_MAX_RATIO,
    AREA_PERFECT_MIN, AREA_PERFECT_MAX, AREA_TIGHT_THRESHOLD, AREA_MAX_RATIO,
    LENGTH_TIGHT_THRESHOLD, LENGTH_MODERATE_THRESHOLD, LENGTH_MAX_RATIO,
    WIDTH_PERFECT_THRESHOLD, WIDTH_GOOD_THRESHOLD, WIDTH_ACCEPTABLE_THRESHOLD, WIDTH_MAX_THRESHOLD
)


class TestPenaltyFunctionConstants(unittest.TestCase):
    """Test all constants are logically ordered and reasonable"""
    
    def test_perimeter_constants_ordering(self):
        """Perimeter constants should be in ascending order"""
        self.assertLess(PERIMETER_PERFECT_MIN, PERIMETER_PERFECT_MAX)
        self.assertLess(PERIMETER_PERFECT_MAX, PERIMETER_TIGHT_THRESHOLD)
        self.assertLess(PERIMETER_TIGHT_THRESHOLD, PERIMETER_MAX_RATIO)
    
    def test_area_constants_ordering(self):
        """Area constants should be in ascending order"""
        self.assertLess(AREA_PERFECT_MIN, AREA_PERFECT_MAX)
        self.assertLess(AREA_PERFECT_MAX, AREA_TIGHT_THRESHOLD)
        self.assertLess(AREA_TIGHT_THRESHOLD, AREA_MAX_RATIO)
    
    def test_length_constants_ordering(self):
        """Length constants should be in ascending order"""
        self.assertLess(1.0, LENGTH_TIGHT_THRESHOLD)
        self.assertLess(LENGTH_TIGHT_THRESHOLD, LENGTH_MODERATE_THRESHOLD)
        self.assertLess(LENGTH_MODERATE_THRESHOLD, LENGTH_MAX_RATIO)
    
    def test_width_constants_ordering(self):
        """Width constants should be in ascending order"""
        self.assertLess(0, WIDTH_PERFECT_THRESHOLD)
        self.assertLess(WIDTH_PERFECT_THRESHOLD, WIDTH_GOOD_THRESHOLD)
        self.assertLess(WIDTH_GOOD_THRESHOLD, WIDTH_ACCEPTABLE_THRESHOLD)
        self.assertLess(WIDTH_ACCEPTABLE_THRESHOLD, WIDTH_MAX_THRESHOLD)
    
    def test_fit_thresholds_ordering(self):
        """Fit thresholds should be in ascending order"""
        self.assertLess(FIT_THRESHOLDS['POOR'], FIT_THRESHOLDS['FAIR'])
        self.assertLess(FIT_THRESHOLDS['FAIR'], FIT_THRESHOLDS['GOOD'])
        self.assertLess(FIT_THRESHOLDS['GOOD'], FIT_THRESHOLDS['EXCELLENT'])
    
    def test_constants_reasonable_ranges(self):
        """Constants should be within reasonable ranges"""
        # Perimeter variations shouldn't be extreme
        self.assertLess(PERIMETER_PERFECT_MAX - PERIMETER_PERFECT_MIN, 0.25)
        # Area variations shouldn't be extreme
        self.assertLess(AREA_PERFECT_MAX - AREA_PERFECT_MIN, 0.25)
        # Width tolerances should be reasonable percentages
        self.assertLess(WIDTH_MAX_THRESHOLD, 0.30)  # Max 30% width difference


class TestEnhancedScoring4D(unittest.TestCase):
    """Test the main 4D scoring function"""
    
    def setUp(self):
        """Set up test data"""
        self.user_length = 10.5
        self.user_width = 3.8
        self.user_area = 26.25
        self.user_perimeter = 25.5
        self.shoe_length = 10.5
        self.shoe_width = 3.8
        self.shoe_area = 28.125
        self.shoe_perimeter = 27.0
        self.shoe_type = "casual"
    
    def test_perfect_fit_score(self):
        """Perfect fit should score very high"""
        score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            self.shoe_length, self.shoe_width, self.shoe_area, self.shoe_perimeter,
            self.shoe_type
        )
        self.assertGreaterEqual(score, 80)
        self.assertLessEqual(score, 100)
    
    def test_score_range_validation(self):
        """All scores should be between 0 and 100"""
        test_cases = [
            # Normal cases
            (10.5, 3.8, 26.25, 25.5, 10.5, 3.8, 28.125, 27.0),
            # Tight cases
            (10.5, 3.8, 26.25, 25.5, 10.0, 3.5, 24.0, 25.0),
            # Loose cases
            (10.5, 3.8, 26.25, 25.5, 11.5, 4.2, 32.0, 30.0),
            # Extreme cases
            (10.5, 3.8, 26.25, 25.5, 9.0, 3.0, 20.0, 22.0)
        ]
        
        for user_l, user_w, user_a, user_p, shoe_l, shoe_w, shoe_a, shoe_p in test_cases:
            score = enhanced_score_shoe_4d(
                user_l, user_w, user_a, user_p,
                shoe_l, shoe_w, shoe_a, shoe_p, "casual"
            )
            self.assertGreaterEqual(score, 0, f"Score below 0 for case {test_cases.index((user_l, user_w, user_a, user_p, shoe_l, shoe_w, shoe_a, shoe_p))}")
            self.assertLessEqual(score, 100, f"Score above 100 for case {test_cases.index((user_l, user_w, user_a, user_p, shoe_l, shoe_w, shoe_a, shoe_p))}")
    
    def test_invalid_input_handling(self):
        """Invalid inputs should return 0"""
        invalid_cases = [
            (0, 3.8, 26.25, 25.5, 10.5, 3.8, 28.125, 27.0),  # Zero user length
            (10.5, 0, 26.25, 25.5, 10.5, 3.8, 28.125, 27.0),  # Zero user width
            (10.5, 3.8, 26.25, 25.5, 0, 3.8, 28.125, 27.0),  # Zero shoe length
            (10.5, 3.8, 26.25, 25.5, 10.5, 0, 28.125, 27.0),  # Zero shoe width
            (-1, 3.8, 26.25, 25.5, 10.5, 3.8, 28.125, 27.0),  # Negative value
            (None, 3.8, 26.25, 25.5, 10.5, 3.8, 28.125, 27.0),  # None value
        ]
        
        for case in invalid_cases:
            score = enhanced_score_shoe_4d(*case, "casual")
            self.assertEqual(score, 0, f"Invalid case should return 0: {case}")
    
    def test_shoe_type_clearances(self):
        """Different shoe types should apply different clearances"""
        base_score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            self.shoe_length, self.shoe_width, self.shoe_area, self.shoe_perimeter,
            "casual"
        )
        
        hiking_score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            self.shoe_length, self.shoe_width, self.shoe_area, self.shoe_perimeter,
            "hiking"
        )
        
        # Hiking shoes need more clearance, so same shoe should score lower
        self.assertLess(hiking_score, base_score)
    
    def test_length_penalty_smoothness(self):
        """Length penalties should be smooth, not abrupt"""
        length_ratios = [0.95, 1.00, 1.02, 1.05, 1.08, 1.10]
        scores = []
        
        for ratio in length_ratios:
            test_shoe_length = self.user_length / ratio  # Adjust for clearances
            score = enhanced_score_shoe_4d(
                self.user_length, self.user_width, self.user_area, self.user_perimeter,
                test_shoe_length, self.shoe_width, self.shoe_area, self.shoe_perimeter,
                "casual"
            )
            scores.append(score)
        
        # Check no sudden drops > 20 points between adjacent ratios
        for i in range(1, len(scores)):
            score_drop = scores[i-1] - scores[i]
            self.assertLess(score_drop, 20, f"Sudden score drop at ratio {length_ratios[i]}: {score_drop}")
    
    def test_width_tolerance_improvements(self):
        """Width tolerance should be more forgiving than before"""
        # Test 10% width difference (was 0 score in old algorithm)
        narrow_shoe_width = self.user_width * 0.9  # 10% narrower
        score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            self.shoe_length, narrow_shoe_width, self.shoe_area, self.shoe_perimeter,
            "casual"
        )
        
        # Should get meaningful score, not zero
        self.assertGreater(score, 50, "10% width difference should still be wearable")
        
        # Test 15% width difference
        very_narrow_width = self.user_width * 0.85
        score_15 = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            self.shoe_length, very_narrow_width, self.shoe_area, self.shoe_perimeter,
            "casual"
        )
        
        # Should still get some score
        self.assertGreater(score_15, 30, "15% width difference should still get some score")


class TestLegacyCompatibility(unittest.TestCase):
    """Test backward compatibility with legacy functions"""
    
    def test_enhanced_score_shoe_compatibility(self):
        """Legacy enhanced_score_shoe should work and give similar results"""
        user_length = 10.5
        user_width = 3.8
        shoe_length = 10.5
        shoe_width = 3.8
        
        legacy_score = enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width)
        
        # Should return valid score
        self.assertGreaterEqual(legacy_score, 0)
        self.assertLessEqual(legacy_score, 100)
        
        # Should be reasonably high for perfect fit
        self.assertGreater(legacy_score, 75)


class TestEstimationFunctions(unittest.TestCase):
    """Test perimeter and area estimation functions"""
    
    def test_estimate_perimeter_score(self):
        """Perimeter estimation should work with improved logic"""
        # Perfect perimeter fit
        score = estimate_perimeter_score(10.5, 3.8, 10.5, 3.8)
        self.assertGreater(score, 90)
        
        # Slightly different perimeter
        score_diff = estimate_perimeter_score(10.5, 3.8, 10.3, 3.9)
        self.assertGreater(score_diff, 70)
    
    def test_estimate_area_score(self):
        """Area estimation should work with improved logic"""
        # Perfect area fit
        score = estimate_area_score(10.5, 3.8, 10.5, 3.8)
        self.assertGreater(score, 90)
        
        # Slightly different area
        score_diff = estimate_area_score(10.5, 3.8, 10.3, 3.9)
        self.assertGreater(score_diff, 80)


class TestClearances(unittest.TestCase):
    """Test clearance functions"""
    
    def test_clearance_consistency(self):
        """All clearances should be positive and consistent"""
        shoe_types = ['casual', 'running', 'hiking', 'work']
        
        for shoe_type in shoe_types:
            clearances = get_clearances_by_shoe_type(shoe_type)
            
            # All clearances should be positive
            for key, value in clearances.items():
                self.assertGreater(value, 0, f"{shoe_type}.{key} clearance should be positive")
            
            # Required keys should exist
            required_keys = ['length', 'width', 'perimeter', 'area']
            for key in required_keys:
                self.assertIn(key, clearances, f"{shoe_type} missing {key} clearance")
    
    def test_clearance_ordering(self):
        """Activity shoe types should have higher clearances"""
        casual = get_clearances_by_shoe_type('casual')
        running = get_clearances_by_shoe_type('running')
        hiking = get_clearances_by_shoe_type('hiking')
        
        # Running and hiking should have higher clearances than casual
        self.assertGreater(running['length'], casual['length'])
        self.assertGreater(hiking['length'], casual['length'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_extreme_ratios(self):
        """Test extreme size ratios don't break the algorithm"""
        user_length = 10.5
        user_width = 3.8
        user_area = 26.25
        user_perimeter = 25.5
        
        extreme_cases = [
            # Very tight shoes
            (8.0, 3.0, 18.0, 20.0),
            # Very loose shoes  
            (13.0, 5.0, 40.0, 35.0),
            # Weird aspect ratios
            (15.0, 2.0, 22.5, 34.0),
            (8.0, 6.0, 36.0, 28.0)
        ]
        
        for shoe_l, shoe_w, shoe_a, shoe_p in extreme_cases:
            score = enhanced_score_shoe_4d(
                user_length, user_width, user_area, user_perimeter,
                shoe_l, shoe_w, shoe_a, shoe_p, "casual"
            )
            
            # Should not crash and should return valid score
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
    
    def test_none_area_perimeter_handling(self):
        """Test handling when area/perimeter are None"""
        score = enhanced_score_shoe_4d(
            10.5, 3.8, None, None,
            10.5, 3.8, None, None, "casual"
        )
        
        # Should fallback to estimation and not crash
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_boundary_threshold_scores(self):
        """Test scores exactly at threshold boundaries"""
        # Create scenarios that hit exact threshold values
        user_length = 10.0
        user_width = 4.0
        user_area = 25.0
        user_perimeter = 25.0
        
        # Test length ratio exactly at tight threshold (1.02)
        tight_shoe_length = (user_length + 0.25) / LENGTH_TIGHT_THRESHOLD  # Add clearance then divide
        score = enhanced_score_shoe_4d(
            user_length, user_width, user_area, user_perimeter,
            tight_shoe_length, user_width, user_area, user_perimeter, "casual"
        )
        
        # Should handle boundary correctly
        self.assertGreater(score, 70)  # Should be in good range


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_function_execution_time(self):
        """Function should execute quickly"""
        import time
        
        start_time = time.time()
        
        # Run many calculations
        for _ in range(1000):
            enhanced_score_shoe_4d(10.5, 3.8, 26.25, 25.5, 10.5, 3.8, 28.125, 27.0, "casual")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete 1000 calculations in reasonable time
        self.assertLess(execution_time, 1.0, "Function should be performant")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)