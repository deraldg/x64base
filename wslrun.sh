#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPDIR="$ROOT/dottalkpp"
BIN="$APPDIR/bin-wsl/dottalkpp"
WORKDIR="$APPDIR/data"

[[ -x "$BIN" ]] || { echo "ERROR: $BIN not found or not executable. Build first."; exit 1; }
[[ -d "$WORKDIR" ]] || { echo "ERROR: Work dir $WORKDIR not found."; exit 1; }

cd "$WORKDIR"
exec "$BIN" "$@"
