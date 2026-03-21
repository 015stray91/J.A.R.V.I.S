"""
Kernel and ROM development manager for Jarvis X
Provides build diagnostics and quick error triage for Android/Linux development
"""

from pathlib import Path
from typing import Dict, List
import re
from utils.logger import get_logger

logger = get_logger()


class KernelRomManager:
    """Analyzes kernel/ROM build logs and returns actionable diagnostics"""

    def analyze_build_log(self, log_path: str) -> Dict[str, object]:
        """Analyze a build log and extract likely root causes"""
        if not log_path:
            return {
                "success": False,
                "message": "No log file path provided"
            }

        path = Path(log_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"Build log not found: {path}"
            }

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            findings = self._extract_findings(text)

            return {
                "success": True,
                "message": f"Analyzed {path.name}",
                "path": str(path),
                "error_count": len(findings),
                "findings": findings[:20]
            }
        except Exception as e:
            logger.error(f"Failed to analyze log {path}: {e}")
            return {
                "success": False,
                "message": f"Failed to analyze log: {e}"
            }

    def _extract_findings(self, log_text: str) -> List[Dict[str, str]]:
        """Extract key error signatures and remediation hints"""
        lines = log_text.splitlines()
        findings: List[Dict[str, str]] = []

        patterns = [
            (r"fatal error: (.+)", "Missing header or dependency", "Install missing package/toolchain and verify include paths."),
            (r"undefined reference to (.+)", "Linker symbol missing", "Ensure object/library is linked and symbol is exported."),
            (r"No rule to make target '(.+)'", "Missing make target", "Check Makefile path, generated files, and target name."),
            (r"ninja: error: (.+)", "Ninja build error", "Inspect generated build graph and dependency declarations."),
            (r"ld\.lld: error: (.+)", "LLVM linker error", "Validate linker flags, ABI target, and library ordering."),
            (r"FAILED: (.+)", "Build step failed", "Inspect preceding command output for root cause."),
            (r"error: (.+)", "Compiler error", "Review compiler diagnostics and involved source lines."),
        ]

        for idx, line in enumerate(lines, start=1):
            lowered = line.lower()
            if "warning:" in lowered and "error:" not in lowered:
                continue

            for raw_pattern, category, hint in patterns:
                match = re.search(raw_pattern, line, flags=re.IGNORECASE)
                if match:
                    findings.append({
                        "line": str(idx),
                        "category": category,
                        "details": match.group(0)[:240],
                        "hint": hint
                    })
                    break

        return findings

