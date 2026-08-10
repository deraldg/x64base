#!/usr/bin/env bash
# Compatibility entrypoint for the maintained checkout-relative WSL builder.
#
# The former implementation embedded one workstation's development path,
# deleted that checkout's build directory, and temporarily replaced vcpkg.json.
# Those behaviors made the script invalid in publication staging and unsafe
# after interruption.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "NOTE: wsl_build_dottalkpp.sh is a compatibility name; using wslbuild.sh." >&2
exec "$ROOT/wslbuild.sh" "$@"
