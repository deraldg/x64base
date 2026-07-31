#!/usr/bin/env bash
set -euo pipefail

# datarun_wsl.sh
# - find newest WSL-built dottalkpp (from build-wsl* / build*)
# - copy it to ~/code/ccode/dottalkpp/bin
# - chmod +x
# - cd to ~/code/ccode/dottalkpp/data and run dottalkpp
# - return to ~/code/ccode

ROOT="${HOME}/code/ccode"
APP_DIR="${ROOT}/dottalkpp"
BIN_DIR="${APP_DIR}/bin"
DATA_DIR="${APP_DIR}/data"

if [[ ! -d "${APP_DIR}" ]]; then
  echo "ERROR: expected app directory not found: ${APP_DIR}" >&2
  exit 1
fi

mkdir -p "${BIN_DIR}"

# Find newest built dottalkpp under common build directories (relative to current dir)
# If you run this from somewhere else, it still works by searching under ${ROOT}.
NEWEST_SRC="$(
  find "${ROOT}" \
    -type f -name dottalkpp \
    \( -path "*/build-wsl*" -o -path "*/build*" \) \
    -printf '%T@ %p\n' 2>/dev/null \
  | sort -nr \
  | awk 'NR==1{print $2}'
)"

if [[ -z "${NEWEST_SRC}" || ! -f "${NEWEST_SRC}" ]]; then
  echo "ERROR: could not find a built 'dottalkpp' under ${ROOT}/build* or ${ROOT}/build-wsl*" >&2
  exit 1
fi

DEST="${BIN_DIR}/dottalkpp"

echo "Using newest build: ${NEWEST_SRC}"
echo "Copying to:         ${DEST}"

cp -f "${NEWEST_SRC}" "${DEST}"
chmod +x "${DEST}"

# Run from data directory, then return to ROOT
pushd "${DATA_DIR}" >/dev/null

echo "Running from:       $(pwd)"
echo "Executing:          ${DEST}"
"${DEST}" "$@"

popd >/dev/null
cd "${ROOT}"
echo "Returned to:        $(pwd)"
