# py12_guard.ps1 -- make bare `python` safe inside the x64base (ccode) tree.
#
# Why: the house standard is that host Python running repo tools uses the repo venv
# (.venv312 / $py12), never bare `python` (which resolves to the wrong interpreter and fails on
# yaml-importing tools). That rule is easy to forget when authoring a command. This guard makes
# the environment forgive the slip: inside D:\code\ccode, bare `python` routes to $py12; anywhere
# else it behaves normally. It is the daily-cost safety net that complements the repo gate
# (tools/staging/check_host_python.py), which keeps NEW docs/scripts using the canonical form.
#
# Install once: add this line to your PowerShell profile ($PROFILE), then reopen the shell:
#     . D:\code\ccode\tools\ps\py12_guard.ps1

$Global:Py12 = 'D:\code\ccode\.venv312\Scripts\python.exe'

function python {
    if ($PWD.Path -like 'D:\code\ccode*' -and (Test-Path $Global:Py12)) {
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
