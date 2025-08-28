"""Basic tests for the Cannabis Stash Tracker Bot."""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.config import BIOAVAILABILITY_RATES
from bot.services.consumption_service import ConsumptionService

class TestConsumptionService(unittest.TestCase):
    """Test consumption service calculations."""
    
    def test_absorbed_thc_calculation(self):
        """Test THC absorption calculations."""
        # Test smoking 1g of 20% THC flower
        absorbed = ConsumptionService.calculate_absorbed_thc(1.0, 20.0, "smoke")
        expected = 1000 * 0.20 * BIOAVAILABILITY_RATES["smoke"]  # 55mg
        self.assertEqual(absorbed, round(expected, 2))
        
        # Test 10mg edible
        absorbed = ConsumptionService.calculate_absorbed_thc(0.01, 100.0, "edible")
        expected = 10 * BIOAVAILABILITY_RATES["edible"]  # 1.2mg
        self.assertEqual(absorbed, round(expected, 2))
        
        # Test 0.1g dab at 80% THC
        absorbed = ConsumptionService.calculate_absorbed_thc(0.1, 80.0, "dab")
        expected = 100 * 0.80 * BIOAVAILABILITY_RATES["dab"]  # 52mg
        self.assertEqual(absorbed, round(expected, 2))
    
    def test_invalid_method(self):
        """Test invalid consumption method raises error."""
        with self.assertRaises(ValueError):
            ConsumptionService.calculate_absorbed_thc(1.0, 20.0, "invalid_method")

class TestBioavailabilityRates(unittest.TestCase):
    """Test bioavailability configuration."""
    
    def test_all_methods_present(self):
        """Test all consumption methods have bioavailability rates."""
        required_methods = ["smoke", "vaporizer", "dab", "edible", "tincture", "capsule"]
        
        for method in required_methods:
            self.assertIn(method, BIOAVAILABILITY_RATES)
            self.assertIsInstance(BIOAVAILABILITY_RATES[method], float)
            self.assertGreater(BIOAVAILABILITY_RATES[method], 0)
            self.assertLessEqual(BIOAVAILABILITY_RATES[method], 1)

if __name__ == "__main__":
    unittest.main()
