#!/usr/bin/env bash
set -euo pipefail

# Cleanup script for run_jarvis_ram.sh.
# Unmounts RAM workspace and resets zram devices created by launcher.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE="${SCRIPT_DIR}/.jarvisx_ram_state"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "RAM cleanup is Linux-only."
  exit 1
fi

if [[ ! -f "${STATE_FILE}" ]]; then
  echo "No RAM workspace state file found. Nothing to clean."
  exit 0
fi

# shellcheck disable=SC1090
source "${STATE_FILE}"

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required for RAM cleanup."
  exit 1
fi

if [[ -n "${mount:-}" ]] && mountpoint -q "${mount}"; then
  sudo umount "${mount}" || true
fi

if [[ "${backend:-}" == "tmpfs" ]]; then
  if [[ -n "${mount:-}" ]]; then
    sudo rmdir "${mount}" 2>/dev/null || true
  fi
fi

if [[ "${backend:-}" == "zram" ]]; then
  if [[ -n "${extra_swap_device:-}" ]]; then
    sudo swapoff "${extra_swap_device}" 2>/dev/null || true
    sudo zramctl --reset "${extra_swap_device}" 2>/dev/null || true
  fi

  if [[ -n "${device:-}" ]]; then
    sudo zramctl --reset "${device}" 2>/dev/null || true
  fi

  if [[ -n "${mount:-}" ]]; then
    sudo rmdir "${mount}" 2>/dev/null || true
  fi
fi

rm -f "${STATE_FILE}"
echo "Jarvis X RAM workspace cleanup complete."
