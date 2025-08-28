"""Visualization commands for charts and data insights."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime

from bot.services.visualization_service import VisualizationService

class VisualizationCommands(commands.Cog):
    """Commands for data visualization and charts."""
    
    def __init__(self, bot):
        self.bot = bot

    viz_group = app_commands.Group(name="charts", description="Data visualization and charts")

    @viz_group.command(name="consumption", description="View consumption trends chart")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def consumption_chart(self, interaction: discord.Interaction, days: int = 30):
        """Display consumption trends visualization."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get chart data
            chart_data = await VisualizationService.generate_consumption_chart_data(user_id, days)
            
            if chart_data['status'] != 'success':
                embed = discord.Embed(
                    title="📊 Consumption Chart",
                    description=chart_data['message'],
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"📊 Consumption Trends - Last {days} Days",
                color=0x2196F3
            )
            
            # Summary stats
            summary = chart_data['summary']
            embed.add_field(
                name="📈 Overview",
                value=f"**Total Sessions:** {summary['total_sessions']}\n"
                      f"**Total THC:** {summary['total_thc_mg']:.1f}mg\n"
                      f"**Daily Average:** {summary['avg_daily_thc']:.1f}mg\n"
                      f"**Active Days:** {summary['active_days']}/{days}\n"
                      f"**Unique Strains:** {summary['unique_strains']}",
                inline=False
            )
            
            # Method breakdown chart
            method_data = chart_data['method_breakdown']
            if method_data:
                method_counts = {method: data['count'] for method, data in method_data.items()}
                method_chart = VisualizationService.create_ascii_bar_chart(
                    method_counts, "Sessions by Method"
                )
                embed.add_field(
                    name="🔥 Method Distribution",
                    value=method_chart,
                    inline=False
                )
            
            # Daily trend (last 7 days)
            daily_data = chart_data['daily_consumption']
            if daily_data:
                recent_days = dict(list(daily_data.items())[-7:])  # Last 7 days
                daily_thc = {date.split('-')[2]: data['thc_mg'] for date, data in recent_days.items()}
                
                if daily_thc:
                    daily_chart = VisualizationService.create_ascii_bar_chart(
                        daily_thc, "Daily THC (Last 7 Days)"
                    )
                    embed.add_field(
                        name="📅 Recent Daily Trends",
                        value=daily_chart,
                        inline=False
                    )
            
            # Top strains
            strain_data = chart_data['strain_breakdown']
            if strain_data:
                # Sort by usage count and take top 5
                top_strains = dict(sorted(strain_data.items(), 
                                        key=lambda x: x[1]['count'], 
                                        reverse=True)[:5])
                
                strain_text = ""
                for strain, data in top_strains.items():
                    avg_rating = sum(data['ratings']) / len(data['ratings']) if data['ratings'] else 0
                    stars = "⭐" * round(avg_rating) if avg_rating > 0 else "No ratings"
                    strain_text += f"**{strain}:** {data['count']} sessions, {data['thc_mg']:.0f}mg THC {stars}\n"
                
                embed.add_field(
                    name="🌿 Top Strains",
                    value=strain_text or "No strain data available",
                    inline=False
                )
            
            embed.set_footer(text=f"📊 Analysis based on {summary['total_sessions']} sessions")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating chart: {str(e)}",
                ephemeral=True
            )

    @viz_group.command(name="tolerance", description="View tolerance heatmap")
    async def tolerance_heatmap(self, interaction: discord.Interaction):
        """Display tolerance trends heatmap."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get heatmap data
            heatmap_data = await VisualizationService.generate_tolerance_heatmap_data(user_id)
            
            if heatmap_data['status'] != 'success':
                embed = discord.Embed(
                    title="🔥 Tolerance Heatmap",
                    description=heatmap_data['message'],
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🔥 Tolerance & Effectiveness Heatmap",
                description=heatmap_data['analysis_period'],
                color=0xFF9800
            )
            
            # Weekly breakdown
            weekly_data = heatmap_data['heatmap_data']
            heatmap_text = ""
            
            for week, data in list(weekly_data.items())[-8:]:  # Last 8 weeks
                week_date = datetime.strptime(week, '%Y-%m-%d').strftime('%m/%d')
                heatmap_text += f"**{week_date}** {data['trend_indicator']} "
                heatmap_text += f"Rating: {data['avg_rating']}/5, "
                heatmap_text += f"Dosage: {data['avg_dosage']}mg, "
                heatmap_text += f"Sessions: {data['sessions']}\n"
            
            embed.add_field(
                name="📅 Weekly Effectiveness Trends",
                value=heatmap_text or "No data available",
                inline=False
            )
            
            # Efficiency trends
            if len(weekly_data) >= 4:
                recent_weeks = list(weekly_data.items())[-4:]
                efficiency_data = {week.split('-')[1] + '/' + week.split('-')[2]: data['efficiency'] 
                                 for week, data in recent_weeks}
                
                efficiency_chart = VisualizationService.create_ascii_bar_chart(
                    efficiency_data, "Efficiency Trend (Rating/mg)"
                )
                embed.add_field(
                    name="⚡ Efficiency Analysis",
                    value=efficiency_chart,
                    inline=False
                )
            
            # Legend
            embed.add_field(
                name="🔍 Legend",
                value="🟢 Excellent week (4+ rating)\n"
                      "🟡 Good week (3-4 rating)\n"
                      "🔴 Challenging week (<3 rating)\n"
                      "**Efficiency:** Effect rating per mg THC",
                inline=False
            )
            
            embed.set_footer(text="💡 Lower efficiency may indicate tolerance buildup")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating heatmap: {str(e)}",
                ephemeral=True
            )

    @viz_group.command(name="efficiency", description="Compare method efficiency")
    @app_commands.describe(days="Number of days to analyze (default: 60)")
    async def efficiency_chart(self, interaction: discord.Interaction, days: int = 60):
        """Display method efficiency comparison chart."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get efficiency data
            efficiency_data = await VisualizationService.generate_method_efficiency_chart(user_id, days)
            
            if efficiency_data['status'] != 'success':
                embed = discord.Embed(
                    title="⚡ Method Efficiency",
                    description=efficiency_data['message'],
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"⚡ Method Efficiency Analysis - Last {days} Days",
                description=f"Based on {efficiency_data['total_sessions']} sessions",
                color=0xFF5722
            )
            
            # Efficiency ranking
            method_data = efficiency_data['efficiency_data']
            ranking_text = ""
            
            for i, (method, data) in enumerate(method_data.items(), 1):
                ranking_text += f"**{i}. {method.title()}**\n"
                ranking_text += f"   Efficiency: {data['efficiency_score']}/100\n"
                ranking_text += f"   Avg Rating: {data['avg_rating']}/5 ⭐\n"
                ranking_text += f"   Sessions: {data['sessions']}\n"
                ranking_text += f"   💡 {data['recommendation']}\n\n"
            
            embed.add_field(
                name="🏆 Efficiency Rankings",
                value=ranking_text or "No data available",
                inline=False
            )
            
            # Bioavailability comparison
            bioavail_data = {method: data['avg_bioavailability'] 
                           for method, data in method_data.items() 
                           if data['avg_bioavailability'] > 0}
            
            if bioavail_data:
                bioavail_chart = VisualizationService.create_ascii_bar_chart(
                    bioavail_data, "Average Bioavailability %"
                )
                embed.add_field(
                    name="🧪 Bioavailability Comparison",
                    value=bioavail_chart,
                    inline=False
                )
            
            # THC per session comparison
            thc_data = {method: data['avg_thc_per_session'] for method, data in method_data.items()}
            thc_chart = VisualizationService.create_ascii_bar_chart(
                thc_data, "Avg THC per Session (mg)"
            )
            embed.add_field(
                name="📊 THC Consumption by Method",
                value=thc_chart,
                inline=False
            )
            
            embed.set_footer(text="⚡ Efficiency = Effect Rating ÷ THC Consumed")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating efficiency chart: {str(e)}",
                ephemeral=True
            )

    @viz_group.command(name="strains", description="View strain effectiveness radar")
    async def strain_radar(self, interaction: discord.Interaction):
        """Display strain effectiveness radar chart."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get radar data
            radar_data = await VisualizationService.generate_strain_effectiveness_radar(user_id)
            
            if radar_data['status'] != 'success':
                embed = discord.Embed(
                    title="🎯 Strain Effectiveness Radar",
                    description=radar_data['message'],
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🎯 Strain Effectiveness Analysis",
                description=f"Analyzed {radar_data['qualified_strains']} strains with 3+ sessions",
                color=0x4CAF50
            )
            
            # Top performing strains
            strain_data = radar_data['radar_data']
            top_strains = dict(list(strain_data.items())[:5])  # Top 5
            
            for strain, metrics in top_strains.items():
                strain_text = f"**Overall Score:** {metrics['overall_score']}/5 ⭐\n"
                strain_text += f"**Effectiveness:** {metrics['effectiveness']}/5\n"
                strain_text += f"**Consistency:** {metrics['consistency']}/5\n"
                strain_text += f"**Efficiency:** {metrics['efficiency']}/5\n"
                strain_text += f"**Versatility:** {metrics['versatility']}/5\n"
                strain_text += f"**Frequency:** {metrics['frequency']}/5\n"
                strain_text += f"Sessions: {metrics['sessions']} | Avg Dose: {metrics['avg_dosage']}mg"
                
                embed.add_field(
                    name=f"🌿 {strain}",
                    value=strain_text,
                    inline=True
                )
            
            # Metrics explanation
            explanation = radar_data['metrics_explanation']
            explain_text = "\n".join([f"**{metric.title()}:** {desc}" 
                                    for metric, desc in explanation.items()])
            
            embed.add_field(
                name="📚 Metrics Guide",
                value=explain_text,
                inline=False
            )
            
            # Overall scores chart
            if len(strain_data) > 1:
                score_data = {strain[:10]: data['overall_score'] 
                            for strain, data in list(strain_data.items())[:6]}
                score_chart = VisualizationService.create_ascii_bar_chart(
                    score_data, "Overall Scores"
                )
                embed.add_field(
                    name="🏆 Score Comparison",
                    value=score_chart,
                    inline=False
                )
            
            embed.set_footer(text="🎯 Higher scores indicate better overall performance")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating radar chart: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(VisualizationCommands(bot))
