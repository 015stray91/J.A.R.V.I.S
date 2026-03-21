#!/usr/bin/env bash
set -euo pipefail

echo "================================================"
echo "  JARVIS X - Installation Script (Linux/macOS)"
echo "================================================"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed or not in PATH"
  echo "Install Python 3.10+ and retry."
  exit 1
fi

echo "[1/5] Python found: $(python3 --version)"
echo

echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
  echo "Virtual environment already exists"
else
  python3 -m venv venv
fi
echo

echo "[3/5] Installing dependencies..."
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt || {
  echo
  echo "Warning: Some optional packages failed to install."
  echo "Core CLI features should still work."
  echo
}
echo

echo "[4/5] Setting up configuration..."
if [ -f "config/config.json" ]; then
  echo "Configuration file already exists"
else
  cp config/config.example.json config/config.json
  echo "Configuration file created"
fi
echo

echo "[5/5] Creating directories..."
mkdir -p logs screenshots
echo

echo "================================================"
echo "  Installation Complete!"
echo "================================================"
echo
echo "To start Jarvis:"
echo "  ./venv/bin/python main.py"
echo
echo "Or use helper scripts:"
echo "  ./run_jarvis.sh"
echo "  ./run_cli.sh"
echo
