param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

# This was two lines: Set-Location into labtalk, then a bare `python`. On this
# machine bare `python` resolves to the vcpkg python3, which has neither
# tkinter nor PyYAML -- measured 2026-09-18 -- so the portal window has not
# opened from its own launcher for as long as PATH has resolved that way, and
# the only symptom was the portal's own "GUI unavailable" line, which never
# named the interpreter it was running under.
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $repoRoot "launch-common.ps1")

$portal = Join-Path $repoRoot "labtalk\portal\labtalk_portal.py"
Assert-DotTalkPath -LiteralPath $portal -Label "LabTalk portal"

# --audit, --audit-write and --run-item are HEADLESS and need yaml only. The
# repo venv serves those today and refusing it over a toolkit the run will
# never load would be a refusal for its own sake.
$headlessOnly = $false
if ($AppArgs) {
    $gui = @($AppArgs | Where-Object { $_ -notlike '--audit*' -and $_ -notlike '--run-item*' })
    $headlessOnly = ($gui.Count -eq 0)
}

$python = Resolve-LabTalkPython -RepoRoot $repoRoot -RequireTk (-not $headlessOnly)

# The portal reads registries by paths relative to the labtalk directory.
Push-Location (Join-Path $repoRoot "labtalk")
try {
    $runArgs = @($portal) + (Get-DotTalkAppArgs -AppArgs $AppArgs)
    & $python @runArgs
    Set-DotTalkLastExitCode
}
finally {
    Pop-Location
}
