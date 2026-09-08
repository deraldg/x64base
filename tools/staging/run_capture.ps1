# tools/staging/run_capture.ps1
#
# RUN A DOTTALK++ COMMAND OR SCRIPT AND PUT THE WHOLE TRANSCRIPT IN A FILE.
#
# WHY THIS EXISTS. A big run -- REGRESSION ALL above all -- produces thousands of
# lines that otherwise have to be copied out of a console by hand. The three
# obvious alternatives were each measured and each fails:
#
#   SET ALTERNATE      -- AlternateCapture REFUSES to take the routed channel
#                         when an operator capture already holds it, and says so
#                         (cmd_regression.cpp). A spec that needs the channel
#                         reports UNMEASURED instead of running. So an operator
#                         capture cannot wrap a REGRESSION run.
#   Start-Transcript   -- measured 2026-09-04: captured its own headers and
#                         NOTHING from the engine.
#   the .alt files     -- only specs carrying capture_routed_channel write one,
#                         and REGRESSION ALL produces no single file of its own.
#
# WHAT WORKS is stdout redirection off a DIRECT exe launch, which is already the
# established pattern: pk_durability_child.ps1 invokes the exe with --script and
# pipes its output. This wraps that.
#
# IT DOES NOT GO THROUGH datarun.ps1, on purpose and for the same reason the
# child launcher does not: datarun calls Update-DotTalkRuntimeExe, which may COPY
# the runtime, and copying over a running binary fails on Windows. This copies
# nothing and builds nothing -- run .\build.ps1 yourself first if you need to.
#
# IT RUNS dottalkpp\bin\dottalkpp.exe WITH THE WORKING DIRECTORY AT dottalkpp\,
# AND BOTH HALVES OF THAT ARE LOAD-BEARING. MEASURED 2026-09-08, the first cut of
# this script got both wrong and produced a session unlike the one anybody uses:
#
#   THE ENGINE DERIVES ITS DATA ROOT FROM THE CURRENT DIRECTORY. Starting in
#   dottalkpp\data gave DATA = dottalkpp\data\data, so every path slot pointed at
#   a directory that does not exist, the L3 arm and the spec were both 'not on
#   disk', and PKPOLICY reported all fifteen markers missing. NOTHING RAN.
#   (The harness was right throughout: it printed NOT RUN and UNMEASURED rather
#   than a pass or a failure. A missing instrument did not read like a green one.)
#
#   THE .ini FILES LIVE BESIDE THE bin COPY OF THE EXE and are looked up in the
#   EXE'S OWN DIRECTORY. Launching build\src\Release\dottalkpp.exe therefore ran
#   with NO dottalkpp.ini and NO init.ini -- a different session again.
#
# So the default exe is the bin copy, which is what datarun runs. That copy can
# be STALE relative to a fresh build, and staleness that is not announced is how
# a run gets credited to code it never executed, so this REPORTS both timestamps
# every time and REFUSES TO RUN on a mismatch -- it does not warn and proceed,
# for the reasons recorded at the staleness block below. -UseBuildExe overrides
# and accepts the missing .ini that comes with it; -AllowStale overrides and
# measures the older bin copy on purpose.
#
# USAGE
#   .\tools\staging\run_capture.ps1 -Command "REGRESSION ALL" -Out tmp\regall.txt
#   .\tools\staging\run_capture.ps1 -Script dottalkpp\data\scripts\pk_policy_regression.dts -Out tmp\pkp.txt
#   .\tools\staging\run_capture.ps1 -Command "REGRESSION PKDURABLE" -Out tmp\pkd.txt -AllowHostCommands
#   .\tools\staging\run_capture.ps1 -Command "REGRESSION ALL" -Out tmp\old.txt -AllowStale
#
# THE ORDER THAT BITES: build, THEN .\datarun.ps1, THEN capture. Running datarun
# before the build refreshes the bin copy from the PREVIOUS build and the capture
# then measures the wrong binary. That happened on 2026-09-08 and is why the
# staleness check now refuses.
#
# -Command may be given more than once and the lines run in order:
#   -Command "REGRESSION ALL","REGRESSION PKPOLICY"
# which is the ONE arrangement that reproduces the AIF-158 contamination, because
# both run in a SINGLE PROCESS. Two separate invocations of this script are two
# processes and will not reproduce it.
#
# QUIT is appended automatically. Do not put it in -Command.

