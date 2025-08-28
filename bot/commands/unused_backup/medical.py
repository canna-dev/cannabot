"""Medical symptom tracking and correlation analysis."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime, timedelta

from bot.database.models import ConsumptionEntry, User
from bot.services.consumption_service import ConsumptionService

# Common medical symptoms that cannabis users track
MEDICAL_SYMPTOMS = [
    "anxiety", "depression", "insomnia", "pain", "nausea", "appetite_loss",
    "migraines", "muscle_spasms", "inflammation", "ptsd", "seizures", "glaucoma",
    "arthritis", "fibromyalgia", "crohns", "epilepsy", "cancer_pain", "stress"
]

class MedicalCommands(commands.Cog):
    """Medical symptom tracking and analysis commands."""
    
    def __init__(self, bot):
        self.bot = bot

    medical_group = app_commands.Group(name="medical", description="Track symptoms and medical cannabis effectiveness")

    @medical_group.command(name="log", description="Log consumption for a specific medical symptom")
    @app_commands.describe(
        symptom="Medical symptom you're treating",
        product_type="Type of cannabis product",
        amount="Amount consumed",
        method="Consumption method",
        strain="Strain name (optional)",
        thc_percent="THC percentage (optional)",
        effect_rating="Effectiveness rating 1-5 stars",
        notes="Additional notes"
    )
    @app_commands.choices(product_type=[
        app_commands.Choice(name="Flower", value="flower"),
        app_commands.Choice(name="Concentrate", value="concentrate"),
        app_commands.Choice(name="Edible", value="edible"),
        app_commands.Choice(name="Tincture", value="tincture"),
        app_commands.Choice(name="Topical", value="topical"),
        app_commands.Choice(name="Capsule", value="capsule")
    ])
    @app_commands.choices(method=[
        app_commands.Choice(name="Smoke", value="smoke"),
        app_commands.Choice(name="Vaporizer", value="vaporizer"), 
        app_commands.Choice(name="Dab", value="dab"),
        app_commands.Choice(name="Edible", value="edible"),
        app_commands.Choice(name="Tincture", value="tincture"),
        app_commands.Choice(name="Topical", value="topical"),
        app_commands.Choice(name="Capsule", value="capsule")
    ])
    async def log_medical(
        self,
        interaction: discord.Interaction,
        symptom: str,
        product_type: str,
        amount: float,
        method: str,
        effect_rating: int,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None
    ):
        """Log medical cannabis consumption."""
        try:
            if effect_rating < 1 or effect_rating > 5:
                await interaction.response.send_message(
                    "❌ Effect rating must be between 1 and 5",
                    ephemeral=True
                )
                return

            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be positive",
                    ephemeral=True
                )
                return

            user_id = interaction.user.id
            
            # Log the consumption with symptom
            entry, warnings = await ConsumptionService.log_consumption(
                user_id=user_id,
                product_type=product_type,
                amount=amount,
                method=method,
                strain=strain,
                thc_percent=thc_percent,
                effect_rating=effect_rating,
                notes=notes,
                symptom=symptom.lower()
            )

            embed = discord.Embed(
                title="🏥 Medical Consumption Logged",
                color=0x4CAF50
            )

            embed.add_field(
                name="🎯 Symptom",
                value=symptom.replace("_", " ").title(),
                inline=True
            )

            embed.add_field(
                name="🌿 Treatment", 
                value=f"{amount}g {product_type}" + (f" ({strain})" if strain else ""),
                inline=True
            )

            embed.add_field(
                name="🔥 Method",
                value=method.title(),
                inline=True
            )

            stars = "⭐" * effect_rating
            embed.add_field(
                name="⭐ Effectiveness",
                value=f"{stars} {effect_rating}/5",
                inline=True
            )

            embed.add_field(
                name="💊 Absorbed THC",
                value=f"{entry.absorbed_thc_mg:.1f}mg",
                inline=True
            )

            if notes:
                embed.add_field(
                    name="📝 Notes",
                    value=notes,
                    inline=False
                )

            if warnings:
                embed.add_field(
                    name="⚠️ Warnings",
                    value="\n".join(warnings),
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error logging medical consumption: {str(e)}", 
                ephemeral=True
            )

    @medical_group.command(name="symptoms", description="View your tracked symptoms and their treatments")
    @app_commands.describe(days="Number of days to analyze")
    async def view_symptoms(
        self,
        interaction: discord.Interaction,
        days: int = 30
    ):
        """View tracked symptoms and treatment effectiveness."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get consumption entries with symptoms
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Filter by date range and entries with symptoms
            cutoff_date = datetime.now() - timedelta(days=days)
            medical_entries = [
                e for e in entries 
                if e.timestamp and e.timestamp >= cutoff_date and e.symptom
            ]

            if not medical_entries:
                embed = discord.Embed(
                    title="🏥 Medical Symptom Tracking",
                    description=f"No medical consumption logged in the last {days} days.\nUse `/medical log` to start tracking!",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Analyze symptoms
            symptom_data = {}
            for entry in medical_entries:
                symptom = entry.symptom
                if symptom not in symptom_data:
                    symptom_data[symptom] = {
                        'sessions': 0,
                        'total_thc': 0,
                        'ratings': [],
                        'methods': {},
                        'strains': {}
                    }
                
                symptom_data[symptom]['sessions'] += 1
                symptom_data[symptom]['total_thc'] += entry.absorbed_thc_mg
                
                if entry.effect_rating:
                    symptom_data[symptom]['ratings'].append(entry.effect_rating)
                
                symptom_data[symptom]['methods'][entry.method] = \
                    symptom_data[symptom]['methods'].get(entry.method, 0) + 1
                
                if entry.strain:
                    symptom_data[symptom]['strains'][entry.strain] = \
                        symptom_data[symptom]['strains'].get(entry.strain, 0) + 1

            embed = discord.Embed(
                title=f"🏥 Medical Symptom Report - Last {days} Days",
                color=0x2196F3
            )

            # Summary
            total_medical_sessions = len(medical_entries)
            unique_symptoms = len(symptom_data)
            total_medical_thc = sum(e.absorbed_thc_mg for e in medical_entries)

            embed.add_field(
                name="📊 Overview",
                value=f"**Medical Sessions:** {total_medical_sessions}\n"
                      f"**Symptoms Treated:** {unique_symptoms}\n"
                      f"**Total Medical THC:** {total_medical_thc:.1f}mg",
                inline=False
            )

            # Top symptoms by frequency
            top_symptoms = sorted(symptom_data.items(), key=lambda x: x[1]['sessions'], reverse=True)
            
            symptom_text = ""
            for symptom, data in top_symptoms[:6]:  # Top 6 symptoms
                avg_rating = sum(data['ratings']) / len(data['ratings']) if data['ratings'] else 0
                avg_thc = data['total_thc'] / data['sessions']
                stars = "⭐" * round(avg_rating) if avg_rating > 0 else "No rating"
                
                symptom_name = symptom.replace("_", " ").title()
                symptom_text += f"**{symptom_name}**\n"
                symptom_text += f"  • {data['sessions']} sessions, {avg_thc:.1f}mg avg\n"
                symptom_text += f"  • Effectiveness: {stars}"
                if avg_rating > 0:
                    symptom_text += f" ({avg_rating:.1f}/5)"
                symptom_text += "\n\n"

            embed.add_field(
                name="🎯 Symptoms Treated",
                value=symptom_text.strip(),
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error viewing symptoms: {str(e)}", 
                ephemeral=True
            )

    @medical_group.command(name="analyze", description="Analyze effectiveness for a specific symptom")
    @app_commands.describe(
        symptom="Symptom to analyze",
        days="Number of days to analyze"
    )
    async def analyze_symptom(
        self,
        interaction: discord.Interaction,
        symptom: str,
        days: int = 90
    ):
        """Analyze treatment effectiveness for a specific symptom."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            symptom_lower = symptom.lower()
            
            # Get consumption entries for this symptom
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Filter by symptom and date range
            cutoff_date = datetime.now() - timedelta(days=days)
            symptom_entries = [
                e for e in entries 
                if e.timestamp and e.timestamp >= cutoff_date 
                and e.symptom and e.symptom.lower() == symptom_lower
            ]

            if not symptom_entries:
                embed = discord.Embed(
                    title=f"🏥 {symptom.title()} Analysis",
                    description=f"No consumption logged for {symptom} in the last {days} days",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Analyze effectiveness
            total_sessions = len(symptom_entries)
            total_thc = sum(e.absorbed_thc_mg for e in symptom_entries)
            avg_thc_per_session = total_thc / total_sessions

            # Rating analysis
            rated_entries = [e for e in symptom_entries if e.effect_rating]
            avg_effectiveness = sum(e.effect_rating for e in rated_entries if e.effect_rating) / len(rated_entries) if rated_entries else 0

            # Method analysis
            method_effectiveness = {}
            method_usage = {}
            for entry in symptom_entries:
                method = entry.method
                method_usage[method] = method_usage.get(method, 0) + 1
                
                if entry.effect_rating:
                    if method not in method_effectiveness:
                        method_effectiveness[method] = []
                    method_effectiveness[method].append(entry.effect_rating)

            # Strain analysis
            strain_effectiveness = {}
            strain_usage = {}
            for entry in symptom_entries:
                if entry.strain:
                    strain = entry.strain
                    strain_usage[strain] = strain_usage.get(strain, 0) + 1
                    
                    if entry.effect_rating:
                        if strain not in strain_effectiveness:
                            strain_effectiveness[strain] = []
                        strain_effectiveness[strain].append(entry.effect_rating)

            embed = discord.Embed(
                title=f"🏥 {symptom.replace('_', ' ').title()} Analysis - Last {days} Days",
                color=0x4CAF50
            )

            # Overview
            stars = "⭐" * round(avg_effectiveness) if avg_effectiveness > 0 else "No ratings"
            embed.add_field(
                name="📊 Treatment Overview",
                value=f"**Total Sessions:** {total_sessions}\n"
                      f"**Average Effectiveness:** {stars}"
                      + (f" ({avg_effectiveness:.1f}/5)" if avg_effectiveness > 0 else "") + f"\n"
                      f"**Average THC per Session:** {avg_thc_per_session:.1f}mg\n"
                      f"**Total THC Used:** {total_thc:.1f}mg",
                inline=False
            )

            # Most effective methods
            method_avg = {}
            if method_effectiveness:
                method_avg = {
                    method: sum(ratings) / len(ratings)
                    for method, ratings in method_effectiveness.items()
                    if len(ratings) >= 2  # At least 2 ratings
                }
                
                if method_avg:
                    best_methods = sorted(method_avg.items(), key=lambda x: x[1], reverse=True)[:3]
                    method_text = "\n".join([
                        f"• **{method.title()}:** {'⭐' * round(rating)} {rating:.1f}/5 "
                        f"({method_usage[method]} sessions)"
                        for method, rating in best_methods
                    ])
                    
                    embed.add_field(
                        name="🔥 Most Effective Methods",
                        value=method_text,
                        inline=False
                    )

            # Most effective strains
            strain_avg = {}
            if strain_effectiveness:
                strain_avg = {
                    strain: sum(ratings) / len(ratings)
                    for strain, ratings in strain_effectiveness.items()
                    if len(ratings) >= 2  # At least 2 ratings
                }
                
                if strain_avg:
                    best_strains = sorted(strain_avg.items(), key=lambda x: x[1], reverse=True)[:3]
                    strain_text = "\n".join([
                        f"• **{strain}:** {'⭐' * round(rating)} {rating:.1f}/5 "
                        f"({strain_usage[strain]} sessions)"
                        for strain, rating in best_strains
                    ])
                    
                    embed.add_field(
                        name="🌿 Most Effective Strains",
                        value=strain_text,
                        inline=False
                    )

            # Usage patterns
            if total_sessions >= 7:  # If enough data
                # Calculate frequency
                frequency = total_sessions / days
                if frequency >= 1:
                    frequency_text = f"{frequency:.1f} sessions per day"
                elif frequency >= 0.2:
                    frequency_text = f"{frequency * 7:.1f} sessions per week"
                else:
                    frequency_text = f"{total_sessions} sessions in {days} days"

                # Recent trend
                recent_entries = [e for e in symptom_entries if e.timestamp and e.timestamp >= datetime.now() - timedelta(days=7)]
                recent_sessions = len(recent_entries)
                weekly_frequency = recent_sessions
                
                trend_text = f"**Usage Frequency:** {frequency_text}\n"
                trend_text += f"**Recent Activity:** {weekly_frequency} sessions this week"
                
                if recent_sessions > 0:
                    recent_avg_rating = sum(e.effect_rating for e in recent_entries if e.effect_rating) / len([e for e in recent_entries if e.effect_rating])
                    if recent_avg_rating > 0:
                        trend_text += f"\n**Recent Effectiveness:** {'⭐' * round(recent_avg_rating)} {recent_avg_rating:.1f}/5"

                embed.add_field(
                    name="📈 Usage Patterns",
                    value=trend_text,
                    inline=False
                )

            # Recommendations
            recommendations = []
            
            if method_effectiveness and len(method_avg) > 1:
                best_method = max(method_avg.items(), key=lambda x: x[1])
                if best_method[1] >= 4.0:
                    recommendations.append(f"💡 **{best_method[0].title()}** works best for you ({best_method[1]:.1f}/5)")

            if strain_effectiveness and len(strain_avg) > 1:
                best_strain = max(strain_avg.items(), key=lambda x: x[1])
                if best_strain[1] >= 4.0:
                    recommendations.append(f"🌿 **{best_strain[0]}** is most effective ({best_strain[1]:.1f}/5)")

            if avg_effectiveness < 3.0 and len(rated_entries) >= 3:
                recommendations.append("⚠️ Consider trying different methods or strains for better results")
            elif avg_effectiveness >= 4.0:
                recommendations.append("✅ Your current treatment approach is highly effective!")

            if recommendations:
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(recommendations),
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error analyzing symptom: {str(e)}", 
                ephemeral=True
            )

    @medical_group.command(name="compare", description="Compare effectiveness between different symptoms")
    @app_commands.describe(days="Number of days to analyze")
    async def compare_symptoms(
        self,
        interaction: discord.Interaction,
        days: int = 60
    ):
        """Compare treatment effectiveness across different symptoms."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get all medical consumption
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Filter by date range and entries with symptoms
            cutoff_date = datetime.now() - timedelta(days=days)
            medical_entries = [
                e for e in entries 
                if e.timestamp and e.timestamp >= cutoff_date and e.symptom and e.effect_rating
            ]

            if not medical_entries:
                embed = discord.Embed(
                    title="🏥 Symptom Comparison",
                    description=f"No rated medical consumption found in the last {days} days",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Group by symptom
            symptom_data = {}
            for entry in medical_entries:
                symptom = entry.symptom
                if symptom not in symptom_data:
                    symptom_data[symptom] = {
                        'ratings': [],
                        'thc_amounts': [],
                        'sessions': 0
                    }
                
                symptom_data[symptom]['ratings'].append(entry.effect_rating)
                symptom_data[symptom]['thc_amounts'].append(entry.absorbed_thc_mg)
                symptom_data[symptom]['sessions'] += 1

            # Calculate averages
            symptom_analysis = {}
            for symptom, data in symptom_data.items():
                if len(data['ratings']) >= 2:  # At least 2 ratings
                    symptom_analysis[symptom] = {
                        'avg_rating': sum(data['ratings']) / len(data['ratings']),
                        'avg_thc': sum(data['thc_amounts']) / len(data['thc_amounts']),
                        'sessions': data['sessions'],
                        'consistency': 1 - (max(data['ratings']) - min(data['ratings'])) / 4  # Consistency score
                    }

            if not symptom_analysis:
                embed = discord.Embed(
                    title="🏥 Symptom Comparison",
                    description="Not enough data for comparison (need at least 2 rated sessions per symptom)",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🏥 Symptom Treatment Comparison - Last {days} Days",
                color=0x2196F3
            )

            # Sort by effectiveness
            by_effectiveness = sorted(symptom_analysis.items(), key=lambda x: x[1]['avg_rating'], reverse=True)
            
            effectiveness_text = ""
            for symptom, data in by_effectiveness:
                stars = "⭐" * round(data['avg_rating'])
                consistency_emoji = "🎯" if data['consistency'] > 0.7 else "📊"
                
                symptom_name = symptom.replace("_", " ").title()
                effectiveness_text += f"**{symptom_name}**\n"
                effectiveness_text += f"  • Effectiveness: {stars} {data['avg_rating']:.1f}/5\n"
                effectiveness_text += f"  • Sessions: {data['sessions']}, Avg THC: {data['avg_thc']:.1f}mg\n"
                effectiveness_text += f"  • Consistency: {consistency_emoji} {data['consistency']*100:.0f}%\n\n"

            embed.add_field(
                name="🏆 Effectiveness Rankings",
                value=effectiveness_text.strip(),
                inline=False
            )

            # Sort by THC efficiency (lower THC, higher effectiveness is better)
            efficiency_scores = {
                symptom: data['avg_rating'] / data['avg_thc'] if data['avg_thc'] > 0 else 0
                for symptom, data in symptom_analysis.items()
            }
            
            by_efficiency = sorted(efficiency_scores.items(), key=lambda x: x[1], reverse=True)
            
            if len(by_efficiency) > 1:
                efficiency_text = ""
                for symptom, efficiency in by_efficiency[:5]:
                    data = symptom_analysis[symptom]
                    symptom_name = symptom.replace("_", " ").title()
                    efficiency_text += f"• **{symptom_name}:** {efficiency:.2f} effectiveness per mg\n"
                    efficiency_text += f"  ({data['avg_rating']:.1f}/5 at {data['avg_thc']:.1f}mg avg)\n"

                embed.add_field(
                    name="⚡ THC Efficiency",
                    value=efficiency_text.strip(),
                    inline=False
                )

            # Insights
            insights = []
            
            # Best treated symptom
            best_symptom = by_effectiveness[0]
            if best_symptom[1]['avg_rating'] >= 4.0:
                insights.append(f"✅ **{best_symptom[0].replace('_', ' ').title()}** is your most effectively treated symptom")

            # Consistent treatments
            consistent_symptoms = [s for s, d in symptom_analysis.items() if d['consistency'] > 0.8]
            if consistent_symptoms:
                insights.append(f"🎯 Most consistent results with: {', '.join([s.replace('_', ' ').title() for s in consistent_symptoms[:2]])}")

            # Low effectiveness warning
            low_effectiveness = [s for s, d in symptom_analysis.items() if d['avg_rating'] < 3.0]
            if low_effectiveness:
                insights.append(f"⚠️ Consider adjusting treatment for: {', '.join([s.replace('_', ' ').title() for s in low_effectiveness[:2]])}")

            if insights:
                embed.add_field(
                    name="💡 Key Insights",
                    value="\n".join(insights),
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error comparing symptoms: {str(e)}", 
                ephemeral=True
            )

    @medical_group.command(name="export", description="Export your medical data for healthcare providers")
    @app_commands.describe(days="Number of days to export")
    async def export_medical_data(
        self,
        interaction: discord.Interaction,
        days: int = 90
    ):
        """Export medical consumption data."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get medical consumption data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            # Filter by date range and medical entries
            cutoff_date = datetime.now() - timedelta(days=days)
            medical_entries = [
                e for e in entries 
                if e.timestamp and e.timestamp >= cutoff_date and e.symptom
            ]

            if not medical_entries:
                embed = discord.Embed(
                    title="📄 Medical Data Export",
                    description=f"No medical consumption data found in the last {days} days",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Create CSV-like text format
            export_text = "Date,Time,Symptom,Product,Amount,THC%,Method,Absorbed_THC_mg,Effectiveness,Notes\n"
            
            for entry in sorted(medical_entries, key=lambda x: x.timestamp or datetime.min):
                timestamp = entry.timestamp or datetime.now()
                date_str = timestamp.strftime("%Y-%m-%d")
                time_str = timestamp.strftime("%H:%M")
                
                # Clean data for CSV
                symptom = (entry.symptom or "unknown").replace("_", " ").title()
                product = f"{entry.type}" + (f" ({entry.strain})" if entry.strain else "")
                thc_pct = f"{entry.thc_percent}%" if entry.thc_percent else "Unknown"
                effectiveness = f"{entry.effect_rating}/5" if entry.effect_rating else "Not rated"
                notes = (entry.notes or "").replace(",", ";").replace("\n", " ")  # CSV safe
                
                export_text += f"{date_str},{time_str},{symptom},{product},{entry.amount}g,{thc_pct},{entry.method.title()},{entry.absorbed_thc_mg:.1f}mg,{effectiveness},\"{notes}\"\n"

            # Create summary
            total_sessions = len(medical_entries)
            total_thc = sum(e.absorbed_thc_mg for e in medical_entries)
            avg_effectiveness = sum(e.effect_rating for e in medical_entries if e.effect_rating) / len([e for e in medical_entries if e.effect_rating])
            
            summary = f"""MEDICAL CANNABIS CONSUMPTION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Period: {days} days ({cutoff_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')})

SUMMARY:
- Total medical sessions: {total_sessions}
- Total THC consumed: {total_thc:.1f}mg
- Average effectiveness: {avg_effectiveness:.1f}/5 stars
- Symptoms treated: {len(set(e.symptom for e in medical_entries))}

DETAILED DATA:
{export_text}

NOTE: This data is for medical tracking purposes only and should be discussed with your healthcare provider.
"""

            # Split into chunks if too long for Discord
            max_length = 1900  # Leave room for formatting
            
            if len(summary) <= max_length:
                embed = discord.Embed(
                    title="📄 Medical Data Export",
                    description=f"```csv\n{summary}\n```",
                    color=0x4CAF50
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # Send summary first
                summary_lines = summary.split('\n')
                summary_part = '\n'.join(summary_lines[:15])  # First 15 lines
                
                embed = discord.Embed(
                    title="📄 Medical Data Export - Summary",
                    description=f"```\n{summary_part}\n```",
                    color=0x4CAF50
                )
                embed.add_field(
                    name="ℹ️ Note",
                    value="This is a summary. Full data is too large for Discord. Consider using a medical app for complete tracking.",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error exporting medical data: {str(e)}", 
                ephemeral=True
            )

    # Autocomplete for symptom field
    @log_medical.autocomplete('symptom')
    @analyze_symptom.autocomplete('symptom')
    async def symptom_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Provide autocomplete for symptoms."""
        matching_symptoms = [
            symptom for symptom in MEDICAL_SYMPTOMS 
            if current.lower() in symptom.lower()
        ]
        
        return [
            app_commands.Choice(name=symptom.replace("_", " ").title(), value=symptom)
            for symptom in matching_symptoms[:25]  # Discord limit
        ]

async def setup(bot):
    await bot.add_cog(MedicalCommands(bot))
