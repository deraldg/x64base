#!/usr/bin/env bash
set -euo pipefail

export VCPKG_ROOT="${VCPKG_ROOT:-$HOME/vcpkg}"

SRC="/mnt/d/code/ccode"
BROOT="$HOME/wsl-build/ccode"
BUILD="$BROOT/build-wsl"

OUTDIR="$SRC/dottalkpp/bin-wsl"
OUTBIN="$OUTDIR/dottalkpp"

MANIFEST="$SRC/vcpkg.json"
MANIFEST_WIN="$SRC/vcpkg.json.win"
MANIFEST_WSL="$SRC/vcpkg-wsl.json"

require_dpkg_package() {
  local pkg="$1"
  local why="$2"
  if ! dpkg-query -W -f='${Status}\n' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
    echo "ERROR: missing system package: $pkg" >&2
    echo "  reason: $why" >&2
    return 1
  fi
}

preflight_wsl_system_packages() {
  local missing=0

  require_dpkg_package "bison" \
    "vcpkg Linux dependency resolution can pull gettext, which expects bison." || missing=1

  if grep -q '"wxwidgets"' "$MANIFEST_WSL"; then
    require_dpkg_package "libx11-dev" \
      "wxWidgets -> gtk3 -> cairo[x11] requires X11 development headers." || missing=1
    require_dpkg_package "libxft-dev" \
      "wxWidgets -> gtk3 -> cairo[x11] requires Xft development headers." || missing=1
    require_dpkg_package "libxext-dev" \
      "wxWidgets -> gtk3 -> cairo[x11] requires Xext development headers." || missing=1
    require_dpkg_package "libxi-dev" \
      "wxWidgets / GTK accessibility stack via at-spi2-core requires XInput development headers." || missing=1
    require_dpkg_package "libxtst-dev" \
      "wxWidgets / GTK accessibility stack via at-spi2-core requires Xtst development headers." || missing=1
    require_dpkg_package "libxrandr-dev" \
      "wxWidgets / GTK3 requires XRandR development headers." || missing=1
  fi

  if [[ "$missing" -ne 0 ]]; then
    echo >&2
    echo "Install the missing WSL packages, then rerun:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y bison libx11-dev libxft-dev libxext-dev libxi-dev libxtst-dev libxrandr-dev" >&2
    exit 1
  fi
}

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: source not found: $SRC" >&2
  exit 1
fi

if [[ ! -d "$VCPKG_ROOT" ]]; then
  echo "ERROR: VCPKG_ROOT not found: $VCPKG_ROOT" >&2
  exit 1
fi

if [[ ! -f "$MANIFEST_WSL" ]]; then
  echo "ERROR: missing $MANIFEST_WSL" >&2
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: missing $MANIFEST" >&2
  exit 1
fi

preflight_wsl_system_packages

mkdir -p "$BROOT"
rm -rf "$BUILD"

# Swap in WSL manifest so vcpkg does not try to build Windows-only pieces.
cp -f "$MANIFEST" "$MANIFEST_WIN"
cp -f "$MANIFEST_WSL" "$MANIFEST"

cleanup() {
  if [[ -f "$MANIFEST_WIN" ]]; then
    cp -f "$MANIFEST_WIN" "$MANIFEST"
    rm -f "$MANIFEST_WIN"
  fi
}
trap cleanup EXIT

cmake -S "$SRC" -B "$BUILD" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" \
  -DVCPKG_TARGET_TRIPLET=x64-linux \
  -DCMAKE_BUILD_TYPE=Release \
  -DDOTTALK_WITH_TV=ON \
  -DDOTTALK_WITH_INDEX=ON \
  -DBUILD_PYDOTTALK=OFF

cmake --build "$BUILD" -j

mkdir -p "$OUTDIR"

BIN_CANDIDATE_1="$BUILD/src/dottalkpp"
BIN_CANDIDATE_2="$BUILD/dottalkpp"

if [[ -f "$BIN_CANDIDATE_1" ]]; then
  cp -f "$BIN_CANDIDATE_1" "$OUTBIN"
elif [[ -f "$BIN_CANDIDATE_2" ]]; then
  cp -f "$BIN_CANDIDATE_2" "$OUTBIN"
else
  echo "ERROR: built executable not found." >&2
  echo "Checked:" >&2
  echo "  $BIN_CANDIDATE_1" >&2
  echo "  $BIN_CANDIDATE_2" >&2
  exit 1
fi

chmod +x "$OUTBIN"

echo "Built WSL binary and copied to:"
echo "  $OUTBIN"
