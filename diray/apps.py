# apps.py
from django.apps import AppConfig

class DirayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diray'
    
    def ready(self):
        # Import signals if you have any
        try:
            import diray.signals
        except ImportError:
            pass