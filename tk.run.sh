#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${ROOT}/tools/gui_preview/dottalk_gui_preview.py"

if [[ ! -f "${APP}" ]]; then
  echo "ERROR: Tk preview launcher not found: ${APP}" >&2
  exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "ERROR: python3 tkinter support is not installed in WSL." >&2
  echo "Install it with:" >&2
  echo "  sudo apt update" >&2
  echo "  sudo apt install -y python3-tk" >&2
  exit 1
fi

cd "${ROOT}"
exec python3 "${APP}" "$@"
