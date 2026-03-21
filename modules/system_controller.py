"""
System Controller for Jarvis X
Handles system-level operations (volume, power, system info, etc.)
"""

import subprocess
import os
from typing import Dict
import psutil
from utils.logger import get_logger
from utils.config_manager import get_config
from utils.helpers import format_file_size

logger = get_logger()
config = get_config()


class SystemController:
    """Controls system-level operations"""

    def __init__(self):
        pass

    def set_volume(self, level: int) -> Dict[str, any]:
        """
        Set system volume (0-100)
        """
        try:
            if not 0 <= level <= 100:
                return {
                    'success': False,
                    'message': "Volume must be between 0 and 100"
                }

            logger.info(f"Setting volume to {level}%")

            try:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)

                # Set volume (0.0 to 1.0)
                volume.SetMasterVolumeLevelScalar(level / 100, None)

                return {
                    'success': True,
                    'message': f"Volume set to {level}%"
                }

            except ImportError:
                # Fallback using nircmd (if available)
                try:
                    # nircmd setsysvolume 65535 = 100%
                    volume_value = int((level / 100) * 65535)
                    subprocess.run(['nircmd', 'setsysvolume', str(volume_value)],
                                 check=True, capture_output=True)
                    return {
                        'success': True,
                        'message': f"Volume set to {level}%"
                    }
                except Exception:
                    return {
                        'success': False,
                        'message': "Volume control requires pycaw library or nircmd utility"
                    }

        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def adjust_volume(self, direction: str, step: int = 10) -> Dict[str, any]:
        """
        Adjust volume up or down
        """
        try:
            current_volume = self.get_volume()

            if direction.lower() == 'up':
                new_volume = min(100, current_volume + step)
            elif direction.lower() == 'down':
                new_volume = max(0, current_volume - step)
            else:
                return {
                    'success': False,
                    'message': "Direction must be 'up' or 'down'"
                }

            return self.set_volume(new_volume)

        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def mute(self) -> Dict[str, any]:
        """
        Mute/unmute system audio
        """
        try:
            logger.info("Toggling mute")

            try:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)

                # Toggle mute
                current_mute = volume.GetMute()
                volume.SetMute(not current_mute, None)

                state = "muted" if not current_mute else "unmuted"
                return {
                    'success': True,
                    'message': f"System {state}"
                }

            except ImportError:
                # Fallback using nircmd
                try:
                    subprocess.run(['nircmd', 'mutesysvolume', '2'],
                                 check=True, capture_output=True)
                    return {
                        'success': True,
                        'message': "Audio toggled"
                    }
                except Exception:
                    return {
                        'success': False,
                        'message': "Mute control requires pycaw library or nircmd utility"
                    }

        except Exception as e:
            logger.error(f"Error toggling mute: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def get_volume(self) -> int:
        """Get current system volume (0-100)"""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)

            return int(volume.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            return 50  # Default fallback

    def get_system_info(self) -> Dict[str, any]:
        """
        Get comprehensive system information
        """
        try:
            logger.info("Gathering system information")

            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory information
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = format_file_size(memory.used)
            memory_total = format_file_size(memory.total)

            # Disk information
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = format_file_size(disk.free)
            disk_total = format_file_size(disk.total)

            # Battery information (if available)
            battery_info = None
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        'percent': battery.percent,
                        'plugged_in': battery.power_plugged,
                        'time_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
            except Exception:
                pass

            info = {
                'success': True,
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'used': memory_used,
                    'total': memory_total
                },
                'disk': {
                    'percent': disk_percent,
                    'free': disk_free,
                    'total': disk_total
                },
                'battery': battery_info
            }

            logger.debug(f"System info: CPU {cpu_percent}%, RAM {memory_percent}%")
            return info

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def lock_screen(self) -> Dict[str, any]:
        """
        Lock the workstation
        """
        try:
            logger.info("Locking workstation")

            # Windows lock
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'],
                         check=True)

            return {
                'success': True,
                'message': "Workstation locked"
            }

        except Exception as e:
            logger.error(f"Error locking screen: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def shutdown(self, force: bool = False) -> Dict[str, any]:
        """
        Shutdown the system
        """
        try:
            logger.warning("Initiating system shutdown")

            if force:
                subprocess.run(['shutdown', '/s', '/f', '/t', '0'], check=True)
            else:
                subprocess.run(['shutdown', '/s', '/t', '0'], check=True)

            return {
                'success': True,
                'message': "Shutdown initiated"
            }

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def restart(self, force: bool = False) -> Dict[str, any]:
        """
        Restart the system
        """
        try:
            logger.warning("Initiating system restart")

            if force:
                subprocess.run(['shutdown', '/r', '/f', '/t', '0'], check=True)
            else:
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True)

            return {
                'success': True,
                'message': "Restart initiated"
            }

        except Exception as e:
            logger.error(f"Error during restart: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def sleep(self) -> Dict[str, any]:
        """
        Put system to sleep
        """
        try:
            logger.info("Putting system to sleep")

            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'],
                         check=True)

            return {
                'success': True,
                'message': "System going to sleep"
            }

        except Exception as e:
            logger.error(f"Error putting system to sleep: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def get_wifi_status(self) -> Dict[str, any]:
        """Get current Wi-Fi connection status."""
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip() or 'No output'
            return {
                'success': result.returncode == 0,
                'message': 'Wi-Fi status collected' if result.returncode == 0 else 'Failed to read Wi-Fi status',
                'output': output
            }
        except Exception as e:
            logger.error(f"Error getting Wi-Fi status: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def get_ram_acceleration_status(self) -> Dict[str, any]:
        """Return RAM acceleration (zram) status on Linux, with platform guidance elsewhere."""
        if os.name == 'nt':
            return {
                'success': True,
                'enabled': False,
                'message': 'zram is Linux-only. On Windows use page-file tuning or RAM-disk tools for similar behavior.'
            }

        try:
            result = subprocess.run(
                ['zramctl'],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip()
            enabled = result.returncode == 0 and 'zram' in output.lower()
            return {
                'success': result.returncode == 0,
                'enabled': enabled,
                'message': 'zram status collected' if result.returncode == 0 else 'Unable to read zram status',
                'output': output
            }
        except Exception as e:
            return {
                'success': False,
                'enabled': False,
                'message': f'Error checking zram status: {e}'
            }

    def enable_ram_acceleration(self, size_gb: int = 4) -> Dict[str, any]:
        """Enable zram swap on Linux; provide safe guidance on non-Linux systems."""
        if os.name == 'nt':
            return {
                'success': False,
                'message': 'zram cannot be enabled on Windows. Use Linux for zram or configure a RAM-disk utility.'
            }

        # Best-effort setup. Requires root/sudo privileges on Linux.
        commands = [
            'modprobe zram',
            f'echo $(( {size_gb} * 1024 * 1024 * 1024 )) | sudo tee /sys/block/zram0/disksize',
            'sudo mkswap /dev/zram0',
            'sudo swapon -p 100 /dev/zram0'
        ]

        outputs = []
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
            out = (result.stdout or '').strip() or (result.stderr or '').strip()
            outputs.append({'command': cmd, 'success': result.returncode == 0, 'output': out})
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': 'Failed enabling zram. Root permissions and zram support are required.',
                    'steps': outputs
                }

        return {
            'success': True,
            'message': f'zram enabled with approximately {size_gb} GB compressed swap.',
            'steps': outputs
        }

    def disable_ram_acceleration(self) -> Dict[str, any]:
        """Disable zram swap on Linux."""
        if os.name == 'nt':
            return {
                'success': False,
                'message': 'zram disable is Linux-only.'
            }

        commands = [
            'sudo swapoff /dev/zram0',
            'echo 1 | sudo tee /sys/block/zram0/reset'
        ]

        outputs = []
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
            out = (result.stdout or '').strip() or (result.stderr or '').strip()
            outputs.append({'command': cmd, 'success': result.returncode == 0, 'output': out})

        any_success = any(step['success'] for step in outputs)
        return {
            'success': any_success,
            'message': 'zram disable attempted. Verify with zram status.',
            'steps': outputs
        }

    def list_wifi_profiles(self) -> Dict[str, any]:
        """List saved Wi-Fi profiles."""
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip() or 'No output'
            return {
                'success': result.returncode == 0,
                'message': 'Wi-Fi profiles listed' if result.returncode == 0 else 'Failed to list Wi-Fi profiles',
                'output': output
            }
        except Exception as e:
            logger.error(f"Error listing Wi-Fi profiles: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def wifi_connect(self, profile_name: str) -> Dict[str, any]:
        """Connect to a saved Wi-Fi profile by name."""
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'connect', f'name={profile_name}'],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip() or 'No output'
            return {
                'success': result.returncode == 0,
                'message': f"Wi-Fi connect requested for '{profile_name}'" if result.returncode == 0 else f"Failed to connect Wi-Fi profile '{profile_name}'",
                'output': output
            }
        except Exception as e:
            logger.error(f"Error connecting Wi-Fi: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def wifi_disconnect(self) -> Dict[str, any]:
        """Disconnect current Wi-Fi network."""
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'disconnect'],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip() or 'No output'
            return {
                'success': result.returncode == 0,
                'message': 'Wi-Fi disconnected' if result.returncode == 0 else 'Failed to disconnect Wi-Fi',
                'output': output
            }
        except Exception as e:
            logger.error(f"Error disconnecting Wi-Fi: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def wifi_toggle(self, enabled: bool) -> Dict[str, any]:
        """Enable or disable Wi-Fi adapter (Windows)."""
        try:
            state = 'ENABLED' if enabled else 'DISABLED'
            # This targets the common adapter name; user can adjust adapter name if needed.
            command = (
                "Get-NetAdapter | Where-Object {$_.InterfaceDescription -match 'Wireless|Wi-Fi'} "
                f"| ForEach-Object {{ Set-NetAdapter -Name $_.Name -AdminStatus {state} -Confirm:$false }}"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip() or 'No output'
            return {
                'success': result.returncode == 0,
                'message': f"Wi-Fi {'enabled' if enabled else 'disabled'}" if result.returncode == 0 else f"Failed to {'enable' if enabled else 'disable'} Wi-Fi",
                'output': output
            }
        except Exception as e:
            logger.error(f"Error toggling Wi-Fi: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def bluetooth_toggle(self, enabled: bool) -> Dict[str, any]:
        """Enable or disable Bluetooth radios (best effort on Windows)."""
        try:
            state = 'Up' if enabled else 'Down'
            command = (
                "Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue "
                f"| ForEach-Object {{ {'Enable-PnpDevice' if enabled else 'Disable-PnpDevice'} -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue }}"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                check=False
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip() or 'No output'
            return {
                'success': result.returncode == 0,
                'message': f"Bluetooth toggle command sent ({state})" if result.returncode == 0 else 'Failed to toggle Bluetooth',
                'output': output
            }
        except Exception as e:
            logger.error(f"Error toggling Bluetooth: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

