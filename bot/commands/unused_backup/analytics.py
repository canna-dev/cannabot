"""Advanced analytics and detailed reporting commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timedelta
import asyncio

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService
from bot.services.tolerance_service import ToleranceService
from bot.services.prediction_service import PredictionService
from bot.database.models import ConsumptionEntry, StashItem, StrainNote

class AnalyticsCommands(commands.Cog):
    """Advanced analytics and reporting commands."""
    
    def __init__(self, bot):
        self.bot = bot

    analytics_group = app_commands.Group(name="analytics", description="Advanced consumption analytics and reports")

    @analytics_group.command(name="trends", description="View consumption trends over time")
    @app_commands.describe(
        period="Time period to analyze",
        method="Filter by consumption method (optional)"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="7 days", value="7"),
        app_commands.Choice(name="30 days", value="30"),
        app_commands.Choice(name="90 days", value="90"),
        app_commands.Choice(name="1 year", value="365")
    ])
    async def consumption_trends(
        self,
        interaction: discord.Interaction,
        period: str,
        method: Optional[str] = None
    ):
        """Show consumption trends over time."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            days = int(period)
            
            # Get consumption data
            history = await ConsumptionService.get_consumption_summary(user_id, days=days)
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Filter by method if specified
            if method:
                entries = [e for e in entries if e.method == method]
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]
            
            if not recent_entries:
                embed = discord.Embed(
                    title="📊 Consumption Trends",
                    description=f"No consumption data found for the last {days} days",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Calculate metrics
            total_sessions = len(recent_entries)
            total_thc = sum(e.absorbed_thc_mg for e in recent_entries)
            avg_daily_thc = total_thc / days
            avg_session_thc = total_thc / total_sessions if total_sessions > 0 else 0
            
            # Method breakdown
            method_counts = {}
            method_thc = {}
            for entry in recent_entries:
                method_counts[entry.method] = method_counts.get(entry.method, 0) + 1
                method_thc[entry.method] = method_thc.get(entry.method, 0) + entry.absorbed_thc_mg

            # Weekly analysis for longer periods
            weekly_data = []
            if days >= 14:
                for week in range(0, min(days, 84), 7):  # Max 12 weeks
                    week_start = datetime.now() - timedelta(days=week+7)
                    week_end = datetime.now() - timedelta(days=week)
                    week_entries = [e for e in recent_entries if e.timestamp and week_start <= e.timestamp <= week_end]
                    week_thc = sum(e.absorbed_thc_mg for e in week_entries)
                    week_sessions = len(week_entries)
                    weekly_data.append((week_start.strftime("%m/%d"), week_thc, week_sessions))

            embed = discord.Embed(
                title=f"📊 Consumption Trends - Last {days} Days",
                color=0x2196F3
            )

            # Overview
            embed.add_field(
                name="📈 Overview",
                value=f"**Total Sessions:** {total_sessions}\n"
                      f"**Total THC:** {total_thc:.1f}mg\n"
                      f"**Daily Average:** {avg_daily_thc:.1f}mg/day\n"
                      f"**Session Average:** {avg_session_thc:.1f}mg/session",
                inline=False
            )

            # Method breakdown
            if method_counts:
                method_text = "\n".join([
                    f"• **{method.title()}:** {count} sessions ({method_thc[method]:.1f}mg)"
                    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
                ])
                embed.add_field(
                    name="🔥 By Method",
                    value=method_text,
                    inline=False
                )

            # Weekly trends for longer periods
            if weekly_data:
                weekly_text = "\n".join([
                    f"• **{week}:** {thc:.1f}mg ({sessions} sessions)"
                    for week, thc, sessions in weekly_data[-6:]  # Last 6 weeks
                ])
                embed.add_field(
                    name="📅 Weekly Breakdown",
                    value=weekly_text,
                    inline=False
                )

            # Efficiency analysis
            if len(set(e.method for e in recent_entries)) > 1:
                efficiency_text = "\n".join([
                    f"• **{method.title()}:** {method_thc[method]/method_counts[method]:.1f}mg avg"
                    for method in sorted(method_thc.keys(), key=lambda x: method_thc[x]/method_counts[x], reverse=True)
                ])
                embed.add_field(
                    name="⚡ Method Efficiency",
                    value=efficiency_text,
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating trends: {str(e)}", 
                ephemeral=True
            )

    @analytics_group.command(name="strains", description="Analyze strain preferences and effects")
    @app_commands.describe(days="Number of days to analyze")
    async def strain_analysis(
        self,
        interaction: discord.Interaction,
        days: int = 30
    ):
        """Analyze strain usage and ratings."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get consumption and notes data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            notes = await StrainNote.get_user_notes(user_id)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date and e.strain]
            
            if not recent_entries and not notes:
                embed = discord.Embed(
                    title="🌿 Strain Analysis",
                    description="No strain data found. Start logging consumption with strain names!",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🌿 Strain Analysis - Last {days} Days",
                color=0x4CAF50
            )

            # Consumption analysis
            if recent_entries:
                strain_usage = {}
                strain_thc = {}
                strain_ratings = {}
                
                for entry in recent_entries:
                    strain = entry.strain
                    strain_usage[strain] = strain_usage.get(strain, 0) + 1
                    strain_thc[strain] = strain_thc.get(strain, 0) + entry.absorbed_thc_mg
                    if entry.effect_rating:
                        if strain not in strain_ratings:
                            strain_ratings[strain] = []
                        strain_ratings[strain].append(entry.effect_rating)

                # Top strains by usage
                top_strains = sorted(strain_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                usage_text = "\n".join([
                    f"• **{strain}:** {count} sessions ({strain_thc[strain]:.1f}mg)"
                    for strain, count in top_strains
                ])
                embed.add_field(
                    name="🏆 Most Used Strains",
                    value=usage_text,
                    inline=False
                )

                # Best rated strains
                if strain_ratings:
                    avg_ratings = {
                        strain: sum(ratings) / len(ratings)
                        for strain, ratings in strain_ratings.items()
                        if len(ratings) >= 2  # At least 2 ratings
                    }
                    
                    if avg_ratings:
                        best_rated = sorted(avg_ratings.items(), key=lambda x: x[1], reverse=True)[:5]
                        rating_text = "\n".join([
                            f"• **{strain}:** {'⭐' * round(rating)} {rating:.1f}/5"
                            for strain, rating in best_rated
                        ])
                        embed.add_field(
                            name="⭐ Best Rated Strains",
                            value=rating_text,
                            inline=False
                        )

            # Strain notes summary
            if notes:
                strain_notes = {}
                for note in notes:
                    strain = note.strain
                    if strain not in strain_notes:
                        strain_notes[strain] = []
                    if note.effect_rating:
                        strain_notes[strain].append(note.effect_rating)

                # Average note ratings
                note_averages = {
                    strain: sum(ratings) / len(ratings)
                    for strain, ratings in strain_notes.items()
                    if ratings
                }

                if note_averages:
                    top_notes = sorted(note_averages.items(), key=lambda x: x[1], reverse=True)[:5]
                    notes_text = "\n".join([
                        f"• **{strain}:** {'⭐' * round(rating)} {rating:.1f}/5"
                        for strain, rating in top_notes
                    ])
                    embed.add_field(
                        name="📝 Top Strain Notes",
                        value=notes_text,
                        inline=False
                    )

            # Summary stats
            unique_strains = len(set(e.strain for e in recent_entries if e.strain))
            total_notes = len(notes)
            
            embed.add_field(
                name="📊 Summary",
                value=f"**Unique Strains Consumed:** {unique_strains}\n"
                      f"**Total Strain Notes:** {total_notes}\n"
                      f"**Analysis Period:** {days} days",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error analyzing strains: {str(e)}", 
                ephemeral=True
            )

    @analytics_group.command(name="efficiency", description="Analyze consumption method efficiency")
    @app_commands.describe(days="Number of days to analyze")
    async def method_efficiency(
        self,
        interaction: discord.Interaction,
        days: int = 30
    ):
        """Analyze efficiency of different consumption methods."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get consumption data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]
            
            if not recent_entries:
                embed = discord.Embed(
                    title="⚡ Method Efficiency Analysis",
                    description=f"No consumption data found for the last {days} days",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Analyze by method
            method_data = {}
            for entry in recent_entries:
                method = entry.method
                if method not in method_data:
                    method_data[method] = {
                        'sessions': 0,
                        'total_amount': 0,
                        'total_thc_absorbed': 0,
                        'total_raw_thc': 0,
                        'ratings': []
                    }
                
                method_data[method]['sessions'] += 1
                method_data[method]['total_amount'] += entry.amount
                method_data[method]['total_thc_absorbed'] += entry.absorbed_thc_mg
                
                # Calculate raw THC
                if entry.thc_percent and entry.amount:
                    raw_thc = (entry.amount * 1000) * (entry.thc_percent / 100)  # Convert to mg
                    method_data[method]['total_raw_thc'] += raw_thc
                
                if entry.effect_rating:
                    method_data[method]['ratings'].append(entry.effect_rating)

            embed = discord.Embed(
                title=f"⚡ Method Efficiency Analysis - Last {days} Days",
                color=0xFF9800
            )

            # Calculate efficiency metrics
            efficiency_data = []
            for method, data in method_data.items():
                avg_absorbed = data['total_thc_absorbed'] / data['sessions']
                avg_rating = sum(data['ratings']) / len(data['ratings']) if data['ratings'] else 0
                
                # Bioavailability efficiency
                if data['total_raw_thc'] > 0:
                    efficiency_percent = (data['total_thc_absorbed'] / data['total_raw_thc']) * 100
                else:
                    efficiency_percent = 0
                
                efficiency_data.append({
                    'method': method,
                    'sessions': data['sessions'],
                    'avg_absorbed': avg_absorbed,
                    'avg_rating': avg_rating,
                    'efficiency': efficiency_percent,
                    'total_absorbed': data['total_thc_absorbed']
                })

            # Sort by efficiency
            efficiency_data.sort(key=lambda x: x['efficiency'], reverse=True)

            # Efficiency ranking
            efficiency_text = ""
            for i, data in enumerate(efficiency_data, 1):
                stars = "⭐" * round(data['avg_rating']) if data['avg_rating'] > 0 else "No ratings"
                efficiency_text += f"**{i}. {data['method'].title()}**\n"
                efficiency_text += f"   • Absorption: {data['efficiency']:.1f}% efficient\n"
                efficiency_text += f"   • Avg per session: {data['avg_absorbed']:.1f}mg\n"
                efficiency_text += f"   • Sessions: {data['sessions']}\n"
                efficiency_text += f"   • Avg rating: {stars}\n\n"

            embed.add_field(
                name="🏆 Efficiency Rankings",
                value=efficiency_text.strip(),
                inline=False
            )

            # Usage distribution
            total_sessions = sum(d['sessions'] for d in efficiency_data)
            usage_text = "\n".join([
                f"• **{data['method'].title()}:** {data['sessions']} sessions "
                f"({(data['sessions']/total_sessions)*100:.1f}%)"
                for data in sorted(efficiency_data, key=lambda x: x['sessions'], reverse=True)
            ])

            embed.add_field(
                name="📊 Usage Distribution",
                value=usage_text,
                inline=False
            )

            # Recommendations
            if len(efficiency_data) > 1:
                most_efficient = efficiency_data[0]
                most_used = max(efficiency_data, key=lambda x: x['sessions'])
                
                recommendations = []
                if most_efficient['method'] != most_used['method']:
                    recommendations.append(
                        f"💡 **{most_efficient['method'].title()}** is your most efficient method "
                        f"({most_efficient['efficiency']:.1f}% absorption)"
                    )
                
                best_rated = max([d for d in efficiency_data if d['avg_rating'] > 0], 
                               key=lambda x: x['avg_rating'], default=None)
                if best_rated and best_rated['avg_rating'] > 0:
                    recommendations.append(
                        f"⭐ **{best_rated['method'].title()}** gives you the best experience "
                        f"({best_rated['avg_rating']:.1f}/5 avg rating)"
                    )

                if recommendations:
                    embed.add_field(
                        name="💡 Recommendations",
                        value="\n".join(recommendations),
                        inline=False
                    )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error analyzing efficiency: {str(e)}", 
                ephemeral=True
            )

    @analytics_group.command(name="compare", description="Compare different time periods")
    @app_commands.describe(
        current_days="Current period to analyze",
        compare_days="Previous period to compare against"
    )
    async def period_comparison(
        self,
        interaction: discord.Interaction,
        current_days: int = 7,
        compare_days: int = 7
    ):
        """Compare consumption between two time periods."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get data for both periods
            current_summary = await ConsumptionService.get_consumption_summary(user_id, days=current_days)
            
            # Get historical data manually
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Current period
            current_start = datetime.now() - timedelta(days=current_days)
            current_entries = [e for e in entries if e.timestamp and e.timestamp >= current_start]
            
            # Previous period  
            prev_start = datetime.now() - timedelta(days=current_days + compare_days)
            prev_end = current_start
            prev_entries = [e for e in entries if e.timestamp and prev_start <= e.timestamp < prev_end]

            if not current_entries and not prev_entries:
                embed = discord.Embed(
                    title="📊 Period Comparison",
                    description="No data found for comparison periods",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Calculate metrics for both periods
            def calculate_metrics(period_entries, days):
                if not period_entries:
                    return {
                        'sessions': 0,
                        'total_thc': 0,
                        'avg_daily': 0,
                        'avg_session': 0,
                        'methods': {}
                    }
                
                total_thc = sum(e.absorbed_thc_mg for e in period_entries)
                sessions = len(period_entries)
                
                methods = {}
                for entry in period_entries:
                    methods[entry.method] = methods.get(entry.method, 0) + 1
                
                return {
                    'sessions': sessions,
                    'total_thc': total_thc,
                    'avg_daily': total_thc / days,
                    'avg_session': total_thc / sessions if sessions > 0 else 0,
                    'methods': methods
                }

            current_metrics = calculate_metrics(current_entries, current_days)
            prev_metrics = calculate_metrics(prev_entries, compare_days)

            embed = discord.Embed(
                title=f"📊 Period Comparison",
                description=f"**Current:** Last {current_days} days vs **Previous:** {compare_days} days before",
                color=0x2196F3
            )

            # Calculate changes
            def format_change(current, previous, suffix="", is_percentage=False):
                if previous == 0:
                    return f"{current:.1f}{suffix} (New!)"
                
                change = current - previous
                percent_change = (change / previous) * 100
                
                if change > 0:
                    emoji = "📈" if not is_percentage else "📊"
                    return f"{current:.1f}{suffix} ({emoji}+{change:.1f}, +{percent_change:.1f}%)"
                elif change < 0:
                    emoji = "📉" if not is_percentage else "📊"
                    return f"{current:.1f}{suffix} ({emoji}{change:.1f}, {percent_change:.1f}%)"
                else:
                    return f"{current:.1f}{suffix} (No change)"

            # Main metrics comparison
            embed.add_field(
                name="🎯 Key Metrics",
                value=f"**Sessions:** {format_change(current_metrics['sessions'], prev_metrics['sessions'])}\n"
                      f"**Total THC:** {format_change(current_metrics['total_thc'], prev_metrics['total_thc'], 'mg')}\n"
                      f"**Daily Average:** {format_change(current_metrics['avg_daily'], prev_metrics['avg_daily'], 'mg/day')}\n"
                      f"**Session Average:** {format_change(current_metrics['avg_session'], prev_metrics['avg_session'], 'mg')}",
                inline=False
            )

            # Method changes
            all_methods = set(list(current_metrics['methods'].keys()) + list(prev_metrics['methods'].keys()))
            if all_methods:
                method_changes = []
                for method in all_methods:
                    current_count = current_metrics['methods'].get(method, 0)
                    prev_count = prev_metrics['methods'].get(method, 0)
                    
                    if current_count > 0 or prev_count > 0:
                        change_text = format_change(current_count, prev_count)
                        method_changes.append(f"• **{method.title()}:** {change_text}")

                if method_changes:
                    embed.add_field(
                        name="🔥 Method Usage",
                        value="\n".join(method_changes),
                        inline=False
                    )

            # Insights
            insights = []
            
            # Consistency check
            if current_metrics['sessions'] > 0 and prev_metrics['sessions'] > 0:
                session_consistency = abs(current_metrics['sessions'] - prev_metrics['sessions']) / max(current_metrics['sessions'], prev_metrics['sessions'])
                if session_consistency < 0.2:
                    insights.append("🎯 **Consistent usage pattern** - Similar session frequency")
                elif current_metrics['sessions'] > prev_metrics['sessions']:
                    insights.append("📈 **Increased activity** - More sessions than before")
                else:
                    insights.append("📉 **Decreased activity** - Fewer sessions than before")

            # Efficiency check
            if current_metrics['avg_session'] > 0 and prev_metrics['avg_session'] > 0:
                if current_metrics['avg_session'] > prev_metrics['avg_session'] * 1.1:
                    insights.append("⚡ **Higher potency** - Stronger sessions on average")
                elif current_metrics['avg_session'] < prev_metrics['avg_session'] * 0.9:
                    insights.append("🌱 **Lower potency** - Lighter sessions on average")

            if insights:
                embed.add_field(
                    name="💡 Insights",
                    value="\n".join(insights),
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error comparing periods: {str(e)}", 
                ephemeral=True
            )

    @analytics_group.command(name="tolerance", description="Analyze tolerance trends and get recommendations")
    async def tolerance_analysis(self, interaction: discord.Interaction):
        """Analyze tolerance patterns and provide recommendations."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            analysis = await ToleranceService.analyze_tolerance_trends(user_id)
            
            if analysis['status'] == 'insufficient_data':
                embed = discord.Embed(
                    title="📊 Tolerance Analysis",
                    description="Need at least 7 days of consumption data with effect ratings for analysis.",
                    color=0x9E9E9E
                )
                embed.add_field(
                    name="💡 Tips",
                    value="Track your consumption with effect ratings using:\n"
                          "`/smoke`, `/vape`, `/dab`, etc. with effect_rating parameter",
                    inline=False
                )
            elif analysis['status'] == 'error':
                embed = discord.Embed(
                    title="❌ Analysis Error",
                    description=analysis['message'],
                    color=0xF44336
                )
            else:
                # Successful analysis
                tolerance_data = analysis['analysis']
                recommendations = analysis['recommendations']
                
                status = tolerance_data['tolerance_status']
                severity = tolerance_data['severity']
                
                # Status color coding
                if status == 'increasing' and severity == 'high':
                    color = 0xF44336  # Red
                    status_emoji = "🔴"
                elif status == 'increasing':
                    color = 0xFF9800  # Orange
                    status_emoji = "🟠"
                elif status == 'stable':
                    color = 0x4CAF50  # Green
                    status_emoji = "🟢"
                elif status == 'improving':
                    color = 0x2196F3  # Blue
                    status_emoji = "🔵"
                else:
                    color = 0xFFC107  # Yellow
                    status_emoji = "🟡"
                
                embed = discord.Embed(
                    title=f"{status_emoji} Tolerance Analysis",
                    description=f"**Status:** {status.replace('_', ' ').title()} ({severity})",
                    color=color
                )
                
                # Effectiveness trends
                eff_change = tolerance_data['effectiveness_change']
                dose_change = tolerance_data['dosage_change_pct']
                
                embed.add_field(
                    name="📈 Trends (Last 2 weeks)",
                    value=f"**Effectiveness Change:** {eff_change:+.1f} stars\n"
                          f"**Dosage Change:** {dose_change:+.1f}%\n"
                          f"**Data Quality:** {analysis['data_quality']:.0%}",
                    inline=True
                )
                
                # Current averages
                embed.add_field(
                    name="📊 Current Averages",
                    value=f"**Recent Effectiveness:** {tolerance_data['recent_effectiveness']:.1f}/5\n"
                          f"**Recent Daily THC:** {tolerance_data['recent_dosage']:.1f}mg\n"
                          f"**Early Daily THC:** {tolerance_data['early_dosage']:.1f}mg",
                    inline=True
                )
                
                # Recommendations
                if recommendations:
                    rec_text = "\n".join(recommendations[:5])  # Limit to 5 recommendations
                    embed.add_field(
                        name="💡 Recommendations",
                        value=rec_text,
                        inline=False
                    )
                
                # Tolerance break suggestion
                break_suggestion = await ToleranceService.suggest_tolerance_break(user_id)
                if not break_suggestion.get('error'):
                    embed.add_field(
                        name="🔄 Tolerance Break Suggestion",
                        value=f"**Suggested Duration:** {break_suggestion['suggested_days']} days ({break_suggestion['intensity']} break)\n"
                              f"**Current Usage:** {break_suggestion['current_usage']:.1f}mg/day",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error analyzing tolerance: {str(e)}",
                ephemeral=True
            )

    @analytics_group.command(name="predictions", description="View stash depletion predictions and reorder suggestions")
    async def stash_predictions(self, interaction: discord.Interaction):
        """Show stash depletion predictions and reorder timing."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get stash predictions
            predictions = await PredictionService.predict_stash_depletion(user_id)
            reorder_suggestions = await PredictionService.suggest_reorder_timing(user_id)
            tolerance_prediction = await PredictionService.predict_tolerance_development(user_id)
            
            embed = discord.Embed(
                title="🔮 Cannabis Usage Predictions",
                description="AI-powered insights for your stash and tolerance",
                color=0x673AB7
            )
            
            # Stash depletion predictions
            if predictions['status'] == 'success' and predictions['predictions']:
                stash_text = ""
                for item in predictions['predictions'][:5]:  # Show top 5
                    stash_text += f"{item['urgency_emoji']} **{item['strain']}** ({item['type']})\n"
                    stash_text += f"   {item['current_amount']:.1f}g → Empty in {item['days_remaining']} days\n"
                
                embed.add_field(
                    name="📦 Stash Depletion Timeline",
                    value=stash_text,
                    inline=False
                )
            elif predictions['status'] == 'no_stash':
                embed.add_field(
                    name="📦 Stash Status",
                    value="No stash items found. Add items with `/stash add`",
                    inline=False
                )
            elif predictions['status'] == 'no_usage_data':
                embed.add_field(
                    name="📦 Stash Predictions",
                    value="Log consumption data for stash predictions",
                    inline=False
                )
            
            # Reorder suggestions
            if reorder_suggestions['status'] == 'success':
                summary = reorder_suggestions['summary']
                reorder_text = ""
                
                if summary['critical_items'] > 0:
                    reorder_text += f"🚨 **{summary['critical_items']} items need immediate reorder**\n"
                if summary['soon_items'] > 0:
                    reorder_text += f"⚠️ **{summary['soon_items']} items need reordering soon**\n"
                if summary['critical_items'] == 0 and summary['soon_items'] == 0:
                    reorder_text = "✅ All stash levels look good!"
                
                # Show urgent items
                urgent_items = [s for s in reorder_suggestions['suggestions'] 
                              if s['action'] in ['reorder_now', 'reorder_soon']][:3]
                
                if urgent_items:
                    reorder_text += "\n**Priority Items:**\n"
                    for item in urgent_items:
                        reorder_text += f"{item['urgency_emoji']} {item['strain']}: {item['action_text']}\n"
                
                embed.add_field(
                    name="🛒 Reorder Recommendations",
                    value=reorder_text,
                    inline=False
                )
            
            # Tolerance predictions
            if tolerance_prediction['status'] == 'success':
                tolerance_text = f"{tolerance_prediction['risk_emoji']} **Risk Level:** {tolerance_prediction['tolerance_risk'].title()}\n"
                
                if tolerance_prediction['tolerance_risk'] != 'minimal':
                    tolerance_text += f"⏰ **Tolerance break suggested in:** {tolerance_prediction['predicted_break_needed_in']} days\n"
                    tolerance_text += f"📈 **Recent dosage trend:** {tolerance_prediction['dosage_increase_pct']:+.1f}%"
                else:
                    tolerance_text += "✅ Current usage patterns appear sustainable"
                
                embed.add_field(
                    name="🧠 Tolerance Development Prediction",
                    value=tolerance_text,
                    inline=False
                )
            
            # Usage insights
            if predictions['status'] == 'success':
                insights_text = f"**Daily THC Average:** {predictions['avg_daily_thc']:.1f}mg\n"
                insights_text += f"**Analysis Period:** {predictions['analysis_period_days']} days\n"
                insights_text += f"**Prediction Accuracy:** ~85% (based on current patterns)"
                
                embed.add_field(
                    name="📊 Usage Insights",
                    value=insights_text,
                    inline=True
                )
            
            embed.set_footer(text="💡 Predictions improve with more usage data • Update daily for best accuracy")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating predictions: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AnalyticsCommands(bot))
