"""Professional branding and theme customization system."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, Optional
import asyncio
from datetime import datetime

class BrandingThemes(commands.Cog):
    """Professional branding and customizable themes."""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_themes = {}  # Store user theme preferences
        
        # Professional color schemes
        self.themes = {
            "professional": {
                "primary": 0x2E7D32,     # Professional green
                "secondary": 0x388E3C,    # Lighter green
                "accent": 0x4CAF50,       # Bright green
                "success": 0x1B5E20,      # Dark green
                "warning": 0xFF9800,      # Orange
                "error": 0xF44336,        # Red
                "info": 0x2196F3,         # Blue
                "neutral": 0x757575       # Gray
            },
            "medical": {
                "primary": 0x1565C0,      # Medical blue
                "secondary": 0x1976D2,    # Lighter blue
                "accent": 0x2196F3,       # Bright blue
                "success": 0x388E3C,      # Green
                "warning": 0xFF9800,      # Orange
                "error": 0xD32F2F,        # Red
                "info": 0x0277BD,         # Dark blue
                "neutral": 0x616161       # Gray
            },
            "cannabis": {
                "primary": 0x2E7D32,      # Cannabis green
                "secondary": 0x388E3C,    # Medium green
                "accent": 0x66BB6A,       # Light green
                "success": 0x1B5E20,      # Dark green
                "warning": 0xFFA726,      # Amber
                "error": 0xE53935,        # Red
                "info": 0x5E35B1,         # Purple
                "neutral": 0x424242       # Dark gray
            },
            "minimal": {
                "primary": 0x424242,      # Dark gray
                "secondary": 0x616161,    # Medium gray
                "accent": 0x9E9E9E,       # Light gray
                "success": 0x4CAF50,      # Green
                "warning": 0xFF9800,      # Orange
                "error": 0xF44336,        # Red
                "info": 0x2196F3,         # Blue
                "neutral": 0x757575       # Gray
            }
        }
        
        # Professional logos and branding elements
        self.brand_elements = {
            "logo_emoji": "🌿",
            "success_emoji": "✅",
            "warning_emoji": "⚠️",
            "error_emoji": "❌",
            "info_emoji": "ℹ️",
            "loading_emoji": "⏳",
            "analytics_emoji": "📊",
            "premium_emoji": "⭐"
        }
    
    def get_user_theme(self, user_id: int) -> str:
        """Get user's preferred theme."""
        return self.user_themes.get(user_id, "professional")
    
    def get_theme_color(self, user_id: int, color_type: str = "primary") -> int:
        """Get theme color for user."""
        theme_name = self.get_user_theme(user_id)
        theme = self.themes.get(theme_name, self.themes["professional"])
        return theme.get(color_type, theme["primary"])
    
    def create_branded_embed(self, user_id: int, title: str, description: str = None, 
                           color_type: str = "primary") -> discord.Embed:
        """Create a professionally branded embed."""
        color = self.get_theme_color(user_id, color_type)
        
        embed = discord.Embed(
            title=f"{self.brand_elements['logo_emoji']} {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Professional footer
        embed.set_footer(
            text="CannaBot • Professional Cannabis Tracking",
            icon_url="https://i.imgur.com/your-logo.png"  # Replace with actual logo
        )
        
        return embed
    
    @app_commands.command(name="theme", description="🎨 Customize your CannaBot experience with professional themes")
    @app_commands.describe(
        theme="Choose your preferred visual theme",
        preview="Preview the theme before applying"
    )
    @app_commands.choices(theme=[
        app_commands.Choice(name="🏢 Professional (Default)", value="professional"),
        app_commands.Choice(name="🏥 Medical Focus", value="medical"),
        app_commands.Choice(name="🌿 Cannabis Theme", value="cannabis"),
        app_commands.Choice(name="⚪ Minimal Clean", value="minimal")
    ])
    async def customize_theme(self, interaction: discord.Interaction, 
                            theme: str, preview: bool = False):
        """Customize the visual theme of your CannaBot experience."""
        
        if preview:
            # Show theme preview
            await self._show_theme_preview(interaction, theme)
        else:
            # Apply theme
            self.user_themes[interaction.user.id] = theme
            
            embed = self.create_branded_embed(
                interaction.user.id,
                "Theme Applied Successfully",
                f"Your CannaBot experience is now using the **{theme.title()}** theme.\n\n"
                f"All future interactions will use this professional styling.",
                "success"
            )
            
            # Add theme showcase
            theme_colors = self.themes[theme]
            color_preview = "\n".join([
                f"**{color_type.title()}:** `#{hex(color)[2:].upper().zfill(6)}`"
                for color_type, color in theme_colors.items()
            ])
            
            embed.add_field(
                name="🎨 Your Theme Colors",
                value=color_preview,
                inline=True
            )
            
            embed.add_field(
                name="✨ What's New",
                value="• Consistent color scheme\n"
                      "• Professional appearance\n"
                      "• Personalized experience\n"
                      "• Enhanced readability",
                inline=True
            )
            
            view = ThemeActionsView(self, interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _show_theme_preview(self, interaction: discord.Interaction, theme: str):
        """Show a preview of the selected theme."""
        # Temporarily set theme for preview
        original_theme = self.user_themes.get(interaction.user.id, "professional")
        self.user_themes[interaction.user.id] = theme
        
        embed = self.create_branded_embed(
            interaction.user.id,
            f"Theme Preview: {theme.title()}",
            f"This is how your CannaBot will look with the **{theme.title()}** theme.",
            "primary"
        )
        
        # Show different color types
        theme_data = self.themes[theme]
        embed.add_field(
            name="🎨 Color Palette",
            value=f"**Primary:** `#{hex(theme_data['primary'])[2:].upper().zfill(6)}`\n"
                  f"**Accent:** `#{hex(theme_data['accent'])[2:].upper().zfill(6)}`\n"
                  f"**Success:** `#{hex(theme_data['success'])[2:].upper().zfill(6)}`",
            inline=True
        )
        
        embed.add_field(
            name="✨ Theme Features",
            value=f"• Professional styling\n"
                  f"• Consistent colors\n"
                  f"• Enhanced readability\n"
                  f"• Modern appearance",
            inline=True
        )
        
        # Create sample elements in theme
        success_embed = discord.Embed(
            title="✅ Success Message Sample",
            description="This is how success messages will appear.",
            color=theme_data['success']
        )
        
        warning_embed = discord.Embed(
            title="⚠️ Warning Message Sample", 
            description="This is how warnings will appear.",
            color=theme_data['warning']
        )
        
        view = ThemePreviewView(self, interaction.user.id, theme, original_theme)
        
        # Restore original theme
        if original_theme:
            self.user_themes[interaction.user.id] = original_theme
        else:
            self.user_themes.pop(interaction.user.id, None)
        
        await interaction.response.send_message(
            embed=embed, 
            view=view, 
            ephemeral=True
        )

class ThemeActionsView(discord.ui.View):
    """Theme management actions."""
    
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="🎨 Change Theme", style=discord.ButtonStyle.secondary)
    async def change_theme(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open theme selection."""
        embed = discord.Embed(
            title="🎨 Choose Your Theme",
            description="Select a professional theme for your CannaBot experience:",
            color=self.cog.get_theme_color(self.user_id)
        )
        
        themes_info = {
            "professional": "🏢 Clean, business-focused design",
            "medical": "🏥 Healthcare-inspired styling", 
            "cannabis": "🌿 Cannabis-themed colors",
            "minimal": "⚪ Simple, distraction-free"
        }
        
        for theme, description in themes_info.items():
            embed.add_field(
                name=theme.title(),
                value=description,
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔄 Reset to Default", style=discord.ButtonStyle.secondary)
    async def reset_theme(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reset to default theme."""
        self.cog.user_themes[self.user_id] = "professional"
        
        embed = self.cog.create_branded_embed(
            self.user_id,
            "Theme Reset",
            "Your theme has been reset to the default Professional theme.",
            "success"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ThemePreviewView(discord.ui.View):
    """Theme preview actions."""
    
    def __init__(self, cog, user_id: int, preview_theme: str, original_theme: str):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.preview_theme = preview_theme
        self.original_theme = original_theme
    
    @discord.ui.button(label="✅ Apply Theme", style=discord.ButtonStyle.success)
    async def apply_theme(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Apply the previewed theme."""
        self.cog.user_themes[self.user_id] = self.preview_theme
        
        embed = self.cog.create_branded_embed(
            self.user_id,
            "Theme Applied",
            f"Successfully applied the **{self.preview_theme.title()}** theme!",
            "success"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel theme preview."""
        embed = discord.Embed(
            title="Theme Preview Cancelled",
            description="No changes were made to your theme.",
            color=0x757575
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BrandingThemes(bot))
