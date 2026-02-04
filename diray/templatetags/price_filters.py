# templatetags/price_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def price_eur(price_mad):
    """Convert MAD to EUR for templates"""
    try:
        if isinstance(price_mad, (Decimal, float, int)):
            # Use default rate or get from database
            from diray.models import CurrencyRate
            try:
                currency_rate = CurrencyRate.objects.first()
                eur_rate = currency_rate.eur_rate if currency_rate else Decimal('0.093')
            except:
                eur_rate = Decimal('0.093')
            
            converted = float(price_mad) * float(eur_rate)
            return round(converted, 2)
    except:
        pass
    return 0

@register.filter
def price_usd(price_mad):
    """Convert MAD to USD for templates"""
    try:
        if isinstance(price_mad, (Decimal, float, int)):
            # Use default rate or get from database
            from diray.models import CurrencyRate
            try:
                currency_rate = CurrencyRate.objects.first()
                usd_rate = currency_rate.usd_rate if currency_rate else Decimal('0.100')
            except:
                usd_rate = Decimal('0.100')
            
            converted = float(price_mad) * float(usd_rate)
            return round(converted, 2)
    except:
        pass
    return 0

@register.filter
def convert_price(value, request):
    """
    Convert MAD value to preferred currency from session.
    Usage: {{ price_mad|convert_price:request }}
    """
    try:
        if value is None:
            return 0
            
        from diray.models import CurrencyRate
        preferred_currency = request.session.get('preferred_currency', 'MAD')
        
        if preferred_currency == 'MAD':
            return float(value)
            
        rate_obj = CurrencyRate.objects.filter(currency_code=preferred_currency).first()
        if rate_obj:
            rate = float(rate_obj.rate_to_mad)
            return float(value) * rate
        
        # Fallback to hardcoded rates if not in DB
        fallbacks = {
            'EUR': 0.093,
            'USD': 0.100,
            'GBP': 0.079,
            'CAD': 0.136,
            'AED': 0.367
        }
        return float(value) * fallbacks.get(preferred_currency, 1.0)
    except:
        return value

@register.filter
def currency_symbol(currency_code):
    """Return the symbol for a currency code"""
    symbols = {
        'MAD': 'MAD',
        'EUR': '€',
        'USD': '$',
        'GBP': '£',
        'CAD': 'C$',
        'AED': 'AED'
    }
    return symbols.get(currency_code, currency_code)

@register.filter
def format_currency(value, currency='MAD'):
    """Format price with currency symbol"""
    try:
        if value is None:
            return f"0 {currency}"
        
        value = float(value)
        
        # Format with thousands separator
        formatted = f"{value:,.0f}".replace(',', ' ')
        
        # Add currency symbol
        if currency == 'EUR':
            return f"{formatted} €"
        elif currency == 'USD':
            return f"${formatted}"
        else:
            return f"{formatted} {currency}"
    except:
        return f"0 {currency}"