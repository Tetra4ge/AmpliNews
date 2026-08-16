import unittest
import math
from services.vector_service import calculate_learning_rate, compute_shifted_vector

class TestVectorService(unittest.TestCase):
    def test_calculate_learning_rate(self):
        # Bounce / low read time
        self.assertEqual(calculate_learning_rate(read_duration_seconds=3, liked=False, rejected_biased=False), 0.0)
        
        # Read duration > 60s
        self.assertEqual(calculate_learning_rate(read_duration_seconds=75, liked=False, rejected_biased=False), 0.05)
        
        # Liked
        self.assertEqual(calculate_learning_rate(read_duration_seconds=10, liked=True, rejected_biased=False), 0.10)
        
        # Too biased (overrides like/duration)
        self.assertEqual(calculate_learning_rate(read_duration_seconds=120, liked=True, rejected_biased=True), -0.15)

    def test_compute_shifted_vector_normalization(self):
        # Initial unit vectors
        user_vec = [1.0, 0.0, 0.0]
        article_vec = [0.0, 1.0, 0.0]
        
        # Shift towards article by L = 0.10
        shifted = compute_shifted_vector(user_vec, article_vec, 0.10)
        
        # Expected magnitude should be exactly 1.0 after L2 norm
        magnitude = math.sqrt(sum(x * x for x in shifted))
        self.assertAlmostEqual(magnitude, 1.0, places=6)
        
        # Verify user vector shifted closer to article vector (higher component in 2nd dimension)
        self.assertGreater(shifted[1], 0.0)

    def test_compute_shifted_vector_negative_shift(self):
        user_vec = [0.7071, 0.7071, 0.0]
        article_vec = [0.0, 1.0, 0.0]
        
        # Negative shift (Too Biased)
        shifted = compute_shifted_vector(user_vec, article_vec, -0.15)
        
        magnitude = math.sqrt(sum(x * x for x in shifted))
        self.assertAlmostEqual(magnitude, 1.0, places=6)
        
        # Component in 2nd dimension should decrease because we shift away from article
        self.assertLess(shifted[1], user_vec[1])

if __name__ == "__main__":
    unittest.main()

