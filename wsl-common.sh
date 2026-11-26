#!/usr/bin/env bash
# Shared helpers for the Linux/WSL launchers in this checkout.
#
# SOURCE THIS FILE, DO NOT EXECUTE IT.
#
# This is the Linux peer of launch-common.ps1's Select-DotTalkNewestExisting,
# and it exists for the same reason that function does: a working checkout can
# hold several staged dottalkpp binaries at once, and a launcher that takes the
# FIRST path that happens to exist will silently run whichever tree it happened
# to list first -- which is not the tree you just built.
#
# As of 2026-09-16 this checkout carried, at the same time:
#
#   dottalkpp/bin-wsl/dottalkpp        2026-07-31   staged by datarun.sh / the wsl preset
#   dottalkpp/bin-wsl-lean/dottalkpp   2026-09-04   staged by wslbuild.sh (the wsl-lean preset)
#
# wslbuild.sh is the maintained Linux builder and stages into bin-wsl-lean.
# Every launcher here used to read bin-wsl only, so a Linux user who built with
# the maintained builder and then ran a launcher executed a binary 35 days old
# and was told nothing about it.
#
# NAMING WHICH TREE WON IS THE WHOLE FIX. The notice goes to stderr so that
# "$(dottalk_newest_existing ...)" captures the path and nothing else.

# Absolute directory of the script that sourced this file's caller.
# Callers pass their own "${BASH_SOURCE[0]}".
dottalk_wsl_root() {
    local self="${1:?dottalk_wsl_root requires the caller BASH_SOURCE[0] path}"
    cd "$(dirname "${self}")" && pwd
}

# dottalk_newest_existing LABEL CANDIDATE [CANDIDATE...]
#
# Echoes the newest candidate that exists, by mtime, on stdout. Announces the
# winner on stderr. Returns 1 and echoes nothing when none of them exist.
dottalk_newest_existing() {
    local label="${1:?dottalk_newest_existing requires a label}"
    shift

    local newest="" newest_mtime=-1 candidate candidate_mtime found=0

    for candidate in "$@"; do
        [[ -n "${candidate}" && -f "${candidate}" ]] || continue
        found=$((found + 1))
        candidate_mtime="$(stat -c '%Y' "${candidate}" 2>/dev/null || echo -1)"
        if (( candidate_mtime > newest_mtime )); then
            newest="${candidate}"
            newest_mtime="${candidate_mtime}"
        fi
    done

    if [[ -z "${newest}" ]]; then
        return 1
    fi

    printf '%s: using %s (%s)\n' \
        "${label}" "${newest}" "$(date -d "@${newest_mtime}" '+%Y-%m-%d %H:%M:%S')" >&2

    if (( found > 1 )); then
        printf '%s: %d other staged binary/binaries were older and were not used.\n' \
            "${label}" "$((found - 1))" >&2
    fi

    printf '%s\n' "${newest}"
}

# The staged-runtime search order for this checkout, newest wins regardless of
# the order given. bin-wsl-lean is listed first only so that a reader sees the
# maintained lane first; the ordering carries no precedence.
dottalk_runtime_candidates() {
    local root="${1:?dottalk_runtime_candidates requires the checkout root}"
    printf '%s\n' \
        "${root}/dottalkpp/bin-wsl-lean/dottalkpp" \
        "${root}/dottalkpp/bin-wsl/dottalkpp" \
        "${root}/dottalkpp/bin/dottalkpp"
}
