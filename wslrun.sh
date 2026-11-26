#!/usr/bin/env bash
# Run the staged Linux dottalkpp over dottalkpp/data.
#
# Does not build. Use ./wslbuild.sh for that -- it is the maintained Linux
# builder and stages into dottalkpp/bin-wsl-lean.
#
# This launcher used to read dottalkpp/bin-wsl and nothing else, so after a
# wslbuild.sh build it executed whatever older binary happened to be sitting in
# bin-wsl, silently. It now takes the NEWEST staged binary and says which one.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wsl-common.sh
source "${ROOT}/wsl-common.sh"

WORKDIR="${ROOT}/dottalkpp/data"

mapfile -t CANDIDATES < <(dottalk_runtime_candidates "${ROOT}")

if ! BIN="$(dottalk_newest_existing "wsl-run" "${CANDIDATES[@]}")"; then
    echo "ERROR: no staged Linux dottalkpp found. Looked for:" >&2
    printf '  %s\n' "${CANDIDATES[@]}" >&2
    echo "Build one first:  ./wslbuild.sh" >&2
    exit 1
fi

[[ -x "${BIN}" ]] || {
    echo "ERROR: staged binary is not executable: ${BIN}" >&2
    echo "Fix with:  chmod +x ${BIN}" >&2
    exit 1
}

[[ -d "${WORKDIR}" ]] || {
    echo "ERROR: work dir not found: ${WORKDIR}" >&2
    exit 1
}

cd "${WORKDIR}"
exec "${BIN}" "$@"
