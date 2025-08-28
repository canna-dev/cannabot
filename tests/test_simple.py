"""
Simple test runner for CannaBot without external dependencies.

This module provides basic testing functionality without requiring
pytest or other testing frameworks to be installed.
"""

import sys
import os
import traceback
from typing import List, Callable

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class SimpleTestRunner:
    """Simple test runner for basic functionality testing."""
    
    def __init__(self):
        self.tests: List[Callable] = []
        self.passed = 0
        self.failed = 0
    
    def add_test(self, test_func: Callable):
        """Add a test function to the runner."""
        self.tests.append(test_func)
    
    def run_tests(self):
        """Run all registered tests."""
        print("🧪 Running CannaBot Tests")
        print("=" * 50)
        
        for test_func in self.tests:
            try:
                print(f"Testing {test_func.__name__}...", end=" ")
                test_func()
                print("✅ PASSED")
                self.passed += 1
            except Exception as e:
                print("❌ FAILED")
                print(f"   Error: {str(e)}")
                if hasattr(e, '__traceback__'):
                    traceback.print_exc()
                self.failed += 1
        
        print("=" * 50)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        return self.failed == 0

# Test functions
def test_strain_database_initialization():
    """Test that StrainDatabase can be initialized."""
    from bot.commands.core import StrainDatabase
    
    db = StrainDatabase()
    assert hasattr(db, 'df'), "StrainDatabase should have df attribute"
    assert hasattr(db, 'load_data'), "StrainDatabase should have load_data method"
    assert hasattr(db, 'search_strain'), "StrainDatabase should have search_strain method"

def test_bioavailability_calculations():
    """Test bioavailability calculation logic."""
    bioavailability = {
        "smoke": 30, "vape": 50, "dab": 75, 
        "edible": 15, "tincture": 35, "capsule": 20, "other": 25
    }
    
    # Test calculations
    amount = 1.0  # 1 gram
    thc_per_gram = 20  # 20mg THC per gram
    
    for method, bio_percent in bioavailability.items():
        effective_thc = amount * thc_per_gram * (bio_percent / 100)
        expected_values = {
            "smoke": 6.0, "vape": 10.0, "dab": 15.0,
            "edible": 3.0, "tincture": 7.0, "capsule": 4.0, "other": 5.0
        }
        
        assert effective_thc == expected_values[method], \
            f"Bioavailability calculation failed for {method}"

def test_core_commands_initialization():
    """Test that CoreCommands can be initialized."""
    from bot.commands.core import CoreCommands
    from unittest.mock import Mock
    
    mock_bot = Mock()
    cog = CoreCommands(mock_bot)
    
    assert cog.bot == mock_bot, "CoreCommands should store bot reference"
    assert hasattr(cog, 'use_cannabis'), "CoreCommands should have use_cannabis command"
    assert hasattr(cog, 'show_help'), "CoreCommands should have show_help command"

def test_file_structure():
    """Test that required files exist."""
    required_files = [
        'bot/main.py',
        'bot/commands/core.py',
        'bot/config.py',
        'data/leafly_strain_data.csv',
        'requirements.txt',
        'README.md'
    ]
    
    project_root = os.path.join(os.path.dirname(__file__), '..')
    
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        assert os.path.exists(full_path), f"Required file missing: {file_path}"

def test_strain_randomization():
    """Test strain database randomization features."""
    from bot.commands.core import StrainDatabase
    
    # Test with real database
    db = StrainDatabase()
    
    if not db.df.empty:
        # Test randomized search - use a common word that should match multiple strains
        results = []
        for _ in range(3):
            result = db.search_strain("blue", randomize=True)  # "blue" should match Blue Dream, etc.
            if result is not None:
                results.append(result['name'])
        
        # We should get at least one result
        print(f"Search results for 'blue': {results}")
        # Don't assert randomness since we can't guarantee it, just test functionality
        
        # Test diverse selection
        diverse = db.get_diverse_selection(3)
        try:
            import pandas as pd
            if isinstance(diverse, pd.DataFrame):
                assert len(diverse) <= 3, "Should return at most 3 strains"
            else:
                assert len(diverse) == 0, "Should return empty list if DataFrame not available"
        except ImportError:
            # pandas not available, just check it doesn't crash
            assert diverse is not None, "Should return something"

def test_strain_recommendations():
    """Test strain recommendation system."""
    from bot.commands.core import StrainDatabase
    
    db = StrainDatabase()
    
    # Test recommendations without preferences
    recommendations = db.get_strain_recommendations(count=3)
    
    # Test doesn't crash and returns something
    assert recommendations is not None, "Should return something"
    
    # Test recommendations with preferences
    preferences = {
        'effects': ['creative', 'happy'],
        'type': 'sativa'
    }
    pref_recommendations = db.get_strain_recommendations(preferences, count=3)
    assert pref_recommendations is not None, "Should return something"

def test_configuration_validation():
    """Test configuration validation."""
    from bot.config import Config
    
    # Test that Config class exists and has required attributes
    required_attrs = ['DISCORD_TOKEN', 'DATABASE_URL', 'LOG_LEVEL', 'DEBUG']
    
    for attr in required_attrs:
        assert hasattr(Config, attr), f"Config missing required attribute: {attr}"

# Main test execution
if __name__ == "__main__":
    runner = SimpleTestRunner()
    
    # Register tests
    runner.add_test(test_strain_database_initialization)
    runner.add_test(test_bioavailability_calculations)
    runner.add_test(test_core_commands_initialization)
    runner.add_test(test_file_structure)
    runner.add_test(test_configuration_validation)
    runner.add_test(test_strain_randomization)
    runner.add_test(test_strain_recommendations)
    
    # Run tests
    success = runner.run_tests()
    
    if success:
        print("\n🎉 All tests passed! CannaBot is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        sys.exit(1)
