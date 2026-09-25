# py12_guard.ps1 -- make bare `python` safe inside the x64base (ccode) tree.
#
# Why: the house standard is that host Python running repo tools uses the repo venv
# (.venv312 / $py12), never bare `python` (which resolves to the wrong interpreter and fails on
# yaml-importing tools). That rule is easy to forget when authoring a command. This guard makes
# the environment forgive the slip: inside the clone, bare `python` routes to $py12; anywhere
# else it behaves normally. It is the daily-cost safety net that complements the repo gate
# (tools/staging/check_host_python.py), which keeps NEW docs/scripts using the canonical form.
#
# Install once: add a line like this to your PowerShell profile ($PROFILE), then reopen the
# shell -- the path is wherever YOUR clone lives, and nothing below depends on it:
#     . <your-clone>\tools\ps\py12_guard.ps1

# THE CLONE IS NOT ON A KNOWN DRIVE. This file used to pin 'D:\code\ccode' twice -- once for
# the venv and once for the `-like` test below -- so the guard silently did nothing on any
# other machine or drive letter. It now derives the root from its OWN location (this file is
# <root>\tools\ps\py12_guard.ps1), which is the shape AIFgen.ps1:48 and
# backup_essential_drop.ps1 already use. A clone on an SD card whose letter changes between
# machines works without editing anything.
$Global:X64BaseRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Global:Py12 = Join-Path $Global:X64BaseRoot '.venv312\Scripts\python.exe'

function python {
    if ($PWD.Path -like ($Global:X64BaseRoot + '*') -and (Test-Path $Global:Py12)) {
        & $Global:Py12 @args
    } else {
        $real = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue |
                Select-Object -First 1
        if ($real) { & $real.Source @args }
        else { Write-Error 'python.exe not found on PATH (and not in the ccode tree).' }
    }
}

# `python3` is not standard on Windows; alias it to the same guarded function for pasted commands.
Set-Alias -Name python3 -Value python -Scope Global -Force
