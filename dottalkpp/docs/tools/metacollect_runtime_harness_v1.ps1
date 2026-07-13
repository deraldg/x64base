param(
    [string]$WorkspaceRoot = "D:\code\ccode",
    [string]$DotTalkRoot = "",
    [string]$DottalkExe = "",
    [string]$MatrixCsv = ".\docs\generated\reports\metacollect_runtime_proof_matrix_seed_v1.csv",
    [string]$OutputCsv = ".\docs\generated\reports\metacollect_runtime_proof_results_v1.csv",
    [int]$TimeoutSeconds = 12,
    [switch]$Execute,
    [string]$AuthorizationToken = ""
)

$ErrorActionPreference = "Stop"
$ExpectedToken = "DOTARCH-AUTHORIZE-METACOLLECT-RUNTIME-HARNESS-V1"

if (-not $DotTalkRoot) { $DotTalkRoot = (Get-Location).Path }

if (-not $DottalkExe) {
    $candidates = @(
        (Join-Path $WorkspaceRoot "build\src\Release\dottalkpp.exe"),
        (Join-Path $WorkspaceRoot "build\src\Debug\dottalkpp.exe"),
        (Join-Path $WorkspaceRoot "build\Release\dottalkpp.exe"),
        (Join-Path $WorkspaceRoot "build\Debug\dottalkpp.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $DottalkExe = $c; break }
    }
}

Write-Host "METACOLLECT Runtime Harness v1"
Write-Host "Status: GUARDED_RUNTIME_HARNESS"
Write-Host "WorkspaceRoot: $WorkspaceRoot"
Write-Host "DotTalkRoot: $DotTalkRoot"
Write-Host "DottalkExe: $DottalkExe"
Write-Host "MatrixCsv: $MatrixCsv"
Write-Host "OutputCsv: $OutputCsv"
Write-Host "Execute requested: $Execute"
Write-Host "Exact authorization token supplied: $([bool]($AuthorizationToken -eq $ExpectedToken))"
Write-Host "Source mutation authorized: no"
Write-Host "CMake mutation authorized: no"
Write-Host "HELP DATA rebuild authorized: no"
Write-Host "CMDHELPCHK mutation authorized: no"
Write-Host "DBF writes authorized directly by this tool: no"
Write-Host "Metadata table writes authorized: no"
Write-Host "C:/dottalkpp promotion authorized: no"
Write-Host "Deletion authorized: no"
Write-Host "Header Batch 7 authorized: no"
Write-Host ""

if (-not (Test-Path $MatrixCsv)) { throw "Runtime matrix CSV not found: $MatrixCsv" }

if ($Execute -and $AuthorizationToken -ne $ExpectedToken) {
    throw "Execute requested but exact authorization token was not supplied. Required: $ExpectedToken"
}
if ($Execute -and (-not $DottalkExe)) {
    throw "DotTalk++ executable path is empty. Pass -DottalkExe explicitly."
}

if ($Execute -and (-not (Test-Path $DottalkExe))) {
    throw "DotTalk++ executable not found. Pass -DottalkExe explicitly."
}

New-Item -ItemType Directory -Force ".\docs\generated\reports" | Out-Null

$ReportMd = ".\docs\generated\reports\metacollect_runtime_harness_v1.md"
$HarnessCsv = ".\docs\generated\reports\metacollect_runtime_harness_v1.csv"

$matrixRows = @(Import-Csv $MatrixCsv)
if ($matrixRows.Count -eq 0) { throw "Runtime matrix CSV contains zero rows: $MatrixCsv" }

function Shorten {
    param([string]$Text, [int]$Max = 1200)
    if ($null -eq $Text) { return "" }
    $clean = $Text -replace "`r", " " -replace "`n", " "
    if ($clean.Length -gt $Max) { return $clean.Substring(0, $Max) + "..." }
    return $clean
}

function Invoke-DotTalkCommand {
    param([string]$ExePath, [string]$WorkingDirectory, [string]$CommandText, [int]$Timeout)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $ExePath
    $psi.WorkingDirectory = $WorkingDirectory
    $inputText = $CommandText + "`r`nQUIT`r`n"
    $tempInput = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllBytes($tempInput, [System.Text.Encoding]::ASCII.GetBytes($inputText))

    $psi.UseShellExecute = $false
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/c type `"$tempInput`" | `"$ExePath`""
    $psi.RedirectStandardInput = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi

    if (-not $p.Start()) { throw "Failed to start process: $ExePath" }

    $exited = $p.WaitForExit($Timeout * 1000)
    $timedOut = -not $exited
    if ($timedOut) {
        try { $p.Kill() } catch {}
    }

    $stdout = ""
    $stderr = ""
    try { $stdout = $p.StandardOutput.ReadToEnd() } catch {}
    try { $stderr = $p.StandardError.ReadToEnd() } catch {}

    $exitCode = ""
    if (-not $timedOut) {
        try { $exitCode = [string]$p.ExitCode } catch {}
    }

    if ($tempInput -and (Test-Path $tempInput)) {
        try { Remove-Item $tempInput -Force } catch {}
    }

    return [pscustomobject]@{
        TimedOut = $timedOut
        ExitCode = $exitCode
        Stdout = $stdout
        Stderr = $stderr
    }
}

$results = @()
$harnessRows = @()

foreach ($row in $matrixRows) {
    $seq = [string]$row.Seq
    $category = [string]$row.Category
    $token = [string]$row.Token
    $expectedLayer = [string]$row.ExpectedLayer
    $purpose = [string]$row.Purpose
    $proofCommand = [string]$row.ProofCommand
    $expectedEvidence = [string]$row.ExpectedEvidence
    $risk = [string]$row.Risk
    $notes = [string]$row.Notes

    $executable = $true
    $skipReason = ""

    if (-not $proofCommand -or $proofCommand -eq "(none)") {
        $executable = $false
        $skipReason = "no proof command"
    }
    if ($category -eq "extractor-canary") {
        $executable = $false
        $skipReason = "extractor canary is source-review only"
    }

    $plannedStatus = "DRY_RUN_PLANNED"
    if (-not $executable) { $plannedStatus = "SKIP_NON_EXECUTABLE_ROW" }
    elseif ($Execute) { $plannedStatus = "EXECUTE_REQUESTED" }

    $harnessRows += [pscustomobject]@{
        Seq = $seq
        Category = $category
        Token = $token
        ProofCommand = $proofCommand
        Executable = [string]$executable
        DryRunStatus = $plannedStatus
        SkipReason = $skipReason
        Risk = $risk
        Notes = $notes
    }

    $runtimeStatus = $plannedStatus
    $exitCode = ""
    $timedOut = ""
    $stdoutExcerpt = ""
    $stderrExcerpt = ""
    $errorText = $skipReason
    $runtimeAuthorized = "False"

    if ($Execute -and $executable) {
        $runtimeAuthorized = "True"
        $errorText = ""
        try {
            $run = Invoke-DotTalkCommand -ExePath $DottalkExe -WorkingDirectory $WorkspaceRoot -CommandText $proofCommand -Timeout $TimeoutSeconds
            $exitCode = $run.ExitCode
            $timedOut = [string]$run.TimedOut
            $stdoutExcerpt = Shorten $run.Stdout
            $stderrExcerpt = Shorten $run.Stderr

            if ($run.TimedOut) {
                $runtimeStatus = "TIMEOUT_REVIEW"
            } elseif ($run.ExitCode -and $run.ExitCode -ne "0") {
                $runtimeStatus = "RUNTIME_CRASH_REVIEW"
            } elseif ($run.Stdout -or $run.Stderr) {
                $runtimeStatus = "RUNTIME_OUTPUT_CAPTURED"
            } else {
                $runtimeStatus = "NO_OUTPUT_REVIEW"
            }
        } catch {
            $runtimeStatus = "HARNESS_ERROR"
            $errorText = $_.Exception.Message
        }
    }

    $results += [pscustomobject]@{
        Seq = $seq
        Category = $category
        Token = $token
        ExpectedLayer = $expectedLayer
        Purpose = $purpose
        ProofCommand = $proofCommand
        ExpectedEvidence = $expectedEvidence
        Risk = $risk
        RuntimeStatus = $runtimeStatus
        ExitCode = $exitCode
        TimedOut = $timedOut
        StdoutExcerpt = $stdoutExcerpt
        StderrExcerpt = $stderrExcerpt
        ErrorText = $errorText
        DottalkExe = $DottalkExe
        WorkspaceRoot = $WorkspaceRoot
        Notes = $notes
        RuntimeExecutionAuthorized = $runtimeAuthorized
        SourceMutationAuthorized = "False"
        HelpDataRebuildAuthorized = "False"
        CmdhelpchkMutationAuthorized = "False"
        DbfWritesAuthorizedDirectlyByHarness = "False"
        MetadataTableWritesAuthorized = "False"
        PromotionAuthorized = "False"
        DeletionAuthorized = "False"
        HeaderBatch7Authorized = "False"
    }
}

$harnessRows | Export-Csv -NoTypeInformation -Encoding UTF8 $HarnessCsv
$results | Export-Csv -NoTypeInformation -Encoding UTF8 $OutputCsv

$executableCount = @($harnessRows | Where-Object { $_.Executable -eq "True" }).Count
$skipCount = @($harnessRows | Where-Object { $_.Executable -ne "True" }).Count
$executedCount = @($results | Where-Object { $_.RuntimeExecutionAuthorized -eq "True" }).Count
$statusGroups = @($results | Group-Object RuntimeStatus | Sort-Object Name)

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# METACOLLECT Runtime Harness v1")
$md.Add("")
if ($Execute) { $md.Add("Status: GUARDED_RUNTIME_HARNESS / EXECUTION_ATTEMPTED") }
else { $md.Add("Status: DRY_RUN / RUNTIME_NOT_EXECUTED") }
$md.Add("")
$md.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$md.Add("")
$md.Add("## Safety Header")
$md.Add("")
$md.Add("Runtime execution requested: $Execute")
$md.Add("Authorization token accepted: $($AuthorizationToken -eq $ExpectedToken)")
$md.Add("Source mutation authorized: no")
$md.Add("CMake mutation authorized: no")
$md.Add("HELP DATA rebuild authorized: no")
$md.Add("CMDHELPCHK mutation authorized: no")
$md.Add("DBF writes authorized directly by this tool: no")
$md.Add("Metadata table writes authorized: no")
$md.Add("C:/dottalkpp promotion authorized: no")
$md.Add("Deletion authorized: no")
$md.Add("Header Batch 7 authorized: no")
$md.Add("")
$md.Add("## Inputs")
$md.Add("")
$md.Add("- Matrix CSV: $MatrixCsv")
$md.Add("- DotTalk++ executable: $DottalkExe")
$md.Add("- WorkspaceRoot: $WorkspaceRoot")
$md.Add("- TimeoutSeconds: $TimeoutSeconds")
$md.Add("")
$md.Add("## Rollup")
$md.Add("")
$md.Add("| Metric | Count |")
$md.Add("|---|---:|")
$md.Add("| matrix rows | $($matrixRows.Count) |")
$md.Add("| executable rows | $executableCount |")
$md.Add("| skipped/non-executable rows | $skipCount |")
$md.Add("| executed rows | $executedCount |")
$md.Add("")
$md.Add("## Runtime Status Summary")
$md.Add("")
$md.Add("| Runtime Status | Count |")
$md.Add("|---|---:|")
foreach ($g in $statusGroups) { $md.Add("| $($g.Name) | $($g.Count) |") }
$md.Add("")
$md.Add("## Matrix Rows")
$md.Add("")
$md.Add("| Seq | Category | Token | Command | Status | Risk |")
$md.Add("|---:|---|---|---|---|---|")
foreach ($r in $results) {
    $cmd = ([string]$r.ProofCommand).Replace("|", "/")
    $md.Add("| $($r.Seq) | $($r.Category) | $($r.Token) | $cmd | $($r.RuntimeStatus) | $($r.Risk) |")
}
$md.Add("")
$md.Add("## Interpretation")
$md.Add("")
if ($Execute) {
    $md.Add("Runtime execution was attempted under the exact authorization token. These rows are runtime evidence captures, not final HELP or metadata-table judgments.")
} else {
    $md.Add("This was a dry run. No runtime commands were executed. The output validates harness inputs, executable row selection, skip reasons, and future proof row shape.")
}
$md.Add("")
$md.Add("## Outputs")
$md.Add("")
$md.Add("- docs/generated/reports/metacollect_runtime_harness_v1.md")
$md.Add("- docs/generated/reports/metacollect_runtime_harness_v1.csv")
$md.Add("- docs/generated/reports/metacollect_runtime_proof_results_v1.csv")
$md.Add("")
$md.Add("## Safety Confirmation")
$md.Add("")
if ($Execute) { $md.Add("- Runtime execution occurred only because -Execute and the exact authorization token were supplied.") }
else { $md.Add("- No runtime execution occurred because -Execute was not supplied.") }
$md.Add("- No source files were edited.")
$md.Add("- No CMake files were edited.")
$md.Add("- HELP DATA was not rebuilt.")
$md.Add("- CMDHELPCHK was not modified.")
$md.Add("- No DBFs were written directly by this harness.")
$md.Add("- No metadata tables were written.")
$md.Add("- Nothing was promoted to C:/dottalkpp.")
$md.Add("- No deletion occurred.")
$md.Add("- Header Batch 7 was not authorized.")
$md | Out-File $ReportMd -Encoding UTF8

Write-Host "METACOLLECT runtime harness report wrote $ReportMd"
Write-Host "METACOLLECT runtime harness matrix report wrote $HarnessCsv"
Write-Host "METACOLLECT runtime proof results wrote $OutputCsv"
Write-Host "Matrix rows: $($matrixRows.Count)"
Write-Host "Executable rows: $executableCount"
Write-Host "Skipped rows: $skipCount"
Write-Host "Executed rows: $executedCount"
if ($Execute) { Write-Host "Runtime execution occurred under exact authorization token." }
else { Write-Host "Dry run only; no runtime execution occurred." }
Write-Host "No source files were edited."
Write-Host "No CMake files were edited."
Write-Host "HELP DATA was not rebuilt."
Write-Host "CMDHELPCHK was not modified."
Write-Host "No DBFs were written directly by this harness."
Write-Host "No metadata tables were written."
Write-Host "Nothing was promoted to C:/dottalkpp."
Write-Host "No deletion occurred."
Write-Host "Header Batch 7 was not authorized."
