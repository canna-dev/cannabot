"""Data visualization service for cannabis consumption charts and graphs."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

from bot.database.models import ConsumptionEntry, StashItem
from bot.services.consumption_service import ConsumptionService

class VisualizationService:
    """Service for generating data visualizations and charts."""
    
    @staticmethod
    async def generate_consumption_chart_data(user_id: int, days: int = 30) -> Dict:
        """Generate chart data for consumption trends."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=1000)
            
            if not entries:
                return {'status': 'no_data', 'message': 'No consumption data found'}
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]
            
            if not recent_entries:
                return {'status': 'no_recent_data', 'message': f'No data found for last {days} days'}
            
            # Generate daily data points
            daily_data = {}
            method_data = {}
            strain_data = {}
            
            for entry in recent_entries:
                if not entry.timestamp:
                    continue
                    
                date_str = entry.timestamp.strftime('%Y-%m-%d')
                
                # Daily totals
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        'thc_mg': 0,
                        'sessions': 0,
                        'avg_rating': 0,
                        'ratings': []
                    }
                
                daily_data[date_str]['thc_mg'] += entry.absorbed_thc_mg
                daily_data[date_str]['sessions'] += 1
                
                if entry.effect_rating:
                    daily_data[date_str]['ratings'].append(entry.effect_rating)
                
                # Method breakdown
                if entry.method not in method_data:
                    method_data[entry.method] = {'count': 0, 'thc_mg': 0}
                method_data[entry.method]['count'] += 1
                method_data[entry.method]['thc_mg'] += entry.absorbed_thc_mg
                
                # Strain breakdown
                if entry.strain:
                    if entry.strain not in strain_data:
                        strain_data[entry.strain] = {'count': 0, 'thc_mg': 0, 'ratings': []}
                    strain_data[entry.strain]['count'] += 1
                    strain_data[entry.strain]['thc_mg'] += entry.absorbed_thc_mg
                    if entry.effect_rating:
                        strain_data[entry.strain]['ratings'].append(entry.effect_rating)
            
            # Calculate average ratings for daily data
            for date, data in daily_data.items():
                if data['ratings']:
                    data['avg_rating'] = sum(data['ratings']) / len(data['ratings'])
                del data['ratings']  # Remove raw ratings list
            
            # Sort daily data by date
            sorted_daily = dict(sorted(daily_data.items()))
            
            # Generate chart structure for Discord embed visualization
            chart_data = {
                'status': 'success',
                'period': f'{days} days',
                'daily_consumption': sorted_daily,
                'method_breakdown': method_data,
                'strain_breakdown': strain_data,
                'summary': {
                    'total_sessions': len(recent_entries),
                    'total_thc_mg': sum(e.absorbed_thc_mg for e in recent_entries),
                    'avg_daily_thc': sum(e.absorbed_thc_mg for e in recent_entries) / days,
                    'unique_strains': len(strain_data),
                    'active_days': len(daily_data)
                }
            }
            
            return chart_data
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def generate_tolerance_heatmap_data(user_id: int) -> Dict:
        """Generate heatmap data showing effectiveness over time."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=200)
            
            # Filter entries with ratings
            rated_entries = [e for e in entries if e.timestamp and e.effect_rating]
            
            if len(rated_entries) < 10:
                return {'status': 'insufficient_data', 'message': 'Need at least 10 rated sessions'}
            
            # Create weekly buckets
            weekly_data = {}
            
            for entry in rated_entries:
                if not entry.timestamp:
                    continue
                    
                # Get week start (Monday)
                week_start = entry.timestamp - timedelta(days=entry.timestamp.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = {
                        'ratings': [],
                        'dosages': [],
                        'sessions': 0
                    }
                
                weekly_data[week_key]['ratings'].append(entry.effect_rating)
                weekly_data[week_key]['dosages'].append(entry.absorbed_thc_mg)
                weekly_data[week_key]['sessions'] += 1
            
            # Calculate averages for each week
            heatmap_data = {}
            for week, data in weekly_data.items():
                if data['ratings']:
                    avg_rating = sum(data['ratings']) / len(data['ratings'])
                    avg_dosage = sum(data['dosages']) / len(data['dosages'])
                    
                    # Create effectiveness score (rating per mg of THC)
                    efficiency = avg_rating / avg_dosage if avg_dosage > 0 else 0
                    
                    heatmap_data[week] = {
                        'avg_rating': round(avg_rating, 1),
                        'avg_dosage': round(avg_dosage, 1),
                        'efficiency': round(efficiency * 100, 1),  # Scale for readability
                        'sessions': data['sessions'],
                        'trend_indicator': '🟢' if avg_rating >= 4 else '🟡' if avg_rating >= 3 else '🔴'
                    }
            
            return {
                'status': 'success',
                'heatmap_data': dict(sorted(heatmap_data.items())),
                'analysis_period': f'{len(rated_entries)} rated sessions across {len(heatmap_data)} weeks'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def generate_method_efficiency_chart(user_id: int, days: int = 60) -> Dict:
        """Generate efficiency comparison chart for different consumption methods."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=500)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]
            
            if not recent_entries:
                return {'status': 'no_data', 'message': f'No data found for last {days} days'}
            
            # Group by method
            method_stats = {}
            
            for entry in recent_entries:
                method = entry.method
                
                if method not in method_stats:
                    method_stats[method] = {
                        'sessions': 0,
                        'total_thc': 0,
                        'total_amount': 0,
                        'ratings': [],
                        'bioavailability_samples': []
                    }
                
                stats = method_stats[method]
                stats['sessions'] += 1
                stats['total_thc'] += entry.absorbed_thc_mg
                stats['total_amount'] += entry.amount
                
                if entry.effect_rating:
                    stats['ratings'].append(entry.effect_rating)
                
                # Calculate actual bioavailability if we have THC% data
                if entry.thc_percent and entry.amount > 0:
                    raw_thc = (entry.amount * 1000) * (entry.thc_percent / 100)
                    if raw_thc > 0:
                        actual_bioavailability = (entry.absorbed_thc_mg / raw_thc) * 100
                        stats['bioavailability_samples'].append(actual_bioavailability)
            
            # Calculate efficiency metrics
            efficiency_chart = {}
            
            for method, stats in method_stats.items():
                if stats['sessions'] == 0:
                    continue
                
                avg_thc_per_session = stats['total_thc'] / stats['sessions']
                avg_amount_per_session = stats['total_amount'] / stats['sessions']
                avg_rating = sum(stats['ratings']) / len(stats['ratings']) if stats['ratings'] else 0
                
                # Efficiency score: rating per mg of THC
                efficiency_score = avg_rating / avg_thc_per_session if avg_thc_per_session > 0 and avg_rating > 0 else 0
                
                # Average bioavailability
                avg_bioavailability = sum(stats['bioavailability_samples']) / len(stats['bioavailability_samples']) if stats['bioavailability_samples'] else 0
                
                efficiency_chart[method] = {
                    'sessions': stats['sessions'],
                    'avg_thc_per_session': round(avg_thc_per_session, 1),
                    'avg_amount_per_session': round(avg_amount_per_session, 2),
                    'avg_rating': round(avg_rating, 1),
                    'efficiency_score': round(efficiency_score * 100, 1),  # Scale for readability
                    'avg_bioavailability': round(avg_bioavailability, 1),
                    'recommendation': VisualizationService._get_method_recommendation(method, efficiency_score, avg_rating, stats['sessions'])
                }
            
            # Sort by efficiency score
            sorted_efficiency = dict(sorted(efficiency_chart.items(), 
                                          key=lambda x: x[1]['efficiency_score'], 
                                          reverse=True))
            
            return {
                'status': 'success',
                'efficiency_data': sorted_efficiency,
                'analysis_period': f'{days} days',
                'total_sessions': sum(stats['sessions'] for stats in method_stats.values())
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def _get_method_recommendation(method: str, efficiency_score: float, avg_rating: float, sessions: int) -> str:
        """Generate recommendation text for a consumption method."""
        if sessions < 3:
            return "Need more data for reliable recommendation"
        
        if efficiency_score > 0.15 and avg_rating >= 4:
            return f"🏆 Excellent choice - highly efficient and effective"
        elif efficiency_score > 0.10 and avg_rating >= 3.5:
            return f"⭐ Good option - solid efficiency and satisfaction"
        elif avg_rating >= 4:
            return f"😊 Great effects but consider dosage optimization"
        elif efficiency_score > 0.10:
            return f"⚡ Efficient method but effects could be better"
        else:
            return f"📊 Consider adjusting dosage or trying different strains"
    
    @staticmethod
    async def generate_strain_effectiveness_radar(user_id: int) -> Dict:
        """Generate radar chart data for strain effectiveness across different metrics."""
        try:
            entries = await ConsumptionEntry.get_user_consumption(user_id, limit=300)
            
            # Group by strain
            strain_metrics = {}
            
            for entry in entries:
                if not entry.strain or not entry.effect_rating:
                    continue
                
                strain = entry.strain
                
                if strain not in strain_metrics:
                    strain_metrics[strain] = {
                        'ratings': [],
                        'dosages': [],
                        'sessions': 0,
                        'methods': {}
                    }
                
                metrics = strain_metrics[strain]
                metrics['ratings'].append(entry.effect_rating)
                metrics['dosages'].append(entry.absorbed_thc_mg)
                metrics['sessions'] += 1
                
                # Track methods used with this strain
                method = entry.method
                if method not in metrics['methods']:
                    metrics['methods'][method] = 0
                metrics['methods'][method] += 1
            
            # Calculate radar chart metrics for top strains
            radar_data = {}
            
            # Only include strains with at least 3 sessions
            qualified_strains = {k: v for k, v in strain_metrics.items() if v['sessions'] >= 3}
            
            for strain, metrics in qualified_strains.items():
                if not metrics['ratings']:
                    continue
                
                avg_rating = sum(metrics['ratings']) / len(metrics['ratings'])
                avg_dosage = sum(metrics['dosages']) / len(metrics['dosages'])
                
                # Calculate consistency (lower std deviation = higher consistency)
                rating_variance = sum((r - avg_rating) ** 2 for r in metrics['ratings']) / len(metrics['ratings'])
                consistency_score = max(0, 5 - rating_variance)  # Scale: 5 = very consistent, 0 = very inconsistent
                
                # Calculate efficiency (rating per mg)
                efficiency = (avg_rating / avg_dosage * 10) if avg_dosage > 0 else 0  # Scale for visibility
                
                # Calculate versatility (how many different methods used)
                versatility = min(5, len(metrics['methods']))  # Scale: 5 = used with many methods
                
                # Calculate frequency score (how often used)
                frequency = min(5, metrics['sessions'] / 2)  # Scale: 5 = very frequent use
                
                radar_data[strain] = {
                    'effectiveness': round(avg_rating, 1),  # 1-5 scale
                    'consistency': round(consistency_score, 1),  # 1-5 scale
                    'efficiency': round(min(5, efficiency), 1),  # 1-5 scale
                    'versatility': versatility,  # 1-5 scale
                    'frequency': round(frequency, 1),  # 1-5 scale
                    'sessions': metrics['sessions'],
                    'avg_dosage': round(avg_dosage, 1),
                    'overall_score': round((avg_rating + consistency_score + min(5, efficiency) + versatility + frequency) / 5, 1)
                }
            
            # Sort by overall score
            sorted_radar = dict(sorted(radar_data.items(), 
                                     key=lambda x: x[1]['overall_score'], 
                                     reverse=True))
            
            return {
                'status': 'success',
                'radar_data': sorted_radar,
                'metrics_explanation': {
                    'effectiveness': 'Average effect rating (1-5)',
                    'consistency': 'How consistent the effects are',
                    'efficiency': 'Effect strength per mg of THC',
                    'versatility': 'Works well with different methods',
                    'frequency': 'How often you use this strain'
                },
                'qualified_strains': len(qualified_strains)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def create_ascii_bar_chart(data: Dict, title: str, max_width: int = 20) -> str:
        """Create a simple ASCII bar chart for Discord display."""
        try:
            if not data:
                return "No data available for chart"
            
            # Find max value for scaling
            max_value = max(data.values())
            if max_value == 0:
                return "All values are zero"
            
            chart_lines = [f"📊 **{title}**", "```"]
            
            for label, value in data.items():
                # Scale bar length
                bar_length = int((value / max_value) * max_width)
                bar = "█" * bar_length + "░" * (max_width - bar_length)
                
                # Truncate long labels
                short_label = label[:10] + "..." if len(label) > 10 else label
                
                chart_lines.append(f"{short_label:12} │{bar}│ {value:.1f}")
            
            chart_lines.append("```")
            return "\n".join(chart_lines)
            
        except Exception as e:
            return f"Error creating chart: {str(e)}"
