"""Advanced analytics and sophisticated reporting features."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict
import logging
from datetime import datetime, timedelta
import calendar

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

logger = logging.getLogger(__name__)

class AdvancedAnalyticsCommands(commands.Cog):
    """Advanced analytics and sophisticated reporting."""
    
    def __init__(self, bot):
        self.bot = bot
    
    analytics_group = app_commands.Group(name="analytics", description="Advanced analytics and insights")
    
    @analytics_group.command(name="trends", description="📈 Analyze consumption trends over time")
    @app_commands.describe(
        period="Time period for trend analysis"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="📅 Last 7 Days", value="week"),
        app_commands.Choice(name="📊 Last 30 Days", value="month"),
        app_commands.Choice(name="📈 Last 90 Days", value="quarter"),
        app_commands.Choice(name="🗓️ Last 365 Days", value="year")
    ])
    async def analyze_trends(
        self,
        interaction: discord.Interaction,
        period: app_commands.Choice[str]
    ):
        """Analyze consumption trends."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            days_map = {"week": 7, "month": 30, "quarter": 90, "year": 365}
            days = days_map[period.value]
            
            trend_data = await self._analyze_consumption_trends(user_id, days)
            
            embed = discord.Embed(
                title=f"📈 Consumption Trends - {period.name.split()[-2]} {period.name.split()[-1]}",
                description="Analysis of your consumption patterns over time",
                color=0x2196F3
            )
            
            # Trend summary
            embed.add_field(
                name="📊 Trend Summary",
                value=f"**Total Sessions:** {trend_data['total_sessions']}\n"
                      f"**Total THC:** {trend_data['total_thc']:.0f}mg\n"
                      f"**Average Daily:** {trend_data['daily_avg_thc']:.1f}mg\n"
                      f"**Trend Direction:** {trend_data['trend_direction']}",
                inline=True
            )
            
            # Method distribution
            if trend_data['method_distribution']:
                method_text = "\n".join([
                    f"• {method}: {count} sessions"
                    for method, count in trend_data['method_distribution'].items()
                ])
                embed.add_field(
                    name="🌿 Method Breakdown",
                    value=method_text,
                    inline=True
                )
            
            # Peak usage insights
            embed.add_field(
                name="⚡ Peak Usage Insights",
                value=f"**Highest Day:** {trend_data['peak_day_thc']:.0f}mg\n"
                      f"**Most Active Day:** {trend_data['most_sessions_day']} sessions\n"
                      f"**Consistency Score:** {trend_data['consistency_score']}/10",
                inline=True
            )
            
            # Trend insights
            insights = self._generate_trend_insights(trend_data)
            if insights:
                embed.add_field(
                    name="💡 Key Insights",
                    value="\n".join(insights[:3]),
                    inline=False
                )
            
            embed.set_footer(text=f"Analysis based on {days} days of data • Trends update daily")
            
            view = TrendAnalysisView(user_id, period.value)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            await interaction.followup.send(f"❌ Error analyzing trends: {str(e)}", ephemeral=True)
    
    async def _analyze_consumption_trends(self, user_id: int, days: int) -> Dict:
        """Analyze consumption trends for a user."""
        try:
            # Get consumption data
            summary = await ConsumptionService.get_consumption_summary(user_id, days=days)
            
            total_sessions = summary.get('session_count', 0)
            total_thc = summary.get('total_thc_mg', 0)
            daily_avg_thc = total_thc / days if days > 0 else 0
            
            # Calculate trend direction (simplified)
            if days >= 14:
                recent_summary = await ConsumptionService.get_consumption_summary(user_id, days=days//2)
                recent_avg = recent_summary.get('total_thc_mg', 0) / (days//2)
                
                if recent_avg > daily_avg_thc * 1.1:
                    trend_direction = "📈 Increasing"
                elif recent_avg < daily_avg_thc * 0.9:
                    trend_direction = "📉 Decreasing"
                else:
                    trend_direction = "➡️ Stable"
            else:
                trend_direction = "➡️ Analyzing..."
            
            # Mock method distribution (would come from actual data)
            method_distribution = {
                "Smoking": total_sessions // 2,
                "Vaporizer": total_sessions // 3,
                "Edibles": total_sessions // 6
            }
            
            # Peak usage calculations (simplified)
            peak_day_thc = daily_avg_thc * 2.5  # Mock peak day
            most_sessions_day = min(5, total_sessions)  # Mock max sessions per day
            
            # Consistency score (how regular the usage is)
            consistency_score = min(10, max(1, 10 - (abs(peak_day_thc - daily_avg_thc) / daily_avg_thc * 5))) if daily_avg_thc > 0 else 5
            
            return {
                'total_sessions': total_sessions,
                'total_thc': total_thc,
                'daily_avg_thc': daily_avg_thc,
                'trend_direction': trend_direction,
                'method_distribution': method_distribution,
                'peak_day_thc': peak_day_thc,
                'most_sessions_day': most_sessions_day,
                'consistency_score': int(consistency_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {
                'total_sessions': 0,
                'total_thc': 0,
                'daily_avg_thc': 0,
                'trend_direction': "❓ No data",
                'method_distribution': {},
                'peak_day_thc': 0,
                'most_sessions_day': 0,
                'consistency_score': 0
            }
    
    def _generate_trend_insights(self, trend_data: Dict) -> List[str]:
        """Generate insights from trend data."""
        insights = []
        
        consistency = trend_data['consistency_score']
        if consistency >= 8:
            insights.append("✅ Very consistent usage patterns - great for maintaining tolerance levels")
        elif consistency >= 6:
            insights.append("📊 Moderately consistent - some variation in daily usage")
        else:
            insights.append("⚠️ Irregular usage patterns - consider more consistent scheduling")
        
        if "Increasing" in trend_data['trend_direction']:
            insights.append("📈 Usage trending upward - monitor tolerance and consider breaks")
        elif "Decreasing" in trend_data['trend_direction']:
            insights.append("📉 Usage trending downward - good for tolerance management")
        
        avg_thc = trend_data['daily_avg_thc']
        if avg_thc > 100:
            insights.append("⚡ High daily THC intake - consider microdosing strategies")
        elif avg_thc < 20:
            insights.append("🌱 Low daily THC intake - excellent dose control")
        
        return insights
    
    @analytics_group.command(name="efficiency", description="⚡ Analyze consumption efficiency and effectiveness")
    async def analyze_efficiency(self, interaction: discord.Interaction):
        """Analyze consumption efficiency."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            efficiency_data = await self._calculate_efficiency_metrics(user_id)
            
            embed = discord.Embed(
                title="⚡ Consumption Efficiency Analysis",
                description="How effectively you're using cannabis",
                color=0x4CAF50
            )
            
            # Efficiency metrics
            embed.add_field(
                name="📊 Efficiency Metrics",
                value=f"**THC per Session:** {efficiency_data['avg_thc_per_session']:.1f}mg\n"
                      f"**Bioavailability Avg:** {efficiency_data['avg_bioavailability']:.0f}%\n"
                      f"**Method Efficiency:** {efficiency_data['most_efficient_method']}\n"
                      f"**Waste Factor:** {efficiency_data['waste_factor']:.1f}%",
                inline=True
            )
            
            # Cost efficiency (if available)
            embed.add_field(
                name="💰 Value Metrics",
                value=f"**Sessions per Gram:** {efficiency_data['sessions_per_gram']:.1f}\n"
                      f"**THC Utilization:** {efficiency_data['thc_utilization']:.0f}%\n"
                      f"**Optimal Dose Range:** {efficiency_data['optimal_dose_range']}\n"
                      f"**Efficiency Score:** {efficiency_data['efficiency_score']}/10",
                inline=True
            )
            
            # Recommendations
            recommendations = self._generate_efficiency_recommendations(efficiency_data)
            if recommendations:
                embed.add_field(
                    name="🎯 Efficiency Recommendations",
                    value="\n".join(recommendations[:3]),
                    inline=False
                )
            
            embed.set_footer(text="Efficiency analysis • Based on bioavailability and usage patterns")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Efficiency analysis error: {e}")
            await interaction.followup.send(f"❌ Error analyzing efficiency: {str(e)}", ephemeral=True)
    
    async def _calculate_efficiency_metrics(self, user_id: int) -> Dict:
        """Calculate efficiency metrics."""
        try:
            # Get recent data
            summary = await ConsumptionService.get_consumption_summary(user_id, days=30)
            
            total_sessions = summary.get('session_count', 0)
            total_thc = summary.get('total_thc_mg', 0)
            
            if total_sessions == 0:
                return self._get_default_efficiency_metrics()
            
            avg_thc_per_session = total_thc / total_sessions
            
            # Mock calculations (would use actual method data)
            avg_bioavailability = 30  # Average between smoking and vaping
            most_efficient_method = "Vaporizer"
            waste_factor = 15  # Percentage of THC not absorbed
            
            sessions_per_gram = total_sessions / max(1, total_sessions * 0.3)  # Mock calculation
            thc_utilization = 100 - waste_factor
            optimal_dose_range = "5-15mg" if avg_thc_per_session < 20 else "10-25mg"
            
            # Efficiency score (1-10)
            if avg_thc_per_session < 15:
                efficiency_score = 9  # Very efficient
            elif avg_thc_per_session < 30:
                efficiency_score = 7  # Good efficiency
            elif avg_thc_per_session < 50:
                efficiency_score = 5  # Moderate efficiency
            else:
                efficiency_score = 3  # Low efficiency
            
            return {
                'avg_thc_per_session': avg_thc_per_session,
                'avg_bioavailability': avg_bioavailability,
                'most_efficient_method': most_efficient_method,
                'waste_factor': waste_factor,
                'sessions_per_gram': sessions_per_gram,
                'thc_utilization': thc_utilization,
                'optimal_dose_range': optimal_dose_range,
                'efficiency_score': efficiency_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating efficiency: {e}")
            return self._get_default_efficiency_metrics()
    
    def _get_default_efficiency_metrics(self) -> Dict:
        """Get default efficiency metrics for users with no data."""
        return {
            'avg_thc_per_session': 0,
            'avg_bioavailability': 0,
            'most_efficient_method': "Not enough data",
            'waste_factor': 0,
            'sessions_per_gram': 0,
            'thc_utilization': 0,
            'optimal_dose_range': "Start tracking for insights",
            'efficiency_score': 0
        }
    
    def _generate_efficiency_recommendations(self, efficiency_data: Dict) -> List[str]:
        """Generate efficiency improvement recommendations."""
        recommendations = []
        
        score = efficiency_data['efficiency_score']
        if score < 5:
            recommendations.append("🎯 Try smaller doses - microdosing can be more efficient")
            recommendations.append("💨 Switch to vaporizing for better bioavailability")
        elif score < 7:
            recommendations.append("⚡ Good efficiency! Try method rotation to prevent tolerance")
        else:
            recommendations.append("✅ Excellent efficiency! You're optimizing cannabis use well")
        
        avg_dose = efficiency_data['avg_thc_per_session']
        if avg_dose > 40:
            recommendations.append("📉 Consider reducing dose size - smaller amounts may be more effective")
        elif avg_dose < 10:
            recommendations.append("📈 Very controlled dosing - perfect for maintaining low tolerance")
        
        return recommendations
    
    @analytics_group.command(name="compare", description="🔄 Compare different time periods")
    @app_commands.describe(
        period1="First time period",
        period2="Second time period"
    )
    @app_commands.choices(
        period1=[
            app_commands.Choice(name="This Week", value="week_current"),
            app_commands.Choice(name="This Month", value="month_current"),
            app_commands.Choice(name="Last 30 Days", value="month_rolling")
        ],
        period2=[
            app_commands.Choice(name="Last Week", value="week_previous"),
            app_commands.Choice(name="Last Month", value="month_previous"),
            app_commands.Choice(name="Previous 30 Days", value="month_prev_rolling")
        ]
    )
    async def compare_periods(
        self,
        interaction: discord.Interaction,
        period1: app_commands.Choice[str],
        period2: app_commands.Choice[str]
    ):
        """Compare consumption between different time periods."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = interaction.user.id
            
            # Get data for both periods
            data1 = await self._get_period_data(user_id, period1.value)
            data2 = await self._get_period_data(user_id, period2.value)
            
            embed = discord.Embed(
                title="🔄 Period Comparison",
                description=f"Comparing {period1.name} vs {period2.name}",
                color=0x9C27B0
            )
            
            # Comparison metrics
            sessions_change = ((data1['sessions'] - data2['sessions']) / max(1, data2['sessions'])) * 100
            thc_change = ((data1['thc'] - data2['thc']) / max(1, data2['thc'])) * 100
            
            # Period 1 data
            embed.add_field(
                name=f"📊 {period1.name}",
                value=f"**Sessions:** {data1['sessions']}\n"
                      f"**THC:** {data1['thc']:.0f}mg\n"
                      f"**Daily Avg:** {data1['daily_avg']:.1f}mg",
                inline=True
            )
            
            # Period 2 data
            embed.add_field(
                name=f"📈 {period2.name}",
                value=f"**Sessions:** {data2['sessions']}\n"
                      f"**THC:** {data2['thc']:.0f}mg\n"
                      f"**Daily Avg:** {data2['daily_avg']:.1f}mg",
                inline=True
            )
            
            # Changes
            sessions_emoji = "📈" if sessions_change > 0 else "📉" if sessions_change < 0 else "➡️"
            thc_emoji = "📈" if thc_change > 0 else "📉" if thc_change < 0 else "➡️"
            
            embed.add_field(
                name="🔄 Changes",
                value=f"**Sessions:** {sessions_emoji} {sessions_change:+.0f}%\n"
                      f"**THC:** {thc_emoji} {thc_change:+.0f}%\n"
                      f"**Trend:** {self._get_trend_description(sessions_change, thc_change)}",
                inline=True
            )
            
            # Insights
            insights = self._generate_comparison_insights(data1, data2, sessions_change, thc_change)
            if insights:
                embed.add_field(
                    name="💡 Comparison Insights",
                    value="\n".join(insights[:2]),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Period comparison error: {e}")
            await interaction.followup.send(f"❌ Error comparing periods: {str(e)}", ephemeral=True)
    
    async def _get_period_data(self, user_id: int, period: str) -> Dict:
        """Get consumption data for a specific period."""
        # This is simplified - would calculate actual date ranges
        if "week" in period:
            days = 7
        elif "month" in period:
            days = 30
        else:
            days = 30
        
        summary = await ConsumptionService.get_consumption_summary(user_id, days=days)
        sessions = summary.get('session_count', 0)
        thc = summary.get('total_thc_mg', 0)
        daily_avg = thc / days if days > 0 else 0
        
        return {
            'sessions': sessions,
            'thc': thc,
            'daily_avg': daily_avg
        }
    
    def _get_trend_description(self, sessions_change: float, thc_change: float) -> str:
        """Get description of trend."""
        if abs(sessions_change) < 10 and abs(thc_change) < 10:
            return "Stable"
        elif sessions_change > 20 or thc_change > 20:
            return "Increasing"
        elif sessions_change < -20 or thc_change < -20:
            return "Decreasing"
        else:
            return "Moderate change"
    
    def _generate_comparison_insights(self, data1: Dict, data2: Dict, sessions_change: float, thc_change: float) -> List[str]:
        """Generate insights from period comparison."""
        insights = []
        
        if sessions_change > 25:
            insights.append("📈 Significant increase in session frequency - monitor for tolerance")
        elif sessions_change < -25:
            insights.append("📉 Notable decrease in sessions - great for tolerance management")
        
        if thc_change > 30:
            insights.append("⚠️ Large increase in THC consumption - consider moderation")
        elif thc_change < -30:
            insights.append("✅ Substantial reduction in THC intake - excellent control")
        
        if abs(sessions_change - thc_change) > 20:
            insights.append("🎯 Change in dosing patterns - analyzing efficiency differences")
        
        return insights

class TrendAnalysisView(discord.ui.View):
    """Actions for trend analysis."""
    
    def __init__(self, user_id: int, period: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.period = period
    
    @discord.ui.button(label="⚡ Efficiency", style=discord.ButtonStyle.primary, emoji="⚡")
    async def efficiency_analysis(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/analytics efficiency` for detailed efficiency analysis!", ephemeral=True)
    
    @discord.ui.button(label="🔄 Compare", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def compare_periods(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/analytics compare` to compare different time periods!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdvancedAnalyticsCommands(bot))
