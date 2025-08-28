"""Enhanced gamification with achievements, seasonal challenges, and smart rewards."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
import calendar

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService
from bot.database.models import ConsumptionEntry, StashItem, StrainNote, Alert

class AchievementsCommands(commands.Cog):
    """Enhanced gamification and achievement commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.seasonal_challenges = self._get_seasonal_challenges()

    def _get_seasonal_challenges(self):
        """Get seasonal challenges based on current month."""
        month = datetime.now().month
        month_name = calendar.month_name[month]
        
        # Base challenges for all seasons
        base_challenges = [
            {
                "id": "daily_tracker",
                "name": "Daily Tracker",
                "description": "Log consumption for 7 consecutive days",
                "emoji": "📅",
                "type": "streak",
                "target": 7,
                "reward": "🏆 Consistency Champion Badge + 100 XP"
            },
            {
                "id": "strain_explorer",
                "name": "Strain Explorer",
                "description": f"Try 5 different strains in {month_name}",
                "emoji": "🌿",
                "type": "variety",
                "target": 5,
                "reward": "🧪 Strain Connoisseur Badge + 150 XP"
            },
            {
                "id": "note_master",
                "name": "Note Master",
                "description": "Write detailed notes for 10 different strains",
                "emoji": "📝",
                "type": "notes",
                "target": 10,
                "reward": "📚 Knowledge Keeper Badge + 200 XP"
            }
        ]
        
        # Seasonal specific challenges
        seasonal_challenges = []
        
        if month in [12, 1, 2]:  # Winter
            seasonal_challenges = [
                {
                    "id": "winter_warrior",
                    "name": "Winter Warrior",
                    "description": "Complete 20 sessions during winter months",
                    "emoji": "❄️",
                    "type": "seasonal",
                    "target": 20,
                    "reward": "❄️ Winter Warrior Badge + 300 XP"
                },
                {
                    "id": "cozy_nights",
                    "name": "Cozy Nights",
                    "description": "Use Indica strains 15 times this winter",
                    "emoji": "🌙",
                    "type": "method",
                    "target": 15,
                    "reward": "🛋️ Cozy Connoisseur Badge + 150 XP"
                }
            ]
        elif month in [3, 4, 5]:  # Spring
            seasonal_challenges = [
                {
                    "id": "spring_renewal",
                    "name": "Spring Renewal",
                    "description": "Take a 3-day tolerance break this spring",
                    "emoji": "🌱",
                    "type": "tolerance",
                    "target": 3,
                    "reward": "🌱 Spring Renewal Badge + 250 XP"
                },
                {
                    "id": "sativa_spring",
                    "name": "Sativa Spring",
                    "description": "Use Sativa strains 20 times this spring",
                    "emoji": "🌞",
                    "type": "method",
                    "target": 20,
                    "reward": "🌞 Energetic Explorer Badge + 200 XP"
                }
            ]
        elif month in [6, 7, 8]:  # Summer
            seasonal_challenges = [
                {
                    "id": "summer_sessions",
                    "name": "Summer Sessions",
                    "description": "Complete 30 sessions during summer",
                    "emoji": "🏖️",
                    "type": "seasonal",
                    "target": 30,
                    "reward": "🏖️ Summer Chill Badge + 350 XP"
                },
                {
                    "id": "vape_vacation",
                    "name": "Vape Vacation",
                    "description": "Use vaping as primary method 25 times",
                    "emoji": "💨",
                    "type": "method",
                    "target": 25,
                    "reward": "💨 Vapor Master Badge + 200 XP"
                }
            ]
        else:  # Fall (9, 10, 11)
            seasonal_challenges = [
                {
                    "id": "harvest_celebration",
                    "name": "Harvest Celebration",
                    "description": "Add 5 new strains to your stash this fall",
                    "emoji": "🍂",
                    "type": "stash",
                    "target": 5,
                    "reward": "🍂 Harvest Master Badge + 300 XP"
                },
                {
                    "id": "cozy_hybrid",
                    "name": "Cozy Hybrid",
                    "description": "Try 10 different hybrid strains this fall",
                    "emoji": "🍁",
                    "type": "variety",
                    "target": 10,
                    "reward": "🍁 Hybrid Harmony Badge + 250 XP"
                }
            ]
        
        return base_challenges + seasonal_challenges

    async def _check_achievements(self, user_id: int) -> List[dict]:
        """Check user's progress on all achievements."""
        achievements = []
        
        # Get user data
        entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
        stash_items = await StashService.get_user_stash(user_id)
        notes = await StrainNote.get_user_notes(user_id)
        
        # Current month for seasonal challenges
        current_month = datetime.now().month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for challenge in self.seasonal_challenges:
            progress = 0
            completed = False
            
            if challenge['type'] == 'streak':
                # Check for consecutive days
                progress = await self._check_streak(entries)
                completed = progress >= challenge['target']
                
            elif challenge['type'] == 'variety':
                # Check strain variety this month
                month_entries = [e for e in entries if e.timestamp and e.timestamp >= month_start and e.strain]
                unique_strains = len(set(e.strain for e in month_entries))
                progress = unique_strains
                completed = progress >= challenge['target']
                
            elif challenge['type'] == 'notes':
                # Check strain notes
                progress = len(set(note.strain for note in notes if note.strain))
                completed = progress >= challenge['target']
                
            elif challenge['type'] == 'seasonal':
                # Check sessions this season
                season_entries = [e for e in entries if e.timestamp and e.timestamp >= month_start]
                progress = len(season_entries)
                completed = progress >= challenge['target']
                
            elif challenge['type'] == 'method':
                # Check specific consumption patterns
                if 'Indica' in challenge['description']:
                    month_entries = [e for e in entries if e.timestamp and e.timestamp >= month_start and e.strain]
                    # Would need strain type data - simplified for now
                    indica_sessions = len([e for e in month_entries if 'indica' in (e.strain or '').lower()])
                    progress = indica_sessions
                elif 'Sativa' in challenge['description']:
                    month_entries = [e for e in entries if e.timestamp and e.timestamp >= month_start and e.strain]
                    sativa_sessions = len([e for e in month_entries if 'sativa' in (e.strain or '').lower()])
                    progress = sativa_sessions
                elif 'vaping' in challenge['description']:
                    month_entries = [e for e in entries if e.timestamp and e.timestamp >= month_start]
                    vape_sessions = len([e for e in month_entries if e.method == 'vape'])
                    progress = vape_sessions
                completed = progress >= challenge['target']
                
            elif challenge['type'] == 'stash':
                # Check stash additions this month (simplified - count current unique strains)
                progress = len(set(item.strain for item in stash_items if item.strain))
                completed = progress >= challenge['target']
                
            elif challenge['type'] == 'tolerance':
                # Check for tolerance breaks (simplified)
                progress = 0  # Would need break tracking
                completed = False
                
            # Calculate percentage
            percentage = min(100, (progress / challenge['target']) * 100) if challenge['target'] > 0 else 0
            
            achievements.append({
                'challenge': challenge,
                'progress': progress,
                'percentage': percentage,
                'completed': completed
            })
        
        return achievements

    async def _check_streak(self, entries: List[ConsumptionEntry]) -> int:
        """Check current consecutive day streak."""
        if not entries:
            return 0
            
        # Get unique days with consumption
        consumption_dates = set()
        for entry in entries:
            if entry.timestamp:
                consumption_dates.add(entry.timestamp.date())
        
        if not consumption_dates:
            return 0
            
        # Check streak from today backwards
        current_date = datetime.now().date()
        streak = 0
        
        while current_date in consumption_dates:
            streak += 1
            current_date -= timedelta(days=1)
            
        return streak

    @app_commands.command(name="achievements", description="View your achievements and seasonal challenges")
    async def show_achievements(self, interaction: discord.Interaction):
        """Display user achievements and progress."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            achievements = await self._check_achievements(user_id)
            
            # Separate completed and in-progress
            completed = [a for a in achievements if a['completed']]
            in_progress = [a for a in achievements if not a['completed']]
            
            embed = discord.Embed(
                title="🏆 Your Cannabis Journey Achievements",
                description=f"Season: **{calendar.month_name[datetime.now().month]}** • "
                           f"Completed: **{len(completed)}** • In Progress: **{len(in_progress)}**",
                color=0xFFD700
            )
            
            # Show completed achievements
            if completed:
                completed_text = ""
                for achievement in completed[:5]:  # Show max 5
                    challenge = achievement['challenge']
                    completed_text += f"{challenge['emoji']} **{challenge['name']}** ✅\n"
                    completed_text += f"   {challenge['description']}\n"
                    completed_text += f"   🎁 {challenge['reward']}\n\n"
                
                embed.add_field(
                    name="🏆 Completed Achievements",
                    value=completed_text.strip(),
                    inline=False
                )
            
            # Show in-progress achievements
            if in_progress:
                progress_text = ""
                for achievement in sorted(in_progress, key=lambda x: x['percentage'], reverse=True)[:5]:
                    challenge = achievement['challenge']
                    progress = achievement['progress']
                    target = challenge['target']
                    percentage = achievement['percentage']
                    
                    # Progress bar
                    filled = int(percentage / 10)
                    bar = "█" * filled + "░" * (10 - filled)
                    
                    progress_text += f"{challenge['emoji']} **{challenge['name']}**\n"
                    progress_text += f"   Progress: {progress}/{target} ({percentage:.0f}%)\n"
                    progress_text += f"   {bar}\n"
                    progress_text += f"   🎁 {challenge['reward']}\n\n"
                
                embed.add_field(
                    name="🎯 In Progress",
                    value=progress_text.strip(),
                    inline=False
                )
            
            # Show next easiest achievements
            if in_progress:
                closest = sorted(in_progress, key=lambda x: x['challenge']['target'] - x['progress'])[:3]
                next_text = ""
                
                for achievement in closest:
                    challenge = achievement['challenge']
                    remaining = challenge['target'] - achievement['progress']
                    next_text += f"{challenge['emoji']} **{challenge['name']}** - {remaining} more needed\n"
                
                embed.add_field(
                    name="🎯 Almost There!",
                    value=next_text,
                    inline=False
                )
            
            # Show monthly stats
            month_entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_entries = [e for e in month_entries if e.timestamp and e.timestamp >= month_start]
            
            if current_month_entries:
                month_sessions = len(current_month_entries)
                month_strains = len(set(e.strain for e in current_month_entries if e.strain))
                month_thc = sum(e.absorbed_thc_mg for e in current_month_entries)
                
                embed.add_field(
                    name=f"📊 {calendar.month_name[datetime.now().month]} Stats",
                    value=f"**Sessions:** {month_sessions}\n"
                          f"**Unique Strains:** {month_strains}\n"
                          f"**Total THC:** {month_thc:.1f}mg",
                    inline=True
                )
            
            embed.set_footer(text="🏆 Complete challenges to earn badges and XP • New challenges each season!")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error loading achievements: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="leaderboard", description="View community leaderboards (mock)")
    async def show_leaderboard(self, interaction: discord.Interaction):
        """Show mock community leaderboards."""
        try:
            user_id = interaction.user.id
            
            # Get user's stats for comparison
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_entries = [e for e in entries if e.timestamp and e.timestamp >= month_start]
            
            user_sessions = len(month_entries)
            user_strains = len(set(e.strain for e in month_entries if e.strain))
            
            embed = discord.Embed(
                title="🏆 Community Leaderboards",
                description=f"**{calendar.month_name[datetime.now().month]}** Monthly Rankings",
                color=0x673AB7
            )
            
            # Mock leaderboard data
            sessions_leaderboard = [
                ("🥇 CannaCaptain", 89),
                ("🥈 GreenGuru", 76),
                ("🥉 HerbHero", 68),
                ("4️⃣ StonerSage", 45),
                ("5️⃣ TrichomeTitan", 42),
                (f"👤 {interaction.user.display_name}", user_sessions)
            ]
            
            strains_leaderboard = [
                ("🥇 StrainScout", 23),
                ("🥈 VarietyVanguard", 19),
                ("🥉 FlavorFinder", 16),
                ("4️⃣ TerpeneTaster", 14),
                ("5️⃣ CultivarCollector", 12),
                (f"👤 {interaction.user.display_name}", user_strains)
            ]
            
            # Sessions leaderboard
            sessions_text = "\n".join([
                f"{name}: **{count}** sessions"
                for name, count in sessions_leaderboard
            ])
            
            embed.add_field(
                name="📅 Most Active (Sessions)",
                value=sessions_text,
                inline=True
            )
            
            # Strains leaderboard
            strains_text = "\n".join([
                f"{name}: **{count}** strains"
                for name, count in strains_leaderboard
            ])
            
            embed.add_field(
                name="🌿 Strain Explorer (Unique Strains)",
                value=strains_text,
                inline=True
            )
            
            # Weekly challenges
            weekly_challenges = [
                "🎯 **Mindful Monday**: Rate all your sessions this week",
                "🌿 **Strain Tuesday**: Try a new strain today",
                "🔬 **Wiki Wednesday**: Research and note a strain's terpenes",
                "📈 **Tolerance Thursday**: Check your tolerance trends",
                "🎮 **Fun Friday**: Complete an achievement challenge"
            ]
            
            current_day = datetime.now().weekday()
            today_challenge = weekly_challenges[current_day % len(weekly_challenges)]
            
            embed.add_field(
                name="🗓️ Today's Community Challenge",
                value=today_challenge,
                inline=False
            )
            
            # Community achievements
            embed.add_field(
                name="🏆 This Month's Community Goals",
                value="🎯 **1,000 Community Sessions** (Progress: 847/1000)\n"
                      "🌿 **200 Unique Strains Tried** (Progress: 156/200)\n"
                      "📝 **500 Strain Notes Written** (Progress: 334/500)",
                inline=False
            )
            
            embed.set_footer(text="🌟 Rankings update daily • Compete with friends for badges and bragging rights!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error loading leaderboard: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AchievementsCommands(bot))
