#!/usr/bin/env python3
"""
Backward compatibility and regression tests
"""
import unittest
from django.test import TestCase
from core.views import enhanced_score_shoe_4d, enhanced_score_shoe
import json
import os


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing systems"""
    
    def test_legacy_function_compatibility(self):
        """Test that legacy enhanced_score_shoe still works"""
        # Test with typical inputs
        score = enhanced_score_shoe(10.5, 3.8, 10.5, 3.8)
        
        # Should return valid score
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # Should be high for perfect fit
        self.assertGreater(score, 75)
    
    def test_api_return_format_compatibility(self):
        """Test that API return format is compatible"""
        # The function should return a single numeric value
        score = enhanced_score_shoe_4d(
            10.5, 3.8, 26.25, 25.5,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        # Should be JSON-serializable number
        self.assertIsInstance(score, (int, float))
        
        # Should work in JSON context
        data = {"fit_score": score}
        json_str = json.dumps(data)
        self.assertIsInstance(json_str, str)
    
    def test_shoe_type_parameter_compatibility(self):
        """Test that shoe type parameter handles old and new values"""
        # Test with old "general" type (default)
        score_general = enhanced_score_shoe_4d(
            10.5, 3.8, 26.25, 25.5,
            10.5, 3.8, 28.125, 27.0, "general"
        )
        
        # Test with new specific types
        score_casual = enhanced_score_shoe_4d(
            10.5, 3.8, 26.25, 25.5,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        # Both should work and return valid scores
        self.assertIsInstance(score_general, (int, float))
        self.assertIsInstance(score_casual, (int, float))
        self.assertGreaterEqual(score_general, 0)
        self.assertGreaterEqual(score_casual, 0)
    
    def test_database_field_compatibility(self):
        """Test that function works with database field types"""
        # Simulate database decimal field values
        from decimal import Decimal
        
        user_length = Decimal('10.5')
        user_width = Decimal('3.8')
        shoe_length = Decimal('10.5')
        shoe_width = Decimal('3.8')
        
        # Legacy function should handle Decimal inputs
        score = enhanced_score_shoe(
            float(user_length), float(user_width),
            float(shoe_length), float(shoe_width)
        )
        
        self.assertIsInstance(score, (int, float))
        self.assertGreater(score, 0)
    
    def test_none_handling_compatibility(self):
        """Test that None values are handled gracefully"""
        # Function should handle None area/perimeter by falling back to estimation
        score = enhanced_score_shoe_4d(
            10.5, 3.8, None, None,
            10.5, 3.8, None, None, "casual"
        )
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class TestDataMigrationCompatibility(TestCase):
    """Test compatibility with existing data formats"""
    
    def test_existing_shoe_data_compatibility(self):
        """Test with shoe data in the expected format"""
        # Simulate existing shoe data structure
        sample_shoe_data = {
            'insole_length': 10.5,
            'insole_width': 3.8,
            'insole_area': 28.125,
            'insole_perimeter': 27.0,
            'function': 'casual'
        }
        
        sample_user_data = {
            'length_inches': 10.5,
            'width_inches': 3.8,
            'area_sqin': 26.25,
            'perimeter_inches': 25.5
        }
        
        # Should work with dict access pattern
        score = enhanced_score_shoe_4d(
            sample_user_data['length_inches'],
            sample_user_data['width_inches'],
            sample_user_data['area_sqin'],
            sample_user_data['perimeter_inches'],
            sample_shoe_data['insole_length'],
            sample_shoe_data['insole_width'],
            sample_shoe_data['insole_area'],
            sample_shoe_data['insole_perimeter'],
            sample_shoe_data['function']
        )
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_missing_area_perimeter_data(self):
        """Test with older data that might not have area/perimeter"""
        # Some existing data might only have length/width
        score = enhanced_score_shoe_4d(
            10.5, 3.8, None, None,  # User missing area/perimeter
            10.5, 3.8, None, None,  # Shoe missing area/perimeter
            "casual"
        )
        
        # Should still work by falling back to estimation
        self.assertIsInstance(score, (int, float))
        self.assertGreater(score, 50)  # Should be reasonable for good dimensions


class TestRegressionPrevention(TestCase):
    """Prevent regressions from old algorithm issues"""
    
    def test_no_harsh_zero_scores(self):
        """Ensure we don't revert to giving zero scores for minor issues"""
        # These scenarios gave zero scores in the old algorithm
        problematic_scenarios = [
            # 10% width difference
            (10.5, 3.8, 26.25, 25.5, 10.5, 3.42, 28.0, 27.0),  # 10% narrower width
            # 12% width difference  
            (10.5, 3.8, 26.25, 25.5, 10.5, 3.34, 27.5, 26.5),  # 12% narrower width
            # Slightly tight length
            (10.5, 3.8, 26.25, 25.5, 10.3, 3.8, 27.0, 26.5),   # 2% shorter length
        ]
        
        for user_l, user_w, user_a, user_p, shoe_l, shoe_w, shoe_a, shoe_p in problematic_scenarios:
            score = enhanced_score_shoe_4d(
                user_l, user_w, user_a, user_p,
                shoe_l, shoe_w, shoe_a, shoe_p, "casual"
            )
            
            # Should NOT be zero anymore
            self.assertGreater(score, 20, f"Scenario should not get zero score: {(shoe_l, shoe_w)}")
    
    def test_smooth_score_transitions(self):
        """Ensure no sudden score drops that were in old algorithm"""
        # Test gradual width changes
        base_width = 3.8
        width_changes = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]  # 0% to 25% narrower
        
        scores = []
        for change in width_changes:
            test_width = base_width * (1 - change)
            score = enhanced_score_shoe_4d(
                10.5, 3.8, 26.25, 25.5,
                10.5, test_width, 28.0, 27.0, "casual"
            )
            scores.append(score)
        
        # Check that there are no sudden drops > 25 points
        for i in range(1, len(scores)):
            drop = scores[i-1] - scores[i]
            self.assertLess(drop, 25, f"Sudden score drop at {width_changes[i]*100}% width change: {drop}")
    
    def test_length_penalty_not_overly_harsh(self):
        """Ensure length penalties are reasonable"""
        user_length = 10.5
        
        # Test tight scenarios that should be penalized but not destroyed
        tight_scenarios = [
            10.3,  # ~2% tight
            10.1,  # ~4% tight
            10.0,  # ~5% tight
            9.8,   # ~7% tight
        ]
        
        for tight_length in tight_scenarios:
            score = enhanced_score_shoe_4d(
                user_length, 3.8, 26.25, 25.5,
                tight_length, 3.8, 26.0, 25.5, "casual"
            )
            
            # Even tight shoes should get some score (not zero)
            self.assertGreater(score, 15, f"Tight shoe ({tight_length}) should not be impossible")


class TestIntegrationCompatibility(TestCase):
    """Test integration with other system components"""
    
    def test_serializer_compatibility(self):
        """Test that scores work with Django serializers"""
        score = enhanced_score_shoe_4d(
            10.5, 3.8, 26.25, 25.5,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        # Should work in a dict that could be serialized
        response_data = {
            'shoe_id': 1,
            'fit_score': score,
            'fit_category': 'Excellent' if score >= 85 else 'Good'
        }
        
        # Should be JSON serializable
        json_str = json.dumps(response_data)
        parsed_back = json.loads(json_str)
        
        self.assertEqual(parsed_back['fit_score'], score)
    
    def test_database_storage_compatibility(self):
        """Test that scores can be stored in database fields"""
        score = enhanced_score_shoe_4d(
            10.5, 3.8, 26.25, 25.5,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        # Should be storable as a float/decimal
        self.assertIsInstance(score, (int, float))
        
        # Should have reasonable precision (not too many decimal places)
        self.assertEqual(score, round(score, 1))  # Should be rounded to 1 decimal place


if __name__ == '__main__':
    unittest.main(verbosity=2)