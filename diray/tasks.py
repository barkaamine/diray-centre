# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import requests
import urllib3
from .models import (
    CurrencyRate, DailyStat, VisitorSession, PageView,
    FormSubmission, PhoneCall, WhatsAppClick, Training, ContactRequest,
    TrainingWaitlist, ThreatIP, RateLimitLog
)
from django.db import models

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@shared_task
def update_currency_rates():
    """Update currency rates daily with SSL workaround"""
    try:
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/MAD',
            timeout=10,
            verify=False  # Disable SSL verification
        )
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            
            currencies = {
                'EUR': {'name': 'Euro', 'country': 'Union Européenne', 'flag': '🇪🇺'},
                'USD': {'name': 'Dollar US', 'country': 'États-Unis', 'flag': '🇺🇸'},
                'GBP': {'name': 'Livre Sterling', 'country': 'Royaume-Uni', 'flag': '🇬🇧'},
                'CAD': {'name': 'Dollar Canadien', 'country': 'Canada', 'flag': '🇨🇦'},
                'AED': {'name': 'Dirham Émirati', 'country': 'Émirats Arabes Unis', 'flag': '🇦🇪'},
            }
            
            for currency_code, currency_info in currencies.items():
                if currency_code in rates:
                    try:
                        rate = Decimal(str(rates[currency_code]))
                        rate_to_mad = 1 / rate if rate > 0 else Decimal('0')
                        
                        CurrencyRate.objects.update_or_create(
                            currency_code=currency_code,
                            defaults={
                                'currency_name': currency_info['name'],
                                'country': currency_info['country'],
                                'flag': currency_info['flag'],
                                'rate_to_mad': rate_to_mad,
                            }
                        )
                    except Exception as e:
                        print(f"Error updating {currency_code}: {e}")
            
            # Ensure MAD exists
            CurrencyRate.objects.update_or_create(
                currency_code='MAD',
                defaults={
                    'currency_name': 'Dirham Marocain',
                    'country': 'Maroc',
                    'flag': '🇲🇦',
                    'rate_to_mad': Decimal('1.000000'),
                }
            )
            
            return f"Currency rates updated at {timezone.now()}"
        else:
            return "Failed to fetch currency rates, using defaults"
            
    except Exception as e:
        return f"Error updating currency rates: {str(e)}"

@shared_task
def aggregate_daily_stats():
    """Aggregate daily statistics"""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    try:
        # Get unique visitors
        unique_visitors = VisitorSession.objects.filter(
            start_time__date=yesterday
        ).values('session_id').distinct().count()
        
        # Get total pageviews
        total_pageviews = PageView.objects.filter(
            timestamp__date=yesterday
        ).count()
        
        # Get form submissions
        form_submissions = FormSubmission.objects.filter(
            timestamp__date=yesterday
        ).count()
        
        # Get phone calls
        phone_calls = PhoneCall.objects.filter(
            timestamp__date=yesterday
        ).count()
        
        # Get WhatsApp clicks
        whatsapp_clicks = WhatsAppClick.objects.filter(
            timestamp__date=yesterday
        ).count()
        
        # Calculate average session duration
        sessions = VisitorSession.objects.filter(start_time__date=yesterday)
        avg_duration = 0
        if sessions.exists():
            total_duration = sum(s.session_duration for s in sessions)
            avg_duration = total_duration // sessions.count()
        
        # Find top city
        top_city = ''
        city_counts = PageView.objects.filter(
            timestamp__date=yesterday
        ).exclude(city='').values('city').annotate(
            count=models.Count('id')
        ).order_by('-count').first()
        
        if city_counts:
            top_city = city_counts['city']
        
        # Find top training
        top_training = ''
        training_counts = PageView.objects.filter(
            timestamp__date=yesterday,
            page_title__icontains='Formation'
        ).values('page_title').annotate(
            count=models.Count('id')
        ).order_by('-count').first()
        
        if training_counts:
            top_training = training_counts['page_title'][:200]
        
        # Create or update daily stat
        DailyStat.objects.update_or_create(
            date=yesterday,
            defaults={
                'total_visitors': unique_visitors,
                'total_pageviews': total_pageviews,
                'total_form_submissions': form_submissions,
                'total_phone_calls': phone_calls,
                'total_whatsapp_clicks': whatsapp_clicks,
                'avg_session_duration': avg_duration,
                'top_city': top_city,
                'top_training': top_training,
            }
        )
        
        return f"Daily stats aggregated for {yesterday}"
        
    except Exception as e:
        return f"Error aggregating daily stats: {str(e)}"

@shared_task
def cleanup_old_sessions():
    """Clean up old visitor sessions"""
    cutoff_date = timezone.now() - timedelta(days=30)
    
    try:
        # Delete old sessions
        deleted_count, _ = VisitorSession.objects.filter(
            last_activity__lt=cutoff_date
        ).delete()
        
        # Delete old page views
        pageview_count, _ = PageView.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        return f"Cleaned up {deleted_count} old sessions and {pageview_count} page views"
        
    except Exception as e:
        return f"Error cleaning up sessions: {str(e)}"

@shared_task
def check_rate_limit_violations():
    """Check for rate limit violations and mark threats"""
    from django.db.models import Count
    
    try:
        # Find IPs with more than 5 requests per minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        
        violations = RateLimitLog.objects.filter(
            last_request__gte=one_minute_ago
        ).values('ip_address').annotate(
            total_requests=Count('id')
        ).filter(total_requests__gt=5)
        
        threat_count = 0
        for violation in violations:
            ip_address = violation['ip_address']
            
            # Mark as threat
            ThreatIP.objects.update_or_create(
                ip_address=ip_address,
                defaults={
                    'reason': f'Rate limit violation: {violation["total_requests"]} requests/minute',
                    'threat_level': 'high',
                    'is_blocked': True,
                }
            )
            
            # Update all contact requests from this IP
            ContactRequest.objects.filter(
                ip_address=ip_address
            ).update(is_threat=True, threat_reason='Rate limit violation')
            
            threat_count += 1
        
        return f"Marked {threat_count} IPs as threats"
        
    except Exception as e:
        return f"Error checking rate limits: {str(e)}"

@shared_task
def update_training_analytics():
    """Update training analytics from page views"""
    try:
        # Get yesterday's date
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Get all trainings
        trainings = Training.objects.all()
        
        for training in trainings:
            # Count page views for this training
            view_count = PageView.objects.filter(
                timestamp__date=yesterday,
                url__contains=f"/formations/{training.slug}/"
            ).count()
            
            if view_count > 0:
                training.view_count = models.F('view_count') + view_count
                training.save(update_fields=['view_count'])
        
        return "Training analytics updated"
        
    except Exception as e:
        return f"Error updating training analytics: {str(e)}"

@shared_task
def notify_waitlist(training_id):
    """Notify waitlist when spots become available"""
    try:
        training = Training.objects.get(id=training_id)
        
        # Get first 10 unnotified waitlist entries
        waitlist_entries = TrainingWaitlist.objects.filter(
            training=training,
            notified=False
        ).order_by('created_at')[:10]
        
        notified_count = 0
        for entry in waitlist_entries:
            # In a real implementation, you would send an email here
            # For now, just mark as notified
            entry.notified = True
            entry.save(update_fields=['notified'])
            notified_count += 1
        
        return f"Notified {notified_count} waitlist entries for {training.title}"
        
    except Training.DoesNotExist:
        return f"Training {training_id} not found"
    except Exception as e:
        return f"Error notifying waitlist: {str(e)}"