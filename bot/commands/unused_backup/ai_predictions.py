"""Advanced AI-powered tolerance modeling and consumption optimization."""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class ConsumptionPattern:
    """Data structure for consumption patterns."""
    timestamp: datetime
    thc_amount: float
    method: str
    strain_type: str
    effects_rating: int
    duration_hours: float
    tolerance_level: float

@dataclass
class ToleranceModel:
    """Tolerance prediction model."""
    base_tolerance: float
    tolerance_growth_rate: float
    decay_rate: float
    method_multipliers: Dict[str, float]
    strain_sensitivities: Dict[str, float]

@dataclass
class OptimizationRecommendation:
    """Consumption optimization recommendation."""
    recommended_dose: float
    optimal_method: str
    best_strain_type: str
    timing_suggestion: str
    confidence_score: float
    reasoning: str

class AIPredictions(commands.Cog):
    """AI-powered tolerance modeling and consumption optimization."""
    
    def __init__(self, bot):
        self.bot = bot
        self.tolerance_models = {}  # User tolerance models
        self.consumption_history = {}  # User consumption patterns
        self.optimization_cache = {}  # Cached recommendations
        
        # AI model parameters
        self.method_bioavailability = {
            "smoking": 0.30,
            "vaping": 0.45,
            "edibles": 0.15,
            "tinctures": 0.25,
            "dabbing": 0.75,
            "topicals": 0.05
        }
        
        self.tolerance_factors = {
            "frequency_multiplier": 1.2,  # Daily use increases tolerance
            "amount_multiplier": 1.1,     # Higher doses increase tolerance
            "method_resistance": {         # Different methods build tolerance differently
                "smoking": 1.3,
                "vaping": 1.2,
                "dabbing": 1.5,
                "edibles": 1.1,
                "tinctures": 1.15,
                "topicals": 1.05
            }
        }
    
    async def update_tolerance_model(self, user_id: int, consumption_data: ConsumptionPattern):
        """Update user's tolerance model with new consumption data."""
        if user_id not in self.tolerance_models:
            self.tolerance_models[user_id] = ToleranceModel(
                base_tolerance=1.0,
                tolerance_growth_rate=0.05,
                decay_rate=0.02,
                method_multipliers=self.tolerance_factors["method_resistance"].copy(),
                strain_sensitivities={"indica": 1.0, "sativa": 1.1, "hybrid": 1.05}
            )
        
        if user_id not in self.consumption_history:
            self.consumption_history[user_id] = []
        
        # Add new consumption data
        self.consumption_history[user_id].append(consumption_data)
        
        # Keep last 100 entries for analysis
        if len(self.consumption_history[user_id]) > 100:
            self.consumption_history[user_id] = self.consumption_history[user_id][-100:]
        
        # Update tolerance model based on recent patterns
        await self._recalculate_tolerance_model(user_id)
    
    async def _recalculate_tolerance_model(self, user_id: int):
        """Recalculate tolerance model based on consumption history."""
        history = self.consumption_history.get(user_id, [])
        if len(history) < 3:
            return  # Need at least 3 data points
        
        model = self.tolerance_models[user_id]
        recent_history = history[-30:]  # Last 30 sessions
        
        # Calculate average frequency (sessions per week)
        if len(recent_history) >= 7:
            time_span = (recent_history[-1].timestamp - recent_history[0].timestamp).days
            frequency = len(recent_history) / max(time_span / 7, 1)
            
            # Adjust tolerance based on frequency
            if frequency > 7:  # Daily+ use
                model.tolerance_growth_rate = min(0.15, model.tolerance_growth_rate * 1.2)
            elif frequency > 3:  # Regular use
                model.tolerance_growth_rate = min(0.10, model.tolerance_growth_rate * 1.1)
            else:  # Occasional use
                model.tolerance_growth_rate = max(0.02, model.tolerance_growth_rate * 0.9)
        
        # Calculate current tolerance level
        current_tolerance = self._calculate_current_tolerance(user_id)
        model.base_tolerance = current_tolerance
    
    def _calculate_current_tolerance(self, user_id: int) -> float:
        """Calculate current tolerance level based on recent consumption."""
        history = self.consumption_history.get(user_id, [])
        if not history:
            return 1.0
        
        # Analyze last 14 days
        cutoff_date = datetime.utcnow() - timedelta(days=14)
        recent_sessions = [h for h in history if h.timestamp > cutoff_date]
        
        if not recent_sessions:
            return max(0.5, self.tolerance_models[user_id].base_tolerance * 0.85)  # Tolerance decay
        
        # Calculate tolerance based on frequency and amounts
        total_thc = sum(session.thc_amount for session in recent_sessions)
        session_count = len(recent_sessions)
        avg_daily_thc = total_thc / 14
        
        # Base tolerance calculation
        base_tolerance = 1.0
        if avg_daily_thc > 50:  # Heavy use
            base_tolerance = 2.5
        elif avg_daily_thc > 20:  # Moderate use
            base_tolerance = 1.8
        elif avg_daily_thc > 5:   # Light regular use
            base_tolerance = 1.3
        
        # Adjust for session frequency
        sessions_per_week = session_count / 2
        if sessions_per_week > 10:
            base_tolerance *= 1.4
        elif sessions_per_week > 5:
            base_tolerance *= 1.2
        
        return min(4.0, base_tolerance)  # Cap at 4x tolerance
    
    async def predict_optimal_dose(self, user_id: int, desired_effects: str, 
                                 method: str = None, strain_type: str = None) -> OptimizationRecommendation:
        """Predict optimal dosing for desired effects."""
        if user_id not in self.tolerance_models:
            # Create default model for new users
            await self.update_tolerance_model(user_id, ConsumptionPattern(
                timestamp=datetime.utcnow(),
                thc_amount=5.0,
                method="vaping",
                strain_type="hybrid",
                effects_rating=7,
                duration_hours=2.0,
                tolerance_level=1.0
            ))
        
        model = self.tolerance_models[user_id]
        current_tolerance = self._calculate_current_tolerance(user_id)
        
        # Base dose recommendations for different effect levels
        effect_targets = {
            "microdose": 2.5,
            "light": 5.0,
            "moderate": 10.0,
            "strong": 20.0,
            "very_strong": 35.0
        }
        
        target_dose = effect_targets.get(desired_effects.lower(), 10.0)
        
        # Adjust for tolerance
        adjusted_dose = target_dose * current_tolerance
        
        # Method optimization
        if not method:
            # Recommend best method based on desired effects
            method_recommendations = {
                "microdose": "vaping",
                "light": "vaping",
                "moderate": "smoking",
                "strong": "edibles",
                "very_strong": "dabbing"
            }
            method = method_recommendations.get(desired_effects.lower(), "vaping")
        
        # Adjust dose for method bioavailability
        bioavailability = self.method_bioavailability.get(method, 0.3)
        final_dose = adjusted_dose / bioavailability
        
        # Strain type optimization
        if not strain_type:
            strain_recommendations = {
                "microdose": "hybrid",
                "light": "sativa",
                "moderate": "hybrid",
                "strong": "indica",
                "very_strong": "indica"
            }
            strain_type = strain_recommendations.get(desired_effects.lower(), "hybrid")
        
        # Generate timing suggestion
        timing_suggestion = self._generate_timing_suggestion(user_id, method)
        
        # Calculate confidence based on data quality
        history_length = len(self.consumption_history.get(user_id, []))
        confidence = min(0.95, 0.5 + (history_length * 0.01))
        
        # Generate reasoning
        reasoning = self._generate_reasoning(current_tolerance, method, strain_type, desired_effects)
        
        return OptimizationRecommendation(
            recommended_dose=round(final_dose, 1),
            optimal_method=method,
            best_strain_type=strain_type,
            timing_suggestion=timing_suggestion,
            confidence_score=confidence,
            reasoning=reasoning
        )
    
    def _generate_timing_suggestion(self, user_id: int, method: str) -> str:
        """Generate optimal timing suggestion."""
        history = self.consumption_history.get(user_id, [])
        
        if history:
            # Analyze when user typically consumes
            hours = [h.timestamp.hour for h in history[-20:]]  # Last 20 sessions
            avg_hour = statistics.mean(hours) if hours else 18
            
            if method in ["edibles", "tinctures"]:
                return f"Start around {int(avg_hour)-2}:00 (2h earlier for edibles/tinctures)"
            else:
                return f"Optimal time around {int(avg_hour)}:00 based on your patterns"
        else:
            if method in ["edibles", "tinctures"]:
                return "Start 2-3 hours before desired effect time"
            else:
                return "Evening consumption typically optimal (6-8 PM)"
    
    def _generate_reasoning(self, tolerance: float, method: str, strain_type: str, effects: str) -> str:
        """Generate AI reasoning for recommendations."""
        tolerance_desc = "low" if tolerance < 1.5 else "moderate" if tolerance < 2.5 else "high"
        
        reasoning_parts = [
            f"Based on your {tolerance_desc} tolerance level ({tolerance:.1f}x)",
            f"{method.title()} provides optimal bioavailability for {effects} effects",
            f"{strain_type.title()} strains align with desired experience profile"
        ]
        
        if tolerance > 2.0:
            reasoning_parts.append("Consider a tolerance break to reset sensitivity")
        
        return " • ".join(reasoning_parts)
    
    @app_commands.command(name="predict", description="🤖 Get AI-powered dosing predictions and optimization")
    @app_commands.describe(
        effects="Desired effect level",
        method="Preferred consumption method", 
        strain_type="Preferred strain type"
    )
    @app_commands.choices(effects=[
        app_commands.Choice(name="🌱 Microdose (Subtle)", value="microdose"),
        app_commands.Choice(name="☁️ Light (Relaxed)", value="light"),
        app_commands.Choice(name="🌙 Moderate (Balanced)", value="moderate"),
        app_commands.Choice(name="⭐ Strong (Intense)", value="strong"),
        app_commands.Choice(name="🚀 Very Strong (Maximum)", value="very_strong")
    ])
    @app_commands.choices(method=[
        app_commands.Choice(name="💨 Vaping", value="vaping"),
        app_commands.Choice(name="🚬 Smoking", value="smoking"),
        app_commands.Choice(name="🍪 Edibles", value="edibles"),
        app_commands.Choice(name="💧 Tinctures", value="tinctures"),
        app_commands.Choice(name="🔥 Dabbing", value="dabbing")
    ])
    @app_commands.choices(strain_type=[
        app_commands.Choice(name="🌿 Indica (Relaxing)", value="indica"),
        app_commands.Choice(name="🌱 Sativa (Energizing)", value="sativa"),
        app_commands.Choice(name="🔄 Hybrid (Balanced)", value="hybrid")
    ])
    async def predict_dosing(self, interaction: discord.Interaction, effects: str,
                           method: str = None, strain_type: str = None):
        """Get AI-powered dosing predictions and consumption optimization."""
        
        # Get prediction
        recommendation = await self.predict_optimal_dose(
            interaction.user.id, effects, method, strain_type
        )
        
        embed = discord.Embed(
            title="🤖 AI Dosing Prediction",
            description=f"Personalized optimization for **{effects.replace('_', ' ').title()}** effects",
            color=0x9C27B0
        )
        
        # Main recommendation
        embed.add_field(
            name="🎯 Recommended Dose",
            value=f"**{recommendation.recommended_dose}mg THC**\n"
                  f"Method: {recommendation.optimal_method.title()}\n"
                  f"Strain: {recommendation.best_strain_type.title()}",
            inline=True
        )
        
        # Confidence and timing
        confidence_emoji = "🎯" if recommendation.confidence_score > 0.8 else "📊" if recommendation.confidence_score > 0.6 else "🔄"
        embed.add_field(
            name="📊 Prediction Accuracy",
            value=f"**{confidence_emoji} {recommendation.confidence_score*100:.0f}% confident**\n"
                  f"Timing: {recommendation.timing_suggestion}",
            inline=True
        )
        
        # Current tolerance info
        current_tolerance = self._calculate_current_tolerance(interaction.user.id)
        tolerance_emoji = "🌱" if current_tolerance < 1.5 else "🌿" if current_tolerance < 2.5 else "🔥"
        
        embed.add_field(
            name="🧬 Your Tolerance",
            value=f"**{tolerance_emoji} {current_tolerance:.1f}x baseline**\n"
                  f"Level: {self._get_tolerance_description(current_tolerance)}",
            inline=True
        )
        
        # AI reasoning
        embed.add_field(
            name="🧠 AI Analysis",
            value=recommendation.reasoning,
            inline=False
        )
        
        # Safety recommendations
        safety_tips = self._get_safety_recommendations(recommendation.recommended_dose, recommendation.optimal_method)
        embed.add_field(
            name="⚠️ Safety Guidelines",
            value=safety_tips,
            inline=False
        )
        
        embed.set_footer(text="AI Predictions • Based on your consumption patterns")
        
        view = PredictionActionsView(self, interaction.user.id, recommendation)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    def _get_tolerance_description(self, tolerance: float) -> str:
        """Get human-readable tolerance description."""
        if tolerance < 1.2:
            return "Low (New/Occasional user)"
        elif tolerance < 1.8:
            return "Moderate (Regular user)"
        elif tolerance < 2.5:
            return "High (Frequent user)"
        else:
            return "Very High (Daily+ user)"
    
    def _get_safety_recommendations(self, dose: float, method: str) -> str:
        """Generate safety recommendations based on dose and method."""
        tips = []
        
        if dose > 20:
            tips.append("• High dose - start with half and wait")
        
        if method == "edibles":
            tips.append("• Wait 2+ hours before redosing with edibles")
        elif method == "dabbing":
            tips.append("• Start small with concentrates - very potent")
        
        tips.extend([
            "• Stay hydrated and have snacks ready",
            "• Consume in a safe, comfortable environment"
        ])
        
        return "\n".join(tips)
    
    @app_commands.command(name="tolerance", description="🧬 View your tolerance analysis and predictions")
    async def tolerance_analysis(self, interaction: discord.Interaction):
        """Show detailed tolerance analysis and trends."""
        user_id = interaction.user.id
        current_tolerance = self._calculate_current_tolerance(user_id)
        history = self.consumption_history.get(user_id, [])
        
        embed = discord.Embed(
            title="🧬 Tolerance Analysis",
            description="AI-powered analysis of your cannabis tolerance patterns",
            color=0x4CAF50
        )
        
        # Current tolerance status
        tolerance_emoji = "🌱" if current_tolerance < 1.5 else "🌿" if current_tolerance < 2.5 else "🔥"
        embed.add_field(
            name="📊 Current Tolerance",
            value=f"**{tolerance_emoji} {current_tolerance:.1f}x baseline**\n"
                  f"{self._get_tolerance_description(current_tolerance)}\n"
                  f"Data points: {len(history)}",
            inline=True
        )
        
        # Tolerance trend
        if len(history) >= 10:
            recent_tolerance = self._calculate_tolerance_trend(user_id)
            trend_emoji = "📈" if recent_tolerance > 0 else "📉" if recent_tolerance < 0 else "📊"
            trend_text = "Increasing" if recent_tolerance > 0 else "Decreasing" if recent_tolerance < 0 else "Stable"
            
            embed.add_field(
                name="📈 Tolerance Trend",
                value=f"**{trend_emoji} {trend_text}**\n"
                      f"Change: {recent_tolerance:+.1f}x/week\n"
                      f"Based on last 4 weeks",
                inline=True
            )
        
        # Optimization suggestions
        suggestions = self._generate_tolerance_suggestions(current_tolerance, history)
        embed.add_field(
            name="💡 Optimization Tips",
            value=suggestions,
            inline=True
        )
        
        # Method efficiency analysis
        if history:
            method_analysis = self._analyze_method_efficiency(user_id)
            embed.add_field(
                name="🔬 Method Efficiency",
                value=method_analysis,
                inline=False
            )
        
        embed.set_footer(text="Tolerance Analysis • AI-powered insights")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def _calculate_tolerance_trend(self, user_id: int) -> float:
        """Calculate tolerance change trend over time."""
        history = self.consumption_history.get(user_id, [])
        if len(history) < 10:
            return 0.0
        
        # Compare first half vs second half of recent history
        mid_point = len(history) // 2
        early_sessions = history[:mid_point]
        recent_sessions = history[mid_point:]
        
        early_avg = statistics.mean([s.thc_amount for s in early_sessions])
        recent_avg = statistics.mean([s.thc_amount for s in recent_sessions])
        
        return (recent_avg - early_avg) / len(history) * 7  # Per week
    
    def _generate_tolerance_suggestions(self, tolerance: float, history: List) -> str:
        """Generate personalized tolerance optimization suggestions."""
        suggestions = []
        
        if tolerance > 2.5:
            suggestions.append("🔄 Consider a tolerance break (3-7 days)")
        elif tolerance > 2.0:
            suggestions.append("⚖️ Try reducing dose by 20-30%")
        
        if len(history) >= 5:
            recent_methods = [h.method for h in history[-5:]]
            if len(set(recent_methods)) == 1:
                suggestions.append("🔀 Try rotating consumption methods")
        
        suggestions.append("🌱 Microdosing can help reset sensitivity")
        
        return "\n".join([f"• {s}" for s in suggestions])
    
    def _analyze_method_efficiency(self, user_id: int) -> str:
        """Analyze efficiency of different consumption methods for user."""
        history = self.consumption_history.get(user_id, [])
        method_data = {}
        
        for session in history:
            if session.method not in method_data:
                method_data[session.method] = {"doses": [], "ratings": []}
            method_data[session.method]["doses"].append(session.thc_amount)
            method_data[session.method]["ratings"].append(session.effects_rating)
        
        analysis = []
        for method, data in method_data.items():
            if len(data["doses"]) >= 2:
                avg_dose = statistics.mean(data["doses"])
                avg_rating = statistics.mean(data["ratings"])
                efficiency = avg_rating / avg_dose if avg_dose > 0 else 0
                
                analysis.append(f"**{method.title()}:** {efficiency:.2f} efficiency score")
        
        return "\n".join(analysis) if analysis else "Not enough data for analysis"

