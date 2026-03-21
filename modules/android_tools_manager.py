"""
Android platform tools manager for Jarvis X
Provides adb/fastboot command execution and command syntax guidance
"""

from typing import Dict
import subprocess
import os
import shutil


class AndroidToolsManager:
    """Runs adb/fastboot commands with a practical safety filter"""

    def __init__(self):
        self.adb_allowed_prefixes = [
            "devices", "shell", "reboot", "logcat", "pull", "push", "install",
            "uninstall", "get-state", "get-serialno", "version", "start-server",
            "kill-server", "wait-for-device"
        ]
        self.fastboot_allowed_prefixes = [
            "devices", "getvar", "oem", "reboot", "reboot-bootloader", "continue",
            "flash", "boot", "erase", "set_active"
        ]

    def run_adb(self, args: str) -> Dict[str, object]:
        cmd = (args or "").strip()
        if not cmd:
            return {"success": False, "message": "No adb command arguments provided"}

        if not self._allowed(cmd, self.adb_allowed_prefixes):
            return {"success": False, "message": "adb subcommand is not allowed by current safety policy"}

        return self._run(f"adb {cmd}")

    def run_fastboot(self, args: str) -> Dict[str, object]:
        cmd = (args or "").strip()
        if not cmd:
            return {"success": False, "message": "No fastboot command arguments provided"}

        if not self._allowed(cmd, self.fastboot_allowed_prefixes):
            return {"success": False, "message": "fastboot subcommand is not allowed by current safety policy"}

        return self._run(f"fastboot {cmd}")

    def explain_command(self, command: str) -> Dict[str, object]:
        c = (command or "").strip().lower()
        if not c:
            return {"success": False, "message": "No command to explain"}

        reference = {
            "adb devices": "Lists connected Android devices and their authorization state.",
            "adb shell": "Opens a shell on the connected device for diagnostics and file operations.",
            "adb logcat": "Streams Android logs; use filters like `adb logcat | findstr TAG`.",
            "adb pull": "Copies files from device to host: adb pull /sdcard/file.txt .",
            "adb push": "Copies files from host to device: adb push local.txt /sdcard/local.txt",
            "adb reboot bootloader": "Reboots from Android OS into bootloader/fastboot mode.",
            "fastboot devices": "Lists devices available in fastboot mode.",
            "fastboot getvar all": "Queries bootloader variables (may be verbose).",
            "fastboot flash": "Flashes an image to a partition. Must match device/partition exactly.",
            "fastboot boot": "Temporarily boots an image without permanently flashing it.",
            "fastboot erase": "Erases a partition. Use with caution and correct target only.",
            "fastboot set_active": "Sets active slot (A/B devices): fastboot set_active a|b"
        }

        for key, text in reference.items():
            if c.startswith(key):
                return {"success": True, "command": command, "explanation": text}

        return {
            "success": True,
            "command": command,
            "explanation": (
                "Use structure: tool + subcommand + args. Example: `adb shell getprop` or "
                "`fastboot getvar all`. Verify device mode first (`adb devices` or `fastboot devices`)."
            )
        }

    def pull_from_phone(self, device_path: str, local_path: str) -> Dict[str, object]:
        """Copy data from Android device storage to local path using adb pull."""
        src = (device_path or "").strip().strip('"')
        dst = (local_path or "").strip().strip('"')

        if not src or not dst:
            return {
                "success": False,
                "message": "Both device path and local destination are required"
            }

        try:
            os.makedirs(dst, exist_ok=True)
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not create local destination: {e}"
            }

        return self._run(f'adb pull "{src}" "{dst}"')

    def get_phone_info(self) -> Dict[str, object]:
        """Collect quick phone diagnostics over adb."""
        checks = {
            "devices": "adb devices",
            "model": "adb shell getprop ro.product.model",
            "android_version": "adb shell getprop ro.build.version.release",
            "serial": "adb get-serialno",
            "battery": "adb shell dumpsys battery",
            "storage": "adb shell df /sdcard"
        }

        report = {}
        ok = True
        for key, cmd in checks.items():
            result = self._run(cmd)
            report[key] = result.get("output", result.get("message", "No output"))
            if not result.get("success") and key == "devices":
                ok = False

        return {
            "success": ok,
            "message": "Phone info collected" if ok else "Phone connection failed. Check adb devices and USB debugging.",
            "report": report
        }

    def launch_scrcpy(self) -> Dict[str, object]:
        """Launch scrcpy for USB/Wi-Fi Android screen mirroring."""
        candidates = ["scrcpy"]
        for candidate in candidates:
            try:
                completed = subprocess.run(
                    f"{candidate} --version",
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if completed.returncode == 0:
                    subprocess.Popen(candidate, shell=True)
                    return {
                        "success": True,
                        "message": "Launched scrcpy for phone mirroring"
                    }
            except Exception:
                continue

        return {
            "success": False,
            "message": "scrcpy was not found in PATH. Install scrcpy and retry."
        }

    def launch_glidex(self) -> Dict[str, object]:
        """Launch GlideX app if installed."""
        candidates = [
            "GlideX",
            "GlideXService",
            "C:\\Program Files\\ASUS\\GlideX\\GlideX.exe"
        ]

        for candidate in candidates:
            try:
                if candidate.lower().endswith('.exe') and os.path.exists(candidate):
                    subprocess.Popen(f'"{candidate}"', shell=True)
                    return {
                        "success": True,
                        "message": "Launched GlideX"
                    }

                completed = subprocess.run(
                    f"where {candidate}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if completed.returncode == 0:
                    subprocess.Popen(candidate, shell=True)
                    return {
                        "success": True,
                        "message": "Launched GlideX"
                    }
            except Exception:
                continue

        return {
            "success": False,
            "message": "GlideX was not found. Install ASUS GlideX and retry."
        }

    def firetv_connect(self, ip_address: str) -> Dict[str, object]:
        """Connect adb to Fire TV over local network."""
        ip = (ip_address or '').strip()
        if not ip:
            return {
                'success': False,
                'message': 'No Fire TV IP address provided'
            }
        return self._run(f'adb connect {ip}')

    def firetv_key(self, key_name: str) -> Dict[str, object]:
        """Send a remote-control key to Fire TV via adb shell input keyevent."""
        mapping = {
            'home': '3',
            'back': '4',
            'up': '19',
            'down': '20',
            'left': '21',
            'right': '22',
            'select': '23',
            'ok': '23',
            'playpause': '85',
            'menu': '82'
        }
        key = (key_name or '').strip().lower().replace(' ', '')
        code = mapping.get(key)
        if not code:
            return {
                'success': False,
                'message': f'Unsupported Fire TV key: {key_name}'
            }
        return self._run(f'adb shell input keyevent {code}')

    def _allowed(self, cmd: str, prefixes: list[str]) -> bool:
        lower = cmd.lower().strip()
        return any(lower.startswith(prefix + " ") or lower == prefix for prefix in prefixes)

    @staticmethod
    def _resolve_tool(tool_name: str) -> str:
        """Resolve executable path for tools installed via winget or PATH."""
        resolved = shutil.which(tool_name)
        if resolved:
            return resolved

        local_app_data = os.environ.get('LOCALAPPDATA', '')
        candidates = [
            os.path.join(local_app_data, 'Microsoft', 'WinGet', 'Links', f'{tool_name}.exe'),
            os.path.join(local_app_data, 'Microsoft', 'WindowsApps', f'{tool_name}.exe'),
        ]

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        return tool_name

    def _normalize_command(self, command: str) -> str:
        """Rewrite command with resolved tool path for common Android executables."""
        stripped = (command or '').strip()
        if not stripped:
            return stripped

        parts = stripped.split(' ', 1)
        head = parts[0].lower()
        tail = parts[1] if len(parts) > 1 else ''

        if head in {'adb', 'fastboot', 'scrcpy'}:
            exe = self._resolve_tool(head)
            return f'"{exe}" {tail}'.strip()

        return stripped

    def _run(self, command: str) -> Dict[str, object]:
        try:
            normalized = self._normalize_command(command)
            completed = subprocess.run(normalized, shell=True, capture_output=True, text=True, timeout=90)
            output = (completed.stdout or "").strip() or (completed.stderr or "").strip() or "No output"
            if len(output) > 1600:
                output = "...\n" + output[-1600:]
            return {
                "success": completed.returncode == 0,
                "command": normalized,
                "output": output,
                "exit_code": completed.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "message": f"Command failed: {e}"
            }

