param(
    [string]$RepoRoot = "",
    [string]$DotTalkExe = "",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$LabDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LabTalkRoot = Resolve-Path (Join-Path $LabDir "..\..")
if (-not $RepoRoot) {
    $RepoRoot = Resolve-Path (Join-Path $LabTalkRoot "..")
}
if (-not $DotTalkExe) {
    $DotTalkExe = Join-Path $RepoRoot "dottalkpp\bin\dottalkpp.exe"
}

$RuntimeScript = Join-Path $LabDir "cmdhelp_cmdhelpchk_selfdoc_v0.dts"
$CrosswalkPath = Join-Path $LabTalkRoot "reports\selfdoc\lab_selfdoc_first_crosswalk_v0.md"
$CommandSet = @("CMDHELP", "CMDHELPCHK")
$SourceMap = @{
    "CMDHELP" = "src\cli\cmdhelp.cpp"
    "CMDHELPCHK" = "src\cli\command_helpchk.cpp"
}

Write-Output "LabTalk SelfDoc first lab"
Write-Output "repo_root=$RepoRoot"
Write-Output "labtalk_root=$LabTalkRoot"
Write-Output "runtime_script=$RuntimeScript"
Write-Output "command_set=$($CommandSet -join ', ')"
Write-Output "boundary=report-only; no HELP DATA, DBF metadata, CMDHELPCHK, source, or manual publication mutation"
Write-Output ""

if (-not (Test-Path -LiteralPath $DotTalkExe)) {
    throw "DotTalk++ runtime not found: $DotTalkExe"
}
if (-not (Test-Path -LiteralPath $RuntimeScript)) {
    throw "Runtime script not found: $RuntimeScript"
}

Write-Output "== Runtime HELP/CMDHELPCHK =="
$runtimeOutput = & $DotTalkExe --script $RuntimeScript 2>&1
$runtimeCode = $LASTEXITCODE
$runtimeOutput | ForEach-Object { Write-Output $_ }
Write-Output "runtime_return_code=$runtimeCode"
if ($runtimeCode -ne 0) {
    throw "DotTalk runtime returned $runtimeCode"
}

Write-Output ""
Write-Output "== Contracts Scanner Summary =="
Push-Location -LiteralPath $RepoRoot
try {
    $contractSummary = & $PythonExe "tools\contracts\contract_scan.py" --root $RepoRoot --summary 2>&1
    $contractCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
$contractSummary | ForEach-Object { Write-Output $_ }
Write-Output "contracts_scan_return_code=$contractCode"
if ($contractCode -ne 0) {
    throw "contracts scanner returned $contractCode"
}

Write-Output ""
Write-Output "== Source Usage Contract Crosswalk =="
$rows = @()
foreach ($command in $CommandSet) {
    $rel = $SourceMap[$command]
    $path = Join-Path $RepoRoot $rel
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Expected source file not found: $path"
    }

    $matches = Select-String -LiteralPath $path -Pattern "owner:|command:|usage-access:|@dottalk.usage v1" -CaseSensitive:$false
    $summary = ($matches | ForEach-Object { "L$($_.LineNumber): $($_.Line.Trim())" }) -join "; "
    $rows += [pscustomobject]@{
        Command = $command
        Source = $rel -replace "\\", "/"
        Evidence = $summary
    }
    Write-Output "$command -> $rel"
    Write-Output "  $summary"
}

$RuntimeScriptDisplay = $RuntimeScript -replace "\\", "/"
$report = New-Object System.Collections.Generic.List[string]
$report.Add("# LabTalk SelfDoc First Crosswalk v0")
$report.Add("")
$report.Add("Generated: $(Get-Date -Format s)")
$report.Add("")
$report.Add("Boundary: report-only; no HELP DATA, DBF metadata, CMDHELPCHK, source, or manual publication mutation.")
$report.Add("")
$report.Add("## Runtime Script")
$report.Add("")
$report.Add("- $RuntimeScriptDisplay")
$report.Add("")
$report.Add("## Command Set")
$report.Add("")
foreach ($command in $CommandSet) {
    $report.Add("- $command")
}
$report.Add("")
$report.Add("## Source Usage Contract Crosswalk")
$report.Add("")
$report.Add("| Command | Source | Evidence |")
$report.Add("| --- | --- | --- |")
foreach ($row in $rows) {
    $safeEvidence = $row.Evidence -replace "\|", "/"
    $report.Add("| $($row.Command) | $($row.Source) | $safeEvidence |")
}
$report.Add("")
$report.Add("## Contracts Scanner Summary")
$report.Add("")
$report.Add('```text')
foreach ($line in $contractSummary) {
    $report.Add([string]$line)
}
$report.Add('```')

$crosswalkDir = Split-Path -Parent $CrosswalkPath
New-Item -ItemType Directory -Force -Path $crosswalkDir | Out-Null
$report | Set-Content -LiteralPath $CrosswalkPath -Encoding UTF8

Write-Output ""
Write-Output "crosswalk_report=$CrosswalkPath"
Write-Output "lab_result=PASS"
