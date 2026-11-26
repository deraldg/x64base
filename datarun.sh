#!/usr/bin/env bash
set -euo pipefail

# WSL/Linux peer of datarun.ps1.
# Stages the newest Linux dottalkpp build, runs from dottalkpp/data, and
# optionally executes command lines through a temporary DotScript file.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${ROOT}/dottalkpp"
RUNTIME_DATA="${APP_ROOT}/data"
RUNTIME_DIR="${APP_ROOT}/bin"
RUNTIME_EXE="${RUNTIME_DIR}/dottalkpp"

COMMAND_LINES=()
APP_ARGS=()
COMMANDS_FILE=""
TEMP_SCRIPT=""

usage() {
    cat <<'EOF'
Usage:
  ./datarun.sh [application arguments...]
  ./datarun.sh -CommandLines "COMMAND 1" "COMMAND 2"
  ./datarun.sh --commands-file path/to/script.dts
  ./datarun.sh -CommandLines "COMMAND" -- [application arguments...]

Options:
  -CommandLines, --command-lines
      Treat every following argument up to "--" as a DotTalk++ command line.

  --commands-file FILE
      Read DotTalk++ command lines from FILE. May be combined with
      -CommandLines.

  --launcher-help
      Show this launcher help. Other arguments are passed to dottalkpp.
EOF
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

cleanup() {
    if [[ -n "${TEMP_SCRIPT}" && -f "${TEMP_SCRIPT}" ]]; then
        rm -f -- "${TEMP_SCRIPT}"
    fi
}
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        -CommandLines|--command-lines)
            shift
            while [[ $# -gt 0 && "$1" != "--" ]]; do
                COMMAND_LINES+=("$1")
                shift
            done
            if [[ $# -gt 0 && "$1" == "--" ]]; then
                shift
                APP_ARGS+=("$@")
                break
            fi
            ;;
        --commands-file)
            [[ $# -ge 2 ]] || fail "--commands-file requires a path"
            COMMANDS_FILE="$2"
            shift 2
            ;;
        --launcher-help)
            usage
            exit 0
            ;;
        --)
            shift
            APP_ARGS+=("$@")
            break
            ;;
        *)
            APP_ARGS+=("$1")
            shift
            ;;
    esac
done

[[ -d "${APP_ROOT}" ]] || fail "application root not found: ${APP_ROOT}"
[[ -d "${RUNTIME_DATA}" ]] || fail "runtime data path not found: ${RUNTIME_DATA}"

if [[ -n "${COMMANDS_FILE}" ]]; then
    [[ -f "${COMMANDS_FILE}" ]] || fail "commands file not found: ${COMMANDS_FILE}"
    while IFS= read -r line || [[ -n "${line}" ]]; do
        COMMAND_LINES+=("${line}")
    done < "${COMMANDS_FILE}"
fi

NEWEST_BUILD=""
NEWEST_MTIME=-1
SEARCH_ROOTS=()

# build-wsl-lean / bin-wsl-lean are where wslbuild.sh -- the maintained Linux
# builder -- configures and stages. They were missing from this list, so after
# a wslbuild.sh build this script reported "Using newest build" and then named
# the OLDER bin-wsl copy, because the newer tree was never a candidate.
# Order here carries no precedence: the mtime comparison below decides.
for candidate_root in "${ROOT}/build-wsl-lean" "${APP_ROOT}/bin-wsl-lean" \
                      "${ROOT}/build-wsl"      "${APP_ROOT}/bin-wsl"; do
    if [[ -d "${candidate_root}" ]]; then
        SEARCH_ROOTS+=("${candidate_root}")
    fi
done

[[ ${#SEARCH_ROOTS[@]} -gt 0 ]] ||
    fail "no Linux build roots found; expected build-wsl-lean, build-wsl,
dottalkpp/bin-wsl-lean or dottalkpp/bin-wsl. Build one with ./wslbuild.sh"

while IFS= read -r -d '' candidate; do
    candidate_mtime="$(stat -c '%Y' "${candidate}")"
    if (( candidate_mtime > NEWEST_MTIME )); then
        NEWEST_BUILD="${candidate}"
        NEWEST_MTIME="${candidate_mtime}"
    fi
done < <(find "${SEARCH_ROOTS[@]}" -type f -name dottalkpp -print0 2>/dev/null)

[[ -n "${NEWEST_BUILD}" && -f "${NEWEST_BUILD}" ]] ||
    fail "built executable not found under: ${SEARCH_ROOTS[*]}"

mkdir -p "${RUNTIME_DIR}"

echo "Using newest build: ${NEWEST_BUILD}"
echo "Copying to:         ${RUNTIME_EXE}"
cp -f -- "${NEWEST_BUILD}" "${RUNTIME_EXE}"
chmod +x "${RUNTIME_EXE}"

export DOTTALK_APPEND_TRACE=0
export DOTTALK_INDEX_TRACE=0

if [[ ${#COMMAND_LINES[@]} -gt 0 ]]; then
    TEMP_SCRIPT="$(mktemp "${TMPDIR:-/tmp}/dottalk-codex.XXXXXX.dts")"
    printf '%s\n' "${COMMAND_LINES[@]}" > "${TEMP_SCRIPT}"
fi

echo "Running from:       ${RUNTIME_DATA}"
if [[ -n "${TEMP_SCRIPT}" ]]; then
    echo "Executing:          ${RUNTIME_EXE} --script <temporary.dts>"
    (
        cd "${RUNTIME_DATA}"
        "${RUNTIME_EXE}" --script "${TEMP_SCRIPT}" "${APP_ARGS[@]}"
    )
else
    echo "Executing:          ${RUNTIME_EXE}"
    (
        cd "${RUNTIME_DATA}"
        "${RUNTIME_EXE}" "${APP_ARGS[@]}"
    )
fi
