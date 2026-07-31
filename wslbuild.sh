#!/usr/bin/env bash
# Fast in-loop Linux build. Uses the wsl-lean preset.
#
#   ./wslbuild.sh                      configure if needed, build dottalkpp, stage it
#   ./wslbuild.sh xbase                build one target
#   ./wslbuild.sh dottalkpp -r         build, then run over dottalkpp/data
#   ./wslbuild.sh dottalkpp -t IDXDIFF build, then REGRESSION RUN IDXDIFF with the
#                                      index trace on, all in one command
#
# Safe to invoke from ANY directory, and safe to re-run back to back: the script
# resolves its own location and never leaves you in a different cwd. Do not wrap
# it in a copy-paste block that ends with `cd` -- running that twice fails on the
# second pass, which is exactly how a stale binary got read as a fresh result.
#
# ---------------------------------------------------------------------------
# WHY THERE IS NO MANIFEST SWAP HERE
#
# The full script (wsl_build_dottalkpp.sh) swaps vcpkg-wsl.json over vcpkg.json
# because vcpkg-wsl.json lists tvision and wxwidgets as unconditional
# dependencies. That swap is what an earlier version of this script omitted, and
# omitting it was destructive: CMake re-configures on its own (ninja regenerates
# build.ninja whenever a globbed source set changes, and src/CMakeLists.txt uses
# file(GLOB_RECURSE)), the re-configure re-ran vcpkg in manifest mode against the
# canonical vcpkg.json, and vcpkg reconciled the installed tree to match --
# "Removing 53/53 tvision:x64-linux" -- after which configure died at
# src/tv/CMakeLists.txt find_package(tvision).
#
# The fix is not to replicate the swap. It is to not need it.
#
# The canonical vcpkg.json already carries a features block: tv -> tvision,
# wx -> wxwidgets, python -> pybind11, index -> nothing extra. The wsl-lean
# preset sets VCPKG_MANIFEST_FEATURES=index, so vcpkg installs only the four
# base packages and there is nothing to remove or re-add. vcpkg_installed is
# per-build-dir, so build-wsl-lean never disturbs build-wsl.
#
# vcpkg-wsl.json is therefore redundant with the features block, and is the root
# cause of both the swap dance and the wxwidgets build time on Linux.
# ---------------------------------------------------------------------------
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRESET="wsl-lean"
BUILD="$SRC/build-wsl-lean"
OUTDIR="$SRC/dottalkpp/bin-wsl-lean"

TARGET="${1:-dottalkpp}"
MODE="${2:-}"
REGRESSION="${3:-VUREPAIR}"

: "${VCPKG_ROOT:=$HOME/vcpkg}"
export VCPKG_ROOT

if [[ ! -d "$VCPKG_ROOT" ]]; then
  echo "ERROR: VCPKG_ROOT not found: $VCPKG_ROOT" >&2
  exit 1
fi

if [[ ! -f "$BUILD/CMakeCache.txt" ]]; then
  echo "configuring $PRESET (first run: vcpkg installs 4 base packages, no tvision/wx)"
  cmake --preset "$PRESET"
fi

cmake --build "$BUILD" --target "$TARGET" -j"$(nproc)"

[[ "$TARGET" == "dottalkpp" ]] || exit 0

BIN=""
for cand in "$BUILD/src/dottalkpp" "$BUILD/dottalkpp"; do
  [[ -f "$cand" ]] && BIN="$cand" && break
done

if [[ -z "$BIN" ]]; then
  echo "ERROR: built executable not found under $BUILD" >&2
  exit 1
fi

mkdir -p "$OUTDIR"
cp -f "$BIN" "$OUTDIR/dottalkpp"
chmod +x "$OUTDIR/dottalkpp"

echo "staged: $OUTDIR/dottalkpp  ($(date -r "$OUTDIR/dottalkpp" +%H:%M:%S))"

# Staleness guard: is any source file newer than the staged binary?
#
# Deliberately a single `find -newer ... -print -quit` and NOT a
# `... | sort | head` pipeline. Under `set -o pipefail` (on, above) head closes
# the pipe after one line, sort takes SIGPIPE, the pipeline returns non-zero,
# and `set -e` kills the script -- silently, right after the build, before any
# output. That is exactly what the first version of this guard did on
# 2026-07-30: a guard against silently reading stale results that silently
# produced no result at all. `|| true` and -quit keep it from ever being fatal.
STALE_HIT="$(find "$SRC/src" "$SRC/include" \
               \( -name '*.cpp' -o -name '*.hpp' -o -name '*.h' \) \
               -newer "$OUTDIR/dottalkpp" -print -quit 2>/dev/null || true)"

if [[ -n "$STALE_HIT" ]]; then
  echo "*** WARNING: staged binary is OLDER than $STALE_HIT" >&2
  echo "***          The build did not pick up the newest edit. Do not trust the run." >&2
fi

case "$MODE" in
  -r|--run)
    cd "$SRC/dottalkpp/data"
    exec "$OUTDIR/dottalkpp"
    ;;
  -t|--test)
    echo "--- REGRESSION RUN $REGRESSION (DOTTALK_INDEX_TRACE=1) ---"
    ( cd "$SRC/dottalkpp/data" \
      && printf 'REGRESSION RUN %s\nQUIT\n' "$REGRESSION" \
         | DOTTALK_INDEX_TRACE=1 "$OUTDIR/dottalkpp" )
    ;;
  -a|--all)
    # Full parity suite. Traces OFF: both default to ENABLED when the env var is
    # unset (index_manager.cpp index_trace_enabled_, append_support.cpp
    # append_trace_enabled), so a full run would bury the results under per-record
    # diagnostics. Explicit 0 is required, not merely omitting the variable.
    echo "--- REGRESSION ALL (traces off) ---"
    ( cd "$SRC/dottalkpp/data" \
      && printf 'REGRESSION ALL\nQUIT\n' \
         | DOTTALK_INDEX_TRACE=0 DOTTALK_APPEND_TRACE=0 "$OUTDIR/dottalkpp" )
    ;;
esac
