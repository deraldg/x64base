#!/usr/bin/env bash
# AIF-120 R51 -- is a DEAD owner's lock reclaimed, and is a LIVE owner's lock safe?
#
# R50 section 7: "Crash reclaim is untested. Step 4's B acquired and exited without
# releasing, leaving STUDENTS.dbf.lock behind. Whether the liveness check reclaims it
# is exactly the path AIF-116 broke."
#
# A frontend that dies holding a lock domain is not hypothetical -- R21.4 exists
# because containers go away, and a process can be killed between LOCK and UNLOCK.
# Two directions matter and they pull against each other:
#
#   1. owner DEAD  -> the lock MUST be reclaimed, or one crash wedges the table
#                     until someone runs force_unlock_table by hand
#   2. owner ALIVE -> the lock must NOT be reclaimed. Reclaiming a live owner's
#                     lock IS AIF-116: mutual exclusion silently stops holding
#
# A staleness check that is too eager fails 2; one that is too shy fails 1. This
# runs both against the same binary, in that order, so neither can be satisfied by
# accident.
#
# Run from the repo root in WSL, after ./wslbuild.sh:
#     bash tools/uidef/lock_reclaim_wsl.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

CANDIDATES="dottalkpp/bin-wsl-lean/dottalkpp dottalkpp/bin-wsl/dottalkpp build/wsl-core-vcpkg/src/dottalkpp build/core-vcpkg/src/dottalkpp ./dottalkpp"
DT=""; DT_AGE=0
echo "candidate binaries:"
for c in $CANDIDATES; do
    if [ -x "$c" ]; then
        age=$(stat -c %Y "$c")
        printf '    %-46s %s\n' "$c" "$(date -d @"$age" '+%Y-%m-%d %H:%M')"
        if [ "$age" -gt "$DT_AGE" ]; then DT_AGE=$age; DT="$c"; fi
    fi
done
[ -n "$DT" ] || { echo "no dottalkpp binary -- run ./wslbuild.sh" >&2; exit 2; }
DT="$(cd "$(dirname "$DT")" && pwd)/$(basename "$DT")"
LOCKSRC="src/xbase/xbase_locks.cpp"
if [ -f "$LOCKSRC" ] && [ "$(stat -c %Y "$LOCKSRC")" -gt "$DT_AGE" ]; then
    echo "REFUSED: $DT is older than $LOCKSRC -- rebuild first" >&2; exit 2
fi

WORK="$(mktemp -d /tmp/uidef_reclaim_XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
cp dottalkpp/data/dbf/vfp/STUDENTS.dbf "$WORK/STUDENTS.dbf"
SIDE="$WORK/STUDENTS.dbf.lock"
echo "binary : $DT"
echo

acquire() { printf 'USE %s\nSELECT STUDENTS\nLOCK TABLE\nLOCK STATUS\n' "$WORK/STUDENTS.dbf"; }
status()  { printf 'USE %s\nSELECT STUDENTS\nLOCK STATUS\n' "$WORK/STUDENTS.dbf"; }

echo "=== 1. LIVE owner must NOT be reclaimed (the AIF-116 direction) ==="
F1="$WORK/f1"; mkfifo "$F1"
"$DT" < "$F1" > "$WORK/live.out" 2>&1 &
LIVEPID=$!
exec 8>"$F1"
acquire >&8
sleep 2
echo "    holder pid $LIVEPID is alive; sidecar says:"
sed 's/^/      /' "$SIDE" 2>/dev/null; echo
acquire | timeout 20 "$DT" > "$WORK/live_contender.out" 2>&1
grep -E "LOCK:|Table:" "$WORK/live_contender.out" | sed 's/^/    /'
LIVE_REFUSED=$(grep -c "LOCK: failed" "$WORK/live_contender.out")

echo
echo "=== 2. DEAD owner must BE reclaimed -- holder killed with SIGKILL ==="
kill -9 "$LIVEPID" 2>/dev/null
exec 8>&-
wait "$LIVEPID" 2>/dev/null
sleep 1
echo "    holder pid $LIVEPID killed. Sidecar still present: $([ -f "$SIDE" ] && echo yes || echo NO)"
[ -f "$SIDE" ] && sed 's/^/      /' "$SIDE" && echo
if kill -0 "$LIVEPID" 2>/dev/null; then echo "    WARNING: pid $LIVEPID still alive"; else echo "    confirmed: pid $LIVEPID is gone"; fi
acquire | timeout 20 "$DT" > "$WORK/dead_contender.out" 2>&1
grep -E "LOCK:|Table:" "$WORK/dead_contender.out" | sed 's/^/    /'
DEAD_GOT=$(grep -c "LOCK: table locked" "$WORK/dead_contender.out")

echo
echo "=== verdict ==="
printf '  %-46s : %s\n' "LIVE owner's lock was NOT taken (AIF-116)" \
    "$([ "$LIVE_REFUSED" -ge 1 ] && echo True || echo False)"
printf '  %-46s : %s\n' "DEAD owner's lock WAS reclaimed" \
    "$([ "$DEAD_GOT" -ge 1 ] && echo True || echo False)"
echo
echo "  Both must be True. Only the LIVE case failing is a mutual-exclusion defect;"
echo "  only the DEAD case failing means one crash wedges the table until a human"
echo "  runs force_unlock_table. They are checked in this order deliberately, so a"
echo "  check that simply always reclaims cannot pass by answering the second alone."
