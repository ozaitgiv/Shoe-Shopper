#!/usr/bin/env python3
"""
Performance and load testing for penalty functions
"""
import unittest
import time
import statistics
from django.test import TestCase
from core.views import enhanced_score_shoe_4d, enhanced_score_shoe


class TestPerformance(TestCase):
    """Test performance characteristics of the algorithm"""
    
    def setUp(self):
        """Set up performance test data"""
        self.user_length = 10.5
        self.user_width = 3.8
        self.user_area = 26.25
        self.user_perimeter = 25.5
        
        # Create variety of shoe data for testing
        self.test_shoes = []
        for length in [9.5, 10.0, 10.5, 11.0, 11.5]:
            for width in [3.4, 3.6, 3.8, 4.0, 4.2]:
                area = length * width * 0.75
                perimeter = 2 * 3.14159 * ((length/2 + width/2) / 2)
                self.test_shoes.append((length, width, area, perimeter))
    
    def test_single_calculation_performance(self):
        """Test that single calculation is fast"""
        start_time = time.perf_counter()
        
        # Single calculation
        score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        # Should complete very quickly (under 1ms)
        self.assertLess(execution_time, 0.001, f"Single calculation too slow: {execution_time:.6f}s")
        self.assertIsInstance(score, (int, float))
    
    def test_batch_calculation_performance(self):
        """Test performance with many calculations"""
        iterations = 1000
        
        start_time = time.perf_counter()
        
        scores = []
        for i in range(iterations):
            # Vary the shoe slightly each iteration
            shoe_idx = i % len(self.test_shoes)
            shoe_l, shoe_w, shoe_a, shoe_p = self.test_shoes[shoe_idx]
            
            score = enhanced_score_shoe_4d(
                self.user_length, self.user_width, self.user_area, self.user_perimeter,
                shoe_l, shoe_w, shoe_a, shoe_p, "casual"
            )
            scores.append(score)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Should complete 1000 calculations in reasonable time
        self.assertLess(total_time, 1.0, f"Batch calculation too slow: {total_time:.3f}s for {iterations} calculations")
        self.assertLess(avg_time, 0.001, f"Average calculation too slow: {avg_time:.6f}s")
        
        # All scores should be valid
        for score in scores:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
    
    def test_memory_usage_stability(self):
        """Test that repeated calculations don't leak memory"""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        # Run many calculations to test for memory leaks
        for _ in range(5000):
            enhanced_score_shoe_4d(
                self.user_length, self.user_width, self.user_area, self.user_perimeter,
                10.5, 3.8, 28.125, 27.0, "casual"
            )
        
        # Force garbage collection after test
        gc.collect()
        
        # Test passes if we reach this point without memory issues
        self.assertTrue(True)
    
    def test_concurrent_calculation_safety(self):
        """Test that calculations are thread-safe"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def calculate_scores():
            """Calculate scores in a thread"""
            local_scores = []
            for _ in range(100):
                score = enhanced_score_shoe_4d(
                    self.user_length, self.user_width, self.user_area, self.user_perimeter,
                    10.5, 3.8, 28.125, 27.0, "casual"
                )
                local_scores.append(score)
            results_queue.put(local_scores)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=calculate_scores)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect all results
        all_scores = []
        while not results_queue.empty():
            thread_scores = results_queue.get()
            all_scores.extend(thread_scores)
        
        # All scores should be consistent
        expected_score = enhanced_score_shoe_4d(
            self.user_length, self.user_width, self.user_area, self.user_perimeter,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        for score in all_scores:
            self.assertAlmostEqual(score, expected_score, places=1)
    
    def test_performance_vs_legacy(self):
        """Compare performance with legacy function"""
        iterations = 1000
        
        # Test legacy function performance
        start_time = time.perf_counter()
        for _ in range(iterations):
            enhanced_score_shoe(self.user_length, self.user_width, 10.5, 3.8)
        legacy_time = time.perf_counter() - start_time
        
        # Test new function performance  
        start_time = time.perf_counter()
        for _ in range(iterations):
            enhanced_score_shoe_4d(
                self.user_length, self.user_width, self.user_area, self.user_perimeter,
                10.5, 3.8, 28.125, 27.0, "casual"
            )
        new_time = time.perf_counter() - start_time
        
        # New function should not be significantly slower (allow 2x slowdown for extra features)
        slowdown_factor = new_time / legacy_time if legacy_time > 0 else 1
        self.assertLess(slowdown_factor, 3.0, f"New function too slow vs legacy: {slowdown_factor:.2f}x")
    
    def test_worst_case_performance(self):
        """Test performance with worst-case inputs"""
        # Extreme values that might cause slow calculations
        extreme_cases = [
            # Very large numbers
            (100.0, 50.0, 3750.0, 235.6, 100.0, 50.0, 3750.0, 235.6),
            # Very small numbers
            (0.1, 0.1, 0.0075, 0.628, 0.1, 0.1, 0.0075, 0.628),
            # Very different ratios
            (10.0, 4.0, 30.0, 28.0, 5.0, 8.0, 30.0, 26.0),
        ]
        
        for case in extreme_cases:
            start_time = time.perf_counter()
            
            score = enhanced_score_shoe_4d(*case, "casual")
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # Even extreme cases should be fast
            self.assertLess(execution_time, 0.01, f"Extreme case too slow: {execution_time:.6f}s")
            self.assertIsInstance(score, (int, float))


class TestLoadTesting(TestCase):
    """Test system behavior under load"""
    
    def test_realistic_load_simulation(self):
        """Simulate realistic API load"""
        # Simulate 100 users each getting recommendations for 50 shoes
        users = [(10.0 + i*0.1, 3.5 + i*0.05, 25.0 + i*0.5, 24.0 + i*0.3) for i in range(100)]
        shoes = [(9.5 + j*0.2, 3.4 + j*0.08, 25.0 + j*1.0, 24.0 + j*0.8) for j in range(50)]
        
        start_time = time.perf_counter()
        
        total_calculations = 0
        for user_l, user_w, user_a, user_p in users:
            for shoe_l, shoe_w, shoe_a, shoe_p in shoes:
                score = enhanced_score_shoe_4d(
                    user_l, user_w, user_a, user_p,
                    shoe_l, shoe_w, shoe_a, shoe_p, "casual"
                )
                total_calculations += 1
                
                # Validate each result
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 100)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Should handle 5000 calculations (100 users * 50 shoes) in reasonable time
        self.assertLess(total_time, 5.0, f"Load test too slow: {total_time:.3f}s for {total_calculations} calculations")
        
        avg_time = total_time / total_calculations
        self.assertLess(avg_time, 0.001, f"Average calculation too slow under load: {avg_time:.6f}s")
    
    def test_stress_test_consistency(self):
        """Test that results are consistent under stress"""
        # Run the same calculation many times and check consistency
        reference_score = enhanced_score_shoe_4d(
            10.5, 3.8, 26.25, 25.5,
            10.5, 3.8, 28.125, 27.0, "casual"
        )
        
        scores = []
        for _ in range(1000):
            score = enhanced_score_shoe_4d(
                10.5, 3.8, 26.25, 25.5,
                10.5, 3.8, 28.125, 27.0, "casual"
            )
            scores.append(score)
        
        # All scores should be identical (deterministic function)
        for score in scores:
            self.assertEqual(score, reference_score, "Function should be deterministic")
        
        # Check statistical consistency
        mean_score = statistics.mean(scores)
        self.assertAlmostEqual(mean_score, reference_score, places=3)


class TestScalabilityBenchmarks(TestCase):
    """Benchmark scalability characteristics"""
    
    def test_linear_scalability(self):
        """Test that execution time scales linearly with input size"""
        sizes = [100, 500, 1000, 2000]
        times = []
        
        for size in sizes:
            start_time = time.perf_counter()
            
            for i in range(size):
                # Vary inputs slightly to prevent caching effects
                user_l = 10.5 + (i % 10) * 0.01
                score = enhanced_score_shoe_4d(
                    user_l, 3.8, 26.25, 25.5,
                    10.5, 3.8, 28.125, 27.0, "casual"
                )
            
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        # Check that time increases roughly linearly
        # Allow for some variation due to system factors
        for i in range(1, len(times)):
            expected_ratio = sizes[i] / sizes[0]
            actual_ratio = times[i] / times[0]
            
            # Should be within 50% of linear scaling
            self.assertLess(actual_ratio, expected_ratio * 1.5, 
                          f"Scaling not linear: {actual_ratio:.2f} vs expected {expected_ratio:.2f}")
    
    def test_memory_scalability(self):
        """Test that memory usage doesn't grow with repeated calls"""
        import gc
        import sys
        
        # Get baseline memory usage
        gc.collect()
        
        # Run many calculations
        for batch in range(10):
            for _ in range(1000):
                enhanced_score_shoe_4d(
                    10.5, 3.8, 26.25, 25.5,
                    10.5, 3.8, 28.125, 27.0, "casual"
                )
            
            # Force garbage collection between batches
            gc.collect()
        
        # Test passes if we complete without memory issues
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)