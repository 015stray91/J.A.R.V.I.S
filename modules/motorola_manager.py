"""
Motorola development diagnostics manager for Jarvis X
Focuses on EUD-related status checks and recovery guidance
"""

from typing import Dict
import subprocess
from utils.logger import get_logger

logger = get_logger()


class MotorolaManager:
    """Motorola-specific diagnostics helpers"""

    def diagnose_eud(self) -> Dict[str, object]:
        """Collect diagnostics relevant to Motorola EUD workflows"""
        checks = {
            "adb_devices": "adb devices",
            "fastboot_devices": "fastboot devices",
            "usb_motorola": "powershell -NoProfile -Command \"Get-PnpDevice | Where-Object { $_.FriendlyName -match 'Motorola|QDLoader|Qualcomm|Fastboot|ADB' } | Select-Object -First 25 Status,Class,FriendlyName | Format-Table -AutoSize | Out-String\""
        }

        results = {}
        failed = 0

        for name, command in checks.items():
            result = self._run(command)
            results[name] = result
            if not result.get("success"):
                failed += 1

        mode = self._infer_device_mode(results)
        guidance = self._guidance_for_mode(mode)

        return {
            "success": failed < len(checks),
            "mode": mode,
            "message": "Motorola EUD diagnostics completed",
            "guidance": guidance,
            "results": results
        }

    def _infer_device_mode(self, results: Dict[str, Dict[str, object]]) -> str:
        adb_output = str(results.get("adb_devices", {}).get("output", "")).lower()
        fastboot_output = str(results.get("fastboot_devices", {}).get("output", "")).lower()
        usb_output = str(results.get("usb_motorola", {}).get("output", "")).lower()

        if "device" in adb_output and "list of devices attached" in adb_output:
            lines = [line.strip() for line in adb_output.splitlines() if line.strip()]
            if len(lines) > 1:
                return "adb"

        if "fastboot" in fastboot_output and "< waiting for any device >" not in fastboot_output:
            return "fastboot"

        if "qdloader" in usb_output or "9008" in usb_output:
            return "edl_or_qdloader"

        if "motorola" in usb_output:
            return "motorola_usb_detected"

        return "unknown"

    def _guidance_for_mode(self, mode: str) -> str:
        if mode == "adb":
            return "Device is in ADB mode. You can use adb shell, collect logs, or reboot to bootloader for EUD steps."
        if mode == "fastboot":
            return "Device is in fastboot mode. Verify partitions and bootloader commands before flashing."
        if mode == "edl_or_qdloader":
            return "Device appears in Qualcomm EDL/QDLoader mode. Use trusted blankflash/EUD tooling for your exact model."
        if mode == "motorola_usb_detected":
            return "Motorola USB interface detected, but mode is unclear. Check drivers and cable, then re-run diagnostics."
        return "No clear Motorola mode detected. Ensure drivers are installed and the phone is connected in the expected mode."

    def _run(self, command: str) -> Dict[str, object]:
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=45
            )
            output = (completed.stdout or "").strip() or (completed.stderr or "").strip() or "No output"
            if len(output) > 1400:
                output = "...\n" + output[-1400:]

            return {
                "success": completed.returncode == 0,
                "output": output,
                "exit_code": completed.returncode,
                "command": command
            }
        except Exception as e:
            logger.error(f"Motorola diagnostics command failed: {e}")
            return {
                "success": False,
                "output": str(e),
                "command": command
            }

