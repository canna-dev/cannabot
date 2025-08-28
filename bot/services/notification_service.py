"""Smart notification service for consumption reminders and warnings."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import discord

from bot.database.models import ConsumptionEntry, Alert
from bot.services.tolerance_service import ToleranceService
from bot.services.prediction_service import PredictionService

class NotificationService:
    """Service for intelligent cannabis consumption notifications."""
    
    @staticmethod
    async def check_consumption_reminders(user_id: int) -> Dict:
        """Check if user needs consumption reminders."""
        try:
            # Get recent consumption data
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=100)
            
            if not entries:
                return {'status': 'no_data', 'message': 'No consumption data found'}
            
            # Check last consumption time
            last_entry = max(entries, key=lambda x: x.timestamp or datetime.min)
            hours_since_last = (datetime.now() - (last_entry.timestamp or datetime.now())).total_seconds() / 3600
            
            # Check patterns for personalized reminders
            usual_patterns = await NotificationService._analyze_consumption_patterns(entries)
            
            reminders = []
            
            # Medication reminder (for medical users)
            if hours_since_last > usual_patterns.get('typical_gap_hours', 8):
                if usual_patterns.get('medical_pattern', False):
                    reminders.append({
                        'type': 'medical_reminder',
                        'title': '💊 Medication Reminder',
                        'message': f"It's been {hours_since_last:.1f} hours since your last dose. Time for your medication?",
                        'priority': 'high',
                        'actions': ['Log Consumption', 'Snooze 1h', 'Skip Today']
                    })
            
            # Tolerance break suggestion
            tolerance_data = await ToleranceService.analyze_tolerance_trends(user_id)
            if tolerance_data.get('status') == 'success':
                analysis = tolerance_data['analysis']
                if analysis['tolerance_status'] == 'increasing' and analysis['severity'] == 'high':
                    reminders.append({
                        'type': 'tolerance_warning',
                        'title': '⚠️ Tolerance Alert',
                        'message': 'Your tolerance appears to be increasing. Consider a tolerance break.',
                        'priority': 'medium',
                        'actions': ['Start Break', 'View Analysis', 'Remind Later']
                    })
            
            # Stash reorder reminders
            predictions = await PredictionService.suggest_reorder_timing(user_id)
            if predictions.get('status') == 'success':
                urgent_items = [s for s in predictions['suggestions'] if s['action'] == 'reorder_now']
                if urgent_items:
                    item = urgent_items[0]  # Most urgent
                    reminders.append({
                        'type': 'reorder_reminder',
                        'title': '🛒 Restock Alert',
                        'message': f"Your {item['strain']} is running low ({item['current_amount']:.1f}g remaining)",
                        'priority': 'medium',
                        'actions': ['Mark Restocked', 'View All Stash', 'Remind Tomorrow']
                    })
            
            # Hydration reminder (after consumption)
            if hours_since_last < 2:
                reminders.append({
                    'type': 'hydration_reminder',
                    'title': '💧 Stay Hydrated',
                    'message': 'Remember to drink water and stay hydrated!',
                    'priority': 'low',
                    'actions': ['Got It', 'Remind Later']
                })
            
            return {
                'status': 'success',
                'reminders': reminders,
                'user_patterns': usual_patterns
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def _analyze_consumption_patterns(entries: List[ConsumptionEntry]) -> Dict:
        """Analyze user's consumption patterns for personalized notifications."""
        if not entries:
            return {}
        
        # Sort by timestamp (filter out None timestamps)
        valid_entries = [e for e in entries if e.timestamp is not None]
        sorted_entries = sorted(valid_entries, key=lambda x: x.timestamp or datetime.min)
        
        if len(sorted_entries) < 3:
            return {'insufficient_data': True}
        
        # Calculate gaps between sessions
        gaps = []
        for i in range(1, len(sorted_entries)):
            curr_time = sorted_entries[i].timestamp
            prev_time = sorted_entries[i-1].timestamp
            if curr_time and prev_time:
                gap_hours = (curr_time - prev_time).total_seconds() / 3600
                gaps.append(gap_hours)
        
        # Typical gap calculation
        gaps.sort()
        median_gap = gaps[len(gaps) // 2] if gaps else 8
        
        # Detect medical vs recreational patterns
        # Medical users typically have more regular, frequent dosing
        avg_gap = sum(gaps) / len(gaps) if gaps else 8
        gap_consistency = len([g for g in gaps if abs(g - avg_gap) < avg_gap * 0.3]) / len(gaps) if gaps else 0
        
        medical_pattern = (
            avg_gap < 6 and  # Less than 6 hours between doses
            gap_consistency > 0.6 and  # Consistent timing
            len(sorted_entries) > 20  # Regular usage
        )
        
        # Peak usage times
        hours = [e.timestamp.hour for e in sorted_entries if e.timestamp]
        peak_hours = []
        if hours:
            hour_counts = {}
            for hour in hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            max_count = max(hour_counts.values())
            peak_hours = [h for h, c in hour_counts.items() if c >= max_count * 0.7]
        
        return {
            'typical_gap_hours': median_gap,
            'avg_gap_hours': avg_gap,
            'gap_consistency': gap_consistency,
            'medical_pattern': medical_pattern,
            'peak_hours': peak_hours,
            'total_sessions': len(sorted_entries)
        }
    
    @staticmethod
    async def create_smart_reminder(user_id: int, reminder_type: str, **kwargs) -> Optional[Alert]:
        """Create a smart reminder alert."""
        try:
            # Calculate smart reminder time based on type and user patterns
            patterns = kwargs.get('patterns', {})
            
            if reminder_type == 'medication':
                # Schedule based on typical gap
                hours_delay = patterns.get('typical_gap_hours', 6)
                reminder_time = datetime.now() + timedelta(hours=hours_delay)
                
            elif reminder_type == 'tolerance_break':
                # Suggest at optimal time (usually evening)
                reminder_time = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
                if reminder_time <= datetime.now():
                    reminder_time += timedelta(days=1)
                    
            elif reminder_type == 'reorder':
                # Morning reminder for purchasing
                reminder_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
                if reminder_time <= datetime.now():
                    reminder_time += timedelta(days=1)
                    
            elif reminder_type == 'hydration':
                # 30 minutes after consumption
                reminder_time = datetime.now() + timedelta(minutes=30)
                
            else:
                # Default: 1 hour delay
                reminder_time = datetime.now() + timedelta(hours=1)
            
            # Create alert (simplified for current Alert model)
            alert = Alert(
                user_id=user_id,
                alert_type=reminder_type,
                message=kwargs.get('message', f'{reminder_type.title()} reminder'),
                active=True
            )
            
            await alert.save()
            return alert
            
        except Exception as e:
            print(f"Error creating smart reminder: {e}")
            return None
    
    @staticmethod
    async def get_voice_friendly_shortcuts() -> List[Dict]:
        """Get voice-friendly command shortcuts for mobile users."""
        return [
            {
                'command': '/quick',
                'voice_trigger': 'log session',
                'description': 'Quick consumption logging',
                'example': 'Say: "Hey Siri, log session" then use quick command'
            },
            {
                'command': '/smoke 0.5g',
                'voice_trigger': 'smoke half gram',
                'description': 'Log smoking session',
                'example': 'Say: "smoke half gram" in voice memo, then copy to Discord'
            },
            {
                'command': '/vape 0.2g',
                'voice_trigger': 'vape point two grams',
                'description': 'Log vaping session',
                'example': 'Say amounts clearly for voice recognition'
            },
            {
                'command': '/dashboard',
                'voice_trigger': 'show dashboard',
                'description': 'View usage summary',
                'example': 'Quick overview of your consumption'
            },
            {
                'command': '/stash list',
                'voice_trigger': 'check stash',
                'description': 'View current stash',
                'example': 'See what strains you have available'
            }
        ]
    
    @staticmethod
    async def generate_consumption_shortcuts(user_id: int) -> List[Dict]:
        """Generate personalized quick action shortcuts."""
        try:
            # Get user's common patterns
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=50)
            
            if not entries:
                return []
            
            # Find most common combinations
            combinations = {}
            for entry in entries[-20:]:  # Last 20 sessions
                key = (entry.method, entry.amount, entry.strain or 'Unknown')
                combinations[key] = combinations.get(key, 0) + 1
            
            # Sort by frequency
            common_combos = sorted(combinations.items(), key=lambda x: x[1], reverse=True)[:5]
            
            shortcuts = []
            for (method, amount, strain), count in common_combos:
                shortcuts.append({
                    'label': f"{method.title()} {amount}g {strain}",
                    'command': f"/{method} {amount}g strain:{strain}",
                    'frequency': count,
                    'description': f"Used {count} times recently"
                })
            
            return shortcuts
            
        except Exception as e:
            return []

async def setup_notification_scheduler(bot):
    """Setup background task for checking notifications."""
    
    async def notification_checker():
        """Background task to check and send notifications."""
        while True:
            try:
                # This would check all users' notifications
                # For now, it's a placeholder for the notification system
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Error in notification checker: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    # Start the background task
    bot.loop.create_task(notification_checker())
