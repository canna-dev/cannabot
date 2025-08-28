"""
Test configuration and fixtures for CannaBot tests.

This module sets up pytest configuration and common fixtures
used across the test suite.
"""

import pytest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
pytest_plugins = []

@pytest.fixture
def mock_bot():
    """Create a mock Discord bot for testing."""
    from unittest.mock import Mock
    from discord.ext import commands
    
    bot = Mock(spec=commands.Bot)
    return bot

@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction for testing."""
    from unittest.mock import Mock
    import discord
    
    interaction = Mock(spec=discord.Interaction)
    interaction.response = Mock()
    interaction.response.send_message = Mock()
    interaction.response.is_done.return_value = False
    
    return interaction

@pytest.fixture
def sample_strain_data():
    """Provide sample strain data for testing."""
    return {
        'name': ['Blue Dream', 'OG Kush', 'Green Crack', 'Purple Haze'],
        'type': ['Hybrid', 'Indica', 'Sativa', 'Sativa'],
        'thc_percentage': ['18-24%', '20-25%', '15-20%', '15-20%'],
        'relaxed': ['65%', '85%', '15%', '35%'],
        'happy': ['80%', '60%', '85%', '90%'],
        'euphoric': ['70%', '55%', '75%', '85%'],
        'creative': ['45%', '25%', '80%', '75%'],
        'energetic': ['35%', '15%', '90%', '70%']
    }
