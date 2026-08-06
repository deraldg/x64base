#!/usr/bin/env bash
# sidecar_scratch.sh -- move root-level scratch OUT of ccode into the age-out
# sidecar (D:\code\ccode.sidecar == /mnt/d/code/ccode.sidecar), preserving relative
# paths. Recoverable filesystem move, NEVER git rm. DRY-RUN by default; pass
# --execute to actually move. Reads the reviewed list tools/staging/triage_root_sidecar_v1.txt.
set -euo pipefail
REPO="/mnt/d/code/ccode"
SIDECAR="/mnt/d/code/ccode.sidecar"
LIST="$REPO/tools/staging/triage_root_sidecar_v1.txt"
EXECUTE=0; [ "${1:-}" = "--execute" ] && EXECUTE=1

cd "$REPO"
moved=0; missing=0
while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  # git status --porcelain QUOTES names with spaces/specials; strip surrounding
  # double-quotes so the path matches the real (unquoted) file. Without this, the
  # 4 quoted scratch names silently never moved and falsely reported "gone".
  rel="${rel%\"}"; rel="${rel#\"}"
  if [ ! -e "$rel" ]; then missing=$((missing+1)); continue; fi
  dst="$SIDECAR/$rel"
  if [ "$EXECUTE" = 1 ]; then
    mkdir -p "$(dirname "$dst")"
    mv -f "$rel" "$dst"
    echo "MOVED  $rel"
  else
    echo "DRYRUN $rel"
  fi
  moved=$((moved+1))
done < "$LIST"

echo
if [ "$EXECUTE" = 1 ]; then
  echo "EXECUTED: $moved moved, $missing already gone  ->  $SIDECAR"
  echo "Recover any file by moving it back from ccode.sidecar."
else
  echo "DRY-RUN: $moved would move, $missing already gone. Re-run with --execute to move."
fi
