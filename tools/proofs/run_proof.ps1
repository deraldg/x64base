<#
.SYNOPSIS
  Run a runtime proof, capture the transcript, and distinguish a NULL result
  from a NEGATIVE one.

.WHY THIS EXISTS
  AIF-065 was blocked at source_defined for a day. Proving it took three
  attempts, and TWO OF THE THREE FAILED IN THE HARNESS RATHER THAN THE SUBJECT:

    attempt 1  relative Tee-Object path. datarun.ps1 runs with cwd set to
               dottalkpp\data, so the path retargeted, Tee failed opening it,
               and the failure aborted the pipeline BEFORE the shell ran.
               Result: 134217728 -> 134217728.
    attempt 2  only SETPATH DBF was set, so the CDX container was not findable,
               no auto-attach occurred, and nothing under test executed.
               Result: 134217728 -> 134217728.
    attempt 3  all three path slots set. 134217728 -> 1073741824. Proven.

  The first two are indistinguishable from "the mechanism does not exist" by
  looking at the numbers. A proof harness whose failures look like negative
  findings is worse than no harness, because it manufactures false confidence
  in the null direction.

.WHAT THIS ENFORCES
  1. ABSOLUTE PATHS for the transcript, always. Never inherit the runner cwd.
  2. EXPECTED MARKERS. You must state what success looks like IN THE
     TRANSCRIPT, not only what to measure. If the markers are absent the run is
     reported NULL -- the subject did not execute -- and no verdict is offered
     on the measurements.
  3. BEFORE/AFTER measurement of named files, reported as an explicit delta.
  4. A proofs.yaml-ready block on success, so the evidence lands in the registry
     instead of a chat window (AIF-062: a proof must cite a COMMITTED artifact).

.EXAMPLE
  .\tools\proofs\run_proof.ps1 -Lane AIF-065 -Name mapsize_attach `
    -CommandLines 'SETPATH DBF metadata','SETPATH INDEXES INDEXES/metadata',
                  'SETPATH LMDB LMDB/metadata','USE SYSSUBCMD',
                  'SET ORDER TO SUB_ID','SEEK "SUB_SET_WRAP"' `
    -ExpectMarkers 'Auto-attached order:','Found at' `
    -MeasureFiles @{ env = 'dottalkpp\data\LMDB\metadata\SYSSUBCMD.cdx.d\data.mdb' } `
    -ExpectChange
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]   $Lane,
    [Parameter(Mandatory)][string]   $Name,
    [Parameter(Mandatory)][string[]] $CommandLines,

    # What must appear in the transcript for the run to have MEANT anything.
    # Absent  ->  NULL, not negative.
    [string[]] $ExpectMarkers = @(),

    # name -> path (repo-relative or absolute). Sized before and after.
    [hashtable] $MeasureFiles = @{},

    [switch] $ExpectChange,
    [switch] $ExpectNoChange,

    # Source files whose change is THE SUBJECT of this proof. If any is newer
    # than the runtime binary, the binary cannot contain the change and the run
    # is reported STALE BUILD -- a NULL result, not a negative one.
    #
    # Added after the third harness failure in one afternoon, each at a higher
    # level than the last:
    #   1. the transcript path aborted the pipeline before the shell ran
    #   2. the shell ran but never reached the code path under test
    #   3. the code path ran but THE BINARY PREDATED THE FIX -- sources edited
    #      09:13, dottalkpp.exe built 06:53. The run reported CONTRADICTED,
    #      which read exactly like "the fix does not work".
    # Verifying that the commands executed is not the same as verifying that
    # the change executed.
    [string[]] $SourceUnderTest = @()
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

# Rule 1: absolute, always. This is the bug that killed attempt 1.
$stamp   = Get-Date -Format 'yyyyMMdd'
$runsDir = Join-Path $repo 'labtalk\proofs\runs'
$log     = Join-Path $runsDir ("{0}_{1}_{2}.txt" -f $stamp, $Lane.ToLower().Replace('-',''), $Name)
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null

