"""
UEFI and bootloader diagnostics for Jarvis X
"""

from typing import Dict
import subprocess
from utils.logger import get_logger

logger = get_logger()


class UefiManager:
    """Collects UEFI and boot diagnostics on Windows"""

    def run_diagnostics(self) -> Dict[str, object]:
        checks = {
            "firmware": "powershell -NoProfile -Command \"Confirm-SecureBootUEFI\"",
            "bcd": "bcdedit /enum firmware",
            "volumes": "mountvol",
            "disk_layout": "wmic logicaldisk get deviceid,volumename,filesystem,size,freespace"
        }

        output = {}
        failures = 0

        for name, cmd in checks.items():
            result = self._run(cmd)
            output[name] = result
            if not result.get("success"):
                failures += 1

        return {
            "success": failures < len(checks),
            "message": "UEFI diagnostics completed" if failures < len(checks) else "UEFI diagnostics failed",
            "results": output,
            "failed_checks": failures
        }

    def _run(self, command: str) -> Dict[str, object]:
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=45
            )

            text = (completed.stdout or "").strip()
            err = (completed.stderr or "").strip()
            merged = text if text else err
            if len(merged) > 1200:
                merged = "...\n" + merged[-1200:]

            return {
                "success": completed.returncode == 0,
                "command": command,
                "output": merged or "No output",
                "exit_code": completed.returncode
            }
        except Exception as e:
            logger.error(f"UEFI command error: {e}")
            return {
                "success": False,
                "command": command,
                "output": str(e)
            }

