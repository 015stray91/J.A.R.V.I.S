"""
ROM operations manager for Jarvis X
Provides safe helpers for LP tools, WSL, and container diagnostics
"""

from pathlib import Path
from typing import Dict
import subprocess
from utils.logger import get_logger
from utils.config_manager import get_config

logger = get_logger()
config = get_config()


class RomOpsManager:
    """Handles ROM development operational commands"""

    def __init__(self):
        self.timeout_seconds = config.get("development.timeout_seconds", 180)
        self.workspace_root = Path(config.get("development.workspace_root", "") or Path.cwd())

    def lp_dump(self, image_path: str) -> Dict[str, object]:
        """Run lpdump against a dynamic partition image/super image"""
        command = f'lpdump "{image_path}"'
        return self._run(command)

    def lp_unpack(self, image_path: str, output_dir: str) -> Dict[str, object]:
        """Run lpunpack for super image extraction"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        command = f'lpunpack "{image_path}" "{output_dir}"'
        return self._run(command)

    def wsl_list(self) -> Dict[str, object]:
        """List WSL distros with state/version"""
        return self._run("wsl -l -v")

    def wsl_exec(self, distro: str, cmd: str) -> Dict[str, object]:
        """Execute a read-only diagnostic command in WSL"""
        command = f'wsl -d "{distro}" -- {cmd}'
        return self._run(command)

    def container_list(self) -> Dict[str, object]:
        """List running/all containers"""
        return self._run("docker ps -a")

    def container_logs(self, container_name: str, tail: int = 150) -> Dict[str, object]:
        """Get recent logs from a container"""
        command = f'docker logs --tail {tail} "{container_name}"'
        return self._run(command)

    def _run(self, command: str) -> Dict[str, object]:
        """Run shell command with bounded output"""
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )

            output = self._tail_output(completed.stdout, completed.stderr)
            return {
                "success": completed.returncode == 0,
                "command": command,
                "output": output,
                "exit_code": completed.returncode,
                "message": "Command completed" if completed.returncode == 0 else f"Command failed with code {completed.returncode}"
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "command": command,
                "output": self._tail_output(exc.stdout or "", exc.stderr or ""),
                "message": f"Command timed out after {self.timeout_seconds} seconds"
            }
        except Exception as e:
            logger.error(f"ROM operation command failed: {e}")
            return {
                "success": False,
                "command": command,
                "message": f"Execution error: {e}"
            }

    def _tail_output(self, stdout: str, stderr: str, max_chars: int = 1800) -> str:
        combined = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
        if not combined:
            return "No output"
        if len(combined) <= max_chars:
            return combined
        return "...\n" + combined[-max_chars:]

