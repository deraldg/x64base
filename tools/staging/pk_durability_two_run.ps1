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
# READ RULE: FIFTEEN markers must PRINT and each must match the value this
# driver declares below -- THIRTEEN .T. and TWO deliberately .F. (PKD_T3B and
# PKD_T4, whose reasons are in the .dts and in cmd_regression.cpp). COUNT THEM
# -- an errored marker in this language PRINTS NOTHING rather than going red,
# so fourteen agreeing markers is a failure with a clean face. IF ANY PKD_G* OR
# PKD_W* CONTRADICTS, the arms are UNPROVEN rather than failing.
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
    @{ File = $run1Alt; Name = "PKD_W1_first_key_is_1";                           Expect = $true  },
    @{ File = $run1Alt; Name = "PKD_W5_undeclared_SID_minted_by_name";            Expect = $true  },
    @{ File = $run1Alt; Name = "PKD_W2_second_key_is_2";                          Expect = $true  },
    @{ File = $run1Alt; Name = "PKD_W3_refused_in_declaring_process";             Expect = $true  },
    @{ File = $run1Alt; Name = "PKD_W4_row1_is_ALPHA";                            Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_G1_fixture_reopened";                         Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_G2_key_survived_as_1";                        Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_T1_primary_survived_restart";                 Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_T2_still_1_after_reopen";                     Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_G3_undeclared_append_parked_on_a_blank_row";  Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_G5_undeclared_SID_minted_by_name";            Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_T3_stamped_key_minted_without_a_declaration"; Expect = $true  },
    @{ File = $run2Alt; Name = "PKD_T3B_stamped_key_left_at_zero";                Expect = $false },
    @{ File = $run2Alt; Name = "PKD_T4_the_key_could_be_filled_by_hand";          Expect = $false },
    @{ File = $run2Alt; Name = "PKD_G4_the_new_row_accepts_a_non_key_write";      Expect = $true  }
)

foreach ($f in @($run1Alt, $run2Alt)) {
    if (-not (Test-Path -LiteralPath $f)) {
        Write-Host "PK DURABILITY: FAIL -- no capture at $f; the run did not reach SET ALTERNATE."
        exit 1
    }
}

$run1Text = Get-Content -LiteralPath $run1Alt -Raw
$run2Text = Get-Content -LiteralPath $run2Alt -Raw

$missing      = @()
$contradicted = @()
$agreed       = @()

foreach ($e in $expected) {
    $text = if ($e.File -eq $run1Alt) { $run1Text } else { $run2Text }
    $actual = $null
    if     ($text -match [regex]::Escape($e.Name + ":.T.")) { $actual = $true }
    elseif ($text -match [regex]::Escape($e.Name + ":.F.")) { $actual = $false }

    if     ($null -eq $actual)      { $missing      += $e.Name }
    elseif ($actual -eq $e.Expect)  { $agreed       += $e.Name }
    else {
        $printed  = if ($actual)   { ".T." } else { ".F." }
        $wanted   = if ($e.Expect) { ".T." } else { ".F." }
        $contradicted += "$($e.Name) printed $printed and this spec expects $wanted"
    }
}

Write-Host ""
Write-Host "PKDUR markers: $($agreed.Count) agree, $($contradicted.Count) CONTRADICTED, $($missing.Count) MISSING (of $($expected.Count))"
foreach ($m in $missing)      { Write-Host "  MISSING (printed nothing, which is not a pass): $m" }
foreach ($m in $contradicted) { Write-Host "  CONTRADICTED: $m" }

if ($missing.Count -gt 0) {
    Write-Host "PK DURABILITY: FAIL -- a marker did not print. An errored marker prints nothing rather than going red; treat this as a lost claim, not a pass."
    exit 1
}

$guardsBad = @($contradicted | Where-Object { $_ -like "PKD_G*" -or $_ -like "PKD_W*" })
if ($guardsBad.Count -gt 0) {
    Write-Host "PK DURABILITY: UNPROVEN -- a guard contradicted, so the arms say nothing about durability."
    Write-Host "  PKD_W3 means enforcement is broken on this build ENTIRELY, which is a different finding from a lost declaration."
    Write-Host "  PKD_G5 means the undeclared SID generator did not fire, so PKD_T3 is measuring the wrong thing."
    exit 1
}

if ($contradicted.Count -gt 0) {
    Write-Host "PK DURABILITY: FAIL -- an arm printed the opposite of what this spec expects. Read the CONTRADICTED line rather than assuming which half broke."
    Write-Host "  T1/T2: the declaration did NOT survive the restart -- a fresh process reopened the table, did not redeclare, and a REPLACE overwrote the primary key."
    Write-Host "  T3: a fresh process ENFORCES a key it will not MINT, so the appended row takes a blank primary key nobody can fill."
    Write-Host "  T4: a minted primary key was overwritten by hand -- the refusal is the policy, so a green T4 is lost enforcement."
    Write-Host "  That is the defect AIF-156's header ruling exists to remove. See AI_PRIMARY_KEY_POLICY_CHARTER_V1.md."
    exit 1
}

Write-Host "PK DURABILITY: PASS -- the designation was written by one process and both HONOURED and ACTED ON by another."
Write-Host "  Refused on a write it must refuse, and MINTED on an APPEND that declared nothing."
Write-Host "  This is the only measurement in the tree that can say so; PKPOLICY structurally cannot."
exit 0
