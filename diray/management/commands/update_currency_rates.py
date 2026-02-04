# management/commands/update_currency_rates.py
import json
import requests
import urllib3
from django.core.management.base import BaseCommand
from decimal import Decimal
from diray.models import CurrencyRate

# Disable SSL warnings for environments where certificate verification fails
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Update currency exchange rates from external API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if API fails',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting currency rate update...')
        force_update = options.get('force', False)
        
        try:
            # Main API: exchangerate-api.com
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/MAD',
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                self.process_rates(rates, 'Primary API')
            else:
                self.stdout.write(self.style.WARNING(f'Primary API failed (Status {response.status_code})'))
                self.try_alternative_api(force_update)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
            self.try_alternative_api(force_update)

    def try_alternative_api(self, force_update=False):
        """Try alternative API endpoints if the primary one fails"""
        alternative_apis = [
            'https://open.er-api.com/v6/latest/MAD',
            'https://api.frankfurter.app/latest?from=MAD',
        ]
        
        for api_url in alternative_apis:
            try:
                self.stdout.write(f'Trying {api_url}...')
                response = requests.get(api_url, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get('rates') or data.get('Rates') or data.get('data', {}).get('rates')
                    if rates:
                        self.process_rates(rates, 'Alternative API')
                        return
            except Exception as e:
                continue
        
        self.set_default_rates(force_update)

    def process_rates(self, rates, source):
        """Process and save rates where 1 Foreign Currency = X MAD"""
        currencies = self.get_currency_config()
        updated_count = 0

        for code, info in currencies.items():
            if code in rates:
                try:
                    # Logic: API gives MAD -> Foreign. We want Foreign -> MAD.
                    # Example: If 1 MAD = 0.10 USD, then 1 USD = 1 / 0.10 = 10 MAD
                    raw_rate = Decimal(str(rates[code]))
                    rate_to_mad = (Decimal('1') / raw_rate) if raw_rate > 0 else Decimal('0')
                    
                    self.save_rate(code, info, rate_to_mad)
                    updated_count += 1
                except Exception as e:
                    self.stdout.write(f'Error processing {code}: {e}')

        # Base currency
        self.save_rate('MAD', {'name': 'Dirham Marocain', 'country': 'Maroc', 'flag': '🇲🇦'}, Decimal('1.000000'))
        self.stdout.write(self.style.SUCCESS(f'{source}: Updated {updated_count} rates'))

    def set_default_rates(self, force_update=False):
        """
        Fallback rates for January 2026. 
        Values represent 1 Foreign Currency to MAD.
        """
        defaults = [
            ('MAD', 'Dirham Marocain', 'Maroc', '🇲🇦', Decimal('1.000000')),
            ('EUR', 'Euro', 'Union Européenne', '🇪🇺', Decimal('0.092')), #
            ('GBP', 'Livre Sterling', 'Royaume-Uni', '🇬🇧', Decimal('0.08')), #
            ('USD', 'Dollar US', 'États-Unis', '🇺🇸', Decimal('0.11')), #
            ('CAD', 'Dollar Canadien', 'Canada', '🇨🇦', Decimal('0.15')), #
            ('CHF', 'Franc Suisse', 'Suisse', '🇨🇭', Decimal('0.085')), #
            ('AED', 'Dirham Émirati', 'Émirats Arabes Unis', '🇦🇪', Decimal('0.41')), #
        ]
        
        for code, name, country, flag, rate in defaults:
            self.save_rate(code, {'name': name, 'country': country, 'flag': flag}, rate)
        
        self.stdout.write(self.style.WARNING('API failed. Applied January 2026 default rates.'))

    def save_rate(self, code, info, rate):
        """Helper to update or create records in the database"""
        CurrencyRate.objects.update_or_create(
            currency_code=code,
            defaults={
                'currency_name': info['name'],
                'country': info['country'],
                'flag': info['flag'],
                'rate_to_mad': rate,
            }
        )

    def get_currency_config(self):
        return {
            'EUR': {'name': 'Euro', 'country': 'Union Européenne', 'flag': '🇪🇺'},
            'USD': {'name': 'Dollar US', 'country': 'États-Unis', 'flag': '🇺🇸'},
            'GBP': {'name': 'Livre Sterling', 'country': 'Royaume-Uni', 'flag': '🇬🇧'},
            'CAD': {'name': 'Dollar Canadien', 'country': 'Canada', 'flag': '🇨🇦'},
            'AED': {'name': 'Dirham Émirati', 'country': 'Émirats Arabes Unis', 'flag': '🇦🇪'},
            'CHF': {'name': 'Franc Suisse', 'country': 'Suisse', 'flag': '🇨🇭'},
        }