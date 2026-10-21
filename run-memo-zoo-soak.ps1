# @dottalk.file v1
# subsystem: tools
# layer: runner
# owns: the repeatable replay of the memo zoo M1 soak
# project: project.x64base.runtime
# lane: AIF-070 (memo zoo, MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1)
# owner: member.derald
# status: supported

# THE MEMO ZOO M1 SOAK, AS ONE COMMAND.
#
# WHY THIS SCRIPT EXISTS. The harness (src/memo/memo_zoo.cpp, target memo_zoo)
# and the charter have been in the tree since 2026-08-11, and the four green
# seeds were recorded -- but only as PROSE inside a registry note, in
# labtalk/registries/proofs.d/proof.memo.zoo_orthogonality.yaml. Reproducing the
# soak meant parsing a paragraph for parameters, and `build.ps1` does not build
# the target at all, so the first step was knowledge nobody had written down.
# An operation that cannot be re-run from the tree is a result, not a proof.
#
# THE PARAMETERS BELOW ARE THE RECORDED ONES, and they check out against the
# registry's own totals: 500 + 5,000 + 5,000 + 10,000 = 20,500 generations and
# 1,584 + 22,353 + 29,648 + 50,459 = 104,044 operations, which is exactly what
# that note claims for the four-seed run. If a seed's op count comes back
# different, EITHER the engine changed or the harness did -- that is the point of
# recording them, so say which rather than editing the number.
#
# THE ZOO CLEANS UP AFTER ITSELF, AND NOW SO DOES THE SOAK. memo_zoo.cpp sets
# its store to tmp/memo_zoo.dtx and REMOVES IT at startup ("deterministic fresh
# biosphere per run"), so the file is never input -- it is the leftover of the
# last run. One was found at 584 MB dated 11 August while reclaiming tmp/. This
# script deletes it at the end unless -KeepStore is given.

[CmdletBinding()]
param(
  [string]$BuildDir = "build",
  [string]$Config   = "Release",
  [switch]$SkipBuild,
  [switch]$KeepStore
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

# The four seeds as the proof registry records them. Op counts are EXPECTATIONS,
# not inputs: the harness derives them, and a mismatch is a finding.
$Seeds = @(
  @{ seed = 20260811; generations =   500; extra = @();                             ops =  1584 },
  @{ seed =        7; generations =  5000; extra = @();                             ops = 22353 },
  @{ seed =       42; generations =  5000; extra = @('--population','200');         ops = 29648 },
  @{ seed =     1993; generations = 10000; extra = @('--reopen-every','50');        ops = 50459 }
)

$exe = Join-Path $BuildDir (Join-Path "src" (Join-Path "memo" (Join-Path $Config "memo_zoo.exe")))

if (-not $SkipBuild) {
  Write-Host "--- building the memo_zoo target (build.ps1 does not) ---" -ForegroundColor Cyan
  & cmake --build $BuildDir --config $Config --target memo_zoo
  if ($LASTEXITCODE -ne 0) { throw "memo_zoo build failed with exit $LASTEXITCODE" }
}

if (-not (Test-Path -LiteralPath $exe)) {
  throw "memo_zoo.exe not found at $exe -- configure the build first, or pass -BuildDir."
}

Write-Host ""
Write-Host "--- replaying the four recorded seeds ---" -ForegroundColor Cyan
$totalGens = 0; $totalOps = 0; $failures = @()

foreach ($s in $Seeds) {
  $zooArgs = @('--seed', "$($s.seed)", '--generations', "$($s.generations)") + $s.extra
  Write-Host ""
  Write-Host ("  == seed " + $s.seed + " (" + ($zooArgs -join ' ') + ") ==") -ForegroundColor DarkGray

  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try   { $out = & $exe @zooArgs 2>&1 }
  finally { $ErrorActionPreference = $prev }
  $rc = $LASTEXITCODE

  $report = @($out | Where-Object { $_ -match '^MEMO-ZOO: ' })
  $diverge = @($out | Where-Object { $_ -match 'DIVERGENCE|ZOO-FAIL' })

  if ($rc -ne 0)            { $failures += "seed $($s.seed): exit $rc" }
  if ($diverge.Count -gt 0) { $failures += "seed $($s.seed): $($diverge.Count) divergence/fail line(s)"
                              $diverge | ForEach-Object { Write-Host "    $_" -ForegroundColor Red } }
  if ($report.Count -ne 1)  { $failures += "seed $($s.seed): no single MEMO-ZOO summary line" }
  else {
    Write-Host ("    " + $report[0])
    if ($report[0] -match '^MEMO-ZOO: (\d+) generations, (\d+) ops,') {
      $g = [int]$Matches[1]; $o = [int]$Matches[2]
      $totalGens += $g; $totalOps += $o
      if ($o -ne $s.ops) {
        $failures += "seed $($s.seed): ops $o, recorded $($s.ops) -- the engine or the harness moved"
        Write-Host ("    OPS MISMATCH: got " + $o + ", recorded " + $s.ops) -ForegroundColor Red
      } else {
        Write-Host ("    ops match the recorded " + $s.ops)
      }
    }
  }
}

Write-Host ""
Write-Host "============================================================"
Write-Host ("  generations : " + $totalGens + "   (recorded 20500)")
Write-Host ("  operations  : " + $totalOps + "  (recorded 104044)")
if ($totalGens -ne 20500) { $failures += "generation total $totalGens, recorded 20500" }
if ($totalOps  -ne 104044) { $failures += "operation total $totalOps, recorded 104044" }

if (-not $KeepStore) {
  $store = Join-Path "tmp" "memo_zoo.dtx"
  if (Test-Path -LiteralPath $store) {
    $mb = [math]::Round((Get-Item -LiteralPath $store).Length / 1MB, 1)
    Remove-Item -LiteralPath $store -Force
    Write-Host ("  store       : removed tmp/memo_zoo.dtx (" + $mb + " MB) -- pass -KeepStore to inspect it")
  }
}

if ($failures.Count -eq 0) {
  Write-Host "  VERDICT: PASS -- four seeds, zero divergences, counts as recorded" -ForegroundColor Green
  Write-Host "============================================================"
  exit 0
}
Write-Host ("  VERDICT: FAIL -- " + $failures.Count + " finding(s)") -ForegroundColor Red
$failures | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor Red }
Write-Host "  M2 (concurrency, Sentinel as a second process) IS STILL UNRUN and is" -ForegroundColor Yellow
Write-Host "  claimed nowhere -- do not read an M1 pass as a concurrency result." -ForegroundColor Yellow
Write-Host "============================================================"
exit 2
