"""
Integration manager for Jarvis X
Provides app/web account launchers and simple account hub actions
"""

from typing import Dict
import webbrowser
from urllib.parse import quote_plus
from utils.config_manager import get_config


class IntegrationManager:
    """Launches common account endpoints for connected workflows."""

    def __init__(self):
        self.config = get_config()
        self.service_urls = {
            'gmail': 'https://mail.google.com/',
            'email': 'https://mail.google.com/',
            'alexa': 'https://alexa.amazon.com/',
            'alexaskills': 'https://www.amazon.com/alexa-skills/',
            'facebook': 'https://www.facebook.com/',
            'instagram': 'https://www.instagram.com/',
            'github': 'https://github.com/',
            'discord': 'https://discord.com/app',
            'dropbox': 'https://www.dropbox.com/home',
            'meshare': 'https://play.google.com/store/apps/details?id=com.meshare.meshare',
            'smartz': 'https://play.google.com/store/search?q=smartz&c=apps',
            'coinbase': 'https://www.coinbase.com/',
            'kraken': 'https://www.kraken.com/',
            'trustwallet': 'https://trustwallet.com/'
        }

    def open_service(self, service: str) -> Dict[str, object]:
        key = (service or '').strip().lower().replace(' ', '')
        if not key:
            return {'success': False, 'message': 'No service provided'}

        if key not in self.service_urls:
            return {
                'success': False,
                'message': f'Service not supported yet: {service}'
            }

        url = self.service_urls[key]
        ok = webbrowser.open(url)
        return {
            'success': bool(ok),
            'message': f'Opened {service}',
            'url': url
        }

    def list_services(self) -> Dict[str, object]:
        return {
            'success': True,
            'services': sorted(self.service_urls.keys())
        }

    def open_lyrics(self, query: str) -> Dict[str, object]:
        search = (query or '').strip()
        if not search:
            return {'success': False, 'message': 'No song provided for lyrics lookup'}

        url = f"https://www.google.com/search?q={quote_plus(search + ' lyrics')}"
        ok = webbrowser.open(url)
        return {
            'success': bool(ok),
            'message': f'Opened lyrics for {search}',
            'url': url
        }

    def open_camera_video(self) -> Dict[str, object]:
        # Allow user-defined URL first, otherwise use Alexa web as a practical fallback.
        preferred_url = str(self.config.get('remote.camera.default_video_url', '') or '').strip()
        if preferred_url:
            ok = webbrowser.open(preferred_url)
            return {
                'success': bool(ok),
                'message': 'Opened configured camera video URL on PC',
                'url': preferred_url
            }

        fallback_url = 'https://alexa.amazon.com/spa/index.html#cards/cameras'
        ok = webbrowser.open(fallback_url)
        return {
            'success': bool(ok),
            'message': 'Opened Alexa cameras page on PC',
            'url': fallback_url
        }

