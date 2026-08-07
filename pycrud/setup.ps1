param(
  [switch]$Recreate
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if ((Test-Path .venv) -and $Recreate) { Remove-Item -Recurse -Force .venv }
if (-not (Test-Path .venv)) {
  py -3 -m venv .venv
}
& .\.venv\Scripts\python -m pip install --upgrade pip
& .\.venv\Scripts\pip install -r requirements.txt

Write-Host "Done. Activate with: .\.venv\Scripts\Activate.ps1"
