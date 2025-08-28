"""Mobile-optimized commands with voice shortcuts and quick actions."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime, timedelta
import re

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService
from bot.services.notification_service import NotificationService
from bot.database.models import ConsumptionEntry, StashItem

class MobileCommands(commands.Cog):
    """Mobile-optimized commands for quick cannabis tracking."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="voice", description="Voice-friendly command shortcuts and tips")
    async def voice_shortcuts(self, interaction: discord.Interaction):
        """Show voice-friendly shortcuts for mobile users."""
        try:
            user_id = interaction.user.id
            
            # Get voice shortcuts
            shortcuts = await NotificationService.get_voice_friendly_shortcuts()
            
            # Get personalized shortcuts
            personal_shortcuts = await NotificationService.generate_consumption_shortcuts(user_id)
            
            embed = discord.Embed(
                title="🎤 Voice-Friendly Cannabis Tracking",
                description="Perfect for hands-free logging while medicating or relaxing",
                color=0x9C27B0
            )
            
            # Voice shortcuts
            shortcut_text = ""
            for shortcut in shortcuts[:5]:
                shortcut_text += f"**{shortcut['command']}**\n"
                shortcut_text += f"🎤 Say: \"{shortcut['voice_trigger']}\"\n"
                shortcut_text += f"💡 {shortcut['example']}\n\n"
            
            embed.add_field(
                name="🎤 Voice Commands",
                value=shortcut_text.strip(),
                inline=False
            )
            
            # Personal shortcuts
            if personal_shortcuts:
                personal_text = ""
                for shortcut in personal_shortcuts[:3]:
                    personal_text += f"**{shortcut['label']}**\n"
                    personal_text += f"📱 `{shortcut['command']}`\n"
                    personal_text += f"🔄 {shortcut['description']}\n\n"
                
                embed.add_field(
                    name="⚡ Your Quick Actions",
                    value=personal_text.strip(),
                    inline=False
                )
            
            # Voice tips
            tips = [
                "📱 **Use Siri/Google**: Set up voice shortcuts to open Discord",
                "🎯 **Be Specific**: Say amounts clearly (\"point five grams\")",
                "⏰ **Quick Log**: Use `/quick` for fastest entry",
                "📝 **Voice Memo**: Record details, then copy to Discord",
                "🔄 **Practice**: Common commands become muscle memory"
            ]
            
            embed.add_field(
                name="💡 Voice Tips",
                value="\n".join(tips),
                inline=False
            )
            
            # Quick reference
            embed.add_field(
                name="📚 Quick Reference",
                value="💨 `/quick` - Fastest logging\n"
                      "📊 `/dashboard` - Quick overview\n"
                      "🌿 `/stash list` - Check inventory\n"
                      "🎯 `/log last` - Repeat last session\n"
                      "🔔 `/remind` - Set smart reminders",
                inline=True
            )
            
            embed.set_footer(text="🎤 Perfect for discrete mobile tracking • Voice commands work great with Siri/Google Assistant")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error loading voice shortcuts: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="log", description="Smart logging with voice-optimized parsing")
    @app_commands.describe(
        text="Natural language: 'smoked 0.5g blue dream' or 'vaped point 2 grams sativa'"
    )
    async def smart_log(self, interaction: discord.Interaction, text: str):
        """Parse natural language consumption logging."""
        try:
            user_id = interaction.user.id
            
            # Parse the text input
            parsed = await self._parse_natural_language(text.lower())
            
            if not parsed:
                embed = discord.Embed(
                    title="❌ Couldn't Parse Input",
                    description=f"I couldn't understand: \"{text}\"",
                    color=0xF44336
                )
                embed.add_field(
                    name="💡 Try These Formats",
                    value="• \"smoked 0.5g blue dream\"\n"
                          "• \"vaped point two grams sativa\"\n"
                          "• \"dabbed 0.1 concentrates\"\n"
                          "• \"edible 10mg thc\"",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get strain data if available
            strain_data = None
            if parsed['strain']:
                stash_items = await StashService.get_user_stash(user_id)
                for item in stash_items:
                    if item.strain and parsed['strain'].lower() in item.strain.lower():
                        strain_data = item
                        break
            
            # Log the consumption
            entry = await ConsumptionService.log_consumption(
                user_id=user_id,
                method=parsed['method'],
                amount=parsed['amount'],
                product_type='flower',  # Default to flower
                strain=parsed['strain'],
                thc_percent=strain_data.thc_percent if strain_data else None,
                notes=f"Logged via voice: {text}"
            )
            
            if entry:
                # Handle tuple return from consumption service
                if isinstance(entry, tuple):
                    consumption_entry, warnings = entry
                    absorbed_thc = consumption_entry.absorbed_thc_mg
                else:
                    consumption_entry = entry
                    absorbed_thc = entry.absorbed_thc_mg
                
                embed = discord.Embed(
                    title="✅ Session Logged Successfully",
                    description=f"Parsed: \"{text}\"",
                    color=0x4CAF50
                )
                
                embed.add_field(
                    name="📝 Session Details",
                    value=f"**Method:** {parsed['method'].title()}\n"
                          f"**Amount:** {parsed['amount']}g\n"
                          f"**Strain:** {parsed['strain'] or 'Not specified'}\n"
                          f"**THC Absorbed:** {absorbed_thc:.1f}mg",
                    inline=False
                )
                
                if strain_data:
                    embed.add_field(
                        name="🌿 From Your Stash",
                        value=f"**THC%:** {strain_data.thc_percent}%\n"
                              f"**Remaining:** {strain_data.amount - parsed['amount']:.1f}g",
                        inline=True
                    )
                
                # Quick actions
                embed.add_field(
                    name="⚡ Quick Actions",
                    value="🎯 Say \"repeat\" to log again\n"
                          "📊 Use `/dashboard` for overview\n"
                          "🔔 Use `/remind` for next dose",
                    inline=True
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to log session. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error logging session: {str(e)}",
                ephemeral=True
            )

    async def _parse_natural_language(self, text: str) -> Optional[dict]:
        """Parse natural language input into consumption data."""
        try:
            result = {
                'method': '',
                'amount': 0.0,
                'strain': ''
            }
            
            # Method detection
            methods = {
                'smoke': ['smoked', 'smoke', 'smoking', 'joint', 'blunt', 'pipe', 'bowl'],
                'vape': ['vaped', 'vape', 'vaping', 'vaporized', 'vapor'],
                'dab': ['dabbed', 'dab', 'dabbing', 'concentrate', 'wax', 'shatter'],
                'edible': ['edible', 'ate', 'eaten', 'gummy', 'cookie', 'brownie']
            }
            
            for method, keywords in methods.items():
                if any(keyword in text for keyword in keywords):
                    result['method'] = method
                    break
            
            if not result['method']:
                return None
            
            # Amount detection (support various formats)
            amount_patterns = [
                r'(\d+\.?\d*)\s*g',  # "0.5g", "1.2 g"
                r'(\d+\.?\d*)\s*gram',  # "0.5 gram", "point 5 grams"
                r'point\s*(\d+)',  # "point 5"
                r'(\d+)\s*mg',  # "10mg" for edibles
                r'half',  # "half gram"
                r'quarter'  # "quarter gram"
            ]
            
            amount = None
            for pattern in amount_patterns:
                match = re.search(pattern, text)
                if match:
                    if 'half' in text:
                        amount = 0.5
                    elif 'quarter' in text:
                        amount = 0.25
                    elif 'point' in pattern:
                        amount = float(match.group(1)) / 10  # "point 5" = 0.5
                    elif 'mg' in pattern:
                        amount = float(match.group(1)) / 1000  # Convert mg to g
                    else:
                        amount = float(match.group(1))
                    break
            
            if amount is None:
                return None
            
            result['amount'] = amount
            
            # Strain detection (extract words that might be strain names)
            strain_indicators = ['strain', 'blue', 'green', 'purple', 'white', 'og', 'kush', 'haze', 'diesel', 'dream', 'widow', 'skunk']
            words = text.split()
            
            strain_words = []
            for i, word in enumerate(words):
                # Look for strain name patterns
                if (word in strain_indicators or 
                    word.istitle() or 
                    (i > 0 and words[i-1] in strain_indicators)):
                    strain_words.append(word)
            
            if strain_words:
                result['strain'] = ' '.join(strain_words).title()
            
            return result
            
        except Exception as e:
            return None

    @app_commands.command(name="repeat", description="Repeat your last consumption session")
    async def repeat_last(self, interaction: discord.Interaction):
        """Quickly repeat the last consumption session."""
        try:
            user_id = interaction.user.id
            
            # Get last entry
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1)
            
            if not entries:
                await interaction.response.send_message(
                    "❌ No previous sessions found to repeat.",
                    ephemeral=True
                )
                return
            
            last_entry = entries[0]
            
            # Log identical session
            new_entry = await ConsumptionService.log_consumption(
                user_id=user_id,
                method=last_entry.method,
                amount=last_entry.amount,
                product_type='flower',  # Default to flower
                strain=last_entry.strain,
                thc_percent=last_entry.thc_percent,
                notes="Repeated last session"
            )
            
            if new_entry:
                # Handle tuple return
                if isinstance(new_entry, tuple):
                    consumption_entry, _ = new_entry
                    absorbed_thc = consumption_entry.absorbed_thc_mg
                else:
                    absorbed_thc = new_entry.absorbed_thc_mg
                
                embed = discord.Embed(
                    title="🔄 Session Repeated",
                    description="Logged identical to your last session",
                    color=0x2196F3
                )
                
                embed.add_field(
                    name="📝 Session Details",
                    value=f"**Method:** {last_entry.method.title()}\n"
                          f"**Amount:** {last_entry.amount}g\n"
                          f"**Strain:** {last_entry.strain or 'Not specified'}\n"
                          f"**THC Absorbed:** {absorbed_thc:.1f}mg",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to repeat session. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error repeating session: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="remind", description="Set smart consumption reminders")
    @app_commands.describe(
        when="When to remind: 'in 2 hours', 'at 6pm', 'daily at 8am'",
        message="Custom reminder message (optional)"
    )
    async def set_reminder(
        self, 
        interaction: discord.Interaction, 
        when: str,
        message: Optional[str] = None
    ):
        """Set smart consumption reminders."""
        try:
            user_id = interaction.user.id
            
            # Parse the "when" parameter
            reminder_time = await self._parse_reminder_time(when.lower())
            
            if not reminder_time:
                embed = discord.Embed(
                    title="❌ Couldn't Parse Time",
                    description=f"I couldn't understand: \"{when}\"",
                    color=0xF44336
                )
                embed.add_field(
                    name="💡 Try These Formats",
                    value="• \"in 2 hours\"\n"
                          "• \"in 30 minutes\"\n"
                          "• \"at 6pm\"\n"
                          "• \"tomorrow at 9am\"\n"
                          "• \"daily at 8am\"",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create reminder
            reminder_message = message or f"💊 Cannabis medication reminder"
            
            # Use notification service to create smart reminder
            alert = await NotificationService.create_smart_reminder(
                user_id=user_id,
                reminder_type='medication',
                message=reminder_message,
                patterns={}
            )
            
            if alert:
                embed = discord.Embed(
                    title="✅ Reminder Set",
                    description=f"I'll remind you: **{when}**",
                    color=0x4CAF50
                )
                
                embed.add_field(
                    name="📱 Reminder Details",
                    value=f"**Message:** {reminder_message}\n"
                          f"**Type:** Smart medication reminder\n"
                          f"**Status:** Active",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Tip",
                    value="Reminders adapt to your usage patterns for optimal timing",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to set reminder. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting reminder: {str(e)}",
                ephemeral=True
            )

    async def _parse_reminder_time(self, when: str) -> Optional[datetime]:
        """Parse reminder time from natural language."""
        try:
            now = datetime.now()
            
            # "in X hours/minutes"
            if 'in' in when:
                if 'hour' in when:
                    hours_match = re.search(r'(\d+)\s*hour', when)
                    if hours_match:
                        hours = int(hours_match.group(1))
                        return now + timedelta(hours=hours)
                
                if 'minute' in when:
                    minutes_match = re.search(r'(\d+)\s*minute', when)
                    if minutes_match:
                        minutes = int(minutes_match.group(1))
                        return now + timedelta(minutes=minutes)
            
            # "at Xpm/am"
            if 'at' in when:
                time_match = re.search(r'(\d+)\s*(pm|am)', when)
                if time_match:
                    hour = int(time_match.group(1))
                    period = time_match.group(2)
                    
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    
                    reminder_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                    
                    # If time has passed today, schedule for tomorrow
                    if reminder_time <= now:
                        reminder_time += timedelta(days=1)
                    
                    return reminder_time
            
            # "tomorrow"
            if 'tomorrow' in when:
                tomorrow = now + timedelta(days=1)
                # Default to 9am if no time specified
                return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            
            return None
            
        except Exception:
            return None

async def setup(bot):
    await bot.add_cog(MobileCommands(bot))
