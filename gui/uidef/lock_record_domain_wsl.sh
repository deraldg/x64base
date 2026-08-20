#!/usr/bin/env bash
# AIF-120 R52 -- record granularity and the DOMAIN, against the real binary.
#
# Three items outstanding from R48, R50.7 and R51.5, all the same shape -- proven
# against a recording sink, never against the engine:
#
#   A. R48's record granularity. Bare LOCK is supposed to lock the CURRENT RECORD.
#      If it behaves like a table lock, R48.3's "finer, not safer" is wrong in the
#      direction that matters, and nothing so far would have noticed.
#   B. Whether a record lock blocks a TABLE lock. VFP's FLOCK() fails when another
#      process holds any record. If it does not here, "coarser" is not a superset
#      of "finer" and R48.3's advice to default to table is unsound.
#   C. The domain: TWO areas, all-or-nothing, and the ROLLBACK when the second
#      refuses. R48.4 argued a surviving partial acquisition is worse than no
#      locking. That argument has never been run.
#
# C keeps the rolling-back process ALIVE while a third takes the area it released,
# so process exit cannot explain the release (R50.2).
#
# Run from the repo root in WSL, after ./wslbuild.sh:
#     bash gui/uidef/lock_record_domain_wsl.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

CANDIDATES="dottalkpp/bin-wsl-lean/dottalkpp dottalkpp/bin-wsl/dottalkpp build/wsl-core-vcpkg/src/dottalkpp ./dottalkpp"
DT=""; DT_AGE=0
for c in $CANDIDATES; do
    if [ -x "$c" ]; then
        age=$(stat -c %Y "$c")
        printf 'candidate %-44s %s\n' "$c" "$(date -d @"$age" '+%Y-%m-%d %H:%M')"
        [ "$age" -gt "$DT_AGE" ] && { DT_AGE=$age; DT="$c"; }
    fi
done
[ -n "$DT" ] || { echo "no dottalkpp binary -- run ./wslbuild.sh" >&2; exit 2; }
DT="$(cd "$(dirname "$DT")" && pwd)/$(basename "$DT")"
LOCKSRC="src/xbase/xbase_locks.cpp"
if [ -f "$LOCKSRC" ] && [ "$(stat -c %Y "$LOCKSRC")" -gt "$DT_AGE" ]; then
    echo "REFUSED: $DT is older than $LOCKSRC -- rebuild first" >&2; exit 2
fi

W="$(mktemp -d /tmp/uidef_rd_XXXXXX)"
trap 'rm -rf "$W"' EXIT
cp dottalkpp/data/dbf/vfp/STUDENTS.dbf "$W/"
cp dottalkpp/data/dbf/vfp/ENROLL.dbf   "$W/"
echo "binary : $DT"
echo "tables : $W/{STUDENTS,ENROLL}.dbf"
echo

# GOTO takes a record number -- a TEST artifact, not runtime behaviour. The UIDEF
# runtime never positions: the user navigates the form and the runtime locks
# wherever the pointer already is, which is why R48.2 holds.
rec_hold() { printf 'USE %s/STUDENTS.dbf\nGOTO %s\nLOCK\nLOCK STATUS\n' "$W" "$1"; }
rec_try()  { printf 'USE %s/STUDENTS.dbf\nGOTO %s\nLOCK\nLOCK STATUS\n' "$W" "$1"; }
tbl_try()  { printf 'USE %s/STUDENTS.dbf\nLOCK TABLE\nLOCK STATUS\n' "$W"; }
say()      { grep -E "LOCK:|UNLOCK:|Table:|Record " "$1" | sed 's/^/      /'; }

echo "=== A. bare LOCK must lock ONE record, not the table ==="
FA="$W/fa"; mkfifo "$FA"
"$DT" < "$FA" > "$W/A_holder.out" 2>&1 &
AH=$!
exec 7>"$FA"
rec_hold 1 >&7
sleep 2
echo "  holder has record 1. Another process asks for record 1:"
rec_try 1 | timeout 20 "$DT" > "$W/A_same.out" 2>&1
say "$W/A_same.out"
echo "  ...and for record 5:"
rec_try 5 | timeout 20 "$DT" > "$W/A_other.out" 2>&1
say "$W/A_other.out"
SAME_REFUSED=$(grep -c "LOCK: failed" "$W/A_same.out")
OTHER_GOT=$(grep -cE "LOCK: record .* locked|LOCK: locked" "$W/A_other.out")

