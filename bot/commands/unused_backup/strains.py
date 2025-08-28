"""Strain notes and journaling commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import random

from bot.database.models import StrainNote
from bot.config import EFFECT_RATING_MIN, EFFECT_RATING_MAX

class StrainCommands(commands.Cog):
    """Strain journaling and notes slash commands."""
    
    def __init__(self, bot):
        self.bot = bot

    note_group = app_commands.Group(name="note", description="Manage strain notes and reviews")

    @note_group.command(name="add", description="Add a note/review for a strain")
    @app_commands.describe(
        strain="Name of the strain",
        effect_rating="Effect rating 1-5 stars",
        notes="Your detailed notes about this strain"
    )
    async def add_note(
        self,
        interaction: discord.Interaction,
        strain: str,
        effect_rating: int,
        notes: Optional[str] = None
    ):
        """Add a strain note."""
        try:
            if effect_rating < EFFECT_RATING_MIN or effect_rating > EFFECT_RATING_MAX:
                await interaction.response.send_message(
                    f"❌ Effect rating must be between {EFFECT_RATING_MIN} and {EFFECT_RATING_MAX}",
                    ephemeral=True
                )
                return

            user_id = interaction.user.id
            
            # Create strain note
            strain_note = await StrainNote.create(
                user_id=user_id,
                strain=strain.strip().title(),
                effect_rating=effect_rating,
                notes=notes
            )

            stars = "⭐" * effect_rating
            embed = discord.Embed(
                title="📝 Strain Note Added",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="🌿 Strain",
                value=strain_note.strain,
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating", 
                value=f"{stars} {effect_rating}/5",
                inline=True
            )
            
            if notes:
                embed.add_field(
                    name="📝 Notes",
                    value=notes,
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error adding strain note: {str(e)}", 
                ephemeral=True
            )

    @note_group.command(name="view", description="View notes for a specific strain")
    @app_commands.describe(strain="Name of the strain to view notes for")
    async def view_notes(
        self,
        interaction: discord.Interaction,
        strain: str
    ):
        """View strain notes."""
        try:
            user_id = interaction.user.id
            notes = await StrainNote.get_user_notes(user_id, strain.strip().title())

            if not notes:
                embed = discord.Embed(
                    title="📝 Strain Notes",
                    description=f"No notes found for **{strain.title()}**",
                    color=0x9E9E9E
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title=f"📝 Notes for {strain.title()}",
                color=0x2196F3
            )

            # Calculate average rating
            avg_rating = sum(note.effect_rating for note in notes if note.effect_rating) / len(notes)
            avg_stars = "⭐" * round(avg_rating)
            
            embed.add_field(
                name="📊 Summary",
                value=f"**Average Rating:** {avg_stars} {avg_rating:.1f}/5\n**Total Notes:** {len(notes)}",
                inline=False
            )

            # Show recent notes
            for i, note in enumerate(notes[:5]):  # Show last 5 notes
                stars = "⭐" * (note.effect_rating or 0)
                note_text = note.notes or "*No notes*"
                date_str = note.created_at.strftime("%m/%d/%y") if note.created_at else "Unknown"
                
                embed.add_field(
                    name=f"Note #{i+1} - {date_str}",
                    value=f"{stars} {note.effect_rating}/5\n{note_text}",
                    inline=False
                )

            if len(notes) > 5:
                embed.set_footer(text=f"Showing 5 of {len(notes)} notes")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error viewing strain notes: {str(e)}", 
                ephemeral=True
            )

    @note_group.command(name="list", description="List all your strain notes")
    async def list_notes(self, interaction: discord.Interaction):
        """List all strain notes."""
        try:
            user_id = interaction.user.id
            all_notes = await StrainNote.get_user_notes(user_id)

            if not all_notes:
                embed = discord.Embed(
                    title="📝 Your Strain Notes",
                    description="No strain notes yet! Use `/note add` to start tracking strains.",
                    color=0x9E9E9E
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Group notes by strain
            strain_summaries = {}
            for note in all_notes:
                strain = note.strain
                if strain not in strain_summaries:
                    strain_summaries[strain] = []
                strain_summaries[strain].append(note)

            embed = discord.Embed(
                title="📝 Your Strain Library",
                color=0x2196F3
            )

            # Show summary for each strain
            for strain, notes in strain_summaries.items():
                avg_rating = sum(n.effect_rating for n in notes if n.effect_rating) / len(notes)
                stars = "⭐" * round(avg_rating)
                
                embed.add_field(
                    name=f"🌿 {strain}",
                    value=f"{stars} {avg_rating:.1f}/5 ({len(notes)} notes)",
                    inline=True
                )

            embed.set_footer(text=f"Total: {len(strain_summaries)} strains, {len(all_notes)} notes")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error listing strain notes: {str(e)}", 
                ephemeral=True
            )

    @note_group.command(name="random", description="Get a random strain recommendation from your notes")
    async def random_strain(self, interaction: discord.Interaction):
        """Get random strain recommendation."""
        try:
            user_id = interaction.user.id
            all_notes = await StrainNote.get_user_notes(user_id)

            if not all_notes:
                embed = discord.Embed(
                    title="🎲 Random Strain",
                    description="No strain notes yet! Add some notes first with `/note add`",
                    color=0x9E9E9E
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get high-rated strains (4+ stars)
            good_strains = [note for note in all_notes if note.effect_rating and note.effect_rating >= 4]
            
            if good_strains:
                chosen_note = random.choice(good_strains)
                recommendation_type = "🌟 High-Rated Recommendation"
            else:
                chosen_note = random.choice(all_notes)
                recommendation_type = "🎲 Random Selection"

            stars = "⭐" * (chosen_note.effect_rating or 0)
            
            embed = discord.Embed(
                title=recommendation_type,
                color=0xFF9800
            )
            
            embed.add_field(
                name="🌿 Strain",
                value=chosen_note.strain,
                inline=True
            )
            
            embed.add_field(
                name="⭐ Your Rating",
                value=f"{stars} {chosen_note.effect_rating}/5",
                inline=True
            )
            
            if chosen_note.notes:
                embed.add_field(
                    name="📝 Your Notes",
                    value=chosen_note.notes,
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error getting random strain: {str(e)}", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(StrainCommands(bot))