[CmdletBinding(DefaultParameterSetName = "ByCommand")]
param(
    [Parameter(ParameterSetName = "ByCommand", Mandatory = $true)]
    [string[]] $Command,

    [Parameter(ParameterSetName = "ByScript", Mandatory = $true)]
    [string] $Script,

    [Parameter(Mandatory = $true)]
    [string] $Out,

    # The data-lane acknowledgement. Anything that creates or erases a table
    # under dottalkpp\data needs it.
    [switch] $AllowData,

    # PKDURABLE shells out to launch child processes and is REFUSED without this.
    # The refusal returns normally, so the spec reports an unrun measurement
    # rather than failing -- which is correct and is not what you wanted.
    [switch] $AllowHostCommands,

    # Run build\src\Release\dottalkpp.exe instead of the bin copy. It will start
    # WITHOUT the .ini files, which live in dottalkpp\bin. Use it only when you
    # mean to test a build you have deliberately not promoted.
    [switch] $UseBuildExe,

    # Capture against a bin copy that is OLDER than the build output. Without
    # this the run is REFUSED -- see the staleness block below for why warning
    # was not enough.
    [switch] $AllowStale
)

$ErrorActionPreference = "Stop"

$repo     = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$binExe   = Join-Path $repo "dottalkpp\bin\dottalkpp.exe"
$buildExe = Join-Path $repo "build\src\Release\dottalkpp.exe"

# The working directory is dottalkpp\, NOT dottalkpp\data -- see the header.
$cwd = Join-Path $repo "dottalkpp"

if ($UseBuildExe) { $exe = $buildExe } else { $exe = $binExe }

if (-not (Test-Path -LiteralPath $exe)) {
    Write-Host "RUN-CAPTURE: runtime not found at $exe -- build it first (.\build.ps1)."
    if (-not $UseBuildExe) {
        Write-Host "  The bin copy is what datarun.ps1 runs; .\datarun.ps1 refreshes it."
    }
    exit 2
}

# ANNOUNCE STALENESS RATHER THAN INHERIT IT. A capture credited to code that was
# never in the binary is the failure this whole lane keeps finding.
if ((-not $UseBuildExe) -and (Test-Path -LiteralPath $buildExe)) {
    $tBin   = (Get-Item -LiteralPath $binExe).LastWriteTimeUtc
    $tBuild = (Get-Item -LiteralPath $buildExe).LastWriteTimeUtc
    if ($tBuild -gt $tBin) {
        # THIS REFUSES. IT USED TO WARN AND RUN ANYWAY, AND THAT COST TWO
        # CAPTURES IN ONE DAY (2026-09-08), BOTH OF WHICH PRODUCED
        # CONFIDENT-LOOKING OUTPUT:
        #
        #   1. VARCHARRESET was captured against a stale bin copy and printed
        #      "REGRESSION: unknown option or regression 'VARCHARRESET'". That
        #      reads EXACTLY like a registration that did not take. The only
        #      reason it was not chased as a bug is that someone read the
        #      warning scrolled above 526 lines of output.
        #   2. A promotion was captured after .\datarun.ps1 was run BEFORE the
        #      build rather than after, so 9328 lines showed the promoted spec
        #      absent from the listing and absent from the suite.
        #
        # A WARNING PRINTS ABOVE THE OUTPUT AND THE OUTPUT IS WHAT GETS READ.
        # The file it leaves behind is indistinguishable from a real measurement
        # and outlives the console that warned about it -- which is the same
        # shape as the pre-clear defect fixed further down this file, and as the
        # PKDURABLE stale-.alt failure of 2026-09-07. Three instances, one
        # lesson: EVIDENCE THAT CAN BE READ LATER MUST NOT BE PRODUCED BY A RUN
        # THE OPERATOR WAS ONLY WARNED ABOUT.
        #
        # -AllowStale exists because capturing against the shipped bin copy on
        # purpose is legitimate; it just has to be said out loud.
        $msg = @(
            "RUN-CAPTURE: REFUSED -- the bin copy is OLDER than the build output.",
            ("  bin   : " + $tBin.ToString("yyyy-MM-dd HH:mm:ss") + "Z  " + $binExe),
            ("  build : " + $tBuild.ToString("yyyy-MM-dd HH:mm:ss") + "Z  " + $buildExe),
            "  This capture would NOT exercise your newest build, and the file it",
            "  wrote would look exactly like one that did.",
            "  Run .\datarun.ps1 once to refresh the bin copy (then re-run this),",
            "  or pass -UseBuildExe to run the build output directly,",
            "  or pass -AllowStale if you MEAN to measure the older bin copy."
        ) -join [Environment]::NewLine

        if (-not $AllowStale) {
            # No output file is created: the refusal happens before the
            # pre-clear, so a previous run's file is left untouched rather than
            # replaced by nothing. PROVEN 2026-09-08 with a sentinel file, which
            # survived the refusal intact.
            #
            # THE DETAIL IS PRINTED, AND ONLY A ONE-LINER IS THROWN. `throw` on a
            # multi-line string collapses every newline into PowerShell's
            # exception block and renders as an unreadable wall -- measured on
            # the first version of this guard, which was WORSE TO READ than the
            # warning it replaced. The whole point of refusing rather than
            # warning is that the operator reads the reason.
            Write-Host ""
            Write-Host $msg
            Write-Host ""
            throw "RUN-CAPTURE: REFUSED -- stale bin copy; see the lines above."
        }

        Write-Host $msg.Replace("REFUSED", "ALLOWED STALE")
        Write-Host "  -AllowStale was passed; proceeding against the older bin copy."
    }
}

