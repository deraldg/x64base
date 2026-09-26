# OI-031: prove the BRACKETED REGRESSION PATH reports a NULLASSERT failure.
#
# THE GAP IS NARROW AND IS NOT "the spec cannot fail". It can: its first run was
# 17/21 with exactly NL_T11/T12/T14/T16 red and all five guards green, the
# prediction element for element. That run was taken by DOTSCRIPT. The BRACKETED
# path -- the L3 catalog-isolation arm before and after, the CatalogBracket, the
# marker-count grader and the NULLASSERT rollup -- HAS ONLY EVER SEEN IT GREEN.
# Containing a spec that can fail and REPORTING that failure are different
# claims, and DEF_FAMILY is the proof they are different: it printed a full
# 22-line transcript and returned NO VERDICT AT ALL, neither PASS nor FAIL nor a
# count, while looking perfectly healthy.
#
# AND 2026-09-19's DEF_FAMILY RED DOES NOT CLOSE THIS. DEF_FAMILY is graded by
# DefFamilyV1, a transcript-block validator. NULLASSERT is graded by
# RemainingDefaultV1, the MARKER counter. Different graders. That run proved the
# validator rollup surfaces a FAIL; this one asks the marker rollup.
#
# THE BACK-OUT IS SIX LINES, NOT A FILE RESTORE, AND THAT MATTERS. 22c748381
# touched four files but only src/xbase/dbarea.cpp is the engine half, and that
# file has moved since: 377 lines at the parent, 425 at the fix, 475 at HEAD.
# Restoring the parent's whole file would back out the fix PLUS ~50 lines of
# unrelated later work, and a red could then be caused by either. So HEAD's file
# is used with exactly one lambda reverted -- diffed and shown to differ by those
# six lines and nothing else before this script was written.
#
# The .dts is NOT touched. Its four arms were deliberately never retuned after
# the 17/21, so the markers that went red are the markers that ship; restoring
# the spec would change what is being measured.

$ErrorActionPreference = "Stop"
# Derived, never hardcoded: this file lives at <repo>/dottalkpp/data/scripts/.
Set-Location (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path

$src  = "src\xbase\dbarea.cpp"
# IT CUTS ITS OWN COPIES, so a fresh clone can run it. The first version read
# them out of tmp\oi031\, which exists on exactly one machine -- a harness that
# only runs where it was written is a transcript, not an instrument.
$work = Join-Path $env:TEMP ("oi031_" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work -Force | Out-Null
$head = Join-Path $work "dbarea.HEAD.cpp"
$back = Join-Path $work "dbarea.backedout.cpp"
Copy-Item $src $head -Force

# THE ONE FUNCTIONAL LINE OF 22c748381. Everything else that commit added to
# this file is the COMMENT explaining it, which is why the back-out is six lines
# and not a restore of the parent's whole file: 377 lines at the parent, 425 at
# the fix, 475 at HEAD, so a file restore would drag in unrelated later work and
# a red could then have been caused by either.
$fixed  = "        field1,`n        [&] {`n            if (fieldIsNullable(field1)) setFieldNull(field1, false);`n            return set(field1, stored_value);`n        },`n        err);`n"
$prefix = "        field1, [&] { return set(field1, stored_value); }, err);`n"

$text = [System.IO.File]::ReadAllText($src) -replace "`r`n", "`n"
$hits = ([regex]::Matches($text, [regex]::Escape($fixed))).Count
if ($hits -ne 1) {
    throw "Expected the fixed lambda EXACTLY once in $src, found $hits. The shape has moved -- STOP and re-read before backing anything out."
}
[System.IO.File]::WriteAllText($back, $text.Replace($fixed, $prefix))
$exp = (& git hash-object $head)
Write-Host "cut a backed-out copy under $work -- one lambda, nothing else" -ForegroundColor DarkGray

# DEFECT 1, FOUND BY THIS SCRIPT'S OWN STAMP PRINT ON THE FIRST RUN.
#
# Copy-Item PRESERVES THE SOURCE FILE'S LastWriteTime. Both staged copies were
# written minutes before the phase-1 compile, so restoring one gave
# src\xbase\dbarea.cpp an mtime OLDER than the .obj phase 1 had just produced.
# MSBuild compared the two, decided the source was stale, and SKIPPED THE
# COMPILE -- so phase 2 relinked nothing and re-measured the BACKED-OUT binary.
# Both phases stamped 9/19/2026 1:07:33 PM, identical, and phase 2's FAIL was
# not a control at all.
#
# Swap-then-touch. The touch is the fix; the copy alone is the bug.
function Set-DbArea([string]$from) {
    Copy-Item $from $src -Force
    (Get-Item $src).LastWriteTime = Get-Date
    Write-Host ("  swapped in {0}, mtime forced to now" -f (Split-Path -Leaf $from)) -ForegroundColor DarkGray
}

function Invoke-Build([string]$label) {
    Write-Host ""
    Write-Host "=============== BUILD ($label) ===============" -ForegroundColor Cyan
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        # DEFECT 2: an UNASSIGNED pipeline joins the function's OUTPUT stream,
        # so the caller captured the build log AND the timestamp as one array
        # and the banner-trap lines printed empty. Route it to the host.
        & .\build.ps1 2>&1 | Select-Object -Last 6 | Out-Host
        Write-Host ("build exit $LASTEXITCODE")
        if ($LASTEXITCODE -ne 0) { throw "BUILD FAILED ($label)" }
    } finally { $ErrorActionPreference = $prev }
    $exe = "build\src\Release\dottalkpp.exe"
    $ts  = (Get-Item $exe).LastWriteTime
    Write-Host ("  {0} binary stamp: {1}" -f $label, $ts) -ForegroundColor Yellow
    return ,$ts
}

# THE STAMP IS NOW A HARD GATE, NOT A PRINTOUT. Phase 2 measuring phase 1's
# binary is the one failure that reads as a finding, so it is refused rather
# than reported.
function Assert-Rebuilt($before, $after) {
    if ($null -ne $before -and $before -eq $after) {
        throw ("THE BINARY DID NOT MOVE ({0}). Phase 2 would re-measure phase 1's " +
               "build and its verdict would be meaningless. Stop here." -f $after)
    }
}

function Invoke-Nullassert([string]$label) {
    Write-Host ""
    Write-Host "=============== REGRESSION RUN NULLASSERT ($label) ===============" -ForegroundColor Cyan
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        & .\datarun.ps1 -AppArgs '--script','scripts\oi031_nullassert_bracketed.dts' 2>&1 |
            Select-String -Pattern 'NL_G|NL_T|NL_P|NULLASSERT|L3 CATALOG|markers' |
            ForEach-Object { Write-Host ("  " + $_) }
    } finally { $ErrorActionPreference = $prev }
}