function Resolve-Measured([string]$p) {
    if ([System.IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $repo $p }
}
function Get-SizeOrNull([string]$p) {
    if (Test-Path $p) { (Get-Item $p).Length } else { $null }
}

# Rule 0: is the change under test actually IN the binary?
if ($SourceUnderTest.Count -gt 0) {
    $exe = Join-Path $repo 'dottalkpp\bin\dottalkpp.exe'
    if (-not (Test-Path $exe)) {
        $exe = Join-Path $repo 'build\src\Release\dottalkpp.exe'
    }
    if (Test-Path $exe) {
        $exeTime = (Get-Item $exe).LastWriteTime
        $stale = @()
        foreach ($s in $SourceUnderTest) {
            $sp = Resolve-Measured $s
            if ((Test-Path $sp) -and (Get-Item $sp).LastWriteTime -gt $exeTime) {
                $stale += ("{0}  (edited {1}, binary built {2})" -f `
                    $s, (Get-Item $sp).LastWriteTime.ToString('HH:mm:ss'), `
                    $exeTime.ToString('HH:mm:ss'))
            }
        }
        if ($stale.Count -gt 0) {
            Write-Host ''
            Write-Host 'STALE BUILD -- the binary predates the change under test.' -ForegroundColor Yellow
            $stale | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
            Write-Host 'Any verdict from this run would describe the OLD code.' -ForegroundColor Yellow
            Write-Host 'Rebuild, then run again:' -ForegroundColor Yellow
            Write-Host '    cmake --build build --target dottalkpp --config Release' -ForegroundColor Yellow
            exit 2
        }
        Write-Host ("  binary    {0}  (newer than the source under test)" -f `
            $exeTime.ToString('yyyy-MM-dd HH:mm:ss'))
    }
}

$before = @{}
foreach ($k in $MeasureFiles.Keys) { $before[$k] = Get-SizeOrNull (Resolve-Measured $MeasureFiles[$k]) }

Write-Host "=== proof $Lane / $Name ===" -ForegroundColor Cyan
foreach ($k in $before.Keys) { Write-Host ("  before  {0,-12} {1}" -f $k, $before[$k]) }

Push-Location $repo
try {
    & (Join-Path $repo 'datarun.ps1') -CommandLines $CommandLines *>&1 |
        Tee-Object -FilePath $log
} finally { Pop-Location }

$after = @{}
foreach ($k in $MeasureFiles.Keys) { $after[$k] = Get-SizeOrNull (Resolve-Measured $MeasureFiles[$k]) }

$transcript = if (Test-Path $log) { Get-Content -Raw $log } else { '' }

# Rule 2: did the subject actually run?
$missing = @($ExpectMarkers | Where-Object { $transcript -notmatch [regex]::Escape($_) })

Write-Host ''
Write-Host '=== verdict ===' -ForegroundColor Cyan
foreach ($k in $after.Keys) {
    $b = $before[$k]; $a = $after[$k]
    $delta = if ($null -ne $b -and $null -ne $a) { $a - $b } else { $null }
    Write-Host ("  {0,-12} {1} -> {2}   delta {3}" -f $k, $b, $a, $delta)
}

if ($missing.Count -gt 0) {
    Write-Host ''
    Write-Host 'NULL RESULT -- the subject did not execute.' -ForegroundColor Yellow
    Write-Host 'Expected transcript marker(s) absent:' -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    Write-Host 'The measurements above are MEANINGLESS. This is not a negative' -ForegroundColor Yellow
    Write-Host 'finding: fix the probe and run again.' -ForegroundColor Yellow
    Write-Host "transcript: $log"
    exit 2
}

$changed = $false
foreach ($k in $after.Keys) { if ($before[$k] -ne $after[$k]) { $changed = $true } }

$verdict = 'OBSERVED'
if     ($ExpectChange   -and -not $changed) { $verdict = 'CONTRADICTED (expected a change, saw none)' }
elseif ($ExpectNoChange -and      $changed) { $verdict = 'CONTRADICTED (expected no change, saw one)' }

Write-Host ''
Write-Host "  markers   all present -- the subject ran" -ForegroundColor Green
Write-Host "  verdict   $verdict" -ForegroundColor Green
Write-Host "  transcript $log"

if ($verdict -eq 'OBSERVED') {
    $rel = $log.Substring($repo.Length).TrimStart('\').Replace('\','/')
    Write-Host ''
    Write-Host '--- proofs.yaml block (evidence must cite a COMMITTED artifact) ---'
    Write-Host "  - id: proof.$($Lane.ToLower().Replace('-','.')).$Name"
    Write-Host "    label: TODO one line"
    Write-Host "    state: runtime_observed"
    Write-Host "    source: $rel"
    Write-Host "    return_code: 0"
    Write-Host "    notes: >-"
    foreach ($k in $after.Keys) {
        Write-Host ("      {0}: {1} -> {2}" -f $k, $before[$k], $after[$k])
    }
    Write-Host ''
    Write-Host "git add $rel"
}
exit 0
