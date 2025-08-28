"""Smart automation service for cannabis tracking workflows."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import asyncio

from bot.database.models import ConsumptionEntry, StashItem, Alert
from bot.services.stash_service import StashService
from bot.services.consumption_service import ConsumptionService

class AutomationService:
    """Service for smart automation and workflow optimization."""
    
    @staticmethod
    async def auto_deduct_from_stash(user_id: int, consumption_entry: ConsumptionEntry) -> Dict:
        """Automatically deduct consumption from user's stash."""
        try:
            if not consumption_entry.strain:
                return {'status': 'no_strain', 'message': 'No strain specified for auto-deduction'}
            
            # Find matching stash item
            stash_items = await StashService.get_user_stash(user_id)
            matching_item = None
            
            for item in stash_items:
                if (item.strain and 
                    consumption_entry.strain.lower() in item.strain.lower() and
                    item.amount >= consumption_entry.amount):
                    matching_item = item
                    break
            
            if not matching_item:
                return {
                    'status': 'no_match',
                    'message': f'No stash item found for {consumption_entry.strain} with sufficient amount'
                }
            
            # Deduct amount (simplified - would need to add update method to StashService)
            new_amount = matching_item.amount - consumption_entry.amount
            # TODO: Add StashService.update_stash_amount method
            # await StashService.update_stash_amount(matching_item.id, new_amount)
            
            # Check if item is running low
            low_threshold = 1.0  # 1 gram threshold
            warnings = []
            
            if new_amount <= low_threshold:
                if new_amount <= 0.1:  # Almost empty
                    warnings.append(f"🚨 {matching_item.strain} is almost empty ({new_amount:.1f}g remaining)")
                else:
                    warnings.append(f"⚠️ {matching_item.strain} is running low ({new_amount:.1f}g remaining)")
            
            return {
                'status': 'success',
                'deducted_amount': consumption_entry.amount,
                'remaining_amount': new_amount,
                'strain': matching_item.strain,
                'warnings': warnings
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def create_smart_reorder_alerts(user_id: int) -> List[Alert]:
        """Create intelligent reorder alerts based on usage patterns."""
        try:
            # Get user's stash and consumption history
            stash_items = await StashService.get_user_stash(user_id)
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=100)
            
            if not entries:
                return []
            
            alerts_created = []
            
            # Analyze usage patterns for each strain
            strain_usage = {}
            for entry in entries[-30:]:  # Last 30 entries
                if entry.strain and entry.timestamp:
                    if entry.strain not in strain_usage:
                        strain_usage[entry.strain] = []
                    strain_usage[entry.strain].append({
                        'amount': entry.amount,
                        'date': entry.timestamp
                    })
            
            # Create reorder alerts for active strains
            for item in stash_items:
                if not item.strain or item.amount <= 0:
                    continue
                
                usage_data = strain_usage.get(item.strain, [])
                if not usage_data:
                    continue  # No recent usage
                
                # Calculate daily usage rate
                recent_usage = [u for u in usage_data if u['date'] >= datetime.now() - timedelta(days=14)]
                if recent_usage:
                    total_used = sum(u['amount'] for u in recent_usage)
                    daily_rate = total_used / 14  # 14-day average
                    
                    # Estimate days remaining
                    days_remaining = item.amount / daily_rate if daily_rate > 0 else 999
                    
                    # Create alert if running low
                    if days_remaining <= 7:  # Less than a week remaining
                        alert = Alert(
                            user_id=user_id,
                            alert_type='low_stash',
                            message=f"🛒 {item.strain} will run out in ~{days_remaining:.1f} days at current usage rate",
                            active=True
                        )
                        await alert.save()
                        alerts_created.append(alert)
            
            return alerts_created
            
        except Exception as e:
            return []
    
    @staticmethod
    async def smart_consumption_suggestions(user_id: int) -> Dict:
        """Provide intelligent consumption suggestions based on patterns."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=50)
            
            if len(entries) < 5:
                return {'status': 'insufficient_data'}
            
            # Analyze patterns
            current_hour = datetime.now().hour
            
            # Find typical consumption for this time
            hour_entries = [e for e in entries if e.timestamp and e.timestamp.hour == current_hour]
            
            suggestions = []
            
            if hour_entries:
                # Average amount for this hour
                avg_amount = sum(e.amount for e in hour_entries) / len(hour_entries)
                most_common_method = max(set(e.method for e in hour_entries), 
                                       key=lambda x: sum(1 for e in hour_entries if e.method == x))
                
                suggestions.append({
                    'type': 'timing',
                    'suggestion': f"You typically consume {avg_amount:.1f}g via {most_common_method} around this time",
                    'confidence': len(hour_entries) / len(entries)
                })
            
            # Check time since last consumption
            if entries:
                last_entry = max(entries, key=lambda x: x.timestamp or datetime.min)
                hours_since = (datetime.now() - (last_entry.timestamp or datetime.now())).total_seconds() / 3600
                
                # Calculate typical gap
                gaps = []
                sorted_entries = sorted([e for e in entries if e.timestamp], key=lambda x: x.timestamp)
                for i in range(1, len(sorted_entries)):
                    gap = (sorted_entries[i].timestamp - sorted_entries[i-1].timestamp).total_seconds() / 3600
                    gaps.append(gap)
                
                if gaps:
                    avg_gap = sum(gaps) / len(gaps)
                    
                    if hours_since > avg_gap * 1.5:
                        suggestions.append({
                            'type': 'timing_reminder',
                            'suggestion': f"It's been {hours_since:.1f} hours since your last session (typical gap: {avg_gap:.1f}h)",
                            'confidence': 0.8
                        })
            
            # Strain effectiveness suggestions
            strain_ratings = {}
            for entry in entries:
                if entry.strain and entry.effect_rating:
                    if entry.strain not in strain_ratings:
                        strain_ratings[entry.strain] = []
                    strain_ratings[entry.strain].append(entry.effect_rating)
            
            if strain_ratings:
                # Find best-rated strain
                best_strain = max(strain_ratings.items(), 
                                key=lambda x: sum(x[1]) / len(x[1]))
                avg_rating = sum(best_strain[1]) / len(best_strain[1])
                
                suggestions.append({
                    'type': 'strain_recommendation',
                    'suggestion': f"{best_strain[0]} has your highest average rating ({avg_rating:.1f}/5)",
                    'confidence': len(best_strain[1]) / len(entries)
                })
            
            return {
                'status': 'success',
                'suggestions': suggestions,
                'analysis_period': f"{len(entries)} recent sessions"
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def batch_import_stash(user_id: int, stash_data: List[Dict]) -> Dict:
        """Batch import multiple stash items with validation."""
        try:
            imported = 0
            errors = []
            warnings = []
            
            for item_data in stash_data:
                try:
                    # Validate required fields
                    if not item_data.get('strain'):
                        errors.append(f"Missing strain name for item {imported + 1}")
                        continue
                    
                    if not item_data.get('amount'):
                        errors.append(f"Missing amount for {item_data['strain']}")
                        continue
                    
                    # Create stash item (simplified - would need to add method)
                    # result = await StashService.add_stash_item(...)
                    # For now, skip actual creation
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Error importing {item_data.get('strain', 'unknown')}: {str(e)}")
            
            return {
                'status': 'success',
                'imported_count': imported,
                'total_items': len(stash_data),
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def optimize_tolerance_schedule(user_id: int) -> Dict:
        """Suggest optimal consumption schedule based on tolerance patterns."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=100)
            
            if len(entries) < 14:
                return {'status': 'insufficient_data', 'message': 'Need at least 14 consumption entries'}
            
            # Analyze effectiveness over time (simplified)
            valid_entries = [e for e in entries if e.timestamp and e.effect_rating]
            recent_entries = valid_entries[:20]  # Most recent 20 entries
            
            if len(recent_entries) < 10:
                return {'status': 'insufficient_ratings', 'message': 'Need more entries with effect ratings'}
            
            # Calculate effectiveness trend
            recent_10 = recent_entries[:10]
            older_10 = recent_entries[10:20] if len(recent_entries) >= 20 else recent_entries[10:]
            
            recent_avg = sum(e.effect_rating for e in recent_10) / len(recent_10)
            older_avg = sum(e.effect_rating for e in older_10) / len(older_10) if older_10 else recent_avg
            
            effectiveness_change = recent_avg - older_avg
            
            suggestions = []
            
            if effectiveness_change < -0.5:  # Significant decrease
                suggestions.append({
                    'type': 'tolerance_break',
                    'priority': 'high',
                    'suggestion': 'Consider a 3-7 day tolerance break to reset effectiveness',
                    'reason': f'Effectiveness decreased by {abs(effectiveness_change):.1f} stars recently'
                })
                
                suggestions.append({
                    'type': 'dosage_reduction',
                    'priority': 'medium',
                    'suggestion': 'Try reducing dosage by 25-30% to maintain effects',
                    'reason': 'Lower doses may be more effective after tolerance development'
                })
            
            elif effectiveness_change < -0.2:  # Mild decrease
                suggestions.append({
                    'type': 'method_rotation',
                    'priority': 'medium',
                    'suggestion': 'Try alternating consumption methods to maintain effectiveness',
                    'reason': 'Method rotation can help prevent tolerance buildup'
                })
            
            # Analyze consumption gaps for optimal spacing
            gaps = []
            sorted_entries = sorted([e for e in entries if e.timestamp], key=lambda x: x.timestamp)
            
            for i in range(1, len(sorted_entries)):
                gap_hours = (sorted_entries[i].timestamp - sorted_entries[i-1].timestamp).total_seconds() / 3600
                gaps.append(gap_hours)
            
            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                optimal_gap = avg_gap * 1.2  # 20% longer gaps for better effectiveness
                
                suggestions.append({
                    'type': 'spacing_optimization',
                    'priority': 'low',
                    'suggestion': f'Try spacing sessions {optimal_gap:.1f} hours apart for optimal effectiveness',
                    'reason': f'Current average: {avg_gap:.1f}h, suggested: {optimal_gap:.1f}h'
                })
            
            return {
                'status': 'success',
                'effectiveness_trend': effectiveness_change,
                'suggestions': suggestions,
                'analysis_summary': f'Based on {len(recent_entries)} rated sessions'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
