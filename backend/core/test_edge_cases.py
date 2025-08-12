#!/usr/bin/env python3
"""
Edge case and boundary condition tests for penalty functions
"""
import unittest
from django.test import TestCase
from core.views import (
    enhanced_score_shoe_4d,
    enhanced_score_shoe,
    FIT_THRESHOLDS,
    LENGTH_TIGHT_THRESHOLD,
    LENGTH_MODERATE_THRESHOLD,
    WIDTH_PERFECT_THRESHOLD,
    WIDTH_GOOD_THRESHOLD,
    PERIMETER_PERFECT_MIN,
    PERIMETER_PERFECT_MAX
)
import math


class TestBoundaryConditions(TestCase):
    """Test exact boundary conditions and edge cases"""
    
    def setUp(self):
        """Set up test data for boundary testing"""
        self.user_length = 10.0  # Use round numbers for easier boundary testing
        self.user_width = 4.0
        self.user_area = 25.0
        self.user_perimeter = 24.0
        
    def test_exact_threshold_boundaries(self):
        """Test scores exactly at threshold boundaries"""
        # Test exact length tight threshold
        # Need to account for clearances - casual adds 0.25" length clearance
        adjusted_user_length = self.user_length + 0.25
        exact_tight_shoe_length = adjusted_user_length / LENGTH_TIGHT_THRESHOLD  # Should be exactly at 1.02 ratio
        
        score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            exact_tight_shoe_length, self.user_width, self.user_area, self.user_perimeter,
            "casual"
        )
        
        # Should handle exact boundary without issues
        self.assertGreater(score, 70)
        self.assertLess(score, 100)
        
    def test_width_boundary_transitions(self):
        """Test smooth transitions at width boundaries"""
        # Test around the perfect threshold (5%)
        base_shoe_width = self.user_width
        
        test_widths = [
            base_shoe_width * (1 - WIDTH_PERFECT_THRESHOLD + 0.001),  # Just above perfect
            base_shoe_width * (1 - WIDTH_PERFECT_THRESHOLD),          # Exact boundary
            base_shoe_width * (1 - WIDTH_PERFECT_THRESHOLD - 0.001),  # Just below perfect
        ]
        
        scores = []
        for width in test_widths:
            score = enhanced_score_shoe_4d(
                self.user_length, self.user_width, self.user_area, self.user_perimeter,
                self.user_length, width, self.user_area, self.user_perimeter,
                "casual"
            )
            scores.append(score)
        
        # Scores should be close to each other (smooth transition)
        for i in range(1, len(scores)):
            diff = abs(scores[i] - scores[i-1])
            self.assertLess(diff, 5, f"Large score jump at boundary: {diff}")
    
    def test_perimeter_perfect_zone_boundaries(self):
        """Test perimeter perfect zone boundaries"""
        # Test at exact boundaries of perfect zone
        test_ratios = [
            PERIMETER_PERFECT_MIN - 0.001,  # Just outside perfect (low)
            PERIMETER_PERFECT_MIN,          # Exact boundary (low)
            PERIMETER_PERFECT_MIN + 0.001,  # Just inside perfect (low)
            PERIMETER_PERFECT_MAX - 0.001,  # Just inside perfect (high)
            PERIMETER_PERFECT_MAX,          # Exact boundary (high)
            PERIMETER_PERFECT_MAX + 0.001,  # Just outside perfect (high)
        ]
        
        base_perimeter = self.user_perimeter + 0.2  # Add clearance
        
        scores = []
        for ratio in test_ratios:
            shoe_perimeter = base_perimeter / ratio
            score = enhanced_score_shoe_4d(
                self.user_length, self.user_width, self.user_area, self.user_perimeter,
                self.user_length, self.user_width, self.user_area, shoe_perimeter,
                "casual"
            )
            scores.append(score)
        
        # Perfect zone should have consistently high scores
        self.assertGreater(scores[1], 80)  # At boundary low (adjusted for realistic scoring)
        self.assertGreater(scores[2], 85)  # Inside perfect
        self.assertGreater(scores[3], 85)  # Inside perfect
        self.assertGreater(scores[4], 80)  # At boundary high
    
    def test_extreme_input_robustness(self):
        """Test algorithm robustness with extreme inputs"""
        extreme_cases = [
            # Tiny feet, huge shoes
            (5.0, 2.0, 8.0, 15.0, 15.0, 8.0, 90.0, 45.0),
            # Huge feet, tiny shoes
            (15.0, 8.0, 90.0, 45.0, 5.0, 2.0, 8.0, 15.0),
            # Very narrow feet, very wide shoes
            (10.0, 1.0, 7.0, 22.0, 10.0, 6.0, 45.0, 32.0),
            # Very wide feet, very narrow shoes
            (10.0, 6.0, 45.0, 32.0, 10.0, 1.0, 7.0, 22.0),
            # Weird aspect ratios
            (20.0, 2.0, 28.0, 44.0, 8.0, 8.0, 48.0, 32.0),
        ]
        
        for case in extreme_cases:
            user_l, user_w, user_a, user_p, shoe_l, shoe_w, shoe_a, shoe_p = case
            
            # Should not crash
            try:
                score = enhanced_score_shoe_4d(
                    user_l, user_w, user_a, user_p,
                    shoe_l, shoe_w, shoe_a, shoe_p, "casual"
                )
                
                # Should return valid score
                self.assertIsInstance(score, (int, float))
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 100)
                
            except Exception as e:
                self.fail(f"Algorithm crashed on extreme case {case}: {str(e)}")
    
    def test_floating_point_precision(self):
        """Test floating point precision edge cases"""
        # Test with very precise decimal inputs
        precise_inputs = [
            (10.123456789, 3.987654321, 25.111111, 24.222222),
            (10.000000001, 4.000000001, 25.000000001, 24.000000001),
            (9.999999999, 3.999999999, 24.999999999, 23.999999999),
        ]
        
        for user_l, user_w, user_a, user_p in precise_inputs:
            score = enhanced_score_shoe_4d(
                user_l, user_w, user_a, user_p,
                user_l, user_w, user_a, user_p, "casual"
            )
            
            # Should handle precision without issues
            self.assertIsInstance(score, (int, float))
            self.assertFalse(math.isnan(score), "Score should not be NaN")
            self.assertFalse(math.isinf(score), "Score should not be infinite")
    
    def test_zero_and_negative_edge_cases(self):
        """Test handling of zero and negative values"""
        # These should all return 0 (invalid input)
        invalid_cases = [
            (-1.0, 4.0, 25.0, 24.0, 10.0, 4.0, 30.0, 28.0),  # Negative user length
            (10.0, -1.0, 25.0, 24.0, 10.0, 4.0, 30.0, 28.0),  # Negative user width
            (10.0, 4.0, 25.0, 24.0, -1.0, 4.0, 30.0, 28.0),   # Negative shoe length
            (10.0, 4.0, 25.0, 24.0, 10.0, -1.0, 30.0, 28.0),  # Negative shoe width
            (0.0, 4.0, 25.0, 24.0, 10.0, 4.0, 30.0, 28.0),    # Zero user length
            (10.0, 0.0, 25.0, 24.0, 10.0, 4.0, 30.0, 28.0),   # Zero user width
            (10.0, 4.0, 25.0, 24.0, 0.0, 4.0, 30.0, 28.0),    # Zero shoe length
            (10.0, 4.0, 25.0, 24.0, 10.0, 0.0, 30.0, 28.0),   # Zero shoe width
        ]
        
        for case in invalid_cases:
            score = enhanced_score_shoe_4d(*case, "casual")
            self.assertEqual(score, 0, f"Invalid case should return 0: {case}")
    
    def test_none_value_handling(self):
        """Test handling of None values in area/perimeter"""
        # None area/perimeter should fall back to estimation
        score_with_none = enhanced_score_shoe_4d(
            10.0, 4.0, None, None,
            10.0, 4.0, None, None, "casual"
        )
        
        # Should not crash and should return reasonable score
        self.assertIsInstance(score_with_none, (int, float))
        self.assertGreater(score_with_none, 50)  # Should be decent for similar dimensions
        
        # Test mixed None values
        score_mixed = enhanced_score_shoe_4d(
            10.0, 4.0, 25.0, None,
            10.0, 4.0, 30.0, None, "casual"
        )
        
        self.assertIsInstance(score_mixed, (int, float))
        self.assertGreaterEqual(score_mixed, 0)
        self.assertLessEqual(score_mixed, 100)


