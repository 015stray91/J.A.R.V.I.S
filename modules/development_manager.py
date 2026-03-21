"""
Development workflow manager for Jarvis X
Runs safe coding and project automation tasks in the workspace
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List
from utils.logger import get_logger
from utils.config_manager import get_config

logger = get_logger()
config = get_config()


class DevelopmentManager:
    """Executes curated development tasks for voice-driven workflows"""

    def __init__(self):
        configured_root = config.get("development.workspace_root", "")
        default_root = str(Path.cwd())
        self.workspace_root = Path(configured_root or default_root).expanduser().resolve()

        self.commands = config.get("development.commands", {
            "run_tests": "python -m pytest -q",
            "run_unit_tests": "python test_jarvis.py",
            "install_dependencies": "python -m pip install -r requirements.txt",
            "lint": "python -m pytest -q",
            "build": "python -m compileall .",
            "git_status": "git status",
            "git_pull": "git pull"
        })

        self.timeout_seconds = config.get("development.timeout_seconds", 120)
        self.package_alternatives = {
            "pyaudio": ["pipwin + pyaudio", "sounddevice"],
            "pocketsphinx": ["vosk", "SpeechRecognition online engine"],
            "pyttsx3": ["edge-tts", "gTTS"],
            "pvporcupine": ["simple wake-word detector (built in)"],
            "pyautogui": ["pynput", "pywinauto"],
            "pygetwindow": ["pywinauto"]
        }
        self.tool_alternatives = {
            "adb": ["Android Platform Tools", "KDE Connect (file/control fallback)"],
            "scrcpy": ["GlideX", "Phone Link", "KDE Connect"]
        }

    def run_task(self, task: str) -> Dict[str, object]:
        """Run a named development task"""
        command = self.commands.get(task)

        if not command:
            return {
                "success": False,
                "message": f"Unknown development task: {task}"
            }

        if not self.workspace_root.exists():
            return {
                "success": False,
                "message": f"Workspace path does not exist: {self.workspace_root}"
            }

        logger.info(f"Running development task '{task}': {command}")

        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=self._build_env()
            )

            output = self._tail_output(completed.stdout, completed.stderr)
            success = completed.returncode == 0

            return {
                "success": success,
                "message": "Task completed" if success else f"Task failed with code {completed.returncode}",
                "task": task,
                "command": command,
                "output": output,
                "exit_code": completed.returncode
            }

        except subprocess.TimeoutExpired as exc:
            partial_output = self._tail_output(exc.stdout or "", exc.stderr or "")
            return {
                "success": False,
                "message": f"Task timed out after {self.timeout_seconds} seconds",
                "task": task,
                "command": command,
                "output": partial_output
            }
        except Exception as e:
            logger.error(f"Development task error: {e}")
            return {
                "success": False,
                "message": f"Task execution error: {e}",
                "task": task,
                "command": command
            }

    def diagnose_environment(self) -> Dict[str, object]:
        """Inspect environment readiness and dependency consistency."""
        if not self.workspace_root.exists():
            return {
                "success": False,
                "message": f"Workspace path does not exist: {self.workspace_root}"
            }

        checks = []
        recommendations = []

        requirements_file = self.workspace_root / "requirements.txt"
        venv_dir = self.workspace_root / "venv"

        checks.append({
            "name": "venv_exists",
            "success": venv_dir.exists(),
            "output": str(venv_dir)
        })
        if not venv_dir.exists():
            recommendations.append("Create virtual environment: python -m venv venv")

        checks.append({
            "name": "requirements_exists",
            "success": requirements_file.exists(),
            "output": str(requirements_file)
        })
        if not requirements_file.exists():
            recommendations.append("Add requirements.txt before automated dependency repair")

        py_version = self._run_command("python --version", timeout=20)
        checks.append({
            "name": "python_version",
            "success": py_version.get("success", False),
            "output": py_version.get("output", "")
        })

        pip_check = self._run_command("python -m pip check", timeout=90)
        checks.append({
            "name": "pip_check",
            "success": pip_check.get("success", False),
            "output": pip_check.get("output", "")
        })
        if not pip_check.get("success", False):
            recommendations.append("Dependency conflicts detected. Run self repair apply.")

        compile_check = self._run_command("python -m compileall .", timeout=max(120, self.timeout_seconds))
        checks.append({
            "name": "compile_check",
            "success": compile_check.get("success", False),
            "output": compile_check.get("output", "")
        })
        if not compile_check.get("success", False):
            recommendations.append("Source compile check failed. Review recent syntax changes.")

        overall_ok = all(item.get("success", False) for item in checks)
        alternatives = self.get_dependency_alternatives(checks)
        if alternatives:
            recommendations.append(
                f"Alternative options available for {len(alternatives)} missing dependency/tool item(s)."
            )
        if overall_ok and not recommendations:
            recommendations.append("Environment looks healthy. No repair action needed.")

        return {
            "success": True,
            "healthy": overall_ok,
            "checks": checks,
            "recommendations": recommendations,
            "alternatives": alternatives
        }

    def get_dependency_alternatives(self, checks: List[Dict] = None) -> List[Dict[str, object]]:
        """Return usable alternatives when dependencies/tools are missing."""
        checks = checks or []
        alternatives: List[Dict[str, object]] = []

        combined_output = "\n".join(str(c.get("output", "")) for c in checks)
        missing_packages = self._extract_missing_packages(combined_output)
        for package in sorted(missing_packages):
            options = self.package_alternatives.get(package.lower())
            if options:
                alternatives.append({
                    "type": "python-package",
                    "missing": package,
                    "alternatives": options
                })

        for tool, options in self.tool_alternatives.items():
            if shutil.which(tool):
                continue
            alternatives.append({
                "type": "system-tool",
                "missing": tool,
                "alternatives": options
            })

        return alternatives

    def apply_self_repair(self) -> Dict[str, object]:
        """Run constrained self-repair operations for dependencies and build health."""
        if not self.workspace_root.exists():
            return {
                "success": False,
                "message": f"Workspace path does not exist: {self.workspace_root}"
            }

        steps = [
            ("upgrade_pip", "python -m pip install --upgrade pip", 180),
            ("install_requirements", "python -m pip install -r requirements.txt", 600),
            ("pip_check", "python -m pip check", 120),
            ("compile_check", "python -m compileall .", max(120, self.timeout_seconds))
        ]

        results = []
        failures = []
        for name, command, timeout in steps:
            result = self._run_command(command, timeout=timeout)
            results.append({
                "name": name,
                "command": command,
                "success": result.get("success", False),
                "output": result.get("output", "")
            })
            if not result.get("success", False):
                failures.append(name)

        repaired = len(failures) == 0
        message = "Self repair completed successfully" if repaired else f"Self repair finished with failures: {', '.join(failures)}"
        return {
            "success": repaired,
            "message": message,
            "steps": results,
            "failed_steps": failures
        }

    def _run_command(self, command: str, timeout: int) -> Dict[str, object]:
        """Execute a shell command in workspace context."""
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._build_env()
            )
            return {
                "success": completed.returncode == 0,
                "exit_code": completed.returncode,
                "output": self._tail_output(completed.stdout, completed.stderr)
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "output": self._tail_output(exc.stdout or "", exc.stderr or ""),
                "message": f"Timed out after {timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "output": str(e)
            }

    def _build_env(self) -> Dict[str, str]:
        """Build command environment with virtualenv support"""
        env = os.environ.copy()

        venv_scripts = self.workspace_root / "venv" / "Scripts"
        if venv_scripts.exists():
            existing_path = env.get("PATH", "")
            env["PATH"] = f"{venv_scripts};{existing_path}" if existing_path else str(venv_scripts)

        return env

    def _tail_output(self, stdout: str, stderr: str, max_chars: int = 1200) -> str:
        """Return a compact command output summary"""
        combined = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)

        if not combined:
            return "No output"

        if len(combined) <= max_chars:
            return combined

        return "...\n" + combined[-max_chars:]

    @staticmethod
    def _extract_missing_packages(output: str) -> List[str]:
        """Parse common pip messages for missing package names."""
        if not output:
            return []

        found = set()
        patterns = [
            r"requires\s+([A-Za-z0-9_.-]+),\s+which\s+is\s+not\s+installed",
            r"No\s+module\s+named\s+'([A-Za-z0-9_.-]+)'",
            r"Could\s+not\s+find\s+a\s+version\s+that\s+satisfies\s+the\s+requirement\s+([A-Za-z0-9_.-]+)"
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, output, flags=re.I):
                name = str(match.group(1)).strip()
                if name:
                    found.add(name)

        return sorted(found)

