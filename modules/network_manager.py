"""
Network manager for Jarvis X
Discovers local LAN devices from ARP table
"""

from typing import Dict, List
import re
import subprocess


class NetworkManager:
    """Provides local network discovery helpers."""

    def discover_devices(self) -> Dict[str, object]:
        """List devices visible in local ARP cache."""
        try:
            completed = subprocess.run(['arp', '-a'], capture_output=True, text=True, check=False)
            output = (completed.stdout or '').strip()
            if completed.returncode != 0:
                return {
                    'success': False,
                    'message': (completed.stderr or 'Failed to read ARP table').strip()
                }

            devices = self._parse_arp(output)
            return {
                'success': True,
                'message': f'Discovered {len(devices)} device(s) in ARP table',
                'devices': devices
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Network discovery failed: {e}'
            }

    @staticmethod
    def _parse_arp(text: str) -> List[Dict[str, str]]:
        pattern = re.compile(r'\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f\-]{17})\s+(\w+)', re.I)
        seen = set()
        devices = []

        for line in text.splitlines():
            match = pattern.match(line)
            if not match:
                continue

            ip, mac, entry_type = match.groups()
            key = (ip, mac.lower())
            if key in seen:
                continue

            seen.add(key)
            devices.append({
                'ip': ip,
                'mac': mac,
                'type': entry_type.lower()
            })

        return devices