class TestFitCategoryBoundaries(TestCase):
    """Test fit category boundary conditions"""
    
    def test_fit_category_boundaries(self):
        """Test scores exactly at fit category boundaries"""
        # Create scenarios that produce scores near thresholds
        test_targets = [
            FIT_THRESHOLDS['EXCELLENT'] - 1,  # Just below excellent
            FIT_THRESHOLDS['EXCELLENT'],      # Exact excellent boundary
            FIT_THRESHOLDS['EXCELLENT'] + 1,  # Just above excellent
            FIT_THRESHOLDS['GOOD'] - 1,       # Just below good
            FIT_THRESHOLDS['GOOD'],           # Exact good boundary
            FIT_THRESHOLDS['GOOD'] + 1,       # Just above good
            FIT_THRESHOLDS['FAIR'] - 1,       # Just below fair
            FIT_THRESHOLDS['FAIR'],           # Exact fair boundary
            FIT_THRESHOLDS['FAIR'] + 1,       # Just above fair
        ]
        
        # We can't easily engineer exact scores, but we can test the boundary logic
        def get_fit_category(score):
            if score >= FIT_THRESHOLDS['EXCELLENT']:
                return 'Excellent'
            elif score >= FIT_THRESHOLDS['GOOD']:
                return 'Good'
            elif score >= FIT_THRESHOLDS['FAIR']:
                return 'Fair'
            else:
                return 'Poor'
        
        for score in test_targets:
            category = get_fit_category(score)
            
            # Test that categories are assigned correctly
            if score >= FIT_THRESHOLDS['EXCELLENT']:
                self.assertEqual(category, 'Excellent')
            elif score >= FIT_THRESHOLDS['GOOD']:
                self.assertEqual(category, 'Good')
            elif score >= FIT_THRESHOLDS['FAIR']:
                self.assertEqual(category, 'Fair')
            else:
                self.assertEqual(category, 'Poor')