# Resolve the output path against the repo root when it is relative, so
# -Out tmp\x.txt means the same thing from any working directory.
if ([System.IO.Path]::IsPathRooted($Out)) { $outPath = $Out }
else { $outPath = Join-Path $repo $Out }
$outDir = Split-Path -Parent $outPath
if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# PRE-CLEAR, AND IT SITS HERE ON PURPOSE -- BEFORE ANYTHING THAT CAN FAIL.
#
# A capture file that survives a run which never produced one gets read as that
# run's evidence. This is not hypothetical and it is not new: PKDURABLE was
# OBSERVED reporting PASS on a run that never launched, because the validator
# graded the previous run's .alt files (2026-09-07), and the fix there was WHERE
# the guard sits rather than what it checks. It happened again to this very
# script on 2026-09-08 -- the first cut ran nothing useful, the operator re-ran
# after a fix, and the OLD file was still on disk and was read as the new run.
# It was caught only because the stale file's own INIT block named a binary and
# a data root the fixed script cannot produce.
#
# So: delete first, confirm by asking the filesystem, and refuse to start if the
# file cannot be removed. A run that dies after this point leaves NO file, and a
# missing file is reported as an unrun measurement rather than mistaken for one.
if (Test-Path -LiteralPath $outPath) {
    Remove-Item -LiteralPath $outPath -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $outPath) {
        Write-Host "RUN-CAPTURE: cannot remove the previous capture at $outPath"
        Write-Host "  Refusing to run: a surviving file would be read as this run's evidence."
        exit 2
    }
}

# A SCRATCH SCRIPT, NOT A TRACKED ONE. -Command synthesizes a throwaway .dts
# under tmp\ because --script takes a file and nothing else does.
$temp = $null
if ($PSCmdlet.ParameterSetName -eq "ByCommand") {
    $tmpDir = Join-Path $repo "tmp"
    if (-not (Test-Path -LiteralPath $tmpDir)) {
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    }
    $temp = Join-Path $tmpDir ("run_capture_" + [System.Guid]::NewGuid().ToString("N") + ".dts")
    $lines = @($Command) + @("QUIT")
    Set-Content -LiteralPath $temp -Value $lines -Encoding ASCII
    $scriptPath = $temp
}
else {
    if ([System.IO.Path]::IsPathRooted($Script)) { $scriptPath = $Script }
    else { $scriptPath = Join-Path $repo $Script }
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        Write-Host "RUN-CAPTURE: script not found at $scriptPath"
        exit 2
    }
}

# ENVIRONMENT IS SET FOR THIS PROCESS AND RESTORED, so a capture run cannot
# leave the operator's shell holding a permission it did not ask for.
$savedData = $env:X64BASE_ALLOW_DATA
$savedHost = $env:DOTTALK_ALLOW_HOST_COMMANDS

try {
    if ($AllowData)          { $env:X64BASE_ALLOW_DATA = "1" }
    if ($AllowHostCommands)  { $env:DOTTALK_ALLOW_HOST_COMMANDS = "1" }

    Push-Location $cwd
    try {
        # *> takes stdout AND stderr. The engine's own writes land here because
        # the console buffer IS stdout; what a redirect cannot reach is a child
        # process launched by `!`, whose output goes to its own handle -- that is
        # why PKDURABLE grades .alt files rather than a transcript.
        & $exe --script $scriptPath *> $outPath
        $code = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:X64BASE_ALLOW_DATA = $savedData
    $env:DOTTALK_ALLOW_HOST_COMMANDS = $savedHost
    if ($temp -and (Test-Path -LiteralPath $temp)) {
        Remove-Item -LiteralPath $temp -Force
    }
}

if (Test-Path -LiteralPath $outPath) {
    $n = (Get-Content -LiteralPath $outPath | Measure-Object -Line).Lines
    Write-Host "RUN-CAPTURE: $n line(s) -> $outPath  (exit $code)"
} else {
    Write-Host "RUN-CAPTURE: NO OUTPUT FILE was produced. Treat this as an unrun measurement."
    exit 2
}
exit 0
