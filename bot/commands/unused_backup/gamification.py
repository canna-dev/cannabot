"""Gamification features including achievements, streaks, and leaderboards."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json

from bot.database.models import ConsumptionEntry, StashItem, StrainNote, User
from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

# Achievement definitions
ACHIEVEMENTS = {
    "first_log": {
        "name": "🌱 First Steps",
        "description": "Log your first consumption session",
        "icon": "🌱",
        "points": 10
    },
    "week_streak": {
        "name": "📅 Weekly Warrior",
        "description": "Log consumption for 7 days in a row",
        "icon": "📅",
        "points": 50
    },
    "strain_explorer": {
        "name": "🌿 Strain Explorer",
        "description": "Try 10 different strains",
        "icon": "🌿",
        "points": 100
    },
    "method_master": {
        "name": "🔥 Method Master", 
        "description": "Use 5 different consumption methods",
        "icon": "🔥",
        "points": 75
    },
    "reviewer": {
        "name": "⭐ Strain Reviewer",
        "description": "Write 25 strain notes",
        "icon": "⭐",
        "points": 150
    },
    "efficient": {
        "name": "⚡ Efficiency Expert",
        "description": "Maintain 80%+ bioavailability efficiency for a week",
        "icon": "⚡",
        "points": 200
    },
    "moderate": {
        "name": "🎯 Mindful Consumer",
        "description": "Stay under personal daily limit for 30 days",
        "icon": "🎯",
        "points": 300
    },
    "collector": {
        "name": "📦 Stash Collector",
        "description": "Maintain 20+ stash items",
        "icon": "📦",
        "points": 125
    },
    "centurion": {
        "name": "💯 Centurion",
        "description": "Log 100 consumption sessions",
        "icon": "💯",
        "points": 500
    },
    "medical_warrior": {
        "name": "🏥 Medical Warrior",
        "description": "Log 50 medical consumption sessions",
        "icon": "🏥",
        "points": 250
    }
}

class GamificationCommands(commands.Cog):
    """Gamification features for user engagement."""
    
    def __init__(self, bot):
        self.bot = bot

    game_group = app_commands.Group(name="game", description="Achievements, streaks, and gamification features")

    @game_group.command(name="profile", description="View your cannabis tracking profile and achievements")
    async def view_profile(self, interaction: discord.Interaction):
        """View user's gamification profile."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get user data
            all_entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            stash_items = await StashService.get_stash_items(user_id)
            strain_notes = await StrainNote.get_user_notes(user_id)
            
            # Calculate basic stats
            total_sessions = len(all_entries)
            total_thc = sum(e.absorbed_thc_mg for e in all_entries)
            unique_strains = len(set(e.strain for e in all_entries if e.strain))
            unique_methods = len(set(e.method for e in all_entries))
            
            # Calculate level and XP
            achievements_earned = await self._check_achievements(user_id)
            total_points = sum(ACHIEVEMENTS[ach]["points"] for ach in achievements_earned)
            level = min(1 + total_points // 100, 50)  # Max level 50
            
            # Current streak
            current_streak = await self._calculate_current_streak(user_id)
            
            embed = discord.Embed(
                title=f"🎮 {interaction.user.display_name}'s Cannabis Profile",
                color=0x9C27B0
            )

            # Profile overview
            embed.add_field(
                name="📊 Level & XP",
                value=f"**Level:** {level}\n**XP:** {total_points} points\n**Achievements:** {len(achievements_earned)}/{len(ACHIEVEMENTS)}",
                inline=True
            )

            embed.add_field(
                name="🔥 Current Streak",
                value=f"**{current_streak} days**\n{'🔥' * min(current_streak, 10)}",
                inline=True
            )

            embed.add_field(
                name="📈 Statistics",
                value=f"**Sessions:** {total_sessions}\n**THC Consumed:** {total_thc:.0f}mg\n**Strains Tried:** {unique_strains}",
                inline=True
            )

            # Recent achievements (last 3)
            if achievements_earned:
                recent_achievements = achievements_earned[-3:]
                achievement_text = "\n".join([
                    f"{ACHIEVEMENTS[ach]['icon']} {ACHIEVEMENTS[ach]['name']}"
                    for ach in recent_achievements
                ])
                embed.add_field(
                    name="🏆 Recent Achievements",
                    value=achievement_text,
                    inline=False
                )

            # Progress towards next achievements
            next_achievements = await self._get_next_achievements(user_id)
            if next_achievements:
                progress_text = "\n".join([
                    f"{ach['icon']} {ach['name']}: {ach['progress']}"
                    for ach in next_achievements[:3]
                ])
                embed.add_field(
                    name="🎯 Next Goals",
                    value=progress_text,
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error loading profile: {str(e)}", 
                ephemeral=True
            )

    @game_group.command(name="achievements", description="View all achievements and your progress")
    async def view_achievements(self, interaction: discord.Interaction):
        """View all available achievements."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            achievements_earned = await self._check_achievements(user_id)
            
            embed = discord.Embed(
                title="🏆 Cannabis Tracking Achievements",
                color=0xFF9800
            )

            # Separate earned and unearned
            earned_text = ""
            unearned_text = ""
            
            for ach_id, ach_data in ACHIEVEMENTS.items():
                icon = ach_data["icon"]
                name = ach_data["name"]
                desc = ach_data["description"]
                points = ach_data["points"]
                
                if ach_id in achievements_earned:
                    earned_text += f"✅ {icon} **{name}** ({points} XP)\n    {desc}\n\n"
                else:
                    unearned_text += f"⬜ {icon} **{name}** ({points} XP)\n    {desc}\n\n"

            if earned_text:
                embed.add_field(
                    name=f"🏆 Earned ({len(achievements_earned)}/{len(ACHIEVEMENTS)})",
                    value=earned_text.strip(),
                    inline=False
                )

            if unearned_text:
                embed.add_field(
                    name="🎯 Still Working On",
                    value=unearned_text.strip(),
                    inline=False
                )

            total_points = sum(ACHIEVEMENTS[ach]["points"] for ach in achievements_earned)
            embed.set_footer(text=f"Total XP: {total_points} points")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error loading achievements: {str(e)}", 
                ephemeral=True
            )

    @game_group.command(name="streaks", description="View your logging streaks and consistency")
    async def view_streaks(self, interaction: discord.Interaction):
        """View consumption logging streaks."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get consumption history
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=365)  # Last year
            
            if not entries:
                embed = discord.Embed(
                    title="🔥 Streak Tracker",
                    description="No consumption logged yet! Start tracking to build streaks.",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Calculate streaks
            current_streak = await self._calculate_current_streak(user_id)
            longest_streak = await self._calculate_longest_streak(user_id)
            
            # Calculate consistency
            days_with_logs = set()
            for entry in entries:
                if entry.timestamp:
                    days_with_logs.add(entry.timestamp.date())
            
            # Weekly consistency (last 8 weeks)
            weekly_consistency = []
            for week in range(8):
                week_start = datetime.now() - timedelta(days=(week + 1) * 7)
                week_end = datetime.now() - timedelta(days=week * 7)
                
                week_days = {week_start.date() + timedelta(days=i) for i in range(7)}
                week_logged_days = week_days.intersection(days_with_logs)
                
                consistency = len(week_logged_days) / 7
                weekly_consistency.append(consistency)

            avg_weekly_consistency = sum(weekly_consistency) / len(weekly_consistency) if weekly_consistency else 0

            embed = discord.Embed(
                title="🔥 Streak Tracker",
                color=0xFF5722
            )

            # Streak info
            streak_emoji = "🔥" * min(current_streak, 10)
            embed.add_field(
                name="📈 Current Streak",
                value=f"**{current_streak} days**\n{streak_emoji}",
                inline=True
            )

            embed.add_field(
                name="🏆 Longest Streak",
                value=f"**{longest_streak} days**",
                inline=True
            )

            embed.add_field(
                name="📅 This Week",
                value=f"**{len([d for d in days_with_logs if (datetime.now().date() - d).days < 7])}/7 days**",
                inline=True
            )

            # Consistency metrics
            embed.add_field(
                name="📊 8-Week Consistency",
                value=f"**{avg_weekly_consistency:.1%}**\n" + 
                      "".join(["🟢" if c >= 0.7 else "🟡" if c >= 0.4 else "🔴" for c in weekly_consistency[::-1]]),
                inline=False
            )

            # Streak rewards/motivation
            if current_streak >= 7:
                embed.add_field(
                    name="🎉 Streak Bonus",
                    value="You're on fire! Keep it up for streak achievements!",
                    inline=False
                )
            elif current_streak >= 3:
                embed.add_field(
                    name="🎯 Keep Going",
                    value=f"Just {7 - current_streak} more days for the Weekly Warrior achievement!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="💪 Start Building",
                    value="Log consistently for 7 days to earn your first streak achievement!",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error loading streaks: {str(e)}", 
                ephemeral=True
            )

    @game_group.command(name="leaderboard", description="View server leaderboards (if sharing enabled)")
    @app_commands.describe(category="Leaderboard category to view")
    @app_commands.choices(category=[
        app_commands.Choice(name="Total Sessions", value="sessions"),
        app_commands.Choice(name="Current Streak", value="streak"),
        app_commands.Choice(name="Achievements", value="achievements"),
        app_commands.Choice(name="Strain Explorer", value="strains"),
        app_commands.Choice(name="Method Master", value="methods")
    ])
    async def view_leaderboard(
        self,
        interaction: discord.Interaction,
        category: str = "sessions"
    ):
        """View server leaderboards."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Check if this is a DM
            if not interaction.guild:
                embed = discord.Embed(
                    title="🏆 Leaderboards",
                    description="Leaderboards are only available in servers, not DMs.",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            guild_id = interaction.guild.id
            
            # Get all guild members who have logged consumption and enabled sharing
            # For demo purposes, we'll show sample data since we don't have server-wide data storage yet
            
            embed = discord.Embed(
                title=f"🏆 Server Leaderboard - {category.title()}",
                description="*Leaderboards show users who have enabled global sharing*",
                color=0xFFD700
            )

            # Placeholder leaderboard data
            sample_data = {
                "sessions": [
                    ("CannaExpert#1234", 156),
                    ("GreenThumb#5678", 142),
                    ("StonedScientist#9012", 128),
                    (interaction.user.display_name, 89),
                    ("ChillVibes#3456", 67)
                ],
                "streak": [
                    ("ConsistentUser#7890", 23),
                    ("DailyToker#2468", 18),
                    (interaction.user.display_name, 12),
                    ("WeekendWarrior#1357", 8),
                    ("CasualSmoker#9753", 5)
                ],
                "achievements": [
                    ("AchievementHunter#4682", 8),
                    ("CompletionistCanna#1593", 7),
                    (interaction.user.display_name, 4),
                    ("NewbieCannabis#7410", 3),
                    ("JustStarted#8520", 1)
                ],
                "strains": [
                    ("StrainConnoisseur#9630", 47),
                    ("VarietySeeker#7412", 39),
                    (interaction.user.display_name, 23),
                    ("MonoStrain#8520", 12),
                    ("BasicBud#7410", 8)
                ],
                "methods": [
                    ("MethodMaster#8520", 6),
                    ("VersatileVaper#7410", 5),
                    (interaction.user.display_name, 4),
                    ("OldSchool#9630", 3),
                    ("SingleMethod#1593", 2)
                ]
            }

            leaderboard_data = sample_data.get(category, sample_data["sessions"])
            
            leaderboard_text = ""
            for i, (username, value) in enumerate(leaderboard_data[:10], 1):
                medal = ["🥇", "🥈", "🥉", "🏅", "🏅"][min(i-1, 4)]
                
                if category == "sessions":
                    value_text = f"{value} sessions"
                elif category == "streak":
                    value_text = f"{value} days"
                elif category == "achievements":
                    value_text = f"{value} achievements"
                elif category == "strains":
                    value_text = f"{value} strains"
                elif category == "methods":
                    value_text = f"{value} methods"
                else:
                    value_text = str(value)
                
                leaderboard_text += f"{medal} **{i}.** {username} - {value_text}\n"

            embed.add_field(
                name=f"Top {len(leaderboard_data)} Users",
                value=leaderboard_text,
                inline=False
            )

            embed.add_field(
                name="ℹ️ Note",
                value="This is a preview of server leaderboards. Full implementation requires server-wide data storage and user privacy settings.",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error loading leaderboard: {str(e)}", 
                ephemeral=True
            )

    @game_group.command(name="challenges", description="View weekly and monthly challenges")
    async def view_challenges(self, interaction: discord.Interaction):
        """View current challenges."""
        try:
            user_id = interaction.user.id
            
            # Get current week/month
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday())
            month_start = now.replace(day=1)
            
            embed = discord.Embed(
                title="🎯 Weekly & Monthly Challenges",
                color=0x673AB7
            )

            # Weekly challenges
            weekly_challenges = [
                {
                    "name": "🔥 Consistency King",
                    "description": "Log consumption 5 days this week",
                    "progress": "3/5 days",
                    "reward": "25 XP + Streak bonus"
                },
                {
                    "name": "🌿 Strain Sampler",
                    "description": "Try 3 different strains this week",
                    "progress": "1/3 strains",
                    "reward": "40 XP"
                },
                {
                    "name": "⭐ Quality Control",
                    "description": "Rate 10 consumption sessions",
                    "progress": "7/10 ratings",
                    "reward": "30 XP"
                }
            ]

            weekly_text = ""
            for challenge in weekly_challenges:
                weekly_text += f"**{challenge['name']}**\n"
                weekly_text += f"{challenge['description']}\n"
                weekly_text += f"Progress: {challenge['progress']}\n"
                weekly_text += f"Reward: {challenge['reward']}\n\n"

            embed.add_field(
                name=f"📅 This Week ({week_start.strftime('%m/%d')} - {(week_start + timedelta(days=6)).strftime('%m/%d')})",
                value=weekly_text.strip(),
                inline=False
            )

            # Monthly challenges
            monthly_challenges = [
                {
                    "name": "💯 Century Club",
                    "description": "Log 100 total sessions",
                    "progress": "67/100 sessions",
                    "reward": "200 XP + Special badge"
                },
                {
                    "name": "🏥 Medical Marvel",
                    "description": "Log 20 medical sessions this month",
                    "progress": "8/20 sessions",
                    "reward": "150 XP"
                },
                {
                    "name": "📝 Strain Scholar",
                    "description": "Write detailed notes for 15 strains",
                    "progress": "11/15 notes",
                    "reward": "100 XP + Knowledge badge"
                }
            ]

            monthly_text = ""
            for challenge in monthly_challenges:
                monthly_text += f"**{challenge['name']}**\n"
                monthly_text += f"{challenge['description']}\n"
                monthly_text += f"Progress: {challenge['progress']}\n"
                monthly_text += f"Reward: {challenge['reward']}\n\n"

            embed.add_field(
                name=f"📆 This Month ({month_start.strftime('%B %Y')})",
                value=monthly_text.strip(),
                inline=False
            )

            embed.set_footer(text="Challenges reset weekly/monthly. Complete them for bonus XP!")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error loading challenges: {str(e)}", 
                ephemeral=True
            )

    async def _check_achievements(self, user_id: int) -> List[str]:
        """Check which achievements a user has earned."""
        try:
            # Get user data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            stash_items = await StashService.get_stash_items(user_id)
            strain_notes = await StrainNote.get_user_notes(user_id)
            
            earned = []
            
            # First log
            if len(entries) >= 1:
                earned.append("first_log")
            
            # Week streak
            current_streak = await self._calculate_current_streak(user_id)
            if current_streak >= 7:
                earned.append("week_streak")
            
            # Strain explorer
            unique_strains = len(set(e.strain for e in entries if e.strain))
            if unique_strains >= 10:
                earned.append("strain_explorer")
            
            # Method master
            unique_methods = len(set(e.method for e in entries))
            if unique_methods >= 5:
                earned.append("method_master")
            
            # Reviewer
            if len(strain_notes) >= 25:
                earned.append("reviewer")
            
            # Centurion
            if len(entries) >= 100:
                earned.append("centurion")
            
            # Collector
            if len(stash_items) >= 20:
                earned.append("collector")
            
            # Medical warrior
            medical_entries = [e for e in entries if e.symptom]
            if len(medical_entries) >= 50:
                earned.append("medical_warrior")
            
            return earned
            
        except Exception as e:
            print(f"Error checking achievements: {e}")
            return []

    async def _calculate_current_streak(self, user_id: int) -> int:
        """Calculate current consecutive logging streak."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=365)
            
            if not entries:
                return 0
            
            # Get unique days with logs
            logged_dates = set()
            for entry in entries:
                if entry.timestamp:
                    logged_dates.add(entry.timestamp.date())
            
            # Check consecutive days from today backwards
            current_date = datetime.now().date()
            streak = 0
            
            while current_date in logged_dates:
                streak += 1
                current_date -= timedelta(days=1)
            
            return streak
            
        except Exception as e:
            print(f"Error calculating current streak: {e}")
            return 0

    async def _calculate_longest_streak(self, user_id: int) -> int:
        """Calculate longest ever logging streak."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            if not entries:
                return 0
            
            # Get unique days with logs, sorted
            logged_dates = sorted(set(
                entry.timestamp.date() for entry in entries 
                if entry.timestamp
            ))
            
            if not logged_dates:
                return 0
            
            max_streak = 1
            current_streak = 1
            
            for i in range(1, len(logged_dates)):
                if logged_dates[i] - logged_dates[i-1] == timedelta(days=1):
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            
            return max_streak
            
        except Exception as e:
            print(f"Error calculating longest streak: {e}")
            return 0

    async def _get_next_achievements(self, user_id: int) -> List[Dict]:
        """Get progress towards next achievements."""
        try:
            # Get user data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            stash_items = await StashService.get_stash_items(user_id)
            strain_notes = await StrainNote.get_user_notes(user_id)
            
            earned = await self._check_achievements(user_id)
            next_achievements = []
            
            # Check progress for unearned achievements
            if "first_log" not in earned:
                next_achievements.append({
                    "icon": "🌱",
                    "name": "First Steps",
                    "progress": f"{len(entries)}/1 sessions"
                })
            
            if "week_streak" not in earned:
                current_streak = await self._calculate_current_streak(user_id)
                next_achievements.append({
                    "icon": "📅",
                    "name": "Weekly Warrior",
                    "progress": f"{current_streak}/7 day streak"
                })
            
            if "strain_explorer" not in earned:
                unique_strains = len(set(e.strain for e in entries if e.strain))
                next_achievements.append({
                    "icon": "🌿",
                    "name": "Strain Explorer",
                    "progress": f"{unique_strains}/10 strains"
                })
            
            if "method_master" not in earned:
                unique_methods = len(set(e.method for e in entries))
                next_achievements.append({
                    "icon": "🔥",
                    "name": "Method Master",
                    "progress": f"{unique_methods}/5 methods"
                })
            
            if "reviewer" not in earned:
                next_achievements.append({
                    "icon": "⭐",
                    "name": "Strain Reviewer",
                    "progress": f"{len(strain_notes)}/25 notes"
                })
            
            # Sort by closest to completion
            return sorted(next_achievements, key=lambda x: x["progress"], reverse=True)[:5]
            
        except Exception as e:
            print(f"Error getting next achievements: {e}")
            return []

async def setup(bot):
    await bot.add_cog(GamificationCommands(bot))
