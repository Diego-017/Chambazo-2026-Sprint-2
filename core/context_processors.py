from django.conf import settings

def global_settings(request):
    """Make GOOGLE_MAPS_KEY available to all templates."""
    return {
        'GOOGLE_MAPS_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    }
