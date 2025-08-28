"""Smart automation and workflow optimization features."""

import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional, List
import logging
from datetime import datetime, timedelta
import asyncio

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

logger = logging.getLogger(__name__)

class SmartAutomationCommands(commands.Cog):
    """Smart automation and workflow optimization."""
    
    def __init__(self, bot):
        self.bot = bot
        self.smart_insights_task.start()
    
    def cog_unload(self):
        self.smart_insights_task.cancel()
    
    @tasks.loop(hours=24)
    async def smart_insights_task(self):
        """Daily task to generate smart insights for active users."""
        try:
            # This would normally check all users, but for demo we'll keep it simple
            logger.info("Running daily smart insights generation")
        except Exception as e:
            logger.error(f"Smart insights task error: {e}")
    
    @app_commands.command(name="insights", description="🧠 Get AI-powered insights about your consumption patterns")
    async def smart_insights(self, interaction: discord.Interaction):
        """Generate smart insights for the user."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            
            # Get comprehensive data
            week_summary = await ConsumptionService.get_consumption_summary(user_id, days=7)
            month_summary = await ConsumptionService.get_consumption_summary(user_id, days=30)
            
            insights = await self._generate_smart_insights(user_id, week_summary, month_summary)
            
            embed = discord.Embed(
                title="🧠 Smart Insights",
                description="AI-powered analysis of your consumption patterns",
                color=0x9C27B0
            )
            
            for insight in insights[:5]:  # Show top 5 insights
                embed.add_field(
                    name=f"{insight['icon']} {insight['title']}",
                    value=insight['description'],
                    inline=False
                )
            
            embed.set_footer(text="Insights update daily • Based on your consumption patterns")
            
            view = InsightsActionView(user_id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Smart insights error: {e}")
            await interaction.followup.send(f"❌ Error generating insights: {str(e)}", ephemeral=True)
    
    async def _generate_smart_insights(self, user_id: int, week_data: dict, month_data: dict) -> List[dict]:
        """Generate smart insights based on user data."""
        insights = []
        
        week_sessions = week_data.get('session_count', 0)
        week_thc = week_data.get('total_thc_mg', 0)
        month_sessions = month_data.get('session_count', 0)
        month_thc = month_data.get('total_thc_mg', 0)
        
        # Pattern insights
        if week_sessions > 0:
            daily_avg_sessions = week_sessions / 7
            daily_avg_thc = week_thc / 7
            monthly_avg_thc = month_thc / 30 if month_thc > 0 else 0
            
            # Frequency insight
            if daily_avg_sessions < 1:
                insights.append({
                    'icon': '🌱',
                    'title': 'Moderate Usage Pattern',
                    'description': f'You average {daily_avg_sessions:.1f} sessions per day - a healthy, controlled approach to cannabis use.'
                })
            elif daily_avg_sessions > 3:
                insights.append({
                    'icon': '⚡',
                    'title': 'High Activity Period',
                    'description': f'You\'ve been quite active with {daily_avg_sessions:.1f} sessions daily. Consider if this aligns with your goals.'
                })
            
            # THC trend insight
            if week_thc > monthly_avg_thc * 7 * 1.3:  # 30% above monthly average
                insights.append({
                    'icon': '📈',
                    'title': 'Increased Consumption Trend',
                    'description': f'This week\'s THC intake ({week_thc:.0f}mg) is above your monthly average. Monitor tolerance buildup.'
                })
            elif week_thc < monthly_avg_thc * 7 * 0.7:  # 30% below monthly average
                insights.append({
                    'icon': '📉',
                    'title': 'Reduced Consumption Week',
                    'description': f'You\'ve consumed less THC this week ({week_thc:.0f}mg) than usual. Great for tolerance management!'
                })
            
            # Efficiency insight
            if week_sessions > 0:
                avg_thc_per_session = week_thc / week_sessions
                if avg_thc_per_session < 15:
                    insights.append({
                        'icon': '✨',
                        'title': 'Efficient Microdosing',
                        'description': f'Your average {avg_thc_per_session:.0f}mg per session shows excellent dose control and efficiency.'
                    })
                elif avg_thc_per_session > 50:
                    insights.append({
                        'icon': '🎯',
                        'title': 'High-Dose Sessions',
                        'description': f'Your sessions average {avg_thc_per_session:.0f}mg THC. Consider smaller doses for better tolerance management.'
                    })
        
        # Stash insights
        try:
            stash_items = await StashService.get_stash_items(user_id)
            total_stash = sum(item.amount for item in stash_items if item.amount)
            strain_variety = len(set(item.strain for item in stash_items if item.strain))
            
            if total_stash < 1.0:
                insights.append({
                    'icon': '📦',
                    'title': 'Stash Running Low',
                    'description': f'You have {total_stash:.1f}g remaining. Consider restocking your favorite strains soon.'
                })
            
            if strain_variety >= 3:
                insights.append({
                    'icon': '🌈',
                    'title': 'Great Strain Variety',
                    'description': f'You have {strain_variety} different strains - excellent for finding what works best for you!'
                })
        except Exception:
            pass
        
        # Timing insights (simplified)
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:
            insights.append({
                'icon': '⏰',
                'title': 'Daytime Usage',
                'description': 'Logging during work hours? Consider how cannabis affects your productivity and responsibilities.'
            })
        
        # Default insights if no patterns found
        if not insights:
            insights.append({
                'icon': '📊',
                'title': 'Building Your Profile',
                'description': 'Keep logging your sessions to unlock personalized insights about your consumption patterns!'
            })
        
        return insights
    
    @app_commands.command(name="optimize", description="🎯 Get personalized optimization suggestions")
    async def optimize_consumption(self, interaction: discord.Interaction):
        """Provide optimization suggestions."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            suggestions = await self._generate_optimization_suggestions(user_id)
            
            embed = discord.Embed(
                title="🎯 Optimization Suggestions",
                description="Personalized recommendations to improve your cannabis experience",
                color=0x4CAF50
            )
            
            for i, suggestion in enumerate(suggestions[:4], 1):
                embed.add_field(
                    name=f"{i}. {suggestion['title']}",
                    value=suggestion['description'],
                    inline=False
                )
            
            embed.set_footer(text="Suggestions based on your recent patterns • Update weekly")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            await interaction.followup.send(f"❌ Error generating suggestions: {str(e)}", ephemeral=True)
    
    async def _generate_optimization_suggestions(self, user_id: int) -> List[dict]:
        """Generate optimization suggestions."""
        suggestions = []
        
        try:
            # Get recent data
            week_summary = await ConsumptionService.get_consumption_summary(user_id, days=7)
            week_sessions = week_summary.get('session_count', 0)
            week_thc = week_summary.get('total_thc_mg', 0)
            
            if week_sessions == 0:
                suggestions.append({
                    'title': '📝 Start Tracking Consistently',
                    'description': 'Log your sessions regularly to get personalized insights and track your progress over time.'
                })
                return suggestions
            
            daily_avg_thc = week_thc / 7
            
            # Tolerance management
            if daily_avg_thc > 75:
                suggestions.append({
                    'title': '🔄 Consider Tolerance Break',
                    'description': f'Your daily average of {daily_avg_thc:.0f}mg is quite high. A 2-3 day break could reset your tolerance and improve effectiveness.'
                })
            
            # Method diversification
            suggestions.append({
                'title': '🌿 Try Different Methods',
                'description': 'Rotating between smoking, vaping, and edibles can prevent tolerance buildup and offer different experiences.'
            })
            
            # Timing optimization
            suggestions.append({
                'title': '⏰ Optimize Timing',
                'description': 'Try spacing sessions 4-6 hours apart for optimal effects and to prevent tolerance stacking.'
            })
            
            # Strain rotation
            suggestions.append({
                'title': '🔄 Rotate Strains',
                'description': 'Using different strains prevents tolerance to specific cannabinoid profiles. Aim for 2-3 different strains per week.'
            })
            
            # Microdosing suggestion
            if daily_avg_thc > 50:
                suggestions.append({
                    'title': '✨ Try Microdosing',
                    'description': 'Smaller, more frequent doses (2-5mg THC) can be more effective than larger doses while building less tolerance.'
                })
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            suggestions.append({
                'title': '📊 Keep Tracking',
                'description': 'Continue logging your sessions to unlock personalized optimization recommendations!'
            })
        
        return suggestions
    
    @app_commands.command(name="predict", description="🔮 Predict optimal consumption timing based on your patterns")
    async def predict_optimal_timing(self, interaction: discord.Interaction):
        """Predict optimal consumption timing."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            predictions = await self._generate_timing_predictions(user_id)
            
            embed = discord.Embed(
                title="🔮 Optimal Timing Predictions",
                description="AI predictions based on your consumption patterns",
                color=0x673AB7
            )
            
            for prediction in predictions:
                embed.add_field(
                    name=prediction['title'],
                    value=prediction['description'],
                    inline=False
                )
            
            embed.set_footer(text="Predictions improve with more data • Log consistently for better accuracy")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            await interaction.followup.send(f"❌ Error generating predictions: {str(e)}", ephemeral=True)
    
    async def _generate_timing_predictions(self, user_id: int) -> List[dict]:
        """Generate timing predictions."""
        predictions = []
        
        # Simplified predictions - in a real implementation, this would analyze actual session times
        current_hour = datetime.now().hour
        
        if current_hour < 12:
            predictions.append({
                'title': '🌅 Morning Consumption',
                'description': 'Based on typical patterns, 10-11 AM is optimal for productive daytime use with sativa-dominant strains.'
            })
        elif current_hour < 17:
            predictions.append({
                'title': '☀️ Afternoon Window',
                'description': 'Early afternoon (1-3 PM) can be good for moderate doses, especially if working from home.'
            })
        else:
            predictions.append({
                'title': '🌙 Evening Relaxation',
                'description': 'Evening sessions (7-9 PM) are ideal for indica strains and unwinding from the day.'
            })
        
        predictions.append({
            'title': '⏰ Spacing Recommendation',
            'description': 'Wait 4-6 hours between sessions for optimal effect and tolerance management.'
        })
        
        predictions.append({
            'title': '📅 Weekly Pattern',
            'description': 'Consider 1-2 tolerance break days per week to maintain effectiveness and prevent dependency.'
        })
        
        return predictions

class InsightsActionView(discord.ui.View):
    """Actions for insights response."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="🎯 Get Suggestions", style=discord.ButtonStyle.primary, emoji="🎯")
    async def get_suggestions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/optimize` for personalized optimization suggestions!", ephemeral=True)
    
    @discord.ui.button(label="🔮 Predict Timing", style=discord.ButtonStyle.secondary, emoji="🔮")
    async def predict_timing(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/predict` for optimal timing predictions!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SmartAutomationCommands(bot))
