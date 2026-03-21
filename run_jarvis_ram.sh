#!/usr/bin/env bash
set -euo pipefail

# Run Jarvis X from an in-memory workspace.
# Backend options:
# - auto (default): prefers zram-backed ext4, falls back to tmpfs
# - zram: force zram-backed workspace
# - tmpfs: force tmpfs workspace

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="${JARVIS_RAM_BACKEND:-auto}"
RAM_ROOT="${JARVIS_RAM_ROOT:-/mnt/jarvisx-ram}"
RAM_SIZE="${JARVIS_RAM_SIZE:-8G}"
ZRAM_ALGO="${JARVIS_ZRAM_ALGO:-lz4}"
EXTRA_SWAP_SIZE="${JARVIS_EXTRA_SWAP_SIZE:-0}"
WORK_DIR="${RAM_ROOT}/workspace"
STATE_FILE="${SCRIPT_DIR}/.jarvisx_ram_state"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "RAM workspace mode is Linux-only."
  exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/main.py" ]]; then
  echo "main.py not found in ${SCRIPT_DIR}. Run this script from the project root."
  exit 1
fi

require_sudo() {
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required for RAM workspace setup."
    exit 1
  fi
}

choose_backend() {
  if [[ "${BACKEND}" == "auto" ]]; then
    if command -v zramctl >/dev/null 2>&1 && [[ -e /sys/class/zram-control ]]; then
      echo "zram"
    else
      echo "tmpfs"
    fi
    return
  fi

  if [[ "${BACKEND}" != "zram" && "${BACKEND}" != "tmpfs" ]]; then
    echo "Invalid JARVIS_RAM_BACKEND=${BACKEND}. Use auto, zram, or tmpfs."
    exit 1
  fi

  echo "${BACKEND}"
}

setup_tmpfs() {
  require_sudo
  sudo mkdir -p "${RAM_ROOT}"
  if ! mountpoint -q "${RAM_ROOT}"; then
    sudo mount -t tmpfs -o "size=${RAM_SIZE}" tmpfs "${RAM_ROOT}"
  fi

  cat > "${STATE_FILE}" <<EOF
backend=tmpfs
mount=${RAM_ROOT}
device=
extra_swap_device=
extra_swap_size=0
EOF
}

setup_zram() {
  require_sudo
  if ! command -v zramctl >/dev/null 2>&1; then
    echo "zramctl not found. Install util-linux or set JARVIS_RAM_BACKEND=tmpfs."
    exit 1
  fi

  sudo modprobe zram || true
  local device
  local extra_swap_device=""
  device="$(sudo zramctl --find --size "${RAM_SIZE}" --algorithm "${ZRAM_ALGO}")"
  if [[ -z "${device}" ]]; then
    echo "Failed to allocate zram device."
    exit 1
  fi

  sudo mkfs.ext4 -q "${device}"
  sudo mkdir -p "${RAM_ROOT}"
  sudo mount "${device}" "${RAM_ROOT}"

  # Optional second zram device as compressed swap to improve overall memory pressure behavior.
  if [[ "${EXTRA_SWAP_SIZE}" != "0" ]]; then
    extra_swap_device="$(sudo zramctl --find --size "${EXTRA_SWAP_SIZE}" --algorithm "${ZRAM_ALGO}")"
    if [[ -n "${extra_swap_device}" ]]; then
      sudo mkswap "${extra_swap_device}" >/dev/null
      sudo swapon -p 120 "${extra_swap_device}"
    else
      echo "Warning: could not allocate extra zram swap device (requested ${EXTRA_SWAP_SIZE})."
    fi
  fi

  cat > "${STATE_FILE}" <<EOF
backend=zram
mount=${RAM_ROOT}
device=${device}
extra_swap_device=${extra_swap_device}
extra_swap_size=${EXTRA_SWAP_SIZE}
EOF
}

sync_workspace() {
  mkdir -p "${WORK_DIR}"

  if ! command -v rsync >/dev/null 2>&1; then
    echo "rsync is required to mirror the project into RAM workspace."
    exit 1
  fi

  rsync -a --delete \
    --exclude '.git/' \
    --exclude '.github/' \
    --exclude 'logs/' \
    --exclude '__pycache__/' \
    --exclude '.jarvisx_ram_state' \
    "${SCRIPT_DIR}/" "${WORK_DIR}/"
}

run_from_ram() {
  cd "${WORK_DIR}"

  if [[ -x "./venv/bin/python" ]]; then
    ./venv/bin/python main.py "$@"
  else
    python3 main.py "$@"
  fi
}

ACTIVE_BACKEND="$(choose_backend)"
echo "Preparing RAM workspace using backend: ${ACTIVE_BACKEND}"
echo "RAM workspace size: ${RAM_SIZE}"
if [[ "${EXTRA_SWAP_SIZE}" != "0" ]]; then
  echo "Extra zram swap requested: ${EXTRA_SWAP_SIZE}"
fi

if [[ "${ACTIVE_BACKEND}" == "zram" ]]; then
  setup_zram
else
  setup_tmpfs
fi

sync_workspace
echo "Running Jarvis X from ${WORK_DIR}"
run_from_ram "$@"
