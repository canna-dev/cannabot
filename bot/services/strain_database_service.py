"""Enhanced strain database service using Leafly dataset."""

import csv
import os
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class StrainData:
    """Strain information from Leafly dataset."""
    name: str
    type: str  # indica, sativa, hybrid
    rating: float
    effects: List[str]
    flavors: List[str]
    description: str
    thc_high: Optional[float] = None
    thc_low: Optional[float] = None
    cbd_high: Optional[float] = None
    cbd_low: Optional[float] = None
    terpenes: Optional[List[str]] = None
    most_common_terpene: Optional[str] = None
    medical_uses: Optional[List[str]] = None
    image_url: Optional[str] = None
    # Effect percentages from Leafly data
    relaxed_pct: Optional[float] = None
    happy_pct: Optional[float] = None
    euphoric_pct: Optional[float] = None
    uplifted_pct: Optional[float] = None
    creative_pct: Optional[float] = None
    focused_pct: Optional[float] = None
    energetic_pct: Optional[float] = None
    talkative_pct: Optional[float] = None
    hungry_pct: Optional[float] = None
    sleepy_pct: Optional[float] = None

class StrainDatabaseService:
    """Service for managing and searching strain database."""
    
    def __init__(self, csv_path: str = "data/leafly_strain_data.csv"):
        self.csv_path = csv_path
        self.strains: Dict[str, StrainData] = {}
        self.loaded = False
        
        # Initialize random seed for consistent but varied recommendations
        random.seed()
        
        # Medical condition mappings
        self.medical_mappings = {
            'pain': ['chronic pain', 'arthritis', 'migraine', 'headache', 'muscle spasm'],
            'anxiety': ['anxiety', 'stress', 'ptsd', 'panic'],
            'depression': ['depression', 'mood', 'bipolar'],
            'insomnia': ['insomnia', 'sleep', 'restless'],
            'nausea': ['nausea', 'appetite', 'eating disorder'],
            'seizures': ['epilepsy', 'seizure', 'spasm'],
            'inflammation': ['inflammation', 'arthritis', 'crohn\'s'],
            'glaucoma': ['glaucoma', 'eye pressure'],
            'adhd': ['adhd', 'attention', 'focus'],
            'cancer': ['cancer', 'chemotherapy', 'tumor']
        }

    async def load_database(self) -> bool:
        """Load strain data from CSV file."""
        try:
            if not os.path.exists(self.csv_path):
                # Create sample data if file doesn't exist
                await self._create_sample_data()
                return True
            
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    strain = self._parse_strain_row(row)
                    if strain:
                        # Use lowercase name as key for easy searching
                        self.strains[strain.name.lower()] = strain
            
            self.loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading strain database: {e}")
            return False

    def _parse_strain_row(self, row: Dict) -> Optional[StrainData]:
        """Parse a CSV row into StrainData object."""
        try:
            # Handle different possible column names from Leafly dataset
            name = row.get('Strain', row.get('name', row.get('Name', ''))).strip()
            if not name:
                return None
            
            # Parse strain type
            strain_type = row.get('Type', row.get('type', 'hybrid')).lower()
            
            # Parse rating
            rating = 0.0
            rating_str = row.get('Rating', row.get('rating', '0'))
            try:
                rating = float(rating_str) if rating_str else 0.0
            except ValueError:
                rating = 0.0
            
            # Parse effects (comma-separated)
            effects = []
            effects_str = row.get('Effects', row.get('effects', ''))
            if effects_str:
                effects = [e.strip() for e in effects_str.split(',') if e.strip()]
            
            # Parse flavors (comma-separated)
            flavors = []
            flavors_str = row.get('Flavor', row.get('flavors', row.get('Flavors', '')))
            if flavors_str:
                flavors = [f.strip() for f in flavors_str.split(',') if f.strip()]
            
            # Description
            description = row.get('Description', row.get('description', ''))
            
            # Parse THC percentage from thc_level column
            thc_level = self._parse_percentage(row.get('thc_level', row.get('THC_High', row.get('thc_high', ''))))
            # For backward compatibility, set both high and low to the same value
            thc_high = thc_level
            thc_low = thc_level
            # CBD data not available in this dataset
            cbd_high = None
            cbd_low = None
            
            # Parse terpenes
            terpenes = []
            terpenes_str = row.get('Terpenes', row.get('terpenes', ''))
            if terpenes_str:
                terpenes = [t.strip() for t in terpenes_str.split(',') if t.strip()]
            
            # Parse most common terpene
            most_common_terpene = row.get('most_common_terpene', '')
            if not most_common_terpene or most_common_terpene.lower() in ['[null]', 'null', '']:
                most_common_terpene = None
            
            # Parse medical uses
            medical_uses = []
            medical_str = row.get('Medical', row.get('medical_uses', ''))
            if medical_str:
                medical_uses = [m.strip() for m in medical_str.split(',') if m.strip()]
            
            # Parse image URL
            image_url = row.get('img_url', row.get('Image', row.get('image_url', row.get('photo', ''))))
            # Clean up null values and validate URLs
            if not image_url or image_url.lower() in ['[null]', 'null', ''] or not image_url.startswith('http'):
                # Generate a placeholder image URL based on strain type
                image_url = self._get_placeholder_image(strain_type, name)
            
            # Parse effect percentages
            relaxed_pct = self._parse_percentage(row.get('relaxed', ''))
            happy_pct = self._parse_percentage(row.get('happy', ''))
            euphoric_pct = self._parse_percentage(row.get('euphoric', ''))
            uplifted_pct = self._parse_percentage(row.get('uplifted', ''))
            creative_pct = self._parse_percentage(row.get('creative', ''))
            focused_pct = self._parse_percentage(row.get('focused', ''))
            energetic_pct = self._parse_percentage(row.get('energetic', ''))
            talkative_pct = self._parse_percentage(row.get('talkative', ''))
            hungry_pct = self._parse_percentage(row.get('hungry', ''))
            sleepy_pct = self._parse_percentage(row.get('sleepy', ''))
            
            return StrainData(
                name=name,
                type=strain_type,
                rating=rating,
                effects=effects,
                flavors=flavors,
                description=description,
                thc_high=thc_high,
                thc_low=thc_low,
                cbd_high=cbd_high,
                cbd_low=cbd_low,
                terpenes=terpenes,
                most_common_terpene=most_common_terpene,
                medical_uses=medical_uses,
                image_url=image_url,
                relaxed_pct=relaxed_pct,
                happy_pct=happy_pct,
                euphoric_pct=euphoric_pct,
                uplifted_pct=uplifted_pct,
                creative_pct=creative_pct,
                focused_pct=focused_pct,
                energetic_pct=energetic_pct,
                talkative_pct=talkative_pct,
                hungry_pct=hungry_pct,
                sleepy_pct=sleepy_pct
            )
            
        except Exception as e:
            print(f"Error parsing strain row: {e}")
            return None

    def _parse_percentage(self, value: str) -> Optional[float]:
        """Parse percentage string to float."""
        if not value or value.lower() in ['', 'n/a', 'none', 'unknown']:
            return None
        try:
            # Remove % symbol and convert
            clean_value = re.sub(r'[%\s]', '', str(value))
            return float(clean_value) if clean_value else None
        except ValueError:
            return None

    def get_top_effects(self, strain: StrainData, limit: int = 3) -> List[tuple]:
        """Get the top effects for a strain based on percentages."""
        effects_data = [
            ('😌 Relaxed', strain.relaxed_pct),
            ('😊 Happy', strain.happy_pct),
            ('🚀 Euphoric', strain.euphoric_pct),
            ('⬆️ Uplifted', strain.uplifted_pct),
            ('🎨 Creative', strain.creative_pct),
            ('🎯 Focused', strain.focused_pct),
            ('⚡ Energetic', strain.energetic_pct),
            ('💬 Talkative', strain.talkative_pct),
            ('🍔 Hungry', strain.hungry_pct),
            ('😴 Sleepy', strain.sleepy_pct)
        ]
        
        # Filter out None values and sort by percentage
        valid_effects = [(name, pct) for name, pct in effects_data if pct is not None and pct > 0]
        valid_effects.sort(key=lambda x: x[1], reverse=True)
        
        return valid_effects[:limit]

    def format_effects_display(self, strain: StrainData) -> str:
        """Format effect percentages for display."""
        top_effects = self.get_top_effects(strain, 3)
        if not top_effects:
            return "No effect data available"
        
        effect_strings = [f"{name} {pct:.0f}%" for name, pct in top_effects]
        return " | ".join(effect_strings)

    def _get_placeholder_image(self, strain_type: str, strain_name: str) -> str:
        """Generate placeholder image URL based on strain type and name."""
        # Create a simple color-coded placeholder image URL
        type_colors = {
            'indica': '9C27B0',     # Purple
            'sativa': '4CAF50',     # Green  
            'hybrid': 'FF9800'      # Orange
        }
        
        color = type_colors.get(strain_type.lower(), '607D8B')  # Default grey
        
        # Use a placeholder image service with strain info
        # This creates a simple colored image with text
        encoded_name = strain_name.replace(' ', '%20')
        return f"https://via.placeholder.com/400x300/{color}/FFFFFF?text={encoded_name}%0A({strain_type})"

    def _get_strain_image_url(self, strain_name: str, strain_type: str) -> str:
        """Get strain image URL, with fallback to placeholder."""
        # In a real implementation, you might:
        # 1. Check if image exists in dataset
        # 2. Search Unsplash/cannabis image APIs
        # 3. Use a cannabis strain image database
        
        # For now, return placeholder
        return self._get_placeholder_image(strain_type, strain_name)

    async def _create_sample_data(self):
        """Create sample strain data if CSV doesn't exist."""
        sample_strains = [
            {
                'name': 'Blue Dream',
                'type': 'hybrid',
                'rating': 4.5,
                'effects': ['relaxed', 'happy', 'creative', 'euphoric'],
                'flavors': ['blueberry', 'sweet', 'berry'],
                'description': 'A balanced hybrid with sweet berry flavors and uplifting effects.',
                'thc_high': 24.0,
                'thc_low': 17.0,
                'cbd_high': 2.0,
                'cbd_low': 0.1,
                'terpenes': ['myrcene', 'pinene', 'caryophyllene'],
                'medical_uses': ['depression', 'pain', 'nausea'],
                'image_url': 'https://via.placeholder.com/400x300/4CAF50/FFFFFF?text=Blue%20Dream%0A(hybrid)'
            },
            {
                'name': 'Girl Scout Cookies',
                'type': 'hybrid',
                'rating': 4.6,
                'effects': ['happy', 'relaxed', 'euphoric', 'creative'],
                'flavors': ['sweet', 'earthy', 'pungent'],
                'description': 'A potent hybrid known for its sweet and earthy aroma.',
                'thc_high': 28.0,
                'thc_low': 19.0,
                'cbd_high': 1.0,
                'cbd_low': 0.1,
                'terpenes': ['caryophyllene', 'limonene', 'humulene'],
                'medical_uses': ['pain', 'nausea', 'appetite loss'],
                'image_url': 'https://via.placeholder.com/400x300/FF9800/FFFFFF?text=Girl%20Scout%20Cookies%0A(hybrid)'
            },
            {
                'name': 'OG Kush',
                'type': 'indica',
                'rating': 4.3,
                'effects': ['relaxed', 'happy', 'euphoric', 'sleepy'],
                'flavors': ['earthy', 'pine', 'woody'],
                'description': 'A classic indica strain with strong relaxing effects.',
                'thc_high': 26.0,
                'thc_low': 20.0,
                'cbd_high': 0.5,
                'cbd_low': 0.1,
                'terpenes': ['myrcene', 'limonene', 'caryophyllene'],
                'medical_uses': ['insomnia', 'pain', 'stress'],
                'image_url': 'https://via.placeholder.com/400x300/9C27B0/FFFFFF?text=OG%20Kush%0A(indica)'
            },
            {
                'name': 'Green Crack',
                'type': 'sativa',
                'rating': 4.4,
                'effects': ['energetic', 'focused', 'happy', 'uplifted'],
                'flavors': ['citrus', 'fruity', 'sweet'],
                'description': 'An energizing sativa perfect for daytime use.',
                'thc_high': 24.0,
                'thc_low': 18.0,
                'cbd_high': 1.0,
                'cbd_low': 0.1,
                'terpenes': ['pinene', 'limonene', 'caryophyllene'],
                'medical_uses': ['depression', 'fatigue', 'stress'],
                'image_url': 'https://via.placeholder.com/400x300/4CAF50/FFFFFF?text=Green%20Crack%0A(sativa)'
            }
        ]
        
        for strain_data in sample_strains:
            strain = StrainData(**strain_data)
            self.strains[strain.name.lower()] = strain

    async def search_strain(self, query: str) -> List[StrainData]:
        """Search for strains by name (fuzzy matching)."""
        if not self.loaded:
            await self.load_database()
        
        query_lower = query.lower().strip()
        results = []
        
        # Exact match first
        if query_lower in self.strains:
            results.append(self.strains[query_lower])
            return results
        
        # Partial matches
        for name, strain in self.strains.items():
            if query_lower in name or any(query_lower in word for word in name.split()):
                results.append(strain)
        
        # Sort by rating (highest first) with randomization
        results.sort(key=lambda x: (x.rating + random.uniform(-0.3, 0.3)), reverse=True)
        return results[:10]  # Limit to top 10 results

    async def get_strains_by_effects(self, desired_effects: List[str]) -> List[StrainData]:
        """Find strains that provide specific effects."""
        if not self.loaded:
            await self.load_database()
        
        results = []
        desired_effects_lower = [effect.lower() for effect in desired_effects]
        
        for strain in self.strains.values():
            strain_effects_lower = [effect.lower() for effect in strain.effects]
            
            # Count matching effects
            matches = sum(1 for effect in desired_effects_lower 
                         if any(effect in strain_effect for strain_effect in strain_effects_lower))
            
            if matches > 0:
                results.append((strain, matches))
        
        # Sort by number of matches, then by rating with randomization
        results.sort(key=lambda x: (x[1], x[0].rating + random.uniform(-0.2, 0.2)), reverse=True)
        return [strain for strain, _ in results[:15]]

    async def get_strains_by_medical_condition(self, condition: str) -> List[StrainData]:
        """Find strains suitable for a medical condition."""
        if not self.loaded:
            await self.load_database()
        
        condition_lower = condition.lower()
        results = []
        
        # Find relevant effects for the condition
        relevant_effects = []
        for category, conditions in self.medical_mappings.items():
            if any(condition_lower in cond.lower() for cond in conditions):
                relevant_effects.extend(self._get_effects_for_condition(category))
        
        if not relevant_effects:
            # Fallback to direct medical use search
            for strain in self.strains.values():
                if strain.medical_uses and any(condition_lower in use.lower() for use in strain.medical_uses):
                    results.append(strain)
        else:
            # Search by relevant effects
            results = await self.get_strains_by_effects(relevant_effects)
        
        return results[:10]

    def _get_effects_for_condition(self, condition_category: str) -> List[str]:
        """Get recommended effects for a medical condition category."""
        effect_mapping = {
            'pain': ['relaxed', 'sleepy', 'body-high'],
            'anxiety': ['relaxed', 'calm', 'focused'],
            'depression': ['happy', 'euphoric', 'uplifted'],
            'insomnia': ['sleepy', 'relaxed', 'sedated'],
            'nausea': ['hungry', 'appetite'],
            'inflammation': ['relaxed', 'body-high'],
            'adhd': ['focused', 'creative', 'energetic']
        }
        return effect_mapping.get(condition_category, [])

    async def get_strains_by_type(self, strain_type: str) -> List[StrainData]:
        """Get strains by type (indica, sativa, hybrid)."""
        if not self.loaded:
            await self.load_database()
        
        type_lower = strain_type.lower()
        results = [strain for strain in self.strains.values() 
                  if strain.type.lower() == type_lower]
        
        # Sort by rating with randomization
        results.sort(key=lambda x: x.rating + random.uniform(-0.3, 0.3), reverse=True)
        return results[:20]

    async def get_high_cbd_strains(self, min_cbd: float = 10.0) -> List[StrainData]:
        """Get strains with high CBD content."""
        if not self.loaded:
            await self.load_database()
        
        results = []
        for strain in self.strains.values():
            if strain.cbd_high and strain.cbd_high >= min_cbd:
                results.append(strain)
        
        # Sort by CBD content with slight randomization
        results.sort(key=lambda x: (x.cbd_high or 0) + random.uniform(-1.0, 1.0), reverse=True)
        return results[:15]

    async def get_balanced_strains(self) -> List[StrainData]:
        """Get balanced THC:CBD strains."""
        if not self.loaded:
            await self.load_database()
        
        results = []
        for strain in self.strains.values():
            if (strain.thc_high and strain.cbd_high and 
                strain.thc_high > 0 and strain.cbd_high > 0):
                
                # Consider balanced if CBD is at least 25% of THC content
                ratio = strain.cbd_high / strain.thc_high
                if 0.25 <= ratio <= 4.0:  # 1:4 to 4:1 ratio
                    results.append((strain, ratio))
        
        # Sort by rating with randomization
        results.sort(key=lambda x: x[0].rating + random.uniform(-0.2, 0.2), reverse=True)
        return [strain for strain, _ in results[:15]]

    async def get_strain_recommendations(self, user_preferences: Dict) -> List[StrainData]:
        """Get personalized strain recommendations based on user preferences."""
        if not self.loaded:
            await self.load_database()
        
        # Extract preferences
        preferred_effects = user_preferences.get('effects', [])
        preferred_type = user_preferences.get('type', '')
        medical_conditions = user_preferences.get('medical_conditions', [])
        max_thc = user_preferences.get('max_thc', None)
        min_cbd = user_preferences.get('min_cbd', None)
        
        results = []
        
        for strain in self.strains.values():
            score = 0
            
            # Score based on effects match
            if preferred_effects:
                effect_matches = sum(1 for effect in preferred_effects 
                                   if any(effect.lower() in strain_effect.lower() 
                                         for strain_effect in strain.effects))
                score += effect_matches * 10
            
            # Score based on type match
            if preferred_type and strain.type.lower() == preferred_type.lower():
                score += 15
            
            # Score based on medical conditions
            if medical_conditions and strain.medical_uses:
                medical_matches = sum(1 for condition in medical_conditions 
                                    if any(condition.lower() in use.lower() 
                                          for use in strain.medical_uses))
                score += medical_matches * 20
            
            # Filter by THC/CBD requirements
            if max_thc and strain.thc_high and strain.thc_high > max_thc:
                continue
            if min_cbd and (not strain.cbd_high or strain.cbd_high < min_cbd):
                continue
            
            # Add rating bonus
            score += strain.rating * 2
            
            if score > 0:
                results.append((strain, score))
        
        # Add randomization factor to make recommendations more varied
        for i, (strain, score) in enumerate(results):
            # Add random bonus/penalty (±5 points) to mix up results
            randomized_score = score + random.uniform(-5, 5)
            results[i] = (strain, randomized_score)
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return [strain for strain, _ in results[:10]]

    def get_database_stats(self) -> Dict:
        """Get statistics about the strain database."""
        if not self.loaded:
            return {}
        
        total_strains = len(self.strains)
        type_counts = {}
        avg_rating = 0
        
        for strain in self.strains.values():
            # Count by type
            strain_type = strain.type.lower()
            type_counts[strain_type] = type_counts.get(strain_type, 0) + 1
            
            # Sum ratings
            avg_rating += strain.rating
        
        avg_rating = avg_rating / total_strains if total_strains > 0 else 0
        
        return {
            'total_strains': total_strains,
            'type_distribution': type_counts,
            'average_rating': round(avg_rating, 2),
            'loaded': self.loaded
        }

    async def get_random_strains(self, count: int = 5, strain_type: Optional[str] = None) -> List[StrainData]:
        """Get random strains, optionally filtered by type."""
        if not self.loaded:
            await self.load_database()
        
        available_strains = list(self.strains.values())
        
        # Filter by type if specified
        if strain_type:
            available_strains = [s for s in available_strains if s.type.lower() == strain_type.lower()]
        
        # Return random selection
        if len(available_strains) <= count:
            return available_strains
        
        return random.sample(available_strains, count)

    async def get_surprise_recommendation(self) -> Optional[StrainData]:
        """Get a completely random 'surprise' strain recommendation."""
        if not self.loaded:
            await self.load_database()
        
        # Get high-rated strains (4.0+ rating) for better surprises
        good_strains = [strain for strain in self.strains.values() if strain.rating >= 4.0]
        
        if not good_strains:
            good_strains = list(self.strains.values())
        
        return random.choice(good_strains) if good_strains else None

    async def get_daily_featured_strain(self) -> Optional[StrainData]:
        """Get a 'strain of the day' that changes daily but is consistent for the same day."""
        if not self.loaded:
            await self.load_database()
        
        # Use current date as seed for consistent daily selection
        import datetime
        today = datetime.date.today()
        daily_seed = today.year * 10000 + today.month * 100 + today.day
        
        # Create temporary random generator with daily seed
        daily_random = random.Random(daily_seed)
        
        # Select from highly rated strains
        featured_candidates = [strain for strain in self.strains.values() if strain.rating >= 4.2]
        
        if not featured_candidates:
            featured_candidates = list(self.strains.values())
        
        return daily_random.choice(featured_candidates) if featured_candidates else None

    def shuffle_results(self, results: List[StrainData], randomization_factor: float = 0.3) -> List[StrainData]:
        """Shuffle strain results while maintaining general quality order."""
        if not results:
            return results
        
        # Create tuples with randomized scores
        randomized = []
        for strain in results:
            # Add random factor to rating for shuffling
            random_score = strain.rating + random.uniform(-randomization_factor, randomization_factor)
            randomized.append((strain, random_score))
        
        # Sort by randomized score
        randomized.sort(key=lambda x: x[1], reverse=True)
        
        return [strain for strain, _ in randomized]

# Global instance
strain_db = StrainDatabaseService()
