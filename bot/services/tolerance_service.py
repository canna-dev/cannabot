"""Tolerance tracking and recommendations service."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bot.services.consumption_service import ConsumptionService


class ToleranceService:
    """Service for tracking tolerance patterns and recommendations."""
    
    @staticmethod
    async def analyze_tolerance_trends(user_id: int, days: int = 14) -> Dict:
        """Analyze tolerance trends over specified period."""
        try:
            # Get consumption data for analysis period
            summary = await ConsumptionService.get_consumption_summary(user_id, days=days)
            daily_data = summary.get('daily_data', [])
            
            if len(daily_data) < 7:  # Need at least a week of data
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 7 days of data for tolerance analysis',
                    'recommendation': 'Continue tracking consumption and effects'
                }
            
            # Analyze effectiveness trends
            effectiveness_trend = []
            dosage_trend = []
            
            for day in daily_data:
                if day.get('avg_effect_rating'):
                    effectiveness_trend.append(day['avg_effect_rating'])
                if day.get('total_thc_mg'):
                    dosage_trend.append(day['total_thc_mg'])
            
            # Calculate tolerance indicators
            tolerance_analysis = ToleranceService._calculate_tolerance_metrics(
                effectiveness_trend, dosage_trend
            )
            
            # Generate recommendations
            recommendations = ToleranceService._generate_tolerance_recommendations(
                tolerance_analysis, summary
            )
            
            return {
                'status': 'analyzed',
                'analysis': tolerance_analysis,
                'recommendations': recommendations,
                'data_quality': len(effectiveness_trend) / len(daily_data),
                'period_days': days
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error analyzing tolerance: {str(e)}'
            }
    
    @staticmethod
    def _calculate_tolerance_metrics(effectiveness: List[float], dosage: List[float]) -> Dict:
        """Calculate tolerance-related metrics."""
        if not effectiveness or not dosage:
            return {'insufficient_data': True}
        
        # Split data into early and recent periods
        mid_point = len(effectiveness) // 2
        early_effectiveness = effectiveness[:mid_point]
        recent_effectiveness = effectiveness[mid_point:]
        early_dosage = dosage[:mid_point] if len(dosage) > mid_point else dosage
        recent_dosage = dosage[mid_point:] if len(dosage) > mid_point else dosage
        
        # Calculate averages
        early_eff_avg = sum(early_effectiveness) / len(early_effectiveness)
        recent_eff_avg = sum(recent_effectiveness) / len(recent_effectiveness)
        early_dose_avg = sum(early_dosage) / len(early_dosage)
        recent_dose_avg = sum(recent_dosage) / len(recent_dosage)
        
        # Calculate trends
        effectiveness_change = recent_eff_avg - early_eff_avg
        dosage_change = recent_dose_avg - early_dose_avg
        dosage_change_pct = (dosage_change / early_dose_avg * 100) if early_dose_avg > 0 else 0
        
        # Determine tolerance status
        if effectiveness_change < -0.5 and dosage_change > 0:
            tolerance_status = 'increasing'
            severity = 'high' if effectiveness_change < -1.0 else 'moderate'
        elif effectiveness_change < -0.3:
            tolerance_status = 'slight_increase'
            severity = 'low'
        elif effectiveness_change > 0.3:
            tolerance_status = 'improving'
            severity = 'good'
        else:
            tolerance_status = 'stable'
            severity = 'normal'
        
        return {
            'tolerance_status': tolerance_status,
            'severity': severity,
            'effectiveness_change': effectiveness_change,
            'dosage_change_pct': dosage_change_pct,
            'early_effectiveness': early_eff_avg,
            'recent_effectiveness': recent_eff_avg,
            'early_dosage': early_dose_avg,
            'recent_dosage': recent_dose_avg
        }
    
    @staticmethod
    def _generate_tolerance_recommendations(analysis: Dict, summary: Dict) -> List[str]:
        """Generate personalized tolerance recommendations."""
        recommendations = []
        
        if analysis.get('insufficient_data'):
            return ["Track effects and dosage consistently for personalized recommendations"]
        
        status = analysis.get('tolerance_status')
        severity = analysis.get('severity')
        
        if status == 'increasing':
            if severity == 'high':
                recommendations.extend([
                    "🔄 **Consider a tolerance break** - 3-7 days recommended",
                    "📉 **Reduce dosage by 25-50%** when resuming",
                    "🔄 **Try different consumption methods** to reset receptors",
                    "⏰ **Space sessions further apart** (minimum 2-3 hours)"
                ])
            elif severity == 'moderate':
                recommendations.extend([
                    "⚠️ **Monitor tolerance closely** - consider micro-dosing",
                    "🔄 **Alternate strains** to prevent method-specific tolerance",
                    "⏰ **Increase time between sessions**",
                    "📊 **Track effectiveness ratings** more consistently"
                ])
        
        elif status == 'slight_increase':
            recommendations.extend([
                "📉 **Consider reducing dosage slightly** (10-20%)",
                "🌿 **Try CBD-dominant strains** to modulate tolerance",
                "⏰ **Take occasional rest days** between sessions"
            ])
        
        elif status == 'improving':
            recommendations.extend([
                "✅ **Current approach is working well**",
                "📊 **Continue current dosage and methods**",
                "🎯 **Maintain consistent tracking** for best results"
            ])
        
        elif status == 'stable':
            recommendations.extend([
                "✅ **Tolerance appears stable**",
                "🔄 **Consider rotating strains** for variety",
                "📈 **Track other factors** (sleep, stress, diet) that affect effectiveness"
            ])
        
        # Add method-specific recommendations
        methods = summary.get('methods', [])
        if len(methods) == 1:
            recommendations.append("🔄 **Try alternating consumption methods** to prevent single-method tolerance")
        
        # Add timing recommendations
        avg_daily_thc = summary.get('total_thc_mg', 0) / summary.get('days', 1)
        if avg_daily_thc > 50:
            recommendations.append("⚠️ **Daily intake is high** - consider spreading doses throughout day")
        
        return recommendations
    
    @staticmethod
    async def suggest_tolerance_break(user_id: int) -> Dict:
        """Suggest optimal tolerance break duration based on usage patterns."""
        try:
            # Get recent usage data
            summary = await ConsumptionService.get_consumption_summary(user_id, days=30)
            
            avg_daily_thc = summary.get('total_thc_mg', 0) / 30
            session_frequency = summary.get('session_count', 0) / 30
            
            # Calculate suggested break duration
            if avg_daily_thc > 100:  # Very high usage
                suggested_days = 7
                intensity = "full"
            elif avg_daily_thc > 50:  # High usage
                suggested_days = 5
                intensity = "moderate"
            elif avg_daily_thc > 25:  # Moderate usage
                suggested_days = 3
                intensity = "mild"
            else:  # Low usage
                suggested_days = 2
                intensity = "minimal"
            
            return {
                'suggested_days': suggested_days,
                'intensity': intensity,
                'current_usage': avg_daily_thc,
                'session_frequency': session_frequency,
                'break_benefits': [
                    "🔄 Reset cannabinoid receptors",
                    "💰 Reduce tolerance and save money",
                    "🧠 Improve natural endocannabinoid function",
                    "⭐ Enhance effectiveness when resuming",
                    "🎯 Gain perspective on usage patterns"
                ],
                'tips': [
                    "💧 Stay hydrated throughout the break",
                    "🏃‍♂️ Increase physical activity to boost natural endorphins",
                    "🧘‍♂️ Try meditation or breathing exercises",
                    "😴 Focus on sleep hygiene during the break",
                    "📱 Use this bot to track your break progress"
                ]
            }
            
        except Exception as e:
            return {
                'error': f'Error calculating tolerance break: {str(e)}'
            }
    
    @staticmethod
    async def predict_optimal_dosage(user_id: int, method: str, strain: Optional[str] = None) -> Dict:
        """Predict optimal dosage based on tolerance and history."""
        try:
            # Get consumption history for this method
            summary = await ConsumptionService.get_consumption_summary(user_id, days=14)
            
            # Filter by method and strain if specified
            method_sessions = []
            for day_data in summary.get('daily_data', []):
                # This would need enhancement to track individual sessions by method
                # For now, provide general guidance
                pass
            
            # Get recent effectiveness ratings
            recent_ratings = []
            for day_data in summary.get('daily_data', [])[-7:]:  # Last week
                if day_data.get('avg_effect_rating'):
                    recent_ratings.append(day_data['avg_effect_rating'])
            
            if not recent_ratings:
                return {
                    'recommendation': 'start_low',
                    'message': 'Start with a low dose and track effects',
                    'suggested_amount': 0.1 if method in ['smoking', 'vaporizer'] else 5.0
                }
            
            avg_recent_rating = sum(recent_ratings) / len(recent_ratings)
            
            # Base recommendations on recent effectiveness
            if avg_recent_rating < 2.5:  # Low effectiveness
                adjustment = 'increase'
                multiplier = 1.2
            elif avg_recent_rating > 4.0:  # High effectiveness  
                adjustment = 'maintain'
                multiplier = 1.0
            else:  # Moderate effectiveness
                adjustment = 'slight_increase'
                multiplier = 1.1
            
            return {
                'recommendation': adjustment,
                'multiplier': multiplier,
                'recent_effectiveness': avg_recent_rating,
                'confidence': len(recent_ratings) / 7  # Confidence based on data completeness
            }
            
        except Exception as e:
            return {
                'error': f'Error predicting dosage: {str(e)}'
            }
