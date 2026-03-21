"""
Source analyzer for Jarvis X
Inspects Debian packages, Go modules, TOML files, dot-config files,
and kernel source trees for mainline/compression signals
"""

from pathlib import Path
from typing import Dict, List
import os
import re
import subprocess
import tomllib
from utils.logger import get_logger

logger = get_logger()


class SourceAnalyzer:
    """Provides static inspections for development artifacts"""

    def analyze_toml(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"TOML file not found: {path}"
            }

        try:
            with path.open("rb") as f:
                data = tomllib.load(f)

            top_keys = list(data.keys())
            return {
                "success": True,
                "type": "toml",
                "path": str(path),
                "keys": top_keys[:25],
                "message": f"Parsed TOML with {len(top_keys)} top-level keys"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"TOML parse failed: {e}"
            }

    def analyze_dot_config(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"Config file not found: {path}"
            }

        enabled = 0
        modules = 0
        disabled = 0
        compression = []

        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("# CONFIG_") and line.endswith(" is not set"):
                        disabled += 1
                        continue

                    if line.startswith("CONFIG_") and "=" in line:
                        key, value = line.split("=", 1)
                        if value == "y":
                            enabled += 1
                        elif value == "m":
                            modules += 1

                        if key in {
                            "CONFIG_KERNEL_GZIP",
                            "CONFIG_KERNEL_XZ",
                            "CONFIG_KERNEL_LZ4",
                            "CONFIG_KERNEL_LZMA",
                            "CONFIG_KERNEL_LZO",
                            "CONFIG_KERNEL_ZSTD"
                        } and value == "y":
                            compression.append(key.replace("CONFIG_KERNEL_", "").lower())

            return {
                "success": True,
                "type": "dot_config",
                "path": str(path),
                "enabled_count": enabled,
                "module_count": modules,
                "disabled_count": disabled,
                "kernel_compression": compression,
                "message": "Parsed kernel-style .config"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Config parse failed: {e}"
            }

    def analyze_go_module(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"go.mod not found: {path}"
            }

        module_name = ""
        go_version = ""
        require_count = 0

        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line.startswith("module "):
                        module_name = line.replace("module ", "", 1).strip()
                    elif line.startswith("go "):
                        go_version = line.replace("go ", "", 1).strip()
                    elif re.match(r"^[A-Za-z0-9_.\-/]+\s+v\d", line):
                        require_count += 1

            return {
                "success": True,
                "type": "go_mod",
                "path": str(path),
                "module": module_name,
                "go_version": go_version,
                "require_count": require_count,
                "message": "Parsed Go module file"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"go.mod parse failed: {e}"
            }

    def inspect_deb(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"Debian package not found: {path}"
            }

        if path.suffix.lower() != ".deb":
            return {
                "success": False,
                "message": "File is not a .deb package"
            }

        try:
            command = f'dpkg-deb -I "{path}"'
            completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=40)
            output = (completed.stdout or "").strip() or (completed.stderr or "").strip()

            if completed.returncode != 0:
                # Fallback metadata when dpkg-deb is unavailable on Windows
                size_mb = path.stat().st_size / (1024 * 1024)
                return {
                    "success": True,
                    "type": "deb",
                    "path": str(path),
                    "size_mb": round(size_mb, 2),
                    "message": "dpkg-deb unavailable; reported basic package metadata only"
                }

            return {
                "success": True,
                "type": "deb",
                "path": str(path),
                "details": self._tail(output),
                "message": "Inspected Debian package"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to inspect .deb: {e}"
            }

    def analyze_kernel_source(self, kernel_root: str) -> Dict[str, object]:
        root = Path(kernel_root).expanduser()
        if not root.exists() or not root.is_dir():
            return {
                "success": False,
                "message": f"Kernel source directory not found: {root}"
            }

        makefile = root / "Makefile"
        dot_config = root / ".config"

        if not makefile.exists():
            return {
                "success": False,
                "message": f"Kernel Makefile not found in {root}"
            }

        version = self._parse_kernel_version(makefile)
        compression = self._parse_kernel_compression(dot_config) if dot_config.exists() else []

        readiness_signals = {
            "has_git": (root / ".git").exists(),
            "has_kconfig": (root / "Kconfig").exists(),
            "has_defconfig_tree": (root / "arch").exists(),
            "has_dot_config": dot_config.exists()
        }

        return {
            "success": True,
            "type": "kernel_source",
            "path": str(root),
            "kernel_version": version,
            "compression": compression,
            "readiness": readiness_signals,
            "message": "Kernel source inspection completed"
        }

    def _parse_kernel_version(self, makefile: Path) -> str:
        parts = {}
        wanted = {"VERSION", "PATCHLEVEL", "SUBLEVEL", "EXTRAVERSION"}

        try:
            with makefile.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "=" not in line:
                        continue
                    left, right = [x.strip() for x in line.split("=", 1)]
                    if left in wanted:
                        parts[left] = right

            version = f"{parts.get('VERSION', '0')}.{parts.get('PATCHLEVEL', '0')}.{parts.get('SUBLEVEL', '0')}"
            extra = parts.get("EXTRAVERSION", "")
            return f"{version}{extra}".strip()
        except Exception:
            return "unknown"

    def _parse_kernel_compression(self, dot_config: Path) -> List[str]:
        values = []
        try:
            text = dot_config.read_text(encoding="utf-8", errors="ignore")
            mapping = {
                "CONFIG_KERNEL_GZIP=y": "gzip",
                "CONFIG_KERNEL_XZ=y": "xz",
                "CONFIG_KERNEL_LZ4=y": "lz4",
                "CONFIG_KERNEL_LZMA=y": "lzma",
                "CONFIG_KERNEL_LZO=y": "lzo",
                "CONFIG_KERNEL_ZSTD=y": "zstd"
            }
            for needle, value in mapping.items():
                if needle in text:
                    values.append(value)
            return values
        except Exception:
            return []

    def _tail(self, text: str, max_chars: int = 1200) -> str:
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return "...\n" + text[-max_chars:]

