#!/usr/bin/env bash
set -euo pipefail

# datarun_wsl.sh
# - use newest WSL-built dottalkpp
# - copy it to dottalkpp/bin
# - chmod +x
# - run from dottalkpp/data
# - return to repo root

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${ROOT}/dottalkpp"
BIN_DIR="${APP_DIR}/bin"
DATA_DIR="${APP_DIR}/data"
FALLBACK_BIN="${APP_DIR}/bin-wsl-lean/dottalkpp"
FALLBACK_BIN_2="${APP_DIR}/bin-wsl/dottalkpp"

if [[ ! -d "${APP_DIR}" ]]; then
  echo "ERROR: expected app directory not found: ${APP_DIR}" >&2
  exit 1
fi

mkdir -p "${BIN_DIR}"

NEWEST_SRC="$(
  find "${ROOT}" \
    -type f -name dottalkpp \
    \( -path "*/build-wsl*" -o -path "*/build*" -o -path "*/bin-wsl*" \) \
    -printf '%T@ %p\n' 2>/dev/null \
  | sort -nr \
  | awk 'NR==1{print $2}'
)"

if [[ -z "${NEWEST_SRC}" || ! -f "${NEWEST_SRC}" ]]; then
  if [[ -f "${FALLBACK_BIN}" ]]; then
    NEWEST_SRC="${FALLBACK_BIN}"
  elif [[ -f "${FALLBACK_BIN_2}" ]]; then
    NEWEST_SRC="${FALLBACK_BIN_2}"
  else
    echo "ERROR: could not find a built 'dottalkpp' under ${ROOT}" >&2
    exit 1
  fi
fi

DEST="${BIN_DIR}/dottalkpp"

echo "Using newest build: ${NEWEST_SRC}"
echo "Copying to:         ${DEST}"

cp -f "${NEWEST_SRC}" "${DEST}"
chmod +x "${DEST}"

pushd "${DATA_DIR}" >/dev/null

echo "Running from:       $(pwd)"
echo "Executing:          ${DEST}"
# set -e is on (line 2), so a failing run would exit here and never reach a
# bare "status=$?" -- the popd and the explicit exit below were dead code. The
# "|| status=$?" form is what actually lets the cleanup run.
status=0
"${DEST}" "$@" || status=$?

popd >/dev/null
cd "${ROOT}"
echo "Returned to:        $(pwd)"

exit $status
