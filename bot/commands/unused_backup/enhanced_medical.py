"""Enhanced medical features for symptom tracking and correlation analysis."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import json

from bot.database.models import ConsumptionEntry, StrainNote, MedicalEntry
from bot.services.consumption_service import ConsumptionService

class EnhancedMedicalCommands(commands.Cog):
    """Enhanced medical cannabis tracking and analysis."""
    
    def __init__(self, bot):
        self.bot = bot
        self.symptom_database = self._load_symptom_database()
        self.strain_database = self._load_strain_database()

    def _load_symptom_database(self) -> Dict:
        """Load comprehensive symptom database with cannabis correlations."""
        return {
            # Pain conditions
            "chronic_pain": {
                "category": "pain",
                "description": "Persistent pain lasting >3 months",
                "recommended_cannabinoids": ["THC", "CBD", "CBG"],
                "recommended_terpenes": ["myrcene", "linalool", "caryophyllene"],
                "dosage_range": "2.5-10mg THC",
                "timing": "As needed, preferably evening"
            },
            "arthritis": {
                "category": "pain",
                "description": "Joint inflammation and pain",
                "recommended_cannabinoids": ["CBD", "THC", "CBG"],
                "recommended_terpenes": ["caryophyllene", "limonene"],
                "dosage_range": "5-15mg CBD, 2.5-5mg THC",
                "timing": "Morning and evening"
            },
            "migraine": {
                "category": "pain",
                "description": "Severe headaches with sensitivity",
                "recommended_cannabinoids": ["THC", "CBD"],
                "recommended_terpenes": ["linalool", "pinene"],
                "dosage_range": "2.5-7.5mg THC at onset",
                "timing": "At first sign of migraine"
            },
            
            # Mental health
            "anxiety": {
                "category": "mental_health",
                "description": "Persistent worry and nervousness",
                "recommended_cannabinoids": ["CBD", "low THC"],
                "recommended_terpenes": ["linalool", "limonene", "myrcene"],
                "dosage_range": "10-25mg CBD, <2.5mg THC",
                "timing": "As needed, avoid high THC"
            },
            "depression": {
                "category": "mental_health",
                "description": "Persistent low mood and lack of interest",
                "recommended_cannabinoids": ["THC", "CBD"],
                "recommended_terpenes": ["limonene", "pinene"],
                "dosage_range": "2.5-10mg THC, 5-15mg CBD",
                "timing": "Morning for energy, evening for sleep"
            },
            "ptsd": {
                "category": "mental_health",
                "description": "Post-traumatic stress disorder",
                "recommended_cannabinoids": ["CBD", "THC"],
                "recommended_terpenes": ["linalool", "myrcene"],
                "dosage_range": "5-20mg CBD, 2.5-7.5mg THC",
                "timing": "Evening preferred, micro-dose during day"
            },
            
            # Sleep disorders
            "insomnia": {
                "category": "sleep",
                "description": "Difficulty falling or staying asleep",
                "recommended_cannabinoids": ["THC", "CBN", "CBD"],
                "recommended_terpenes": ["myrcene", "linalool", "terpinolene"],
                "dosage_range": "5-15mg THC, 2-5mg CBN",
                "timing": "1-2 hours before bed"
            },
            "sleep_apnea": {
                "category": "sleep",
                "description": "Breathing interruptions during sleep",
                "recommended_cannabinoids": ["CBD", "low THC"],
                "recommended_terpenes": ["linalool", "myrcene"],
                "dosage_range": "10-30mg CBD, <5mg THC",
                "timing": "Evening, consult doctor"
            },
            
            # Digestive issues
            "nausea": {
                "category": "digestive",
                "description": "Feeling sick to stomach",
                "recommended_cannabinoids": ["THC", "CBD"],
                "recommended_terpenes": ["limonene", "caryophyllene"],
                "dosage_range": "2.5-7.5mg THC",
                "timing": "As needed, start low"
            },
            "ibs": {
                "category": "digestive",
                "description": "Irritable bowel syndrome",
                "recommended_cannabinoids": ["CBD", "THC"],
                "recommended_terpenes": ["caryophyllene", "limonene"],
                "dosage_range": "10-25mg CBD, 2.5-10mg THC",
                "timing": "With meals or as needed"
            },
            
            # Neurological conditions
            "epilepsy": {
                "category": "neurological",
                "description": "Seizure disorder",
                "recommended_cannabinoids": ["CBD", "CBDV"],
                "recommended_terpenes": ["linalool", "caryophyllene"],
                "dosage_range": "Starting 2-5mg/kg CBD (medical supervision required)",
                "timing": "Divided doses throughout day"
            },
            "multiple_sclerosis": {
                "category": "neurological",
                "description": "Autoimmune condition affecting nervous system",
                "recommended_cannabinoids": ["THC", "CBD"],
                "recommended_terpenes": ["caryophyllene", "limonene"],
                "dosage_range": "5-15mg THC, 10-25mg CBD",
                "timing": "Evening preferred"
            }
        }

    def _load_strain_database(self) -> Dict:
        """Load strain database with medical recommendations."""
        return {
            # High CBD strains
            "charlotte's_web": {
                "type": "sativa_dominant",
                "cbd_range": "15-20%",
                "thc_range": "<1%",
                "primary_terpenes": ["myrcene", "pinene", "caryophyllene"],
                "medical_uses": ["epilepsy", "anxiety", "chronic_pain"],
                "effects": ["clear-headed", "relaxing", "anti-inflammatory"]
            },
            "acdc": {
                "type": "sativa_dominant",
                "cbd_range": "14-20%",
                "thc_range": "1-6%",
                "primary_terpenes": ["myrcene", "pinene", "caryophyllene"],
                "medical_uses": ["anxiety", "chronic_pain", "inflammation"],
                "effects": ["uplifting", "clear", "pain-relief"]
            },
            
            # Balanced strains
            "harlequin": {
                "type": "sativa_dominant",
                "cbd_range": "8-16%",
                "thc_range": "7-15%",
                "primary_terpenes": ["myrcene", "pinene", "caryophyllene"],
                "medical_uses": ["chronic_pain", "anxiety", "depression"],
                "effects": ["alert", "relaxed", "mood-boost"]
            },
            "cannatonic": {
                "type": "hybrid",
                "cbd_range": "12-18%",
                "thc_range": "6-17%",
                "primary_terpenes": ["myrcene", "limonene", "caryophyllene"],
                "medical_uses": ["muscle_spasms", "anxiety", "migraines"],
                "effects": ["mild_euphoria", "relaxation", "pain_relief"]
            },
            
            # High THC medicinal
            "og_kush": {
                "type": "indica_dominant",
                "cbd_range": "<1%",
                "thc_range": "20-26%",
                "primary_terpenes": ["myrcene", "limonene", "caryophyllene"],
                "medical_uses": ["chronic_pain", "insomnia", "ptsd"],
                "effects": ["euphoric", "relaxing", "sedating"]
            },
            "granddaddy_purple": {
                "type": "indica",
                "cbd_range": "<1%",
                "thc_range": "17-23%",
                "primary_terpenes": ["myrcene", "pinene", "caryophyllene"],
                "medical_uses": ["insomnia", "chronic_pain", "depression"],
                "effects": ["sleepy", "euphoric", "appetite_stimulation"]
            }
        }

    @app_commands.command(name="symptoms", description="Track symptoms and get cannabis recommendations")
    @app_commands.describe(
        symptoms="Symptoms you're experiencing (comma-separated)",
        severity="Severity level 1-10",
        notes="Additional notes about symptoms"
    )
    async def track_symptoms(
        self,
        interaction: discord.Interaction,
        symptoms: str,
        severity: int,
        notes: Optional[str] = None
    ):
        """Track symptoms and get cannabis recommendations."""
        try:
            user_id = interaction.user.id
            
            if not 1 <= severity <= 10:
                await interaction.response.send_message(
                    "❌ Severity must be between 1 and 10",
                    ephemeral=True
                )
                return
            
            # Parse symptoms
            symptom_list = [s.strip().lower().replace(' ', '_') for s in symptoms.split(',')]
            
            # Create medical entry
            medical_entry = MedicalEntry(
                user_id=user_id,
                entry_type='symptom_tracking',
                symptoms=','.join(symptom_list),
                severity=severity,
                notes=notes or '',
                timestamp=datetime.now()
            )
            await medical_entry.save()
            
            embed = discord.Embed(
                title="🏥 Symptoms Tracked",
                description="Your symptoms have been recorded",
                color=0x2196F3
            )
            
            # Show tracked symptoms
            embed.add_field(
                name="📝 Recorded Symptoms",
                value=f"**Symptoms:** {symptoms}\n"
                      f"**Severity:** {severity}/10\n"
                      f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                      f"**Notes:** {notes or 'None'}",
                inline=False
            )
            
            # Provide recommendations
            recommendations = []
            for symptom in symptom_list:
                if symptom in self.symptom_database:
                    symptom_info = self.symptom_database[symptom]
                    recommendations.append({
                        'symptom': symptom.replace('_', ' ').title(),
                        'info': symptom_info
                    })
            
            if recommendations:
                rec_text = ""
                for rec in recommendations[:3]:  # Show top 3
                    rec_text += f"**{rec['symptom']}**\n"
                    rec_text += f"• Cannabinoids: {', '.join(rec['info']['recommended_cannabinoids'])}\n"
                    rec_text += f"• Dosage: {rec['info']['dosage_range']}\n"
                    rec_text += f"• Timing: {rec['info']['timing']}\n\n"
                
                embed.add_field(
                    name="💊 Cannabis Recommendations",
                    value=rec_text.strip(),
                    inline=False
                )
            
            # Suggest strain matching
            embed.add_field(
                name="🔍 Next Steps",
                value="• Use `/medical strains` to find matching strains\n"
                      "• Log consumption after medication\n"
                      "• Track effectiveness with `/medical effectiveness`\n"
                      "• Review patterns with `/medical medical-report`",
                inline=False
            )
            
            embed.set_footer(text="⚠️ This is not medical advice. Consult your healthcare provider.")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error tracking symptoms: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="strains", description="Find strains for your medical conditions")
    @app_commands.describe(condition="Medical condition or symptom")
    async def find_strains(self, interaction: discord.Interaction, condition: str):
        """Find cannabis strains for specific medical conditions."""
        try:
            condition_key = condition.lower().replace(' ', '_')
            
            embed = discord.Embed(
                title=f"🌿 Cannabis Strains for {condition.title()}",
                color=0x4CAF50
            )
            
            # Check if condition is in our database
            if condition_key in self.symptom_database:
                symptom_info = self.symptom_database[condition_key]
                
                embed.add_field(
                    name="📚 Condition Information",
                    value=f"**Description:** {symptom_info['description']}\n"
                          f"**Category:** {symptom_info['category'].replace('_', ' ').title()}\n"
                          f"**Recommended Cannabinoids:** {', '.join(symptom_info['recommended_cannabinoids'])}\n"
                          f"**Key Terpenes:** {', '.join(symptom_info['recommended_terpenes'])}\n"
                          f"**Dosage Guide:** {symptom_info['dosage_range']}\n"
                          f"**Timing:** {symptom_info['timing']}",
                    inline=False
                )
                
                # Find matching strains
                matching_strains = []
                for strain_name, strain_info in self.strain_database.items():
                    if condition_key in strain_info['medical_uses']:
                        matching_strains.append((strain_name, strain_info))
                
                if matching_strains:
                    strain_text = ""
                    for strain_name, strain_info in matching_strains[:4]:  # Top 4 matches
                        strain_display = strain_name.replace('_', ' ').title()
                        strain_text += f"**{strain_display}** ({strain_info['type'].replace('_', ' ')})\n"
                        strain_text += f"• THC: {strain_info['thc_range']}, CBD: {strain_info['cbd_range']}\n"
                        strain_text += f"• Effects: {', '.join(strain_info['effects'])}\n"
                        strain_text += f"• Key Terpenes: {', '.join(strain_info['primary_terpenes'][:3])}\n\n"
                    
                    embed.add_field(
                        name="🏆 Recommended Strains",
                        value=strain_text.strip(),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🔍 Strain Suggestions",
                        value="No specific strains in database, but look for:\n"
                              f"• High {'/'.join(symptom_info['recommended_cannabinoids'])} strains\n"
                              f"• Strains with {', '.join(symptom_info['recommended_terpenes'][:3])} terpenes",
                        inline=False
                    )
            
            else:
                # General suggestions based on partial matching
                embed.add_field(
                    name="💡 General Guidance",
                    value=f"Condition '{condition}' not found in our database.\n\n"
                          "**General Cannabis Guidelines:**\n"
                          "• **Pain/Inflammation:** High CBD, CBG, caryophyllene\n"
                          "• **Anxiety/Stress:** High CBD, low THC, linalool\n"
                          "• **Sleep Issues:** Indica, high THC, myrcene\n"
                          "• **Nausea:** THC, limonene\n"
                          "• **Appetite:** THC, caryophyllene\n"
                          "• **Depression:** Sativa, limonene, pinene",
                    inline=False
                )
                
                # Show available conditions
                available_conditions = list(self.symptom_database.keys())[:12]
                conditions_text = ", ".join([c.replace('_', ' ') for c in available_conditions])
                
                embed.add_field(
                    name="📋 Available Conditions",
                    value=f"Try: {conditions_text}",
                    inline=False
                )
            
            # Dosage safety information
            embed.add_field(
                name="⚠️ Safety Guidelines",
                value="• Start with lowest effective dose\n"
                      "• Wait 2+ hours before redosing\n"
                      "• Keep a consumption log\n"
                      "• Consult healthcare provider\n"
                      "• Be aware of drug interactions",
                inline=False
            )
            
            embed.set_footer(text="🏥 Always consult your doctor before using cannabis medicinally")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error finding strains: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="effectiveness", description="Track medication effectiveness")
    @app_commands.describe(
        effectiveness="How effective was the medication (1-10)",
        symptoms_improved="Which symptoms improved",
        side_effects="Any side effects experienced"
    )
    async def track_effectiveness(
        self,
        interaction: discord.Interaction,
        effectiveness: int,
        symptoms_improved: Optional[str] = None,
        side_effects: Optional[str] = None
    ):
        """Track cannabis medication effectiveness."""
        try:
            user_id = interaction.user.id
            
            if not 1 <= effectiveness <= 10:
                await interaction.response.send_message(
                    "❌ Effectiveness must be between 1 and 10",
                    ephemeral=True
                )
                return
            
            # Get recent consumption entry to link with
            recent_entries = await ConsumptionEntry.get_user_consumption(user_id, limit=5)
            
            if not recent_entries:
                await interaction.response.send_message(
                    "❌ No recent consumption found. Log consumption first.",
                    ephemeral=True
                )
                return
            
            # Find most recent entry (within last 4 hours)
            recent_entry = None
            for entry in recent_entries:
                if entry.timestamp and (datetime.now() - entry.timestamp).total_seconds() < 14400:  # 4 hours
                    recent_entry = entry
                    break
            
            if not recent_entry:
                await interaction.response.send_message(
                    "❌ No consumption found within last 4 hours. Log consumption first.",
                    ephemeral=True
                )
                return
            
            # Create effectiveness tracking entry
            medical_entry = MedicalEntry(
                user_id=user_id,
                entry_type='effectiveness_tracking',
                effectiveness_rating=effectiveness,
                symptoms_improved=symptoms_improved or '',
                side_effects=side_effects or '',
                consumption_id=recent_entry.id,
                timestamp=datetime.now()
            )
            await medical_entry.save()
            
            embed = discord.Embed(
                title="📈 Effectiveness Tracked",
                description="Your medication effectiveness has been recorded",
                color=0x4CAF50 if effectiveness >= 7 else 0xFF9800 if effectiveness >= 4 else 0xF44336
            )
            
            # Show tracked data
            embed.add_field(
                name="📊 Effectiveness Record",
                value=f"**Effectiveness:** {effectiveness}/10\n"
                      f"**Linked to:** {recent_entry.method.title()} - {recent_entry.amount}g {recent_entry.strain or 'Unknown strain'}\n"
                      f"**Time since dose:** {int((datetime.now() - (recent_entry.timestamp or datetime.now())).total_seconds() / 60)} minutes\n"
                      f"**Symptoms improved:** {symptoms_improved or 'Not specified'}\n"
                      f"**Side effects:** {side_effects or 'None reported'}",
                inline=False
            )
            
            # Provide insights based on effectiveness
            insights = []
            if effectiveness >= 8:
                insights.append("🎯 Excellent effectiveness! This combination seems to work well for you.")
            elif effectiveness >= 6:
                insights.append("👍 Good effectiveness. Consider noting what made this successful.")
            elif effectiveness >= 4:
                insights.append("📊 Moderate effectiveness. Consider adjusting dosage or strain.")
            else:
                insights.append("🔄 Low effectiveness. Consider trying different strain/method/timing.")
            
            if side_effects:
                insights.append("⚠️ Note side effects for future reference. Consider lower dose if uncomfortable.")
            
            if insights:
                embed.add_field(
                    name="💡 Insights",
                    value="\n".join(insights),
                    inline=False
                )
            
            # Suggest next steps
            embed.add_field(
                name="🔍 Next Steps",
                value="• Continue tracking to identify patterns\n"
                      "• Use `/medical report` to review trends\n"
                      "• Adjust dosage based on effectiveness\n"
                      "• Share data with healthcare provider",
                inline=False
            )
            
            embed.set_footer(text="📈 Consistent tracking helps optimize your medication")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error tracking effectiveness: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="medical-report", description="Generate medical cannabis report")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def medical_report(self, interaction: discord.Interaction, days: int = 30):
        """Generate comprehensive medical cannabis report."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get medical and consumption data
            cutoff_date = datetime.now() - timedelta(days=days)
            consumption_entries = await ConsumptionEntry.get_user_consumption(user_id, limit=500)
            recent_consumption = [e for e in consumption_entries if e.timestamp and e.timestamp >= cutoff_date]
            
            # Get medical entries (would need to implement this in models)
            # For now, use consumption data with effect ratings as proxy
            
            if not recent_consumption:
                embed = discord.Embed(
                    title="🏥 Medical Cannabis Report",
                    description=f"No consumption data found for the last {days} days",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🏥 Medical Cannabis Report - Last {days} Days",
                description="Comprehensive analysis of your medical cannabis use",
                color=0x2196F3
            )
            
            # Usage summary
            total_sessions = len(recent_consumption)
            total_thc = sum(e.absorbed_thc_mg for e in recent_consumption)
            avg_daily = total_thc / days if days > 0 else 0
            
            # Effectiveness analysis
            rated_sessions = [e for e in recent_consumption if e.effect_rating is not None]
            if rated_sessions:
                avg_effectiveness = sum(e.effect_rating for e in rated_sessions if e.effect_rating is not None) / len(rated_sessions)
                # Simple trend analysis - comparing first half vs second half
                if len(rated_sessions) >= 10:
                    mid_point = len(rated_sessions) // 2
                    first_half_avg = sum(e.effect_rating for e in rated_sessions[:mid_point] if e.effect_rating is not None) / mid_point
                    second_half_avg = sum(e.effect_rating for e in rated_sessions[mid_point:] if e.effect_rating is not None) / (len(rated_sessions) - mid_point)
                    effectiveness_trend = "improving" if second_half_avg > first_half_avg else "stable"
                else:
                    effectiveness_trend = "stable"
            else:
                avg_effectiveness = 0
                effectiveness_trend = "unknown"
            
            embed.add_field(
                name="📊 Usage Summary",
                value=f"**Total Sessions:** {total_sessions}\n"
                      f"**Total THC Absorbed:** {total_thc:.1f}mg\n"
                      f"**Daily Average:** {avg_daily:.1f}mg/day\n"
                      f"**Avg Effectiveness:** {avg_effectiveness:.1f}/5 ⭐\n"
                      f"**Trend:** {effectiveness_trend.title()}",
                inline=False
            )
            
            # Method analysis
            method_effectiveness = {}
            for entry in rated_sessions:
                method = entry.method
                if method not in method_effectiveness:
                    method_effectiveness[method] = []
                if entry.effect_rating is not None:
                    method_effectiveness[method].append(entry.effect_rating)
            
            if method_effectiveness:
                method_text = ""
                for method, ratings in method_effectiveness.items():
                    avg_rating = sum(ratings) / len(ratings)
                    method_text += f"**{method.title()}:** {avg_rating:.1f}/5 ({len(ratings)} sessions)\n"
                
                embed.add_field(
                    name="⚡ Method Effectiveness",
                    value=method_text,
                    inline=True
                )
            
            # Strain analysis
            strain_effectiveness = {}
            for entry in rated_sessions:
                if entry.strain and entry.effect_rating is not None:
                    strain = entry.strain
                    if strain not in strain_effectiveness:
                        strain_effectiveness[strain] = []
                    strain_effectiveness[strain].append(entry.effect_rating)
            
            if strain_effectiveness:
                # Top 3 most effective strains
                top_strains = sorted(strain_effectiveness.items(), 
                                   key=lambda x: sum(x[1])/len(x[1]), 
                                   reverse=True)[:3]
                
                strain_text = ""
                for strain, ratings in top_strains:
                    avg_rating = sum(ratings) / len(ratings)
                    strain_text += f"**{strain}:** {avg_rating:.1f}/5 ({len(ratings)} uses)\n"
                
                embed.add_field(
                    name="🌿 Top Strains",
                    value=strain_text,
                    inline=True
                )
            
            # Timing analysis
            hour_effectiveness = {}
            for entry in rated_sessions:
                if entry.timestamp and entry.effect_rating is not None:
                    hour = entry.timestamp.hour
                    if hour not in hour_effectiveness:
                        hour_effectiveness[hour] = []
                    hour_effectiveness[hour].append(entry.effect_rating)
            
            if hour_effectiveness:
                # Find best time of day
                best_hours = sorted(hour_effectiveness.items(), 
                                  key=lambda x: sum(x[1])/len(x[1]), 
                                  reverse=True)[:3]
                
                timing_text = ""
                for hour, ratings in best_hours:
                    avg_rating = sum(ratings) / len(ratings)
                    time_str = f"{hour:02d}:00"
                    timing_text += f"**{time_str}:** {avg_rating:.1f}/5\n"
                
                embed.add_field(
                    name="⏰ Optimal Times",
                    value=timing_text,
                    inline=True
                )
            
            # Recommendations
            recommendations = []
            
            if avg_effectiveness < 3.5:
                recommendations.append("📊 Consider adjusting dosage or trying different strains")
            
            if len(method_effectiveness) == 1:
                recommendations.append("🔄 Try different consumption methods for comparison")
            
            if avg_daily > 50:  # High daily usage
                recommendations.append("⚠️ High daily usage - consider tolerance break")
            
            if not rated_sessions:
                recommendations.append("📝 Start rating sessions to track effectiveness")
            
            if recommendations:
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(recommendations),
                    inline=False
                )
            
            # Medical disclaimer
            embed.add_field(
                name="🏥 Medical Note",
                value="This report is for informational purposes only. "
                      "Share with your healthcare provider for medical decisions. "
                      "Always follow your doctor's recommendations.",
                inline=False
            )
            
            embed.set_footer(text=f"📈 Report generated from {total_sessions} sessions over {days} days")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating report: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(EnhancedMedicalCommands(bot))