echo
echo "=== B. does a held RECORD block a TABLE lock? ==="
tbl_try | timeout 20 "$DT" > "$W/B_table.out" 2>&1
say "$W/B_table.out"
TABLE_REFUSED=$(grep -c "LOCK: failed" "$W/B_table.out")
printf '%s\n' 'UNLOCK' >&7
exec 7>&-
wait $AH 2>/dev/null

echo
echo "=== C. the DOMAIN: all-or-nothing across two areas, and the rollback ==="
# CORRECTED. The first version issued USE twice in one session, and USE opens into
# the CURRENT work area -- so the second USE CLOSED ENROLL and replaced it with
# STUDENTS in area 0. The rollback's `SELECT ENROLL` then had nothing to select,
# `UNLOCK TABLE` released the current area (STUDENTS, which this process never
# held) and cheerfully reported "table unlocked", and ENROLL stayed locked.
#
# That is not an engine defect and not a runtime defect -- it is the harness
# omitting a PRECONDITION the UIDEF provider quietly relies on: the provider emits
# `SELECT <alias>`, which presumes every alias in the domain is ALREADY OPEN in a
# work area of its own. Nothing in the runtime or the contract says who issues the
# USE. See R52 section 4.
open_both() { printf 'USE %s/ENROLL.dbf\nSELECT 1\nUSE %s/STUDENTS.dbf\n' "$W" "$W"; }

FC="$W/fc"; mkfifo "$FC"
"$DT" < "$FC" > "$W/C_p1.out" 2>&1 &
CP1=$!
exec 6>"$FC"
# P1 holds STUDENTS only -- the SECOND area in the runtime's sorted order, so the
# contender gets ENROLL first and must give it back.
printf 'USE %s/STUDENTS.dbf\nLOCK TABLE\nLOCK STATUS\n' "$W" >&6
sleep 2

# P2 = the frontend's provider, transcribed, WITH the open precondition.
FD="$W/fd"; mkfifo "$FD"
"$DT" < "$FD" > "$W/C_p2.out" 2>&1 &
CP2=$!
exec 5>"$FD"
open_both >&5
sleep 1
printf 'SELECT ENROLL\nLOCK TABLE\nLOCK STATUS\n' >&5      # first area: succeeds
sleep 1
printf 'SELECT STUDENTS\nLOCK TABLE\n' >&5                  # second area: refused
sleep 1
printf 'SELECT ENROLL\nUNLOCK TABLE\nLOCK STATUS\n' >&5    # ROLLBACK
sleep 2
echo "  P2 (still running) attempted both areas and rolled back:"
say "$W/C_p2.out"
P2_HELD=$(grep -c "LOCK: table locked" "$W/C_p2.out")

echo "  a third process now asks for ENROLL, while P2 is STILL ALIVE:"
printf 'USE %s/ENROLL.dbf\nLOCK TABLE\nLOCK STATUS\n' "$W" | timeout 20 "$DT" > "$W/C_p3.out" 2>&1
say "$W/C_p3.out"
ROLLED_BACK=$(grep -c "LOCK: table locked" "$W/C_p3.out")
printf 'QUIT\n' >&6; printf 'QUIT\n' >&5
exec 6>&-; exec 5>&-
wait $CP1 2>/dev/null; wait $CP2 2>/dev/null

echo
echo "=== verdict ==="
printf '  %-48s : %s\n' "A1 same record refused"          "$([ "$SAME_REFUSED"  -ge 1 ] && echo True || echo False)"
printf '  %-48s : %s\n' "A2 different record granted"     "$([ "$OTHER_GOT"     -ge 1 ] && echo True || echo False)"
printf '  %-48s : %s\n' "B  held record blocks LOCK TABLE" "$([ "$TABLE_REFUSED" -ge 1 ] && echo True || echo False)"
printf '  %-48s : %s\n' "C0 P2 actually held the first area" "$([ "$P2_HELD" -ge 1 ] && echo True || echo False)"
printf '  %-48s : %s\n' "C  rollback released the first area" "$([ "$ROLLED_BACK" -ge 1 ] && echo True || echo False)"
echo
echo "  A1+A2 together are what make bare LOCK a RECORD lock; A1 alone is also"
echo "  satisfied by a table lock, which is the wrong answer wearing the right one."
echo "  B False would mean coarser is not a superset of finer, and R48.3's advice"
echo "  to default to table granularity would be unsound."
echo "  C is checked with P2 alive, so its exit cannot explain P3's success."
