"""
Tutor manager for Jarvis X
Provides teaching-style explanations for development topics and files
"""

from pathlib import Path
from typing import Dict


class TutorManager:
    """Explains technical concepts and code artifacts in plain language"""

    def explain_topic(self, topic: str) -> Dict[str, object]:
        key = (topic or "").strip().lower()
        if not key:
            return {
                "success": False,
                "message": "No topic provided"
            }

        language_result = self._explain_language(key)
        if language_result:
            return {
                "success": True,
                "topic": topic,
                "explanation": language_result
            }

        guides = {
            "filesystem": (
                "File systems are your storage layout rules. Focus on mount points, permissions, "
                "ownership, journaling, and block size. For Android/Linux ROM work: verify partition "
                "tables, filesystem type per partition (ext4/f2fs/erofs), and fstab mappings before flashing."
            ),
            "framework": (
                "Framework work means tracing APIs from interface to implementation. In Android, follow "
                "AOSP layers: app -> framework -> system services -> HAL -> kernel. Make small, reversible "
                "changes and test each layer independently."
            ),
            "hal": (
                "HAL layering separates hardware-specific code from higher framework logic. Keep stable interfaces, "
                "avoid leaking vendor details upward, and validate binder/hidl/aidl contracts with logs and service checks."
            ),
            "kernel": (
                "Kernel mainlining means reducing vendor-specific hacks and aligning with upstream subsystem patterns. "
                "Track defconfig changes, drivers, dtb overlays, and compression settings together to avoid boot mismatches."
            ),
            "build environment": (
                "Reliable build environments use pinned toolchains, reproducible dependency versions, clean build directories, "
                "and scriptable setup. Capture all steps in one script so each build can be reproduced from scratch."
            ),
        }

        for k, text in guides.items():
            if k in key:
                return {"success": True, "topic": topic, "explanation": text}

        return {
            "success": True,
            "topic": topic,
            "explanation": (
                "Start by defining architecture, data flow, and failure points for this topic. "
                "Then test each layer separately, add logs for assumptions, and document exact build/runtime steps."
            )
        }

    def _explain_language(self, key: str) -> str | None:
        """Explain programming languages in plain, practical terms"""
        guides = {
            "python": (
                "Python is the easiest all-purpose tool in this list. Think of it like a universal remote: "
                "simple to read, quick to write, great for automation, tooling, scripts, and AI workflows. "
                "Use it when speed of development matters more than maximum raw performance."
            ),
            "kotlin": (
                "Kotlin is a cleaner, safer version of Java for Android and backend apps. "
                "Think of it as Java with fewer footguns. You still get the Android ecosystem, but with less boilerplate "
                "and better null-safety so apps crash less from bad values."
            ),
            "golang": (
                "Go is built for reliable services and command-line tools. "
                "Think simple syntax + fast binaries + built-in concurrency. "
                "Use it when you want one compiled executable that is easy to deploy and performs consistently."
            ),
            "go": (
                "Go is built for reliable services and command-line tools. "
                "Think simple syntax + fast binaries + built-in concurrency. "
                "Use it when you want one compiled executable that is easy to deploy and performs consistently."
            ),
            "rust": (
                "Rust is for high performance without memory bugs. "
                "Think C/C++ power with a strict safety coach at compile time. "
                "It is harder at first, but excellent for kernels, low-level tooling, and secure systems code."
            ),
            "bison": (
                "Bison is not a full app language. It is a parser generator for compilers/interpreters. "
                "You define grammar rules, and Bison generates parser code. "
                "Use it when building a language, config parser, or command interpreter."
            ),
            "c": (
                "C is close to hardware and very fast, but you manage memory manually. "
                "Great for kernels, embedded code, and performance-critical parts. "
                "You trade convenience for full control."
            ),
            "c++": (
                "C++ is C plus high-level features. It can be extremely fast and flexible, but complexity grows fast. "
                "Great for engines and performance-heavy apps when you need fine control."
            ),
            "java": (
                "Java is stable, enterprise-friendly, and cross-platform through the JVM. "
                "It is verbose compared to Kotlin, but mature and widely used."
            ),
            "javascript": (
                "JavaScript is the language of the web UI, and with Node.js it also runs servers/tools. "
                "Use it for web apps and cross-stack projects where one language everywhere helps."
            ),
            "typescript": (
                "TypeScript is JavaScript with type checking. "
                "Think fewer runtime surprises and easier scaling in big codebases."
            ),
        }

        for language, explanation in guides.items():
            if language in key:
                return explanation

        return None

    def explain_file(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"File not found: {path}"
            }

        ext = path.suffix.lower()
        file_type = {
            ".py": "Python source",
            ".c": "C source",
            ".cpp": "C++ source",
            ".h": "Header",
            ".mk": "Makefile fragment",
            ".bp": "Soong blueprint",
            ".toml": "TOML config",
            ".json": "JSON config",
            ".sh": "Shell script",
            ".conf": "Configuration file",
        }.get(ext, "Text/source file")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            preview = "\n".join(lines[:12])

            return {
                "success": True,
                "path": str(path),
                "file_type": file_type,
                "line_count": len(content.splitlines()),
                "preview": preview,
                "explanation": (
                    f"This looks like {file_type}. Review top-level declarations, configuration keys, "
                    "and any external commands/imports first, then trace how this file is referenced by builds or runtime startup."
                )
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to read file: {e}"
            }

