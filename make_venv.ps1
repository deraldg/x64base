# make_venv.ps1 -- rebuild .venv312 against THIS card's vcpkg python.
# Run once after inserting the card on a machine, and again if the letter changes.
$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$card = Split-Path -Parent $repo
$py   = Join-Path $card "vcpkg\installed\x64-windows\tools\python3\python.exe"
if (-not (Test-Path -LiteralPath $py)) { throw "vcpkg python not found: $py" }
if (Test-Path -LiteralPath (Join-Path $repo ".venv312")) {
    Write-Host "Removing the old .venv312 (its paths point at the previous drive letter)."
    Remove-Item -LiteralPath (Join-Path $repo ".venv312") -Recurse -Force
}
& $py -m venv (Join-Path $repo ".venv312")
if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
# The repo venv carries exactly one dependency today: PyYAML. There is no
# requirements.txt in the tree -- if that changes, this line has to follow it.
& (Join-Path $repo ".venv312\Scripts\python.exe") -m pip install --quiet --upgrade pip pyyaml
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
Write-Host "OK. $repo\.venv312 is built against $py" -ForegroundColor Green
