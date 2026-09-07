# tools/staging/pk_durability_two_run.ps1
#
# AIF-156 -- DOES A PRIMARY KEY DECLARATION SURVIVE A RESTART?
#
# THE ONE QUESTION REGRESSION CANNOT ASK. A .dts runs in ONE process, so no
# marker in PKPOLICY can tell whether the designation was READ BACK from the
# x64 header or merely remembered in a map that had not died yet. This harness
# starts TWO processes: run 1 declares and writes, run 2 reopens WITHOUT
# redeclaring and tries to duplicate the key.
#
# WHY A DRIVER AND NOT A SPEC. The regression registry runs one script in the
# calling process. Two processes need something outside it, and this is the
# smallest thing that works -- it is not a replacement for a spec, it is the
# measurement that tells us whether a spec is worth building.
#
# READ RULE: SIX markers must PRINT and all six read .T. Four in run 1
# (PKD_W1..W4), two guards plus two arms in run 2 (PKD_G1, PKD_G2, PKD_T1,
# PKD_T2). COUNT THEM -- an errored marker in this language PRINTS NOTHING
# rather than going red, so five green markers is a failure with a clean face.
#
# IF PKD_G1 OR PKD_G2 READS .F., the fixture did not survive run 1 and the arms
# are UNPROVEN rather than failing. That is a different finding.
#
# Proof capture is SET ALTERNATE, inside the scripts. DOTSCRIPT ... OUT is NOT a
# proof capture (AIF-081) and is not used here.

$ErrorActionPreference = "Stop"

$repo    = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$scripts = Join-Path $repo "dottalkpp\data\scripts"
$tmp     = Join-Path $repo "dottalkpp\data\tmp"

$run1Script = Join-Path $scripts "pk_durable_write.dts"
$run2Script = Join-Path $scripts "pk_durable_read.dts"
$run1Alt    = Join-Path $tmp "pkdur_run1.alt"
$run2Alt    = Join-Path $tmp "pkdur_run2.alt"

foreach ($p in @($run1Script, $run2Script)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "missing script: $p" }
}

# Stale captures would be read as this run's evidence.
foreach ($p in @($run1Alt, $run2Alt)) {
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
}

$datarun = Join-Path $repo "datarun.ps1"

Write-Host "PKDUR: run 1 of 2 -- declare and write (process 1)"
& $datarun -CommandLines @("DOTSCRIPT $run1Script")

Write-Host "PKDUR: run 2 of 2 -- reopen WITHOUT redeclaring (process 2)"
& $datarun -CommandLines @("DOTSCRIPT $run2Script")

# ---- read the two captures -------------------------------------------------
#
# The marker set is DERIVED from the transcripts, not declared here, for the
# reason cmd_regression.cpp's PKPOLICY entry gives: a count written beside the
# thing it counts is a SECOND DECLARATION and drifts. The expected NAMES are
# listed because a missing marker must be distinguishable from a red one.

$expected = @(
    @{ File = $run1Alt; Name = "PKD_W1_first_key_is_1" },
    @{ File = $run1Alt; Name = "PKD_W2_second_key_is_2" },
    @{ File = $run1Alt; Name = "PKD_W3_refused_in_declaring_process" },
    @{ File = $run1Alt; Name = "PKD_W4_row1_is_ALPHA" },
    @{ File = $run2Alt; Name = "PKD_G1_fixture_reopened" },
    @{ File = $run2Alt; Name = "PKD_G2_key_survived_as_1" },
    @{ File = $run2Alt; Name = "PKD_T1_primary_survived_restart" },
    @{ File = $run2Alt; Name = "PKD_T2_still_1_after_reopen" }
)

foreach ($f in @($run1Alt, $run2Alt)) {
    if (-not (Test-Path -LiteralPath $f)) {
        Write-Host "PK DURABILITY: FAIL -- no capture at $f; the run did not reach SET ALTERNATE."
        exit 1
    }
}

$run1Text = Get-Content -LiteralPath $run1Alt -Raw
$run2Text = Get-Content -LiteralPath $run2Alt -Raw

$missing = @()
$red     = @()
$green   = @()

foreach ($e in $expected) {
    $text = if ($e.File -eq $run1Alt) { $run1Text } else { $run2Text }
    if     ($text -match [regex]::Escape($e.Name + ":.T.")) { $green   += $e.Name }
    elseif ($text -match [regex]::Escape($e.Name + ":.F.")) { $red     += $e.Name }
    else                                                    { $missing += $e.Name }
}

Write-Host ""
Write-Host "PKDUR markers: $($green.Count) green, $($red.Count) red, $($missing.Count) MISSING (of $($expected.Count))"
foreach ($m in $missing) { Write-Host "  MISSING (printed nothing, which is not a pass): $m" }
foreach ($m in $red)     { Write-Host "  RED: $m" }

if ($missing.Count -gt 0) {
    Write-Host "PK DURABILITY: FAIL -- a marker did not print. An errored marker prints nothing rather than going red; treat this as a lost claim, not a pass."
    exit 1
}

$guardsRed = @($red | Where-Object { $_ -like "PKD_G*" -or $_ -like "PKD_W*" })
if ($guardsRed.Count -gt 0) {
    Write-Host "PK DURABILITY: UNPROVEN -- a guard failed, so the arms say nothing about durability."
    Write-Host "  A red PKD_W3 means enforcement is broken on this build ENTIRELY, which is a different finding from a lost declaration."
    exit 1
}

if ($red.Count -gt 0) {
    Write-Host "PK DURABILITY: FAIL -- the declaration did NOT survive the restart."
    Write-Host "  A fresh process reopened the table, did not redeclare, and a REPLACE overwrote the primary key."
    Write-Host "  That is the defect AIF-156's header ruling exists to remove. See AI_PRIMARY_KEY_POLICY_CHARTER_V1.md."
    exit 1
}

Write-Host "PK DURABILITY: PASS -- the designation was written by one process and HONOURED BY ANOTHER."
Write-Host "  This is the only measurement in the tree that can say so; PKPOLICY structurally cannot."
exit 0
