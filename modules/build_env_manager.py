"""
Build environment and script composition manager for Jarvis X
Analyzes build setups and generates practical scripts from intent text
"""

from pathlib import Path
from typing import Dict, List
import json
from utils.logger import get_logger

logger = get_logger()


class BuildEnvManager:
    """Analyzes build environments and composes scripts"""

    def analyze_environment(self, root_path: str) -> Dict[str, object]:
        root = Path(root_path).expanduser()
        if not root.exists() or not root.is_dir():
            return {
                "success": False,
                "message": f"Build root not found: {root}"
            }

        files = {
            "dockerfile": (root / "Dockerfile").exists(),
            "docker_compose": (root / "docker-compose.yml").exists() or (root / "docker-compose.yaml").exists(),
            "makefile": (root / "Makefile").exists(),
            "requirements_txt": (root / "requirements.txt").exists(),
            "pyproject_toml": (root / "pyproject.toml").exists(),
            "package_json": (root / "package.json").exists(),
            "go_mod": (root / "go.mod").exists(),
            "cargo_toml": (root / "Cargo.toml").exists(),
            "android_bp": (root / "Android.bp").exists(),
            "android_mk": (root / "Android.mk").exists(),
        }

        tool_hints = self._recommend_tools(files)

        return {
            "success": True,
            "path": str(root),
            "detected_files": files,
            "tool_hints": tool_hints,
            "message": "Build environment analysis completed"
        }

    def compose_script(self, request: str, script_type: str = "bash") -> Dict[str, object]:
        intent = (request or "").strip()
        if not intent:
            return {
                "success": False,
                "message": "No script request provided"
            }

        kind = script_type.lower().strip()
        if kind not in {"bash", "powershell", "batch"}:
            kind = "bash"

        script = self._generate_script(intent, kind)
        filename = {
            "bash": "generated_build.sh",
            "powershell": "generated_build.ps1",
            "batch": "generated_build.bat"
        }[kind]

        return {
            "success": True,
            "script_type": kind,
            "filename": filename,
            "script": script,
            "message": "Generated script draft"
        }

    def save_script(self, output_path: str, script_content: str) -> Dict[str, object]:
        path = Path(output_path).expanduser()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(script_content, encoding="utf-8")
            return {
                "success": True,
                "path": str(path),
                "message": "Script saved"
            }
        except Exception as e:
            logger.error(f"Failed to save script {path}: {e}")
            return {
                "success": False,
                "message": f"Failed to save script: {e}"
            }

    def _recommend_tools(self, flags: Dict[str, bool]) -> List[str]:
        hints: List[str] = []

        if flags["android_bp"] or flags["android_mk"]:
            hints.append("Android build system detected. Use lunch, m, and soong_ui workflows.")
        if flags["go_mod"]:
            hints.append("Go module detected. Use go test ./..., go vet ./..., and go build ./... .")
        if flags["requirements_txt"] or flags["pyproject_toml"]:
            hints.append("Python environment detected. Use virtualenv and pinned dependency installs.")
        if flags["package_json"]:
            hints.append("Node environment detected. Use npm ci and npm test for reproducible builds.")
        if flags["dockerfile"]:
            hints.append("Container build detected. Use tagged docker build and immutable base images.")
        if not hints:
            hints.append("No common build manifests found. Provide explicit toolchain and entrypoint script.")

        return hints

    def _generate_script(self, intent: str, script_type: str) -> str:
        lower_intent = intent.lower()

        if script_type == "bash":
            lines = [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "",
                "echo \"Starting composed build workflow\"",
            ]
            lines.extend(self._bash_steps(lower_intent))
            return "\n".join(lines) + "\n"

        if script_type == "powershell":
            lines = [
                "$ErrorActionPreference = 'Stop'",
                "Write-Host 'Starting composed build workflow'",
            ]
            lines.extend(self._pwsh_steps(lower_intent))
            return "\n".join(lines) + "\n"

        lines = [
            "@echo off",
            "setlocal enabledelayedexpansion",
            "echo Starting composed build workflow",
        ]
        lines.extend(self._batch_steps(lower_intent))
        return "\n".join(lines) + "\n"

    def _bash_steps(self, text: str) -> List[str]:
        steps = []
        if "clean" in text:
            steps.append("rm -rf out build dist || true")
        if "deps" in text or "dependencies" in text:
            steps.append("python -m pip install -r requirements.txt")
        if "test" in text:
            steps.append("python -m pytest -q")
        if "go" in text:
            steps.append("go test ./...")
            steps.append("go build ./...")
        if "kernel" in text or "rom" in text:
            steps.append("source build/envsetup.sh")
            steps.append("lunch aosp_arm64-userdebug")
            steps.append("m -j$(nproc)")
        if "docker" in text or "container" in text:
            steps.append("docker build -t local/build-env:latest .")
        if not steps:
            steps.append("echo 'No recognized build steps requested. Add project-specific commands.'")
        return steps

    def _pwsh_steps(self, text: str) -> List[str]:
        steps = []
        if "clean" in text:
            steps.append("if (Test-Path out) { Remove-Item -Recurse -Force out }")
        if "deps" in text or "dependencies" in text:
            steps.append("python -m pip install -r requirements.txt")
        if "test" in text:
            steps.append("python -m pytest -q")
        if "go" in text:
            steps.append("go test ./...")
            steps.append("go build ./...")
        if "docker" in text or "container" in text:
            steps.append("docker build -t local/build-env:latest .")
        if not steps:
            steps.append("Write-Host 'No recognized build steps requested. Add project-specific commands.'")
        return steps

    def _batch_steps(self, text: str) -> List[str]:
        steps = []
        if "deps" in text or "dependencies" in text:
            steps.append("python -m pip install -r requirements.txt")
        if "test" in text:
            steps.append("python -m pytest -q")
        if "go" in text:
            steps.append("go test ./...")
            steps.append("go build ./...")
        if not steps:
            steps.append("echo No recognized build steps requested. Add project-specific commands.")
        return steps

