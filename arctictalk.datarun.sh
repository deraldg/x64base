#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${ROOT}/dottalkpp/data/scripts/arctictalk.dts"

if [[ ! -f "${SCRIPT}" ]]; then
  echo "ERROR: ArcticTalk DotScript not found: ${SCRIPT}" >&2
  exit 1
fi

exec bash "${ROOT}/datarun_wsl.sh" --script "${SCRIPT}" "$@"
