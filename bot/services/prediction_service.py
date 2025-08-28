"""Advanced prediction service for usage patterns and stash management."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bot.services.consumption_service import ConsumptionService
from bot.services.stash_service import StashService


class PredictionService:
    """Service for predicting usage patterns and stash needs."""
    
    @staticmethod
    async def predict_stash_depletion(user_id: int) -> Dict:
        """Predict when stash items will run out based on usage patterns."""
        try:
            # Get consumption data for the last 30 days
            summary = await ConsumptionService.get_consumption_summary(user_id, days=30)
            stash_items = await StashService.get_stash_items(user_id)
            
            if not stash_items:
                return {'status': 'no_stash', 'message': 'No stash items to analyze'}
            
            # Calculate average daily consumption by method
            total_days = 30
            methods_usage = {}
            
            # Estimate method-specific usage (simplified)
            total_thc_consumed = summary.get('total_thc_mg', 0)
            avg_daily_thc = total_thc_consumed / total_days if total_thc_consumed > 0 else 0
            
            if avg_daily_thc == 0:
                return {'status': 'no_usage_data', 'message': 'Need usage data for predictions'}
            
            # Predict depletion for each stash item
            predictions = []
            for item in stash_items:
                if item.amount <= 0:
                    continue
                    
                # Estimate daily consumption for this item type
                if item.type == 'flower':
                    # Assume flower makes up 60% of consumption
                    estimated_daily_amount = (avg_daily_thc * 0.6) / ((item.thc_percent or 20) * 10)  # Convert to grams
                elif item.type == 'concentrate':
                    # Assume concentrates make up 30% of consumption  
                    estimated_daily_amount = (avg_daily_thc * 0.3) / ((item.thc_percent or 70) * 10)
                elif item.type == 'edible':
                    # Assume edibles make up 10% of consumption
                    estimated_daily_amount = (avg_daily_thc * 0.1) / 1000  # Already in mg
                else:
                    # Default estimation
                    estimated_daily_amount = avg_daily_thc / ((item.thc_percent or 20) * 20)
                
                if estimated_daily_amount > 0:
                    days_remaining = item.amount / estimated_daily_amount
                    depletion_date = datetime.now() + timedelta(days=days_remaining)
                    
                    # Determine urgency
                    if days_remaining < 3:
                        urgency = 'critical'
                        urgency_emoji = '🔴'
                    elif days_remaining < 7:
                        urgency = 'high'
                        urgency_emoji = '🟠'
                    elif days_remaining < 14:
                        urgency = 'medium'
                        urgency_emoji = '🟡'
                    else:
                        urgency = 'low'
                        urgency_emoji = '🟢'
                    
                    predictions.append({
                        'strain': item.strain or f"{item.type.title()} Item",
                        'type': item.type,
                        'current_amount': item.amount,
                        'days_remaining': int(days_remaining),
                        'depletion_date': depletion_date.strftime('%Y-%m-%d'),
                        'urgency': urgency,
                        'urgency_emoji': urgency_emoji,
                        'estimated_daily_use': estimated_daily_amount
                    })
            
            # Sort by urgency (soonest depletion first)
            predictions.sort(key=lambda x: x['days_remaining'])
            
            return {
                'status': 'success',
                'predictions': predictions,
                'avg_daily_thc': avg_daily_thc,
                'analysis_period_days': total_days
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error predicting stash depletion: {str(e)}'}
    
    @staticmethod
    async def suggest_reorder_timing(user_id: int) -> Dict:
        """Suggest optimal timing for reordering stash items."""
        try:
            predictions = await PredictionService.predict_stash_depletion(user_id)
            
            if predictions['status'] != 'success':
                return predictions
            
            suggestions = []
            for item in predictions['predictions']:
                days_remaining = item['days_remaining']
                
                # Different reorder timing based on item type and availability
                if item['type'] == 'flower':
                    reorder_lead_time = 3  # Can usually get flower quickly
                elif item['type'] == 'concentrate':
                    reorder_lead_time = 5  # Concentrates might take longer
                elif item['type'] == 'edible':
                    reorder_lead_time = 7  # Edibles might need to be made/ordered
                else:
                    reorder_lead_time = 5  # Default
                
                reorder_in_days = max(0, days_remaining - reorder_lead_time)
                reorder_date = datetime.now() + timedelta(days=reorder_in_days)
                
                if reorder_in_days <= 0:
                    action = 'reorder_now'
                    action_text = '🚨 **REORDER NOW**'
                elif reorder_in_days <= 2:
                    action = 'reorder_soon'
                    action_text = f'⚠️ **Reorder in {reorder_in_days} days**'
                else:
                    action = 'monitor'
                    action_text = f'📅 Reorder by {reorder_date.strftime("%m/%d")}'
                
                suggestions.append({
                    'strain': item['strain'],
                    'type': item['type'],
                    'current_amount': item['current_amount'],
                    'days_until_empty': days_remaining,
                    'reorder_in_days': reorder_in_days,
                    'reorder_date': reorder_date.strftime('%Y-%m-%d'),
                    'action': action,
                    'action_text': action_text,
                    'urgency_emoji': item['urgency_emoji']
                })
            
            return {
                'status': 'success',
                'suggestions': suggestions,
                'summary': {
                    'critical_items': len([s for s in suggestions if s['action'] == 'reorder_now']),
                    'soon_items': len([s for s in suggestions if s['action'] == 'reorder_soon']),
                    'total_items': len(suggestions)
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error generating reorder suggestions: {str(e)}'}
    
    @staticmethod
    async def predict_tolerance_development(user_id: int) -> Dict:
        """Predict when tolerance breaks might be needed based on trends."""
        try:
            # Get consumption data for analysis
            summary = await ConsumptionService.get_consumption_summary(user_id, days=21)
            daily_data = summary.get('daily_data', [])
            
            if len(daily_data) < 14:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 14 days of data for tolerance predictions'
                }
            
            # Analyze dosage trends
            recent_week = daily_data[-7:]
            previous_week = daily_data[-14:-7]
            
            recent_avg_thc = sum(day.get('total_thc_mg', 0) for day in recent_week) / 7
            previous_avg_thc = sum(day.get('total_thc_mg', 0) for day in previous_week) / 7
            
            # Analyze effectiveness trends
            recent_effectiveness = [day.get('avg_effect_rating', 0) for day in recent_week if day.get('avg_effect_rating')]
            previous_effectiveness = [day.get('avg_effect_rating', 0) for day in previous_week if day.get('avg_effect_rating')]
            
            recent_eff_avg = sum(recent_effectiveness) / len(recent_effectiveness) if recent_effectiveness else 0
            previous_eff_avg = sum(previous_effectiveness) / len(previous_effectiveness) if previous_effectiveness else 0
            
            # Calculate trends
            dosage_increase = recent_avg_thc - previous_avg_thc
            effectiveness_change = recent_eff_avg - previous_eff_avg
            dosage_increase_pct = (dosage_increase / previous_avg_thc * 100) if previous_avg_thc > 0 else 0
            
            # Predict tolerance development
            if dosage_increase_pct > 20 and effectiveness_change < -0.3:
                tolerance_risk = 'high'
                predicted_break_needed_in = 7  # Days
                risk_emoji = '🔴'
            elif dosage_increase_pct > 10 or effectiveness_change < -0.2:
                tolerance_risk = 'medium'
                predicted_break_needed_in = 14
                risk_emoji = '🟠'
            elif dosage_increase_pct > 5:
                tolerance_risk = 'low'
                predicted_break_needed_in = 21
                risk_emoji = '🟡'
            else:
                tolerance_risk = 'minimal'
                predicted_break_needed_in = 30
                risk_emoji = '🟢'
            
            return {
                'status': 'success',
                'tolerance_risk': tolerance_risk,
                'risk_emoji': risk_emoji,
                'predicted_break_needed_in': predicted_break_needed_in,
                'dosage_increase_pct': dosage_increase_pct,
                'effectiveness_change': effectiveness_change,
                'recent_avg_thc': recent_avg_thc,
                'previous_avg_thc': previous_avg_thc,
                'recommendations': PredictionService._generate_tolerance_prevention_tips(tolerance_risk)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error predicting tolerance: {str(e)}'}
    
    @staticmethod
    def _generate_tolerance_prevention_tips(risk_level: str) -> List[str]:
        """Generate tolerance prevention tips based on risk level."""
        base_tips = [
            "🔄 Rotate between different strains",
            "⏰ Space sessions at least 2-3 hours apart",
            "🧘‍♂️ Try micro-dosing for some sessions"
        ]
        
        if risk_level == 'high':
            return base_tips + [
                "🛑 Consider a 3-5 day tolerance break",
                "📉 Reduce dosage by 25-50% immediately",
                "🔄 Switch consumption methods for 1 week"
            ]
        elif risk_level == 'medium':
            return base_tips + [
                "📉 Reduce dosage by 10-20%",
                "🌿 Add CBD-dominant strains to rotation",
                "📅 Take 1-2 rest days per week"
            ]
        elif risk_level == 'low':
            return base_tips + [
                "👀 Monitor effectiveness ratings closely",
                "🌿 Consider adding CBD strains",
                "📊 Track tolerance indicators"
            ]
        else:
            return base_tips + [
                "✅ Current usage appears sustainable",
                "📈 Continue tracking for early detection"
            ]