$stampBackedOut = $null
$stampRestored  = $null

try {
    Write-Host ""
    Write-Host "############ PHASE 1 -- fix BACKED OUT ############" -ForegroundColor Magenta
    Set-DbArea $back
    $stampBackedOut = Invoke-Build "backed out"
    Invoke-Nullassert "backed out"
    Write-Host ""
    Write-Host "  EXPECT: NL_T11, NL_T12, NL_T14, NL_T16 read .F.; five NL_G* guards .T." -ForegroundColor Yellow
    Write-Host "  THE GRADER FAILS FAST and does NOT print '17 of 21' -- measured on the" -ForegroundColor Yellow
    Write-Host "  first run, it returns at the FIRST mismatch: 'NULLASSERT: FAIL --" -ForegroundColor Yellow
    Write-Host "  marker 16 mismatch' naming NL_T11, then the rollup NULLASSERT: FAIL." -ForegroundColor Yellow
    Write-Host "  So the four reds are read off the MARKER LINES and the verdict off the" -ForegroundColor Yellow
    Write-Host "  rollup; expecting a count would have been reading for the wrong thing." -ForegroundColor Yellow
    Write-Host "  If the GUARDS red too, the fixture broke and the arms prove nothing." -ForegroundColor Yellow
    Write-Host "  If it reads 21/21, the BRACKETED PATH IS NOT REPORTING -- which is" -ForegroundColor Yellow
    Write-Host "          the finding OI-031 was written to look for." -ForegroundColor Yellow
}
finally {
    # ALWAYS restore, whatever happened above.
    Write-Host ""
    Write-Host "############ RESTORE ############" -ForegroundColor Magenta
    Set-DbArea $head
    $after = (& git hash-object $src)
    if ($after -eq $exp) { Write-Host "  restored, byte-identical ($after)" -ForegroundColor Green }
    else { Write-Host "  *** RESTORE DID NOT MATCH ($after vs $exp) -- FIX BY HAND ***" -ForegroundColor Red }
}

Write-Host ""
Write-Host "############ PHASE 2 -- fix RESTORED (the control) ############" -ForegroundColor Magenta
$stampRestored = Invoke-Build "restored"
Assert-Rebuilt $stampBackedOut $stampRestored
Invoke-Nullassert "restored"
Write-Host ""
Write-Host "  EXPECT: 21 of 21, rollup NULLASSERT: PASS." -ForegroundColor Yellow
Write-Host "  A red that does not come back green is a broken harness, not a" -ForegroundColor Yellow
Write-Host "  working grader. The control is what makes phase 1 evidence." -ForegroundColor Yellow

Write-Host ""
Write-Host "############ THE BANNER TRAP ############" -ForegroundColor Magenta
Write-Host "  Both builds print the SAME commit and the SAME dirty flag, because the"
Write-Host "  commit did not move and the tree is modified either way. Only the"
Write-Host "  TIMESTAMP tells them apart -- so check_soak_evidence.py, which proves"
Write-Host "  two runs shared one build by comparing BANNERS, would read these as one"
Write-Host "  build when they are two. Recorded by METADATA_REPORTS on 2026-09-10 and"
Write-Host "  reproduced here."
Write-Host ("  backed out : {0}" -f $stampBackedOut) -ForegroundColor Yellow
Write-Host ("  restored   : {0}" -f $stampRestored)  -ForegroundColor Yellow
Write-Host ""
Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
Write-Host "NOTHING COMMITTED." -ForegroundColor Yellow
