"""Consumption logging commands."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime

from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService
from bot.config import CONSUMPTION_METHODS, PRODUCT_TYPES, COMMON_SYMPTOMS, EFFECT_RATING_MIN, EFFECT_RATING_MAX

# Common medical symptoms that cannabis users track
MEDICAL_SYMPTOMS = [
    "anxiety", "depression", "insomnia", "pain", "nausea", "appetite_loss",
    "migraines", "muscle_spasms", "inflammation", "ptsd", "seizures", "glaucoma",
    "arthritis", "fibromyalgia", "crohns", "epilepsy", "cancer_pain", "stress"
]

class ConsumptionCommands(commands.Cog):
    """Consumption logging slash commands."""
    
    def __init__(self, bot):
        self.bot = bot

    async def _log_consumption_helper(
        self,
        interaction: discord.Interaction,
        method: str,
        amount: float,
        product_type: str = "flower",
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Helper method for logging consumption."""
        try:
            # Validate inputs
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be positive",
                    ephemeral=True
                )
                return

            if thc_percent is not None and (thc_percent < 0 or thc_percent > 100):
                await interaction.response.send_message(
                    "❌ THC percentage must be between 0 and 100",
                    ephemeral=True
                )
                return

            if effect_rating is not None and (effect_rating < EFFECT_RATING_MIN or effect_rating > EFFECT_RATING_MAX):
                await interaction.response.send_message(
                    f"❌ Effect rating must be between {EFFECT_RATING_MIN} and {EFFECT_RATING_MAX}",
                    ephemeral=True
                )
                return

            user_id = interaction.user.id
            
            # Auto-fetch THC percentage from stash if strain is provided but THC% is not
            if strain and thc_percent is None:
                try:
                    stash_items = await StashService.get_stash_items(user_id)
                    # Find matching strain in stash (case-insensitive)
                    matching_item = next(
                        (item for item in stash_items 
                         if item.strain and item.strain.lower() == strain.lower() and item.thc_percent),
                        None
                    )
                    if matching_item:
                        thc_percent = matching_item.thc_percent
                        # Show user we auto-filled the THC%
                        auto_thc_message = f" (THC: {thc_percent}% from stash)"
                    else:
                        auto_thc_message = ""
                except Exception:
                    # If there's any error fetching from stash, just continue without auto-fill
                    auto_thc_message = ""
            else:
                auto_thc_message = ""
            
            # Log consumption
            entry, warnings = await ConsumptionService.log_consumption(
                user_id=user_id,
                product_type=product_type,
                amount=amount,
                method=method,
                strain=strain,
                thc_percent=thc_percent,
                notes=notes,
                symptom=symptom,
                effect_rating=effect_rating
            )

            # Create response embed
            embed = discord.Embed(
                title="✅ Consumption Logged",
                color=0x4CAF50
            )

            # Format the entry details
            strain_text = f" ({strain}{auto_thc_message})" if strain else ""
            unit = "mg" if product_type in ["edible", "tincture", "capsule"] else "g"
            
            embed.add_field(
                name="Session Details",
                value=f"**Method:** {method.title()}\n"
                      f"**Amount:** {amount}{unit} {product_type}{strain_text}\n"
                      f"**THC Absorbed:** {entry.absorbed_thc_mg}mg",
                inline=False
            )

            if entry.thc_percent:
                embed.add_field(
                    name="THC Content",
                    value=f"{entry.thc_percent}%",
                    inline=True
                )

            if effect_rating:
                stars = "⭐" * effect_rating
                embed.add_field(
                    name="Effect Rating",
                    value=f"{stars} {effect_rating}/5",
                    inline=True
                )

            if symptom:
                embed.add_field(
                    name="Symptom",
                    value=symptom.title(),
                    inline=True
                )

            if notes:
                embed.add_field(
                    name="Notes",
                    value=notes,
                    inline=False
                )

            # Add warnings if any
            if warnings:
                warning_text = "\n".join(warnings)
                embed.add_field(
                    name="⚠️ Warnings",
                    value=warning_text,
                    inline=False
                )
                embed.color = 0xFF9800  # Orange for warnings

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error logging consumption: {str(e)}",
                ephemeral=True
            )

    # Autocomplete methods (defined before commands that use them)
    async def strain_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for strains based on user's stash with enhanced indicators."""
        try:
            user_id = interaction.user.id
            stash_items = await StashService.get_stash_items(user_id)
            
            # Get unique strains from stash with enhanced categorization
            stash_strains = []
            for item in stash_items:
                if item.strain and current.lower() in item.strain.lower():
                    # Determine strain type indicator based on name patterns
                    strain_lower = item.strain.lower()
                    if any(indica in strain_lower for indica in ['kush', 'purple', 'bubba', 'afghan', 'northern']):
                        type_emoji = "🟣"  # Indica
                    elif any(sativa in strain_lower for sativa in ['haze', 'diesel', 'jack', 'green', 'sour']):
                        type_emoji = "🟢"  # Sativa  
                    else:
                        type_emoji = "🟡"  # Hybrid/Unknown
                    
                    # Potency indicator
                    if item.thc_percent and item.thc_percent > 25:
                        potency_emoji = "🔥"  # High potency
                    elif item.thc_percent and item.thc_percent > 15:
                        potency_emoji = "⭐"  # Medium potency
                    else:
                        potency_emoji = "🌿"  # Low potency/unknown
                    
                    stash_strains.append({
                        'strain': item.strain,
                        'thc': item.thc_percent or 0,
                        'amount': item.amount,
                        'display': f"🏪{type_emoji}{potency_emoji} {item.strain} ({item.thc_percent or '?'}% THC, {item.amount}g)"
                    })
            
            # Sort by amount remaining (prioritize strains with more stock)
            stash_strains.sort(key=lambda x: x['amount'], reverse=True)
            
            choices = [
                app_commands.Choice(name=strain['display'][:100], value=strain['strain'])
                for strain in stash_strains[:18]  # Leave room for other options
            ]
            
            # If they're typing something not in stash, add it as an option
            if current and current.lower() not in [s['strain'].lower() for s in stash_strains]:
                choices.append(
                    app_commands.Choice(name=f"✨ {current.title()} (New Strain)", value=current.title())
                )
            
            # Add some common strains with type indicators if there's room
            if len(choices) < 25 and current:
                common_strains = [
                    ("🟡⭐ Blue Dream (Hybrid)", "Blue Dream"),
                    ("🟣🔥 OG Kush (Indica)", "OG Kush"), 
                    ("🟡⭐ Girl Scout Cookies (Hybrid)", "Girl Scout Cookies"),
                    ("🟢🔥 Green Crack (Sativa)", "Green Crack"),
                    ("🟡⭐ White Widow (Hybrid)", "White Widow"),
                    ("🟢🔥 Sour Diesel (Sativa)", "Sour Diesel"),
                    ("🟣⭐ Northern Lights (Indica)", "Northern Lights"),
                    ("🟢⭐ Jack Herer (Sativa)", "Jack Herer")
                ]
                
                for display, strain in common_strains:
                    if (current.lower() in strain.lower() and 
                        strain not in [s['strain'] for s in stash_strains] and 
                        len(choices) < 25):
                        choices.append(
                            app_commands.Choice(name=f"🌿 {display}", value=strain)
                        )
            
            return choices
            
        except Exception as e:
            # Fallback to simple text input if there's an error
            return [app_commands.Choice(name=current.title(), value=current.title())] if current else []

    async def symptom_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for symptoms."""
        matching_symptoms = [
            symptom for symptom in MEDICAL_SYMPTOMS 
            if current.lower() in symptom.lower()
        ]
        
        return [
            app_commands.Choice(name=symptom.replace("_", " ").title(), value=symptom)
            for symptom in matching_symptoms[:25]  # Discord limit
        ]

    @app_commands.command(name="smoke", description="Log a smoking session")
    @app_commands.describe(
        amount="Amount smoked in grams",
        strain="Strain name (optional, THC% auto-filled from stash)",
        thc_percent="THC percentage (optional, auto-filled if strain in stash)",
        notes="Session notes (optional)",
        symptom="Symptom being treated (optional)",
        effect_rating="Effect rating 1-5 (optional)"
    )
    @app_commands.autocomplete(strain=strain_autocomplete, symptom=symptom_autocomplete)
    async def smoke(
        self,
        interaction: discord.Interaction,
        amount: float,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Log smoking session."""
        await self._log_consumption_helper(
            interaction, "smoke", amount, "flower", strain, thc_percent, notes, symptom, effect_rating
        )

    @app_commands.command(name="vaporizer", description="Log a vaporizer session")
    @app_commands.describe(
        amount="Amount vaporized in grams",
        strain="Strain name (optional, THC% auto-filled from stash)",
        thc_percent="THC percentage (optional, auto-filled if strain in stash)",
        notes="Session notes (optional)",
        symptom="Symptom being treated (optional)",
        effect_rating="Effect rating 1-5 (optional)"
    )
    @app_commands.autocomplete(strain=strain_autocomplete, symptom=symptom_autocomplete)
    async def vaporizer(
        self,
        interaction: discord.Interaction,
        amount: float,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Log vaporizer session."""
        await self._log_consumption_helper(
            interaction, "vaporizer", amount, "flower", strain, thc_percent, notes, symptom, effect_rating
        )

    @app_commands.command(name="dab", description="Log a dabbing session")
    @app_commands.describe(
        amount="Amount dabbed in grams",
        strain="Concentrate strain (optional, THC% auto-filled from stash)",
        thc_percent="THC percentage (optional, auto-filled if strain in stash)",
        notes="Session notes (optional)",
        symptom="Symptom being treated (optional)",
        effect_rating="Effect rating 1-5 (optional)"
    )
    @app_commands.autocomplete(strain=strain_autocomplete, symptom=symptom_autocomplete)
    async def dab(
        self,
        interaction: discord.Interaction,
        amount: float,
        strain: Optional[str] = None,
        thc_percent: Optional[float] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Log dabbing session."""
        await self._log_consumption_helper(
            interaction, "dab", amount, "dab", strain, thc_percent, notes, symptom, effect_rating
        )

    @app_commands.command(name="edible", description="Log edible consumption")
    @app_commands.describe(
        dose_mg="Dose in milligrams",
        strain="Edible strain/type (optional, THC% auto-filled from stash)",
        notes="Session notes (optional)",
        symptom="Symptom being treated (optional)",
        effect_rating="Effect rating 1-5 (optional)"
    )
    @app_commands.autocomplete(strain=strain_autocomplete, symptom=symptom_autocomplete)
    async def edible(
        self,
        interaction: discord.Interaction,
        dose_mg: float,
        strain: Optional[str] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Log edible consumption."""
        # For edibles, the dose is already in mg, so we need to convert to THC percentage
        # Assume the dose_mg is the actual THC content
        amount_g = dose_mg / 1000  # Convert mg to grams for calculation
        thc_percent = 100.0  # 100% since dose_mg is pure THC content
        
        await self._log_consumption_helper(
            interaction, "edible", amount_g, "edible", strain, thc_percent, notes, symptom, effect_rating
        )

    @app_commands.command(name="tincture", description="Log tincture consumption")
    @app_commands.describe(
        dose_mg="Dose in milligrams THC",
        notes="Session notes (optional)",
        symptom="Symptom being treated (optional)",
        effect_rating="Effect rating 1-5 (optional)"
    )
    @app_commands.autocomplete(symptom=symptom_autocomplete)
    async def tincture(
        self,
        interaction: discord.Interaction,
        dose_mg: float,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Log tincture consumption."""
        # Similar to edibles, convert mg dose to calculation format
        amount_g = dose_mg / 1000
        thc_percent = 100.0
        
        await self._log_consumption_helper(
            interaction, "tincture", amount_g, "tincture", None, thc_percent, notes, symptom, effect_rating
        )

    @app_commands.command(name="capsule", description="Log capsule consumption")
    @app_commands.describe(
        dose_mg="Dose in milligrams THC",
        strain="Capsule strain/type (optional, THC% auto-filled from stash)",
        notes="Session notes (optional)",
        symptom="Symptom being treated (optional)",
        effect_rating="Effect rating 1-5 (optional)"
    )
    @app_commands.autocomplete(strain=strain_autocomplete, symptom=symptom_autocomplete)
    async def capsule(
        self,
        interaction: discord.Interaction,
        dose_mg: float,
        strain: Optional[str] = None,
        notes: Optional[str] = None,
        symptom: Optional[str] = None,
        effect_rating: Optional[int] = None
    ):
        """Log capsule consumption."""
        # Similar to edibles, convert mg dose to calculation format
        amount_g = dose_mg / 1000
        thc_percent = 100.0
        
        await self._log_consumption_helper(
            interaction, "capsule", amount_g, "capsule", strain, thc_percent, notes, symptom, effect_rating
        )

async def setup(bot):
    await bot.add_cog(ConsumptionCommands(bot))
