$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$exePath = Join-Path $repoRoot "build\src\Release\dottalkpp.exe"

Push-Location $repoRoot
try {
    Write-Host "Stage repo: $repoRoot"
    Write-Host ""
    Write-Host "Git status"
    & git -c safe.directory='D:/code/ccode/x64base' -C $repoRoot status --short

    Write-Host ""
    Write-Host "Build artifact"
    if (Test-Path -LiteralPath $exePath) {
        Get-Item -LiteralPath $exePath | Select-Object FullName, Length, LastWriteTime
    } else {
        Write-Host "Missing: $exePath"
    }
}
finally {
    Pop-Location
}
