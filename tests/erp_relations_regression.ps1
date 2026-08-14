param(
    [string]$Executable = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Executable)) {
    $Executable = Join-Path $RepoRoot "build\core-vcpkg\src\dottalkpp.exe"
}

$DataDir = Join-Path $RepoRoot "dottalkpp\data"
$Database = Join-Path $DataDir "cascade_precision_erp\cascade_precision_mfg_erp.sqlite"

if (-not (Test-Path -LiteralPath $Executable)) {
    throw "DotTalk++ executable not found: $Executable"
}
if (-not (Test-Path -LiteralPath $Database)) {
    throw "Cascade ERP database not found: $Database"
}

$StartInfo = [System.Diagnostics.ProcessStartInfo]::new()
$StartInfo.FileName = $Executable
$StartInfo.WorkingDirectory = $DataDir
$StartInfo.UseShellExecute = $false
$StartInfo.RedirectStandardInput = $true
$StartInfo.RedirectStandardOutput = $true
$StartInfo.RedirectStandardError = $true
$StartInfo.CreateNoWindow = $true

$Process = [System.Diagnostics.Process]::new()
$Process.StartInfo = $StartInfo
if (-not $Process.Start()) {
    throw "Failed to start DotTalk++: $Executable"
}

$Process.StandardInput.WriteLine("ERP CHECK")
$Process.StandardInput.WriteLine("ERP RELATIONS")
$Process.StandardInput.WriteLine("EXIT")
$Process.StandardInput.Close()

$Stdout = $Process.StandardOutput.ReadToEnd()
$Stderr = $Process.StandardError.ReadToEnd()
$Process.WaitForExit()

if ($Process.ExitCode -ne 0) {
    throw "DotTalk++ exited $($Process.ExitCode). stderr: $Stderr"
}

$Required = @(
    "FK column mappings: 58 measured",
    "cross-module FK relationships: 26 / expected 26 OK",
    "ERP RELATIONS: 58 foreign-key column mappings",
    "AP_Invoices",
    "PO_ID",
    "Purchase_Orders",
    "Vendor_Items",
    "Items",
    "Item_ID"
)

foreach ($Needle in $Required) {
    if (-not $Stdout.Contains($Needle)) {
        throw "Missing expected ERP output: $Needle"
    }
}

if ($Stdout.Contains("ERP RELATIONS failed:") -or $Stdout.Contains("CHECK WARN")) {
    throw "ERP relation regression reported failure or warning."
}

Write-Output "PASS: ERP RELATIONS reports 58 metadata-derived mappings and ERP CHECK verifies 26 cross-module relationships."
