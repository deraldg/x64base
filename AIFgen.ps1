<#
AIFgen.ps1 -- launcher for the AIF number allocator.

  THIS SCRIPT DOES NOT ALLOCATE ANYTHING. It shells to the one allocator,
  tools/coordination/session_coordinator.py, and does nothing else. That is the
  whole point of it existing.

  The Tier-1 seed says: "Claim lane numbers atomically, never by grep. Grep is
  not an allocator." A second thing that hands out AIF numbers would be exactly
  the defect this repo keeps paying for -- one claim with two homes -- and the
  cost is not theoretical: AIF-135 records that the old lowest-free rule issued
  AIF-043, a live lane, THREE TIMES. The allocator is monotonic max+1 for that
  reason, and this launcher must never second-guess it, predict it, or cache it.

  Interpreter: the repo venv, per CLAUDE.md -- $py12 = .venv312\Scripts\python.exe.
  Not bare `python`, not `py -3`; tools/staging/check_host_python.py gates that.

USAGE
  .\AIFgen.ps1 -Lane triggers-pdlc
  .\AIFgen.ps1 -Lane sqlsel-pdlc -Member member.ai.claude.cowork
  .\AIFgen.ps1 -Lane triggers-pdlc -Number 151
  .\AIFgen.ps1 -Lane triggers-pdlc -Number 146 -BackfillExisting
  .\AIFgen.ps1 -Status

NOTES
  -Number may mint ONLY the next monotonic number; a forward skip is refused by
  the allocator, because a hole created deliberately is still a hole.
  -BackfillExisting is a DIFFERENT operation: attaching a claim file to a number
  already in the universe. Say it out loud or the allocator refuses.

  WRITING THE INTAKE ROW BEFORE RUNNING THIS IS HOW AIF-146 WAS BURNED.
  Claim first, then write the row with the number it gave you.
#>

[CmdletBinding()]
Param(
  [string]$Lane,
  [string]$Member = 'member.derald',
  [string]$Run    = '',
  [int]$Number    = 0,
  [switch]$BackfillExisting,
  [switch]$Status
)

$ErrorActionPreference = 'Stop'

# Repo root is where this script lives, so it works from any working directory.
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$Py = Join-Path $RepoRoot '.venv312\Scripts\python.exe'
if (-not (Test-Path $Py)) {
  Write-Error "AIFgen: repo venv interpreter not found at $Py. Create .venv312 or fix the path; do NOT fall back to bare python -- check_host_python.py gates that."
  exit 1
}

$Coordinator = Join-Path $RepoRoot 'tools\coordination\session_coordinator.py'
if (-not (Test-Path $Coordinator)) {
  Write-Error "AIFgen: allocator not found at $Coordinator. Refusing to invent a number."
  exit 1
}

if ($Status) {
  & $Py $Coordinator --root $RepoRoot status
  exit $LASTEXITCODE
}

if ([string]::IsNullOrWhiteSpace($Lane)) {
  Write-Error "AIFgen: -Lane is required. It is the one field nothing can guess for you, and a claim without it files the number under nothing."
  exit 1
}

# A run id groups a session's claims. Generated only when not supplied, and
# printed below so it is never silently attributed.
if ([string]::IsNullOrWhiteSpace($Run)) {
  $Run = 'AIFGEN-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

$args = @('claim-aif', '--member', $Member, '--run', $Run, '--lane', $Lane)
if ($Number -gt 0)      { $args += @('--number', $Number) }
if ($BackfillExisting)  { $args += '--backfill-existing' }

Write-Host ""
Write-Host "AIFgen -- claiming through tools/coordination/session_coordinator.py"
Write-Host "  member : $Member"
Write-Host "  run    : $Run"
Write-Host "  lane   : $Lane"
if ($Number -gt 0)     { Write-Host "  number : $Number (explicit; allocator still refuses a forward skip)" }
if ($BackfillExisting) { Write-Host "  mode   : BACKFILL -- attaching a claim to a number already in the universe" }
Write-Host ""

& $Py $Coordinator --root $RepoRoot @args
$rc = $LASTEXITCODE

if ($rc -eq 0) {
  Write-Host ""
  Write-Host "NEXT, and in this order: write the intake row in"
  Write-Host "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md using the number above,"
  Write-Host "then commit the row and the .claim file together. The AIF-collision gate"
  Write-Host "checks them; a claim with no row, or a row with no claim, is reported."
} else {
  Write-Host ""
  Write-Host "AIFgen: the allocator refused (exit $rc). Read its message -- it is"
  Write-Host "usually telling you the number is already in the universe, or that you"
  Write-Host "asked for a forward skip. Do not work around it by hand."
}
exit $rc