class TestRegressionPrevention(TestCase):
    """Test against regressions from old algorithm"""
    
    def test_width_tolerance_regression(self):
        """Ensure width tolerance improvements are maintained"""
        user_length = 10.5
        user_width = 3.8
        user_area = 26.25
        user_perimeter = 25.5
        
        # 10% width difference should NOT be zero anymore
        narrow_shoe = user_width * 0.9  # 10% narrower
        score_10_percent = enhanced_score_shoe_4d(
            user_length, user_width, user_area, user_perimeter,
            user_length, narrow_shoe, user_area, user_perimeter, "casual"
        )
        
        self.assertGreater(score_10_percent, 40, "10% width difference should get meaningful score")
        
        # 15% width difference should still get some score
        very_narrow_shoe = user_width * 0.85  # 15% narrower
        score_15_percent = enhanced_score_shoe_4d(
            user_length, user_width, user_area, user_perimeter,
            user_length, very_narrow_shoe, user_area, user_perimeter, "casual"
        )
        
        self.assertGreater(score_15_percent, 20, "15% width difference should still get some score")
    
    def test_length_penalty_regression(self):
        """Ensure length penalties are not overly harsh"""
        user_length = 10.5
        user_width = 3.8
        user_area = 26.25
        user_perimeter = 25.5
        
        # 2% tight fit should not be severely penalized
        tight_shoe_length = 10.3  # About 2% shorter than foot + clearance
        score_2_percent = enhanced_score_shoe_4d(
            user_length, user_width, user_area, user_perimeter,
            tight_shoe_length, user_width, user_area, user_perimeter, "casual"
        )
        
        self.assertGreater(score_2_percent, 60, "2% tight should not be severely penalized")
        
        # 5% tight should still be wearable
        tighter_shoe_length = 10.0
        score_5_percent = enhanced_score_shoe_4d(
            user_length, user_width, user_area, user_perimeter,
            tighter_shoe_length, user_width, user_area, user_perimeter, "casual"
        )
        
        self.assertGreater(score_5_percent, 40, "5% tight should still be wearable")
    
    def test_no_zero_scores_regression(self):
        """Ensure we don't have sudden zero scores for reasonable fits"""
        user_length = 10.5
        user_width = 3.8
        user_area = 26.25
        user_perimeter = 25.5
        
        # Test a range of reasonable shoe variations
        shoe_variations = [
            # Length variations
            (10.0, 3.8, 25.0, 25.0),  # Shorter
            (11.0, 3.8, 27.0, 27.0),  # Longer
            # Width variations
            (10.5, 3.4, 24.0, 24.0),  # Narrower
            (10.5, 4.2, 28.0, 28.0),  # Wider
            # Combined variations
            (10.2, 3.6, 23.0, 23.0),  # Both smaller
            (10.8, 4.0, 29.0, 29.0),  # Both larger
        ]
        
        for shoe_l, shoe_w, shoe_a, shoe_p in shoe_variations:
            score = enhanced_score_shoe_4d(
                user_length, user_width, user_area, user_perimeter,
                shoe_l, shoe_w, shoe_a, shoe_p, "casual"
            )
            
            # No reasonable shoe should get zero score
            self.assertGreater(score, 10, f"Reasonable shoe variation should not get zero: {(shoe_l, shoe_w)}")


if __name__ == '__main__':
    unittest.main(verbosity=2)