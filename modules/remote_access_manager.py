"""
Remote access manager for Jarvis X
Helps with desktop remote settings and KDE Connect integration
"""

from typing import Dict
import subprocess
import os
from utils.logger import get_logger
from utils.config_manager import get_config

logger = get_logger()
config = get_config()


class RemoteAccessManager:
    """Manages remote-access helper actions"""

    def __init__(self):
        self.remote_config = config.get('remote', {})

    def _get_default_kde_device(self) -> str:
        """Get default KDE Connect device id from configuration."""
        kde_cfg = self.remote_config.get('kde_connect', {})
        return str(kde_cfg.get('default_device_id', '')).strip()

    def set_default_kde_device(self, device_id: str) -> Dict[str, object]:
        """Persist default KDE Connect device id to config."""
        device_id = device_id.strip()
        if not device_id:
            return {
                "success": False,
                "message": "No KDE Connect device id provided"
            }

        ok = config.set('remote.kde_connect.default_device_id', device_id, save=True)
        if not ok:
            return {
                "success": False,
                "message": "Failed to save default KDE Connect device id"
            }

        self.remote_config = config.get('remote', {})
        return {
            "success": True,
            "message": f"Default KDE Connect device set to {device_id}",
            "device_id": device_id
        }

    def _get_linux_profile(self, profile_name: str = "default") -> Dict[str, object]:
        """Resolve Linux SSH profile from config."""
        linux_cfg = self.remote_config.get('linux', {})
        profiles = linux_cfg.get('profiles', {})
        profile = profiles.get(profile_name, {})

        if not profile:
            return {
                "success": False,
                "message": f"Linux profile '{profile_name}' not found in config.remote.linux.profiles"
            }

        host = profile.get('host', '').strip()
        user = profile.get('user', '').strip()
        port = int(profile.get('port', 22))
        key_path = profile.get('key_path', '').strip()

        if not host or not user:
            return {
                "success": False,
                "message": f"Linux profile '{profile_name}' must define host and user"
            }

        return {
            "success": True,
            "profile": {
                "host": host,
                "user": user,
                "port": port,
                "key_path": key_path
            }
        }

    @staticmethod
    def _build_ssh_base(profile: Dict[str, object]) -> list:
        """Build base SSH command list from profile."""
        cmd = [
            'ssh',
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-p', str(profile['port'])
        ]

        key_path = str(profile.get('key_path', '')).strip()
        if key_path:
            cmd.extend(['-i', key_path])

        cmd.append(f"{profile['user']}@{profile['host']}")
        return cmd

    @staticmethod
    def _build_scp_base(profile: Dict[str, object]) -> list:
        """Build base SCP command list from profile."""
        cmd = [
            'scp',
            '-P', str(profile['port']),
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new'
        ]

        key_path = str(profile.get('key_path', '')).strip()
        if key_path:
            cmd.extend(['-i', key_path])

        return cmd

    def linux_ping(self, profile_name: str = 'default') -> Dict[str, object]:
        """Verify SSH connectivity to Linux profile."""
        prof_result = self._get_linux_profile(profile_name)
        if not prof_result['success']:
            return prof_result

        profile = prof_result['profile']
        cmd = self._build_ssh_base(profile) + ['echo JARVIS_LINUX_OK']

        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = (completed.stdout or '').strip() or (completed.stderr or '').strip() or 'No output'

            return {
                'success': completed.returncode == 0 and 'JARVIS_LINUX_OK' in output,
                'message': 'Linux connection successful' if completed.returncode == 0 else 'Linux connection failed',
                'output': output,
                'exit_code': completed.returncode,
                'profile': profile_name
            }
        except Exception as e:
            logger.error(f"Linux ping failed: {e}")
            return {
                'success': False,
                'message': f"Linux ping failed: {e}"
            }

    def linux_run(self, command: str, profile_name: str = 'default') -> Dict[str, object]:
        """Run a shell command on Linux machine over SSH."""
        if not command.strip():
            return {
                'success': False,
                'message': 'No Linux command provided'
            }

        prof_result = self._get_linux_profile(profile_name)
        if not prof_result['success']:
            return prof_result

        profile = prof_result['profile']
        cmd = self._build_ssh_base(profile) + [command]

        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = (completed.stdout or '').strip() or (completed.stderr or '').strip() or 'No output'
            return {
                'success': completed.returncode == 0,
                'message': 'Linux command completed' if completed.returncode == 0 else 'Linux command failed',
                'output': output,
                'exit_code': completed.returncode,
                'profile': profile_name,
                'command': command
            }
        except Exception as e:
            logger.error(f"Linux command execution failed: {e}")
            return {
                'success': False,
                'message': f"Linux command execution failed: {e}"
            }

    def linux_sync_to(self, local_path: str, remote_path: str, profile_name: str = 'default') -> Dict[str, object]:
        """Sync file/folder from local Windows machine to Linux via SCP."""
        if not local_path.strip() or not remote_path.strip():
            return {
                'success': False,
                'message': 'Both local_path and remote_path are required for sync'
            }

        prof_result = self._get_linux_profile(profile_name)
        if not prof_result['success']:
            return prof_result

        profile = prof_result['profile']
        scp_cmd = self._build_scp_base(profile)

        # Recursive copy for project folders by default.
        scp_cmd.append('-r')
        scp_cmd.append(local_path)
        scp_cmd.append(f"{profile['user']}@{profile['host']}:{remote_path}")

        try:
            completed = subprocess.run(scp_cmd, capture_output=True, text=True, check=False)
            output = (completed.stdout or '').strip() or (completed.stderr or '').strip() or 'No output'
            return {
                'success': completed.returncode == 0,
                'message': 'Linux sync completed' if completed.returncode == 0 else 'Linux sync failed',
                'output': output,
                'exit_code': completed.returncode,
                'profile': profile_name,
                'local_path': local_path,
                'remote_path': remote_path
            }
        except Exception as e:
            logger.error(f"Linux sync failed: {e}")
            return {
                'success': False,
                'message': f"Linux sync failed: {e}"
            }

    def get_linux_profile_help(self) -> Dict[str, object]:
        """Return quick help text for Linux profile setup."""
        example = {
            "remote": {
                "linux": {
                    "profiles": {
                        "default": {
                            "host": "192.168.1.50",
                            "user": "your_linux_user",
                            "port": 22,
                            "key_path": ""
                        }
                    }
                }
            }
        }
        return {
            'success': True,
            'message': 'Configure Linux SSH profile in config.json under remote.linux.profiles',
            'example': example
        }

    def open_remote_desktop_settings(self) -> Dict[str, object]:
        """Open Windows Remote Desktop settings page"""
        try:
            subprocess.run('start "" "ms-settings:remotedesktop"', shell=True, check=False)
            return {
                "success": True,
                "message": "Opened Remote Desktop settings"
            }
        except Exception as e:
            logger.error(f"Failed to open remote desktop settings: {e}")
            return {
                "success": False,
                "message": f"Could not open Remote Desktop settings: {e}"
            }

    def open_kde_connect(self) -> Dict[str, object]:
        """Launch KDE Connect app if installed"""
        candidates = [
            'kdeconnect-app.exe',
            'kdeconnect-indicator.exe',
            'kdeconnect-cli.exe'
        ]

        for candidate in candidates:
            try:
                completed = subprocess.run(
                    f'where {candidate}',
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if completed.returncode == 0:
                    subprocess.run(f'start "" {candidate}', shell=True, check=False)
                    return {
                        "success": True,
                        "message": f"Opened KDE Connect using {candidate}"
                    }
            except Exception:
                continue

        return {
            "success": False,
            "message": "KDE Connect was not found in PATH. Install KDE Connect for Windows and retry."
        }

    def kde_connect_status(self) -> Dict[str, object]:
        """Get KDE Connect paired device status using CLI if available"""
        return self._run_cli("kdeconnect-cli --list-devices")

    def kde_connect_pair(self, device_id: str) -> Dict[str, object]:
        """Pair with a device by KDE Connect device id"""
        if not device_id:
            return {
                "success": False,
                "message": "No device id provided for pairing"
            }

        return self._run_cli(f'kdeconnect-cli --pair --device "{device_id}"')

    def kde_connect_send_text(self, text: str, device_id: str = "") -> Dict[str, object]:
        """Send text/snippet to paired KDE Connect device."""
        text = text.strip()
        if not text:
            return {
                "success": False,
                "message": "No text provided to send"
            }

        target_device = device_id.strip() or self._get_default_kde_device()
        if not target_device:
            return {
                "success": False,
                "message": "No KDE device selected. Set default device first."
            }

        safe_text = text.replace('"', '\\"')
        return self._run_cli(f'kdeconnect-cli --share "{safe_text}" --device "{target_device}"')

    def kde_connect_send_file(self, file_path: str, device_id: str = "") -> Dict[str, object]:
        """Send file/folder to paired KDE Connect device."""
        file_path = file_path.strip().strip('"')
        if not file_path:
            return {
                "success": False,
                "message": "No file path provided to send"
            }

        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"File path not found: {file_path}"
            }

        target_device = device_id.strip() or self._get_default_kde_device()
        if not target_device:
            return {
                "success": False,
                "message": "No KDE device selected. Set default device first."
            }

        safe_path = file_path.replace('"', '\\"')
        return self._run_cli(f'kdeconnect-cli --share "{safe_path}" --device "{target_device}"')

    def _run_cli(self, command: str) -> Dict[str, object]:
        """Run KDE Connect CLI command and return compact output"""
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )

            output = (completed.stdout or "").strip() or (completed.stderr or "").strip() or "No output"
            return {
                "success": completed.returncode == 0,
                "message": "Command completed" if completed.returncode == 0 else "Command failed",
                "output": output,
                "exit_code": completed.returncode
            }
        except Exception as e:
            logger.error(f"KDE Connect CLI error: {e}")
            return {
                "success": False,
                "message": f"KDE Connect CLI error: {e}"
            }

