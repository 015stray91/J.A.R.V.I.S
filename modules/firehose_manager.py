"""
Firehose and ELF helper for Jarvis X
Provides inspection and compatibility guidance for Qualcomm/Motorola workflows
"""

from pathlib import Path
from typing import Dict


class FirehoseManager:
    """Inspects firehose/ELF files and returns practical guidance"""

    def inspect_firehose(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"Firehose file not found: {path}"
            }

        text = path.read_text(encoding="utf-8", errors="ignore")
        probes = {
            "contains_program": "<program" in text.lower(),
            "contains_patch": "<patch" in text.lower(),
            "contains_read": "read" in text.lower(),
            "contains_sector": "sector" in text.lower(),
            "contains_physical_partition": "physical_partition_number" in text.lower(),
        }

        return {
            "success": True,
            "path": str(path),
            "kind": "firehose_xml",
            "signals": probes,
            "message": "Firehose file inspected",
            "guidance": (
                "Confirm the programmer and target chipset match exactly. Validate partition names and sector ranges "
                "before any write operation. Prefer read/backup operations first, then verify hashes."
            )
        }

    def inspect_elf(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return {
                "success": False,
                "message": f"ELF file not found: {path}"
            }

        try:
            data = path.read_bytes()
        except Exception as e:
            return {
                "success": False,
                "message": f"Unable to read ELF: {e}"
            }

        if len(data) < 20 or data[0:4] != b"\x7fELF":
            return {
                "success": False,
                "message": "File does not appear to be a valid ELF binary"
            }

        elf_class = "64-bit" if data[4] == 2 else "32-bit" if data[4] == 1 else "unknown"
        endian = "little" if data[5] == 1 else "big" if data[5] == 2 else "unknown"

        machine = int.from_bytes(data[18:20], byteorder="little", signed=False)
        machine_map = {
            40: "ARM",
            62: "x86-64",
            183: "AArch64",
            243: "RISC-V"
        }

        return {
            "success": True,
            "path": str(path),
            "kind": "elf_binary",
            "elf_class": elf_class,
            "endianness": endian,
            "machine": machine_map.get(machine, f"machine_{machine}"),
            "message": "ELF header inspected",
            "guidance": (
                "Use a loader/programmer built for the same architecture and target platform. "
                "If architecture or endianness mismatch, do not flash with this binary."
            )
        }

