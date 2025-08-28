"""
Test Suite for CannaBot Core Commands

This module contains unit tests for the core functionality of the CannaBot,
including strain database operations, command processing, and data validation.

Run with: python -m pytest tests/
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch, MagicMock
import discord
from discord.ext import commands

# Import the classes we want to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from bot.commands.core import StrainDatabase, CoreCommands


class TestStrainDatabase:
    """Test suite for StrainDatabase functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.strain_db = StrainDatabase()
        
        # Create mock data for testing
        self.mock_data = pd.DataFrame({
            'name': ['Blue Dream', 'OG Kush', 'Green Crack', 'Purple Haze'],
            'type': ['Hybrid', 'Indica', 'Sativa', 'Sativa'],
            'thc_percentage': ['18-24%', '20-25%', '15-20%', '15-20%'],
            'relaxed': ['65%', '85%', '15%', '35%'],
            'happy': ['80%', '60%', '85%', '90%'],
            'euphoric': ['70%', '55%', '75%', '85%'],
            'creative': ['45%', '25%', '80%', '75%'],
            'energetic': ['35%', '15%', '90%', '70%']
        })
    
    def test_initialization(self):
        """Test that StrainDatabase initializes correctly."""
        db = StrainDatabase()
        assert isinstance(db.df, pd.DataFrame)
    
    @patch('pandas.read_csv')
    def test_load_data_success(self, mock_read_csv):
        """Test successful data loading."""
        mock_read_csv.return_value = self.mock_data
        
        db = StrainDatabase()
        assert len(db.df) == 4
        assert 'Blue Dream' in db.df['name'].values
    
    @patch('pandas.read_csv')
    def test_load_data_failure(self, mock_read_csv):
        """Test graceful handling of data loading failure."""
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        
        db = StrainDatabase()
        assert db.df.empty
    
    def test_search_strain_found(self):
        """Test successful strain search."""
        self.strain_db.df = self.mock_data
        
        result = self.strain_db.search_strain("blue dream")
        assert result is not None
        assert result['name'] == 'Blue Dream'
    
    def test_search_strain_not_found(self):
        """Test strain search with no results."""
        self.strain_db.df = self.mock_data
        
        result = self.strain_db.search_strain("nonexistent strain")
        assert result is None
    
    def test_search_strain_empty_db(self):
        """Test strain search on empty database."""
        self.strain_db.df = pd.DataFrame()
        
        result = self.strain_db.search_strain("any strain")
        assert result is None
    
    def test_get_random_strain(self):
        """Test random strain selection."""
        self.strain_db.df = self.mock_data
        
        result = self.strain_db.get_random_strain()
        assert result is not None
        assert result['name'] in self.mock_data['name'].values
    
    def test_get_random_strain_empty_db(self):
        """Test random strain selection on empty database."""
        self.strain_db.df = pd.DataFrame()
        
        result = self.strain_db.get_random_strain()
        assert result is None
    
    def test_find_by_effects_valid_effect(self):
        """Test finding strains by effects."""
        self.strain_db.df = self.mock_data
        
        results = self.strain_db.find_by_effects("relaxed")
        assert len(results) > 0
        # OG Kush should be first (85% relaxed)
        assert results.iloc[0]['name'] == 'OG Kush'
    
    def test_find_by_effects_invalid_effect(self):
        """Test finding strains by invalid effect."""
        self.strain_db.df = self.mock_data
        
        results = self.strain_db.find_by_effects("invalid_effect")
        assert len(results) == 0
    
    def test_find_by_effects_empty_db(self):
        """Test finding strains by effects on empty database."""
        self.strain_db.df = pd.DataFrame()
        
        results = self.strain_db.find_by_effects("happy")
        assert len(results) == 0


class TestCoreCommands:
    """Test suite for CoreCommands functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.bot = Mock(spec=commands.Bot)
        self.cog = CoreCommands(self.bot)
    
    def test_initialization(self):
        """Test that CoreCommands initializes correctly."""
        assert self.cog.bot == self.bot
    
    @pytest.mark.asyncio
    async def test_bioavailability_calculations(self):
        """Test bioavailability calculations for different methods."""
        # Mock interaction
        interaction = Mock(spec=discord.Interaction)
        interaction.response = Mock()
        interaction.response.send_message = Mock()
        
        # Test different consumption methods
        test_cases = [
            ("smoke", 1.0, 30),  # 1g smoke = 30% bioavailability
            ("vape", 1.0, 50),   # 1g vape = 50% bioavailability  
            ("edible", 1.0, 15), # 1g edible = 15% bioavailability
            ("dab", 0.1, 75),    # 0.1g dab = 75% bioavailability
        ]
        
        for method, amount, expected_bio in test_cases:
            await self.cog.use_cannabis(interaction, method, amount, "Test Strain")
            
            # Verify response was called
            interaction.response.send_message.assert_called()
            
            # Calculate expected THC (amount * 20mg/g * bioavailability)
            expected_thc = amount * 20 * (expected_bio / 100)
            
            # Extract the embed from the call
            call_args = interaction.response.send_message.call_args
            embed = call_args[1]['embed'] if 'embed' in call_args[1] else call_args[0][0]
            
            # Verify THC calculation is in the embed
            assert f"{expected_thc:.1f}mg" in str(embed.fields)


class TestIntegration:
    """Integration tests for combined functionality."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.bot = Mock(spec=commands.Bot)
        self.cog = CoreCommands(self.bot)
    
    @patch('bot.commands.core.strain_db')
    @pytest.mark.asyncio
    async def test_strain_command_with_search(self, mock_strain_db):
        """Test strain command integration with database search."""
        # Mock strain data
        mock_strain = pd.Series({
            'name': 'Blue Dream',
            'type': 'Hybrid',
            'thc_percentage': '18-24%',
            'description': 'A balanced hybrid strain',
            'relaxed': '65%',
            'happy': '80%',
            'euphoric': '70%'
        })
        
        mock_strain_db.search_strain.return_value = mock_strain
        
        # Mock interaction
        interaction = Mock(spec=discord.Interaction)
        interaction.response = Mock()
        interaction.response.send_message = Mock()
        
        # Test strain search
        await self.cog.strains(interaction, search="blue dream")
        
        # Verify database was queried
        mock_strain_db.search_strain.assert_called_with("blue dream")
        
        # Verify response was sent
        interaction.response.send_message.assert_called()


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
