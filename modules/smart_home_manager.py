"""
Smart home manager for Jarvis X
Controls smart switches using local HTTP/webhook endpoints
"""

import asyncio
from typing import Dict
import requests
from utils.config_manager import get_config

try:
    from kasa import SmartPlug, Discover
except ImportError:
    SmartPlug = None
    Discover = None


config = get_config()


class SmartHomeManager:
    """Handles smart-home device actions configured in config.json."""

    def __init__(self):
        self._reload()

    def _reload(self):
        self.smart_home = config.get('smart_home', {})
        self.devices = self.smart_home.get('devices', {})

    def list_devices(self) -> Dict[str, object]:
        self._reload()
        return {
            'success': True,
            'devices': list(self.devices.keys())
        }

    @staticmethod
    def _run_async(coro):
        """Run async smart-home operation from sync context."""
        try:
            return asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    def _discover_kasa_ip(self, device_cfg: Dict[str, object]) -> str:
        """Best-effort local discovery for Kasa device IP."""
        if Discover is None:
            return ''

        model_hint = str(device_cfg.get('model', '')).strip().lower()
        alias_hint = str(device_cfg.get('alias', '')).strip().lower()

        async def _discover():
            devices = await Discover.discover(timeout=6)
            candidates = []

            for ip, dev in devices.items():
                try:
                    await dev.update()
                except Exception:
                    continue

                model = str(getattr(dev, 'model', '')).strip().lower()
                alias = str(getattr(dev, 'alias', '')).strip().lower()
                candidates.append((ip, model, alias))

            if model_hint:
                for ip, model, _alias in candidates:
                    if model_hint in model:
                        return ip

            if alias_hint:
                for ip, _model, alias in candidates:
                    if alias_hint and alias_hint in alias:
                        return ip

            return candidates[0][0] if candidates else ''

        found_ip = self._run_async(_discover())
        return str(found_ip or '').strip()

    def set_switch(self, device_name: str, state: str) -> Dict[str, object]:
        """Set smart switch state to on/off using configured URLs."""
        self._reload()

        key = (device_name or '').strip().lower().replace(' ', '_')
        if not key:
            return {
                'success': False,
                'message': 'No smart switch name provided'
            }

        device = self.devices.get(key)
        if not device:
            return {
                'success': False,
                'message': f"Smart device not configured: {device_name}"
            }

        requested = (state or '').strip().lower()
        if requested not in {'on', 'off'}:
            return {
                'success': False,
                'message': 'State must be on or off'
            }

        device_type = str(device.get('type', 'webhook')).strip().lower()

        if device_type == 'kasa':
            if SmartPlug is None:
                return {
                    'success': False,
                    'message': 'python-kasa is not installed. Install requirements and retry.'
                }

            ip_addr = str(device.get('ip', '')).strip()
            if not ip_addr:
                discovered_ip = self._discover_kasa_ip(device)
                if discovered_ip:
                    config.set(f'smart_home.devices.{key}.ip', discovered_ip, save=True)
                    self._reload()
                    ip_addr = discovered_ip

            if not ip_addr:
                return {
                    'success': False,
                    'message': f"No IP configured for {device_name}. Set smart_home.devices.{key}.ip in config.json"
                }

            async def _toggle_kasa():
                plug = SmartPlug(ip_addr)
                await plug.update()
                if requested == 'on':
                    await plug.turn_on()
                else:
                    await plug.turn_off()

            try:
                self._run_async(_toggle_kasa())
                return {
                    'success': True,
                    'message': f"{device_name} turned {requested} via Kasa"
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"Kasa command failed: {e}"
                }

        if device_type != 'webhook':
            return {
                'success': False,
                'message': f"Unsupported device type for {device_name}"
            }

        target_url = str(device.get(f'{requested}_url', '')).strip()
        if not target_url:
            return {
                'success': False,
                'message': f"No {requested}_url configured for {device_name}"
            }

        method = str(device.get('method', 'POST')).upper()
        headers = device.get('headers', {}) if isinstance(device.get('headers'), dict) else {}
        payload = device.get(f'{requested}_payload', device.get('payload', {}))

        try:
            response = requests.request(method, target_url, headers=headers, json=payload, timeout=15)
            if response.status_code >= 400:
                return {
                    'success': False,
                    'message': f"Switch request failed: HTTP {response.status_code}",
                    'output': response.text[:500]
                }

            return {
                'success': True,
                'message': f"{device_name} turned {requested}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Switch command failed: {e}"
            }

