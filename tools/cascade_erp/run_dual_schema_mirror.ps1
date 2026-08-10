param(
    [string]$ProofPath
)

$ErrorActionPreference = "Stop"
$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $toolRoot)
# System-bundle layout (owner ruling 2026-08-10): see generate_dual_schema_contract.py header.
$mirrorRoot = Join-Path $repoRoot "dottalkpp\data\systems\cascade_erp\sqlite\x64base_mirror"
$physicalRoot = Join-Path $repoRoot "dottalkpp\data\systems\cascade_erp\dbf"
$ecologyTool = Join-Path $repoRoot "tools\database_ecology\database_ecology.py"

& python $ecologyTool cascade-preflight --repo-root $repoRoot
if ($LASTEXITCODE -ne 0) {
    throw "Cascade mirror preflight found ambiguous legacy root output. Review the hash-bound database ecology sidecar plan before rebuilding."
}

New-Item -ItemType Directory -Force -Path $physicalRoot | Out-Null

if (-not $ProofPath) {
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $proofDir = Join-Path $mirrorRoot "proofs"
    New-Item -ItemType Directory -Force -Path $proofDir | Out-Null
    $ProofPath = Join-Path $proofDir ("dual_schema_runtime_" + $stamp + ".txt")
}

& python (Join-Path $toolRoot "generate_dual_schema_contract.py")
if ($LASTEXITCODE -ne 0) {
    throw "Cascade dual-schema generation failed with exit code $LASTEXITCODE"
}

$commands = Get-Content -LiteralPath (Join-Path $mirrorRoot "build_x64base_mirror.dts")
$runtimeOutput = @(& (Join-Path $repoRoot "datarun.ps1") -CommandLines $commands 2>&1)
$runtimeCode = $LASTEXITCODE
$runtimeText = ($runtimeOutput | ForEach-Object { $_.ToString() }) -join "`r`n"
$runtimeText | Set-Content -LiteralPath $ProofPath -Encoding utf8

if ($runtimeCode -ne 0) {
    throw "DotTalk++ mirror build failed with exit code $runtimeCode; proof: $ProofPath"
}

$builds = [regex]::Matches(
    $runtimeText,
    'CASCADE MIRROR BUILD (table|view) ([^ ]+) AS ([^ ]+) EXPECT_ROWS (\d+) EXPECT_FIELDS (\d+)'
)
$validations = [regex]::Matches($runtimeText, 'DDL VALIDATE: OK')
$creates = [regex]::Matches($runtimeText, 'DDL CREATE DBF: OK')
$imports = [regex]::Matches($runtimeText, 'Imported (\d+) records')

if ($builds.Count -ne 43 -or $validations.Count -ne 43 -or $creates.Count -ne 43 -or $imports.Count -ne 43) {
    throw "Incomplete mirror proof: builds=$($builds.Count) validates=$($validations.Count) creates=$($creates.Count) imports=$($imports.Count); proof: $ProofPath"
}

for ($index = 0; $index -lt $builds.Count; $index++) {
    $expected = [int]$builds[$index].Groups[4].Value
    $imported = [int]$imports[$index].Groups[1].Value
    if ($expected -ne $imported) {
        $name = $builds[$index].Groups[2].Value
        throw "Row mismatch for ${name}: expected $expected imported $imported; proof: $ProofPath"
    }
}

$failurePatterns = @(
    'DDL VALIDATE: FAILED',
    'DDL CREATE DBF: schema file not found',
    'IMPORT: cannot open',
    'AUTODBF_CREATE_FAILED',
    'Unknown command:'
)
foreach ($pattern in $failurePatterns) {
    if ($runtimeText.Contains($pattern)) {
        throw "Mirror proof contains failure marker '$pattern'; proof: $ProofPath"
    }
}

$contract = Get-Content -LiteralPath (Join-Path $mirrorRoot "dual_schema_contract.json") -Raw | ConvertFrom-Json
$runtimeIdentity = [regex]::Match($runtimeText, 'dottalk\+\+ v[^\r\n]+').Value
$proofRelative = [System.IO.Path]::GetRelativePath($repoRoot, (Resolve-Path -LiteralPath $ProofPath).Path)
$receipt = [ordered]@{
    status = "runtime_observed_pass"
    observed_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_identity = $runtimeIdentity
    canonical_sqlite_sha256 = $contract.authority.sqlite_sha256_before
    sqlite_hash_unchanged_during_generation = ($contract.authority.sqlite_sha256_before -eq $contract.authority.sqlite_sha256_after)
    sqlite_tables = 34
    sqlite_views = 9
    x64base_table_mirrors = 34
    x64base_materialized_view_snapshots = 9
    x64base_physical_root = "dottalkpp/data/dbf/cascade_erp"
    validated_schemas = 43
    created_dbfs = 43
    imported_objects = 43
    row_counts_reconciled = $true
    proof = $proofRelative.Replace('\', '/')
    semantic_boundary = "SQLite constraints, defaults, indexes, relationships, and view SQL are preserved in sidecars; DBF-native enforcement is not claimed."
}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $mirrorRoot "runtime_status_latest.json") -Encoding utf8

Write-Host "CASCADE DUAL SCHEMA MIRROR: PASS"
Write-Host "  objects validated/created/imported: 43"
Write-Host "  table mirrors: 34"
Write-Host "  materialized view snapshots: 9"
Write-Host "  proof: $ProofPath"
