#!/usr/bin/env bash
# Run the staged Linux dottalkpp over data/, from inside dottalkpp/.
# Peer of the checkout-root ../wslrun.sh; same resolver, one level down.
#
# Does not build. Use ../wslbuild.sh for that.
set -euo pipefail

APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${APPDIR}/.." && pwd)"
# shellcheck source=../wsl-common.sh
source "${ROOT}/wsl-common.sh"

WORKDIR="${APPDIR}/data"

mapfile -t CANDIDATES < <(dottalk_runtime_candidates "${ROOT}")

if ! BIN="$(dottalk_newest_existing "wsl-run" "${CANDIDATES[@]}")"; then
    echo "ERROR: no staged Linux dottalkpp found. Looked for:" >&2
    printf '  %s\n' "${CANDIDATES[@]}" >&2
    echo "Build one first:  ../wslbuild.sh" >&2
    exit 1
fi

[[ -x "${BIN}" ]] || { echo "ERROR: not executable: ${BIN}" >&2; exit 1; }
[[ -d "${WORKDIR}" ]] || { echo "ERROR: work dir not found: ${WORKDIR}" >&2; exit 1; }

cd "${WORKDIR}"
exec "${BIN}" "$@"