class PredictionActionsView(discord.ui.View):
    """Actions for AI predictions."""
    
    def __init__(self, cog, user_id: int, recommendation: OptimizationRecommendation):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.recommendation = recommendation
    
    @discord.ui.button(label="📝 Log This Session", style=discord.ButtonStyle.success, emoji="📝")
    async def log_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Log a session using these recommendations."""
        embed = discord.Embed(
            title="📝 Session Logging",
            description="Use `/consume` command with these AI-recommended settings:\n\n"
                       f"**Amount:** {self.recommendation.recommended_dose}mg\n"
                       f"**Method:** {self.recommendation.optimal_method}\n"
                       f"**Strain Type:** {self.recommendation.best_strain_type}",
            color=0x4CAF50
        )
        
        embed.add_field(
            name="💡 Quick Tip",
            value="After your session, rate the effects to improve future predictions!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔄 Adjust Recommendation", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def adjust_recommendation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Adjust the recommendation parameters."""
        embed = discord.Embed(
            title="🔄 Adjust Recommendations",
            description="Want different suggestions? Try:\n\n"
                       "• Use `/predict` again with different effect level\n"
                       "• Specify different method or strain preferences\n"
                       "• Log more sessions to improve AI accuracy",
            color=0x2196F3
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIPredictions(bot))
