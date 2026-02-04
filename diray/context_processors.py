# context_processors.py
import requests
from django.utils import timezone
from django.conf import settings
from .models import CurrencyRate

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_location_from_ip(ip_address):
    """Get location from IP address using ip-api.com"""
    # Default fallback
    default_location = {'city': 'Casablanca', 'country': 'Maroc', 'countryCode': 'MA'}
    
    # Localhost check
    if ip_address in ['127.0.0.1', 'localhost', '::1']:
        return default_location
    
    try:
        # Use ip-api.com (free, reliable, no SSL for free plan)
        # Using http because the free tier doesn't support https
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'city': data.get('city', 'Casablanca'),
                    'country': data.get('country', 'Maroc'),
                    'countryCode': data.get('countryCode', 'MA')
                }
    except Exception as e:
        print(f"Location detection error: {e}")
        pass
    
    # Fallback to ipapi.co if the first one fails
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=3, verify=False)
        if response.status_code == 200:
            data = response.json()
            if not data.get('error'):
                return {
                    'city': data.get('city', 'Casablanca'),
                    'country': data.get('country_name', 'Maroc'),
                    'countryCode': data.get('country_code', 'MA')
                }
    except Exception as e:
        print(f"Fallback location detection error: {e}")
        pass
    
    return default_location

def currency_rates(request):
    """Add currency rates to context"""
    rates = {}
    try:
        db_rates = CurrencyRate.objects.all()
        for rate in db_rates:
            rates[rate.currency_code] = float(rate.rate_to_mad)
    except:
        rates = {
            'MAD': 1.0,
            'EUR': 0.093,
            'USD': 0.100,
            'GBP': 0.079,
            'CAD': 0.136,
            'AED': 0.367
        }
    
    preferred_currency = request.session.get('preferred_currency', 'MAD')
    
    return {
        'currency_rates': rates,
        'preferred_currency': preferred_currency,
    }

def user_location(request):
    """Add user location to context"""
    ip_address = get_client_ip(request)
    location = get_location_from_ip(ip_address)
    
    return {
        'user_location': location,
    }

def site_settings(request):
    """Add site settings to context"""
    return {
        'SITE_NAME': 'Diray Centre',
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        'CONTACT_PHONE': '+212 779 25 99 42',
        'CONTACT_EMAIL': 'contact@diraycentre.ma',
        'CURRENT_YEAR': timezone.now().year,
    }

# Alias for backward compatibility
site_context = site_settings

def notifications(request):
    """Add user notifications to context"""
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {
            'global_notifications': unread_notifications,
            'unread_notifications_count': unread_count,
        }
    return {
        'global_notifications': [],
        'unread_notifications_count': 0,
    }
