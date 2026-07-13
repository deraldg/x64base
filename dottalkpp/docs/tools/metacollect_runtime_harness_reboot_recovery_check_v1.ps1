$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$CCodeRoot = Split-Path -Parent $ProjectRoot
$OutCsv = ".\docs\generated\reports\metacollect_runtime_harness_reboot_recovery_check_v1.csv"
$OutMd  = ".\docs\generated\reports\metacollect_runtime_harness_reboot_recovery_check_v1.md"

New-Item -ItemType Directory -Force ".\docs\generated\reports" | Out-Null
$rows = New-Object System.Collections.Generic.List[object]

function Add-Row($Category, $Check, $Status, $Path, $Evidence) {
    $rows.Add([pscustomobject]@{
        Category = $Category
        Check = $Check
        Status = $Status
        Path = $Path
        Evidence = $Evidence
    }) | Out-Null
}

function Test-FileRow($Category, $Check, $Path) {
    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path
        Add-Row $Category $Check "PASS" $Path ("Exists; length={0}; lastWrite={1}" -f $item.Length, $item.LastWriteTime)
    } else {
        Add-Row $Category $Check "WARN" $Path "Missing"
    }
}

Test-FileRow "build-output" "dottalkpp executable exists" (Join-Path $CCodeRoot "build\src\Release\dottalkpp.exe")
Test-FileRow "build-output" "lmdb backend smoke executable exists" (Join-Path $CCodeRoot "build\src\tests\Release\dottalkpp_lmdb_backend_smoke.exe")

$metaBins = @(Get-ChildItem -LiteralPath $CCodeRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "\\build\\" -and $_.Name -match "metacollect|dt-meta|dt_meta" })
if ($metaBins.Count -gt 0) {
    foreach ($b in $metaBins) { Add-Row "build-output" "metacollect/dt-meta binary candidate" "PASS" $b.FullName ("Exists; length={0}; lastWrite={1}" -f $b.Length, $b.LastWriteTime) }
} else {
    Add-Row "build-output" "metacollect/dt-meta binary candidate" "WARN" (Join-Path $CCodeRoot "build") "No metacollect/dt-meta named binary found under build; may be library-only or differently named."
}

foreach ($pn in @("dottalkpp","metacollect","dt-meta","dt_meta")) {
    $procs = @(Get-Process -Name $pn -ErrorAction SilentlyContinue)
    if ($procs.Count -eq 0) {
        Add-Row "process-state" "process not running: $pn" "PASS" $pn "No running process found"
    } else {
        Add-Row "process-state" "process running: $pn" "WARN" $pn (($procs | ForEach-Object { "pid=$($_.Id)" }) -join "; ")
    }
}

$metaReports = @(Get-ChildItem -LiteralPath ".\docs\generated" -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "metacollect|metacheck|source_registry|alias" })
if ($metaReports.Count -gt 0) {
    Add-Row "artifact-presence" "metacollect/metacheck generated artifacts found" "PASS" ".\docs\generated" ("Count={0}" -f $metaReports.Count)
} else {
    Add-Row "artifact-presence" "metacollect/metacheck generated artifacts found" "WARN" ".\docs\generated" "No matching generated artifacts found"
}

$stale = @(Get-ChildItem -LiteralPath $ProjectRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "metacollect|harness|runtime" -and $_.Extension -match "\.lock|\.tmp|\.pid|\.lck" })
if ($stale.Count -eq 0) {
    Add-Row "stale-runtime-artifacts" "obvious metacollect runtime lock/temp artifacts" "PASS" $ProjectRoot "No matching .lock/.tmp/.pid/.lck artifacts found"
} else {
    foreach ($s in $stale) { Add-Row "stale-runtime-artifacts" "possible stale runtime artifact" "WARN" $s.FullName ("Exists; length={0}; lastWrite={1}" -f $s.Length, $s.LastWriteTime) }
}

$Ledger = ".\docs\authority\artifact_intake_ledger.jsonl"
if (Test-Path -LiteralPath $Ledger) {
    $ledgerText = Get-Content -LiteralPath $Ledger -Raw
    if ($ledgerText -match "METACOLLECT-RUNTIME-HARNESS-V1-BLOCKED-REBOOT-RESET") {
        Add-Row "ledger-state" "blocked reboot reset record present" "PASS" $Ledger "Found blocked reboot reset intake record"
    } else {
        Add-Row "ledger-state" "blocked reboot reset record present" "WARN" $Ledger "No blocked reboot reset record found"
    }
    if ($ledgerText -match "DOTARCH-AUTHORIZE-METACOLLECT-RUNTIME-HARNESS-V1-EXECUTE") {
        Add-Row "authority-boundary" "runtime harness execution token not recorded" "FAIL" $Ledger "Execution authorization token pattern found"
    } else {
        Add-Row "authority-boundary" "runtime harness execution token not recorded" "PASS" $Ledger "No execution authorization token pattern found"
    }
} else {
    Add-Row "ledger-state" "artifact intake ledger exists" "WARN" $Ledger "Missing ledger"
}

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$fail = @($rows | Where-Object { $_.Status -eq "FAIL" }).Count
$warn = @($rows | Where-Object { $_.Status -eq "WARN" }).Count
$pass = @($rows | Where-Object { $_.Status -eq "PASS" }).Count
$overall = if ($fail -gt 0) { "BLOCKED" } elseif ($warn -gt 0) { "READY_WITH_WARNINGS" } else { "READY" }

$md = @()
$md += "# Metacollect Runtime Harness Reboot Recovery Check v1"
$md += ""
$md += "Status: REPORT_ONLY / OBSERVE"
$md += ""
$md += "runtime_harness_recovery_status: $overall"
$md += ""
$md += "pass_rows: $pass"
$md += "warn_rows: $warn"
$md += "fail_rows: $fail"
$md += ""
$md += "Runtime execution authorized: no"
$md += ""
$md += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += ""
$md += "## Verdict"
$md += ""
if ($overall -eq "READY") { $md += "The environment appears clean for a separate guarded runtime-harness execution proposal." }
elseif ($overall -eq "READY_WITH_WARNINGS") { $md += "The environment has warnings. Review them before any runtime-harness execution proposal." }
else { $md += "The environment is blocked. Do not execute the runtime harness." }
$md += ""
$md += "## Rows"
$md += ""
$md += "| Status | Category | Check | Path | Evidence |"
$md += "|---|---|---|---|---|"
foreach ($r in $rows) {
    $p = ([string]$r.Path) -replace '\|','/'
    $e = ([string]$r.Evidence) -replace '\|','/'
    $c = ([string]$r.Check) -replace '\|','/'
    $md += "| $($r.Status) | $($r.Category) | $c | $p | $e |"
}
$md += ""
$md += "## Safety"
$md += ""
$md += "- This report does not execute the runtime harness."
$md += "- It does not edit source files."
$md += "- It does not write DBFs."
$md += "- It does not rebuild HELP DATA."
$md += "- It does not mutate CMDHELPCHK."
$md += "- It does not promote anything to C:/dottalkpp."
$md += "- It does not delete anything."
$md += "- It does not authorize a new header batch."

$md | Out-File $OutMd -Encoding UTF8
Write-Host "Metacollect runtime harness reboot recovery check wrote $OutCsv"
Write-Host "Metacollect runtime harness reboot recovery check wrote $OutMd"
Write-Host "runtime_harness_recovery_status:" $overall
Write-Host "PASS:" $pass
Write-Host "WARN:" $warn
Write-Host "FAIL:" $fail
