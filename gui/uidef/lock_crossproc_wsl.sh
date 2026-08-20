#!/usr/bin/env bash
# AIF-120 R50 -- does the frontend's lock vocabulary actually exclude, cross-process?
#
# R47, R48 and R49 each closed with the same admission: both providers are proven to
# SAY the right thing and the engine has never HEARD it. The UIDEF runtime acquires a
# lock domain by issuing, for every area in it:
#
#     SELECT <alias>
#     LOCK TABLE          (or bare LOCK, for record granularity -- R48)
#
# and releases with SELECT + UNLOCK. That is the whole vocabulary. This runs it
# against the real binary, from two processes, and asks the only question that
# matters: while one process holds the lock, does the other get refused?
#
# Run from the repo root in WSL, after ./wslbuild.sh:
#     bash gui/uidef/lock_crossproc_wsl.sh
#
# Nothing is written inside the repository: the table is copied to a scratch
# directory first, so the `.lock` sidecars land there and not in a tracked tree.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Pick the NEWEST candidate, and print every one that was considered.
#
# The first version of this file took the first hit from a fixed list, with
# build/wsl-core-vcpkg/src/dottalkpp in it -- an artifact from 2026-08-10 that
# PREDATES AIF-116's fix (fe42666e, 08-15). A fresh build stages to
# dottalkpp/bin-wsl-lean, which was not on the list, so the harness would have
# silently proven cross-process locking against a build nobody ships and reported
# it as a pass. A fallback that picks quietly is a fallback that picks wrong.
CANDIDATES="dottalkpp/bin-wsl-lean/dottalkpp dottalkpp/bin-wsl/dottalkpp build/wsl-core-vcpkg/src/dottalkpp build/core-vcpkg/src/dottalkpp ./dottalkpp"
DT=""
DT_AGE=0
echo "candidate binaries:"
for c in $CANDIDATES; do
    if [ -x "$c" ]; then
        age=$(stat -c %Y "$c")
        printf '    %-46s %s\n' "$c" "$(date -d @"$age" '+%Y-%m-%d %H:%M')"
        if [ "$age" -gt "$DT_AGE" ]; then DT_AGE=$age; DT="$c"; fi
    else
        printf '    %-46s (absent)\n' "$c"
    fi
done
if [ -z "$DT" ]; then
    echo "no dottalkpp binary found -- run ./wslbuild.sh first" >&2
    exit 2
fi
DT="$(cd "$(dirname "$DT")" && pwd)/$(basename "$DT")"

# Refuse an artifact older than the lock source itself. AIF-116 was fixed in this
# file; testing a binary predating it measures a defect that is already closed.
LOCKSRC="src/xbase/xbase_locks.cpp"
if [ -f "$LOCKSRC" ] && [ "$(stat -c %Y "$LOCKSRC")" -gt "$DT_AGE" ]; then
    echo "REFUSED: $DT is older than $LOCKSRC -- rebuild before trusting this" >&2
    exit 2
fi

SRC="dottalkpp/data/dbf/vfp/STUDENTS.dbf"
[ -f "$SRC" ] || { echo "missing $SRC" >&2; exit 2; }

WORK="$(mktemp -d /tmp/uidef_lock_XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
cp "$SRC" "$WORK/STUDENTS.dbf"
for ext in fpt FPT cdx CDX; do
    [ -f "dottalkpp/data/dbf/vfp/STUDENTS.$ext" ] && cp "dottalkpp/data/dbf/vfp/STUDENTS.$ext" "$WORK/" || true
done

echo "binary : $DT"
echo "table  : $WORK/STUDENTS.dbf"
"$DT" --version 2>&1 | head -2 || true
echo

# The frontend's acquire sequence, verbatim. `LOCK STATUS` is the only line this
# harness adds, so the evidence shows what the engine thinks after each attempt.
acquire() { printf 'USE %s\nSELECT STUDENTS\nLOCK TABLE\nLOCK STATUS\n' "$WORK/STUDENTS.dbf"; }
# R50: UNLOCK TABLE, not UNLOCK. Bare UNLOCK unlocks the current RECORD, so the
# first run of this harness showed `Table: LOCKED` still standing after release --
# the runtime's release path was leaking every table lock it took.
release() { printf 'UNLOCK TABLE\nLOCK STATUS\n'; }

echo "=== 1. process A acquires and HOLDS (stdin held open for 5s) ==="
{ acquire; sleep 5; release; } | "$DT" > "$WORK/A.out" 2>&1 &
APID=$!
sleep 2

echo "=== 2. process B issues the SAME sequence while A holds ==="
acquire | timeout 20 "$DT" > "$WORK/B_contended.out" 2>&1
sed 's/^/    /' "$WORK/B_contended.out"

wait $APID
echo
echo "--- what process A saw ---"
sed 's/^/    /' "$WORK/A.out"

echo
echo "=== 3. process B issues it again, after A has exited ==="
{ acquire; release; } | timeout 20 "$DT" > "$WORK/B_free.out" 2>&1
sed 's/^/    /' "$WORK/B_free.out"

echo
echo "=== 4. THE DECISIVE ONE: A releases and stays ALIVE; B must then acquire ==="
echo "    (steps 1-3 cannot tell a working UNLOCK from a process exit)"
FIFO="$WORK/afifo"
mkfifo "$FIFO"
"$DT" < "$FIFO" > "$WORK/A2.out" 2>&1 &
A2PID=$!
exec 9>"$FIFO"
acquire >&9
sleep 2
release >&9                       # A releases, but its stdin stays open
sleep 2
acquire | timeout 20 "$DT" > "$WORK/B_after_release.out" 2>&1
echo "    --- B, with A still running ---"
grep -E "LOCK:|Table:" "$WORK/B_after_release.out" | sed 's/^/    /'
printf 'QUIT\n' >&9
exec 9>&-
wait $A2PID 2>/dev/null
echo "    --- A, which never exited during B's attempt ---"
grep -E "LOCK:|UNLOCK:|Table:" "$WORK/A2.out" | sed 's/^/    /'

echo
echo "=== sidecars left behind in the scratch directory ==="
ls -la "$WORK" | sed 's/^/    /'
echo
echo "READ THIS AGAINST THE CONTRACT:"
echo "  R47 ruled that a busy domain REFUSES rather than queues (FLOCK semantics)."
echo "  Step 2 must therefore show B being refused, NOT B waiting for A."
echo "  Step 3 must show B succeeding once A is gone."
echo "  If step 2 SUCCEEDS, cross-process exclusion is not holding for this build"
echo "  and that is AIF-116's failure mode, not a UIDEF one."
echo "  Step 4 is the one that tests RELEASE rather than process exit: A is still"
echo "  running when B acquires, so B can only succeed if UNLOCK TABLE really"
echo "  released. A's own LOCK STATUS after release must read NOT locked."
