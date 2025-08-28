"""Data export and backup functionality."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timedelta
import json
import csv
import io

from bot.database.models import ConsumptionEntry, StashItem, StrainNote, Alert, User
from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService

class ExportCommands(commands.Cog):
    """Data export and backup commands."""
    
    def __init__(self, bot):
        self.bot = bot

    export_group = app_commands.Group(name="export", description="Export and backup your cannabis tracking data")

    @export_group.command(name="consumption", description="Export consumption history")
    @app_commands.describe(
        format="Export format",
        days="Number of days to export (0 = all time)"
    )
    @app_commands.choices(format=[
        app_commands.Choice(name="CSV (Spreadsheet)", value="csv"),
        app_commands.Choice(name="JSON (Data)", value="json"),
        app_commands.Choice(name="Text (Readable)", value="text")
    ])
    async def export_consumption(
        self,
        interaction: discord.Interaction,
        format: str = "csv",
        days: int = 0
    ):
        """Export consumption data in various formats."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get consumption data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=2000)
            
            # Filter by date if specified
            if days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]
            
            if not entries:
                embed = discord.Embed(
                    title="📤 Export Consumption Data",
                    description="No consumption data found to export",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Generate export based on format
            if format == "csv":
                file_content = self._generate_csv_consumption(entries)
                filename = f"consumption_export_{datetime.now().strftime('%Y%m%d')}.csv"
                file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)
                
            elif format == "json":
                file_content = self._generate_json_consumption(entries)
                filename = f"consumption_export_{datetime.now().strftime('%Y%m%d')}.json"
                file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)
                
            else:  # text format
                file_content = self._generate_text_consumption(entries)
                filename = f"consumption_export_{datetime.now().strftime('%Y%m%d')}.txt"
                file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)

            embed = discord.Embed(
                title="📤 Consumption Data Export",
                color=0x4CAF50
            )
            
            embed.add_field(
                name="📊 Export Details",
                value=f"**Format:** {format.upper()}\n"
                      f"**Records:** {len(entries)}\n"
                      f"**Period:** {'All time' if days == 0 else f'Last {days} days'}",
                inline=False
            )

            embed.add_field(
                name="ℹ️ File Info",
                value=f"**Filename:** {filename}\n"
                      f"**Size:** {len(file_content)} characters",
                inline=False
            )

            await interaction.followup.send(embed=embed, file=file_obj, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error exporting consumption data: {str(e)}", 
                ephemeral=True
            )

    @export_group.command(name="stash", description="Export current stash inventory")
    @app_commands.describe(format="Export format")
    @app_commands.choices(format=[
        app_commands.Choice(name="CSV (Spreadsheet)", value="csv"),
        app_commands.Choice(name="JSON (Data)", value="json"),
        app_commands.Choice(name="Text (Readable)", value="text")
    ])
    async def export_stash(
        self,
        interaction: discord.Interaction,
        format: str = "csv"
    ):
        """Export stash inventory data."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            stash_items = await StashService.get_stash_items(user_id)
            
            if not stash_items:
                embed = discord.Embed(
                    title="📤 Export Stash Data",
                    description="No stash items found to export",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Generate export based on format
            if format == "csv":
                file_content = self._generate_csv_stash(stash_items)
                filename = f"stash_export_{datetime.now().strftime('%Y%m%d')}.csv"
                
            elif format == "json":
                file_content = self._generate_json_stash(stash_items)
                filename = f"stash_export_{datetime.now().strftime('%Y%m%d')}.json"
                
            else:  # text format
                file_content = self._generate_text_stash(stash_items)
                filename = f"stash_export_{datetime.now().strftime('%Y%m%d')}.txt"

            file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)

            embed = discord.Embed(
                title="📤 Stash Inventory Export",
                color=0x4CAF50
            )
            
            total_amount = sum(item.amount for item in stash_items)
            unique_strains = len(set(item.strain for item in stash_items if item.strain))
            
            embed.add_field(
                name="📊 Export Details",
                value=f"**Format:** {format.upper()}\n"
                      f"**Items:** {len(stash_items)}\n"
                      f"**Total Amount:** {total_amount:.1f}g\n"
                      f"**Unique Strains:** {unique_strains}",
                inline=False
            )

            await interaction.followup.send(embed=embed, file=file_obj, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error exporting stash data: {str(e)}", 
                ephemeral=True
            )

    @export_group.command(name="notes", description="Export strain notes and reviews")
    @app_commands.describe(format="Export format")
    @app_commands.choices(format=[
        app_commands.Choice(name="CSV (Spreadsheet)", value="csv"),
        app_commands.Choice(name="JSON (Data)", value="json"),
        app_commands.Choice(name="Text (Readable)", value="text")
    ])
    async def export_notes(
        self,
        interaction: discord.Interaction,
        format: str = "csv"
    ):
        """Export strain notes and reviews."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            notes = await StrainNote.get_user_notes(user_id)
            
            if not notes:
                embed = discord.Embed(
                    title="📤 Export Strain Notes",
                    description="No strain notes found to export",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Generate export based on format
            if format == "csv":
                file_content = self._generate_csv_notes(notes)
                filename = f"strain_notes_export_{datetime.now().strftime('%Y%m%d')}.csv"
                
            elif format == "json":
                file_content = self._generate_json_notes(notes)
                filename = f"strain_notes_export_{datetime.now().strftime('%Y%m%d')}.json"
                
            else:  # text format
                file_content = self._generate_text_notes(notes)
                filename = f"strain_notes_export_{datetime.now().strftime('%Y%m%d')}.txt"

            file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)

            embed = discord.Embed(
                title="📤 Strain Notes Export",
                color=0x4CAF50
            )
            
            unique_strains = len(set(note.strain for note in notes))
            avg_rating = sum(n.effect_rating for n in notes if n.effect_rating) / len([n for n in notes if n.effect_rating])
            
            embed.add_field(
                name="📊 Export Details",
                value=f"**Format:** {format.upper()}\n"
                      f"**Notes:** {len(notes)}\n"
                      f"**Unique Strains:** {unique_strains}\n"
                      f"**Average Rating:** {avg_rating:.1f}/5 ⭐",
                inline=False
            )

            await interaction.followup.send(embed=embed, file=file_obj, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error exporting strain notes: {str(e)}", 
                ephemeral=True
            )

    @export_group.command(name="complete", description="Export all your data (complete backup)")
    @app_commands.describe(
        format="Export format",
        days="Number of days for consumption data (0 = all time)"
    )
    @app_commands.choices(format=[
        app_commands.Choice(name="JSON (Complete Data)", value="json"),
        app_commands.Choice(name="ZIP (Multiple Files)", value="zip")
    ])
    async def export_complete(
        self,
        interaction: discord.Interaction,
        format: str = "json",
        days: int = 0
    ):
        """Export complete data backup."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Get all user data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=2000)
            stash_items = await StashService.get_stash_items(user_id)
            notes = await StrainNote.get_user_notes(user_id)
            alerts = await Alert.get_user_alerts(user_id, enabled_only=False)
            
            # Filter consumption by date if specified
            if days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]

            if format == "json":
                # Create comprehensive JSON backup
                backup_data = {
                    "export_info": {
                        "user_id": user_id,
                        "export_date": datetime.now().isoformat(),
                        "export_type": "complete_backup",
                        "period": "all_time" if days == 0 else f"last_{days}_days"
                    },
                    "consumption_entries": [
                        {
                            "id": entry.id,
                            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                            "type": entry.type,
                            "strain": entry.strain,
                            "amount": entry.amount,
                            "thc_percent": entry.thc_percent,
                            "method": entry.method,
                            "absorbed_thc_mg": entry.absorbed_thc_mg,
                            "effect_rating": entry.effect_rating,
                            "notes": entry.notes,
                            "symptom": entry.symptom
                        }
                        for entry in entries
                    ],
                    "stash_items": [
                        {
                            "id": item.id,
                            "type": item.type,
                            "strain": item.strain,
                            "amount": item.amount,
                            "thc_percent": item.thc_percent,
                            "notes": item.notes,
                            "created_at": item.created_at.isoformat() if item.created_at else None
                        }
                        for item in stash_items
                    ],
                    "strain_notes": [
                        {
                            "id": note.id,
                            "strain": note.strain,
                            "effect_rating": note.effect_rating,
                            "notes": note.notes,
                            "created_at": note.created_at.isoformat() if note.created_at else None
                        }
                        for note in notes
                    ],
                    "alerts": [
                        {
                            "id": alert.id,
                            "alert_type": alert.alert_type,
                            "threshold": alert.threshold,
                            "enabled": alert.enabled,
                            "created_at": alert.created_at.isoformat() if alert.created_at else None
                        }
                        for alert in alerts
                    ],
                    "summary": {
                        "total_consumption_entries": len(entries),
                        "total_stash_items": len(stash_items),
                        "total_strain_notes": len(notes),
                        "total_alerts": len(alerts),
                        "total_thc_consumed": sum(e.absorbed_thc_mg for e in entries),
                        "unique_strains": len(set(e.strain for e in entries if e.strain)),
                        "unique_methods": len(set(e.method for e in entries))
                    }
                }

                file_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
                filename = f"cannabot_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)

                embed = discord.Embed(
                    title="📤 Complete Data Backup",
                    color=0x4CAF50
                )
                
                embed.add_field(
                    name="📊 Backup Contents",
                    value=f"**Consumption Entries:** {len(entries)}\n"
                          f"**Stash Items:** {len(stash_items)}\n"
                          f"**Strain Notes:** {len(notes)}\n"
                          f"**Alerts:** {len(alerts)}",
                    inline=True
                )

                embed.add_field(
                    name="💾 File Details",
                    value=f"**Format:** JSON\n"
                          f"**Size:** {len(file_content):,} chars\n"
                          f"**Period:** {'All time' if days == 0 else f'Last {days} days'}",
                    inline=True
                )

                embed.add_field(
                    name="🔒 Privacy Note",
                    value="This backup contains all your personal cannabis tracking data. Keep it secure and only share with trusted applications.",
                    inline=False
                )

                await interaction.followup.send(embed=embed, file=file_obj, ephemeral=True)

            else:  # ZIP format (placeholder for future implementation)
                embed = discord.Embed(
                    title="📤 Complete Data Backup",
                    description="ZIP format export is coming soon! Use JSON format for now.",
                    color=0xFF9800
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error creating complete backup: {str(e)}", 
                ephemeral=True
            )

    @export_group.command(name="stats", description="Export usage statistics and analytics")
    async def export_stats(self, interaction: discord.Interaction):
        """Export comprehensive usage statistics."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Calculate comprehensive statistics
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            stash_items = await StashService.get_stash_items(user_id)
            notes = await StrainNote.get_user_notes(user_id)
            
            if not entries:
                embed = discord.Embed(
                    title="📊 Export Statistics",
                    description="No data available for statistics export",
                    color=0x9E9E9E
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Calculate statistics
            stats = await self._calculate_comprehensive_stats(entries, stash_items, notes)
            
            # Generate stats report
            file_content = self._generate_stats_report(stats)
            filename = f"cannabot_stats_{datetime.now().strftime('%Y%m%d')}.txt"
            file_obj = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)

            embed = discord.Embed(
                title="📊 Usage Statistics Export",
                color=0x2196F3
            )
            
            embed.add_field(
                name="📈 Report Includes",
                value="• Overall consumption patterns\n"
                      "• Method efficiency analysis\n"  
                      "• Strain preferences\n"
                      "• Time-based trends\n"
                      "• Medical usage (if applicable)",
                inline=False
            )

            embed.add_field(
                name="📊 Data Summary",
                value=f"**Sessions:** {stats['total_sessions']}\n"
                      f"**Period:** {stats['data_period']}\n"
                      f"**Total THC:** {stats['total_thc']:.0f}mg",
                inline=False
            )

            await interaction.followup.send(embed=embed, file=file_obj, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error exporting statistics: {str(e)}", 
                ephemeral=True
            )

    def _generate_csv_consumption(self, entries: list) -> str:
        """Generate CSV format consumption data."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Date", "Time", "Product_Type", "Strain", "Amount_g", "THC_Percent", 
            "Method", "Absorbed_THC_mg", "Effect_Rating", "Symptom", "Notes"
        ])
        
        # Data rows
        for entry in sorted(entries, key=lambda x: x.timestamp or datetime.min):
            timestamp = entry.timestamp or datetime.now()
            writer.writerow([
                timestamp.strftime("%Y-%m-%d"),
                timestamp.strftime("%H:%M:%S"),
                entry.type or "",
                entry.strain or "",
                entry.amount or 0,
                entry.thc_percent or "",
                entry.method or "",
                round(entry.absorbed_thc_mg, 2),
                entry.effect_rating or "",
                entry.symptom or "",
                (entry.notes or "").replace("\n", " ")
            ])
        
        return output.getvalue()

    def _generate_json_consumption(self, entries: list) -> str:
        """Generate JSON format consumption data."""
        data = []
        for entry in entries:
            data.append({
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "product_type": entry.type,
                "strain": entry.strain,
                "amount_grams": entry.amount,
                "thc_percent": entry.thc_percent,
                "method": entry.method,
                "absorbed_thc_mg": entry.absorbed_thc_mg,
                "effect_rating": entry.effect_rating,
                "symptom": entry.symptom,
                "notes": entry.notes
            })
        
        return json.dumps({
            "export_date": datetime.now().isoformat(),
            "total_entries": len(entries),
            "consumption_data": data
        }, indent=2)

    def _generate_text_consumption(self, entries: list) -> str:
        """Generate human-readable text format consumption data."""
        output = []
        output.append("CANNABIS CONSUMPTION LOG")
        output.append("=" * 50)
        output.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append(f"Total Entries: {len(entries)}")
        output.append("")
        
        for entry in sorted(entries, key=lambda x: x.timestamp or datetime.min, reverse=True):
            timestamp = entry.timestamp or datetime.now()
            output.append(f"Date: {timestamp.strftime('%Y-%m-%d %H:%M')}")
            output.append(f"Product: {entry.type}" + (f" ({entry.strain})" if entry.strain else ""))
            output.append(f"Amount: {entry.amount}g")
            if entry.thc_percent:
                output.append(f"THC: {entry.thc_percent}%")
            output.append(f"Method: {entry.method}")
            output.append(f"Absorbed THC: {entry.absorbed_thc_mg:.1f}mg")
            if entry.effect_rating:
                output.append(f"Rating: {'⭐' * entry.effect_rating} ({entry.effect_rating}/5)")
            if entry.symptom:
                output.append(f"Medical: {entry.symptom.replace('_', ' ').title()}")
            if entry.notes:
                output.append(f"Notes: {entry.notes}")
            output.append("-" * 30)
            output.append("")
        
        return "\n".join(output)

    def _generate_csv_stash(self, items: list) -> str:
        """Generate CSV format stash data."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Product_Type", "Strain", "Amount_g", "THC_Percent", "Notes", "Created_Date"])
        
        for item in items:
            writer.writerow([
                item.type or "",
                item.strain or "",
                item.amount or 0,
                item.thc_percent or "",
                (item.notes or "").replace("\n", " "),
                item.created_at.strftime("%Y-%m-%d") if item.created_at else ""
            ])
        
        return output.getvalue()

    def _generate_json_stash(self, items: list) -> str:
        """Generate JSON format stash data."""
        data = [{
            "product_type": item.type,
            "strain": item.strain,
            "amount_grams": item.amount,
            "thc_percent": item.thc_percent,
            "notes": item.notes,
            "created_date": item.created_at.isoformat() if item.created_at else None
        } for item in items]
        
        return json.dumps({
            "export_date": datetime.now().isoformat(),
            "total_items": len(items),
            "stash_inventory": data
        }, indent=2)

    def _generate_text_stash(self, items: list) -> str:
        """Generate text format stash data."""
        output = []
        output.append("CANNABIS STASH INVENTORY")
        output.append("=" * 50)
        output.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append(f"Total Items: {len(items)}")
        output.append("")
        
        # Group by type
        by_type = {}
        for item in items:
            if item.type not in by_type:
                by_type[item.type] = []
            by_type[item.type].append(item)
        
        for product_type, type_items in by_type.items():
            output.append(f"{product_type.upper()}:")
            for item in type_items:
                line = f"  • {item.amount}g"
                if item.strain:
                    line += f" - {item.strain}"
                if item.thc_percent:
                    line += f" ({item.thc_percent}% THC)"
                output.append(line)
                if item.notes:
                    output.append(f"    Notes: {item.notes}")
            output.append("")
        
        return "\n".join(output)

    def _generate_csv_notes(self, notes: list) -> str:
        """Generate CSV format strain notes."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Strain", "Rating", "Notes", "Date_Created"])
        
        for note in notes:
            writer.writerow([
                note.strain or "",
                note.effect_rating or "",
                (note.notes or "").replace("\n", " "),
                note.created_at.strftime("%Y-%m-%d") if note.created_at else ""
            ])
        
        return output.getvalue()

    def _generate_json_notes(self, notes: list) -> str:
        """Generate JSON format strain notes."""
        data = [{
            "strain": note.strain,
            "effect_rating": note.effect_rating,
            "notes": note.notes,
            "created_date": note.created_at.isoformat() if note.created_at else None
        } for note in notes]
        
        return json.dumps({
            "export_date": datetime.now().isoformat(),
            "total_notes": len(notes),
            "strain_notes": data
        }, indent=2)

    def _generate_text_notes(self, notes: list) -> str:
        """Generate text format strain notes."""
        output = []
        output.append("STRAIN NOTES & REVIEWS")
        output.append("=" * 50)
        output.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append(f"Total Notes: {len(notes)}")
        output.append("")
        
        # Group by strain
        by_strain = {}
        for note in notes:
            if note.strain not in by_strain:
                by_strain[note.strain] = []
            by_strain[note.strain].append(note)
        
        for strain, strain_notes in by_strain.items():
            output.append(f"🌿 {strain}")
            output.append("-" * 20)
            
            for note in sorted(strain_notes, key=lambda x: x.created_at or datetime.min, reverse=True):
                date_str = note.created_at.strftime("%Y-%m-%d") if note.created_at else "Unknown"
                rating_str = "⭐" * (note.effect_rating or 0) if note.effect_rating else "Not rated"
                
                output.append(f"Date: {date_str}")
                output.append(f"Rating: {rating_str}")
                if note.notes:
                    output.append(f"Notes: {note.notes}")
                output.append("")
            
            output.append("")
        
        return "\n".join(output)

    async def _calculate_comprehensive_stats(self, entries: list, stash_items: list, notes: list) -> dict:
        """Calculate comprehensive usage statistics."""
        if not entries:
            return {"total_sessions": 0, "data_period": "No data", "total_thc": 0}
        
        # Basic stats
        total_sessions = len(entries)
        total_thc = sum(e.absorbed_thc_mg for e in entries)
        
        # Date range
        timestamps = [e.timestamp for e in entries if e.timestamp]
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            data_period = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
        else:
            data_period = "Unknown"
        
        # Method analysis
        method_counts = {}
        method_thc = {}
        for entry in entries:
            method_counts[entry.method] = method_counts.get(entry.method, 0) + 1
            method_thc[entry.method] = method_thc.get(entry.method, 0) + entry.absorbed_thc_mg
        
        # Strain analysis
        strain_counts = {}
        for entry in entries:
            if entry.strain:
                strain_counts[entry.strain] = strain_counts.get(entry.strain, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "total_thc": total_thc,
            "data_period": data_period,
            "method_counts": method_counts,
            "method_thc": method_thc,
            "strain_counts": strain_counts,
            "stash_items": len(stash_items),
            "strain_notes": len(notes)
        }

    def _generate_stats_report(self, stats: dict) -> str:
        """Generate comprehensive statistics report."""
        output = []
        output.append("CANNABIS USAGE STATISTICS REPORT")
        output.append("=" * 60)
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Data Period: {stats['data_period']}")
        output.append("")
        
        output.append("OVERVIEW")
        output.append("-" * 20)
        output.append(f"Total Sessions: {stats['total_sessions']}")
        output.append(f"Total THC Consumed: {stats['total_thc']:.1f}mg")
        if stats['total_sessions'] > 0:
            output.append(f"Average per Session: {stats['total_thc']/stats['total_sessions']:.1f}mg")
        output.append(f"Current Stash Items: {stats['stash_items']}")
        output.append(f"Strain Notes Written: {stats['strain_notes']}")
        output.append("")
        
        if stats.get('method_counts'):
            output.append("CONSUMPTION METHODS")
            output.append("-" * 20)
            for method, count in sorted(stats['method_counts'].items(), key=lambda x: x[1], reverse=True):
                thc = stats['method_thc'].get(method, 0)
                avg_thc = thc / count if count > 0 else 0
                percentage = (count / stats['total_sessions']) * 100
                output.append(f"{method.title()}: {count} sessions ({percentage:.1f}%) - {avg_thc:.1f}mg avg")
            output.append("")
        
        if stats.get('strain_counts'):
            output.append("TOP STRAINS")
            output.append("-" * 20)
            top_strains = sorted(stats['strain_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
            for strain, count in top_strains:
                percentage = (count / stats['total_sessions']) * 100
                output.append(f"{strain}: {count} sessions ({percentage:.1f}%)")
            output.append("")
        
        output.append("NOTES")
        output.append("-" * 20)
        output.append("This report is generated from your CannaBot tracking data.")
        output.append("Use this information to understand your consumption patterns.")
        output.append("Always consume responsibly and follow local laws.")
        
        return "\n".join(output)

async def setup(bot):
    await bot.add_cog(ExportCommands(bot))
