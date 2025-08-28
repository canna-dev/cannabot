"""Community challenges and social features for CannaBot."""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import json
import logging
from dataclasses import dataclass, asdict
import random

logger = logging.getLogger(__name__)

@dataclass
class Challenge:
    """Community challenge data structure."""
    id: str
    title: str
    description: str
    challenge_type: str  # "consumption", "strain_rating", "tolerance_break", "education"
    start_date: datetime
    end_date: datetime
    target_metric: str
    target_value: float
    participants: Set[int]
    completions: Dict[int, dict]  # user_id -> completion data
    rewards: Dict[str, str]  # reward_type -> reward_description
    difficulty: str  # "easy", "medium", "hard", "expert"
    creator_id: int

@dataclass
class UserProgress:
    """User progress in challenges."""
    user_id: int
    challenge_id: str
    current_value: float
    completion_percentage: float
    last_updated: datetime
    milestones_reached: List[str]

@dataclass
class Leaderboard:
    """Leaderboard for challenges."""
    challenge_id: str
    rankings: List[Dict[str, any]]  # [{user_id, username, score, rank}]
    last_updated: datetime

class CommunityHub(commands.Cog):
    """Community challenges and social features."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_challenges = {}  # challenge_id -> Challenge
        self.user_progress = {}      # user_id -> {challenge_id -> UserProgress}
        self.leaderboards = {}       # challenge_id -> Leaderboard
        self.community_stats = {}    # Global community statistics
        
        # Auto-update tasks
        self.update_leaderboards_task.start()
        self.create_weekly_challenges.start()
        
        # Pre-defined challenge templates
        self.challenge_templates = {
            "mindful_microdose": {
                "title": "🌱 Mindful Microdosing Week",
                "description": "Complete 7 microdose sessions (≤5mg) with mindfulness tracking",
                "challenge_type": "consumption",
                "target_metric": "microdose_sessions",
                "target_value": 7,
                "difficulty": "easy",
                "duration_days": 7,
                "rewards": {
                    "completion": "🏆 Mindful Explorer Badge",
                    "top_3": "⭐ Featured in Hall of Fame"
                }
            },
            "strain_explorer": {
                "title": "🌿 Strain Explorer Challenge",
                "description": "Try and rate 5 different strains with detailed reviews",
                "challenge_type": "strain_rating",
                "target_metric": "unique_strains_rated",
                "target_value": 5,
                "difficulty": "medium",
                "duration_days": 14,
                "rewards": {
                    "completion": "🎯 Strain Connoisseur Badge",
                    "best_reviews": "📝 Review Master Title"
                }
            },
            "tolerance_reset": {
                "title": "🔄 Tolerance Break Challenge",
                "description": "Complete a 7-day tolerance break for sensitivity reset",
                "challenge_type": "tolerance_break",
                "target_metric": "consecutive_days_break",
                "target_value": 7,
                "difficulty": "hard",
                "duration_days": 7,
                "rewards": {
                    "completion": "💎 Willpower Warrior Badge",
                    "perfect_break": "🏅 Iron Will Achievement"
                }
            },
            "education_quest": {
                "title": "📚 Cannabis Education Quest",
                "description": "Learn about terpenes, effects, and methods through bot features",
                "challenge_type": "education",
                "target_metric": "knowledge_points",
                "target_value": 100,
                "difficulty": "medium",
                "duration_days": 21,
                "rewards": {
                    "completion": "🎓 Cannabis Scholar Badge",
                    "top_scorer": "🧠 Master Educator Title"
                }
            }
        }
    
    def cog_unload(self):
        self.update_leaderboards_task.cancel()
        self.create_weekly_challenges.cancel()
    
    @tasks.loop(hours=6)
    async def update_leaderboards_task(self):
        """Update leaderboards every 6 hours."""
        try:
            for challenge_id in self.active_challenges:
                await self.update_leaderboard(challenge_id)
        except Exception as e:
            logger.error(f"Leaderboard update error: {e}")
    
    @tasks.loop(hours=168)  # Weekly
    async def create_weekly_challenges(self):
        """Create new weekly challenges automatically."""
        try:
            # Create 2-3 random challenges each week
            templates = random.sample(list(self.challenge_templates.items()), 2)
            
            for template_id, template in templates:
                await self.create_challenge_from_template(template_id, template)
                
        except Exception as e:
            logger.error(f"Weekly challenge creation error: {e}")
    
    async def create_challenge_from_template(self, template_id: str, template: dict):
        """Create a new challenge from a template."""
        challenge_id = f"{template_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        challenge = Challenge(
            id=challenge_id,
            title=template["title"],
            description=template["description"],
            challenge_type=template["challenge_type"],
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=template["duration_days"]),
            target_metric=template["target_metric"],
            target_value=template["target_value"],
            participants=set(),
            completions={},
            rewards=template["rewards"],
            difficulty=template["difficulty"],
            creator_id=0  # System-created
        )
        
        self.active_challenges[challenge_id] = challenge
        logger.info(f"Created weekly challenge: {challenge.title}")
    
    async def update_leaderboard(self, challenge_id: str):
        """Update leaderboard for a specific challenge."""
        if challenge_id not in self.active_challenges:
            return
        
        challenge = self.active_challenges[challenge_id]
        rankings = []
        
        # Calculate scores for all participants
        for user_id in challenge.participants:
            progress = self.user_progress.get(user_id, {}).get(challenge_id)
            if progress:
                score = progress.current_value
                rankings.append({
                    "user_id": user_id,
                    "username": f"User_{user_id}",  # Would fetch actual username
                    "score": score,
                    "completion_percentage": progress.completion_percentage
                })
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(rankings):
            entry["rank"] = i + 1
        
        self.leaderboards[challenge_id] = Leaderboard(
            challenge_id=challenge_id,
            rankings=rankings,
            last_updated=datetime.utcnow()
        )
    
    async def join_challenge(self, user_id: int, challenge_id: str) -> bool:
        """Join a user to a challenge."""
        if challenge_id not in self.active_challenges:
            return False
        
        challenge = self.active_challenges[challenge_id]
        challenge.participants.add(user_id)
        
        # Initialize user progress
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        self.user_progress[user_id][challenge_id] = UserProgress(
            user_id=user_id,
            challenge_id=challenge_id,
            current_value=0.0,
            completion_percentage=0.0,
            last_updated=datetime.utcnow(),
            milestones_reached=[]
        )
        
        return True
    
    async def update_user_progress(self, user_id: int, challenge_id: str, 
                                 new_value: float, activity_type: str = None):
        """Update user's progress in a challenge."""
        if challenge_id not in self.active_challenges:
            return
        
        challenge = self.active_challenges[challenge_id]
        
        if user_id in self.user_progress and challenge_id in self.user_progress[user_id]:
            progress = self.user_progress[user_id][challenge_id]
            progress.current_value = new_value
            progress.completion_percentage = min(100, (new_value / challenge.target_value) * 100)
            progress.last_updated = datetime.utcnow()
            
            # Check for milestones
            await self._check_milestones(user_id, challenge_id, progress)
            
            # Check for completion
            if progress.completion_percentage >= 100:
                await self._handle_challenge_completion(user_id, challenge_id)
    
    async def _check_milestones(self, user_id: int, challenge_id: str, progress: UserProgress):
        """Check and award milestones."""
        milestones = [25, 50, 75, 90]  # Percentage milestones
        
        for milestone in milestones:
            milestone_key = f"{milestone}%"
            if (progress.completion_percentage >= milestone and 
                milestone_key not in progress.milestones_reached):
                
                progress.milestones_reached.append(milestone_key)
                # Could send milestone notification here
    
    async def _handle_challenge_completion(self, user_id: int, challenge_id: str):
        """Handle challenge completion."""
        challenge = self.active_challenges[challenge_id]
        
        completion_data = {
            "completed_at": datetime.utcnow().isoformat(),
            "final_score": self.user_progress[user_id][challenge_id].current_value,
            "completion_time": datetime.utcnow() - challenge.start_date
        }
        
        challenge.completions[user_id] = completion_data
        
        # Award completion rewards
        # Could trigger notification/badge system here
    
    @app_commands.command(name="challenges", description="🏆 View active community challenges and join competitions")
    async def view_challenges(self, interaction: discord.Interaction):
        """View active community challenges."""
        if not self.active_challenges:
            # Create some sample challenges if none exist
            await self._create_sample_challenges()
        
        embed = discord.Embed(
            title="🏆 Community Challenges",
            description="Join these exciting cannabis community challenges!",
            color=0xFF9800
        )
        
        active_count = len([c for c in self.active_challenges.values() 
                           if c.end_date > datetime.utcnow()])
        
        embed.add_field(
            name="📊 Challenge Hub Stats",
            value=f"**Active Challenges:** {active_count}\n"
                  f"**Total Participants:** {self._get_total_participants()}\n"
                  f"**Challenges Completed:** {self._get_completed_count()}",
            inline=True
        )
        
        # Show top 3 active challenges
        active_challenges = sorted(
            [c for c in self.active_challenges.values() if c.end_date > datetime.utcnow()],
            key=lambda x: len(x.participants),
            reverse=True
        )[:3]
        
        for challenge in active_challenges:
            days_left = (challenge.end_date - datetime.utcnow()).days
            difficulty_emoji = {"easy": "🌱", "medium": "🌿", "hard": "🔥", "expert": "💎"}
            
            embed.add_field(
                name=f"{difficulty_emoji.get(challenge.difficulty, '⭐')} {challenge.title}",
                value=f"{challenge.description}\n"
                      f"**Participants:** {len(challenge.participants)}\n"
                      f"**Time Left:** {days_left} days\n"
                      f"**Difficulty:** {challenge.difficulty.title()}",
                inline=True
            )
        
        # Community highlights
        embed.add_field(
            name="🌟 Community Highlights",
            value="• Weekly challenges refresh every Monday\n"
                  "• Earn badges and titles for completions\n"
                  "• Compete on leaderboards with friends\n"
                  "• Share progress and celebrate together!",
            inline=False
        )
        
        embed.set_footer(text="Community Challenges • Building connections through cannabis")
        
        view = ChallengesView(self, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _create_sample_challenges(self):
        """Create sample challenges for demonstration."""
        for template_id, template in list(self.challenge_templates.items())[:2]:
            await self.create_challenge_from_template(template_id, template)
    
    def _get_total_participants(self) -> int:
        """Get total unique participants across all challenges."""
        all_participants = set()
        for challenge in self.active_challenges.values():
            all_participants.update(challenge.participants)
        return len(all_participants)
    
    def _get_completed_count(self) -> int:
        """Get total completed challenges count."""
        return sum(len(c.completions) for c in self.active_challenges.values())
    
    @app_commands.command(name="leaderboard", description="🏅 View challenge leaderboards and rankings")
    @app_commands.describe(challenge="Choose which challenge leaderboard to view")
    async def view_leaderboard(self, interaction: discord.Interaction, challenge: str = None):
        """View challenge leaderboards."""
        if not self.active_challenges:
            embed = discord.Embed(
                title="🏅 No Active Challenges",
                description="No challenges are currently active. Check back soon for new challenges!",
                color=0x757575
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # If no specific challenge, show overview
        if not challenge:
            await self._show_leaderboard_overview(interaction)
            return
        
        # Show specific challenge leaderboard
        if challenge not in self.leaderboards:
            await self.update_leaderboard(challenge)
        
        if challenge not in self.leaderboards:
            embed = discord.Embed(
                title="🏅 Leaderboard Not Found",
                description="No leaderboard data available for this challenge.",
                color=0x757575
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        leaderboard = self.leaderboards[challenge]
        challenge_obj = self.active_challenges[challenge]
        
        embed = discord.Embed(
            title=f"🏅 {challenge_obj.title} - Leaderboard",
            description=f"Top performers in this {challenge_obj.difficulty} challenge",
            color=0xFFD700
        )
        
        # Show top 10
        top_rankings = leaderboard.rankings[:10]
        
        if top_rankings:
            leaderboard_text = ""
            for entry in top_rankings:
                rank_emoji = ["🥇", "🥈", "🥉"][entry["rank"]-1] if entry["rank"] <= 3 else f"{entry['rank']}."
                
                leaderboard_text += (
                    f"{rank_emoji} **{entry['username']}**\n"
                    f"    Score: {entry['score']:.1f} | "
                    f"Progress: {entry['completion_percentage']:.1f}%\n\n"
                )
            
            embed.add_field(
                name="🏆 Rankings",
                value=leaderboard_text,
                inline=False
            )
        else:
            embed.add_field(
                name="🏆 Rankings",
                value="No participants yet. Be the first to join!",
                inline=False
            )
        
        # Challenge info
        days_left = (challenge_obj.end_date - datetime.utcnow()).days
        embed.add_field(
            name="📋 Challenge Info",
            value=f"**Target:** {challenge_obj.target_value} {challenge_obj.target_metric}\n"
                  f"**Participants:** {len(challenge_obj.participants)}\n"
                  f"**Time Left:** {days_left} days",
            inline=True
        )
        
        # User's position
        user_rank = None
        for entry in leaderboard.rankings:
            if entry["user_id"] == interaction.user.id:
                user_rank = entry
                break
        
        if user_rank:
            embed.add_field(
                name="📍 Your Position",
                value=f"**Rank:** #{user_rank['rank']}\n"
                      f"**Score:** {user_rank['score']:.1f}\n"
                      f"**Progress:** {user_rank['completion_percentage']:.1f}%",
                inline=True
            )
        
        embed.set_footer(text=f"Last updated: {leaderboard.last_updated.strftime('%H:%M %m/%d')}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _show_leaderboard_overview(self, interaction: discord.Interaction):
        """Show overview of all leaderboards."""
        embed = discord.Embed(
            title="🏅 Challenge Leaderboards",
            description="Overview of all active challenge leaderboards",
            color=0xFFD700
        )
        
        for challenge_id, challenge in self.active_challenges.items():
            if challenge.end_date > datetime.utcnow():
                if challenge_id in self.leaderboards:
                    leaderboard = self.leaderboards[challenge_id]
                    top_user = leaderboard.rankings[0] if leaderboard.rankings else None
                    
                    embed.add_field(
                        name=f"🏆 {challenge.title}",
                        value=f"**Leader:** {top_user['username'] if top_user else 'None'}\n"
                              f"**Participants:** {len(challenge.participants)}\n"
                              f"**Days Left:** {(challenge.end_date - datetime.utcnow()).days}",
                        inline=True
                    )
        
        view = LeaderboardActionsView(self, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ChallengesView(discord.ui.View):
    """View for challenge interactions."""
    
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="🎯 Join Challenge", style=discord.ButtonStyle.success, emoji="🎯")
    async def join_challenge(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Join a challenge."""
        # Show available challenges to join
        available_challenges = [
            c for c in self.cog.active_challenges.values()
            if c.end_date > datetime.utcnow() and self.user_id not in c.participants
        ]
        
        if not available_challenges:
            embed = discord.Embed(
                title="🎯 No Available Challenges",
                description="You're already participating in all active challenges, or none are available.",
                color=0x757575
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎯 Join a Challenge",
            description="Choose a challenge to join:",
            color=0x4CAF50
        )
        
        for challenge in available_challenges[:3]:  # Show top 3
            difficulty_emoji = {"easy": "🌱", "medium": "🌿", "hard": "🔥", "expert": "💎"}
            days_left = (challenge.end_date - datetime.utcnow()).days
            
            embed.add_field(
                name=f"{difficulty_emoji.get(challenge.difficulty, '⭐')} {challenge.title}",
                value=f"{challenge.description}\n"
                      f"**Difficulty:** {challenge.difficulty.title()}\n"
                      f"**Time Left:** {days_left} days\n"
                      f"**Participants:** {len(challenge.participants)}",
                inline=True
            )
        
        # Auto-join first available challenge for demo
        if available_challenges:
            first_challenge = available_challenges[0]
            success = await self.cog.join_challenge(self.user_id, first_challenge.id)
            
            if success:
                embed.add_field(
                    name="✅ Joined Successfully!",
                    value=f"You've joined **{first_challenge.title}**!\n"
                          f"Track your progress with consumption logging.",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📊 My Progress", style=discord.ButtonStyle.primary, emoji="📊")
    async def my_progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user's progress in challenges."""
        user_challenges = self.cog.user_progress.get(self.user_id, {})
        
        if not user_challenges:
            embed = discord.Embed(
                title="📊 No Active Challenges",
                description="You're not currently participating in any challenges.\n"
                           "Use the 'Join Challenge' button to get started!",
                color=0x757575
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Your Challenge Progress",
            description="Your progress across all active challenges",
            color=0x2196F3
        )
        
        for challenge_id, progress in user_challenges.items():
            if challenge_id in self.cog.active_challenges:
                challenge = self.cog.active_challenges[challenge_id]
                days_left = (challenge.end_date - datetime.utcnow()).days
                
                progress_bar = self._create_progress_bar(progress.completion_percentage)
                
                embed.add_field(
                    name=f"🎯 {challenge.title}",
                    value=f"{progress_bar} {progress.completion_percentage:.1f}%\n"
                          f"**Progress:** {progress.current_value:.1f}/{challenge.target_value}\n"
                          f"**Time Left:** {days_left} days",
                    inline=True
                )
        
        embed.set_footer(text="Keep logging your activities to track progress!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def _create_progress_bar(self, percentage: float) -> str:
        """Create a visual progress bar."""
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"{'█' * filled}{'░' * empty}"
    
    @discord.ui.button(label="🏅 View Leaderboards", style=discord.ButtonStyle.secondary, emoji="🏅")
    async def view_leaderboards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View challenge leaderboards."""
        # This would trigger the leaderboard command
        embed = discord.Embed(
            title="🏅 Challenge Leaderboards",
            description="Use `/leaderboard` command to view detailed rankings for each challenge!",
            color=0xFFD700
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LeaderboardActionsView(discord.ui.View):
    """Actions for leaderboard interactions."""
    
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="🔄 Refresh Rankings", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_rankings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh leaderboard rankings."""
        embed = discord.Embed(
            title="🔄 Rankings Updated",
            description="Leaderboards have been refreshed with the latest data!",
            color=0x4CAF50
        )
        
        # Update all leaderboards
        for challenge_id in self.cog.active_challenges:
            await self.cog.update_leaderboard(challenge_id)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommunityHub(bot))
