<#
.SYNOPSIS
    Last gate before a push: build the engine on Windows (MSVC) AND in WSL (Linux)
    from the same tree, and fail if either does not build.

.DESCRIPTION
    Recreated 2026-11-26 from an untracked scripts/build_all.ps1 that pinned
    D:\code\ccode and /mnt/d/code/ccode, so it could only ever check one clone on
    one drive. This one checks WHATEVER tree it is pointed at -- the development
    clone, the travelling card clone, or the C:\x64base staging tree before a
    push to main -- and derives the WSL path with `wslpath` instead of assuming
    a drive letter.

    It builds; it does not commit, push, or clean. Both halves use the tree's own
    entry points, so this gate measures what a reader of BUILDING.md would run:

        Windows : cmake --preset <WinPreset> (only if <BuildDir> is not configured
                  yet), then cmake --build <BuildDir> --target dottalkpp --config Release
        WSL     : ./wslbuild.sh dottalkpp   (wsl-lean preset, stages
                  dottalkpp/bin-wsl-lean/dottalkpp)

    Then each built binary is launched once on a one-line script so "it linked"
    is not mistaken for "it runs".

    Exit 0 = both built and ran. Exit 1 = a half failed; the summary names it.

.PARAMETER Root
    Tree to check. Default: the repository this script lives in.
.PARAMETER BuildDir
    Windows build directory. Default: <Root>\build.
.PARAMETER WinPreset
    Configure preset used only when <BuildDir> has no CMakeCache.txt. Default pro-md.
.PARAMETER SkipWindows / SkipWsl
    Run one half only (the summary still says which half was skipped).

.EXAMPLE
    .\tools\staging\dual_build_check.ps1
.EXAMPLE
    .\tools\staging\dual_build_check.ps1 -Root C:\x64base
#>
[CmdletBinding()]
param(
    [string] $Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string] $BuildDir,
    [string] $WinPreset = "pro-md",
    [switch] $SkipWindows,
    [switch] $SkipWsl
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
if (-not $BuildDir) { $BuildDir = Join-Path $Root "build" }
foreach ($need in "CMakeLists.txt", "CMakePresets.json", "wslbuild.sh") {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $need))) {
        throw "Not a buildable x64base tree (missing $need): $Root"
    }
}

$result = [ordered]@{ Windows = "skipped"; WSL = "skipped" }

function Invoke-Step([string] $Label, [scriptblock] $Body) {
    Write-Host ""
    Write-Host "=== $Label ===" -ForegroundColor Cyan
    & $Body
    if ($LASTEXITCODE -ne 0) { throw "$Label failed (exit $LASTEXITCODE)" }
}

$probe = Join-Path ([IO.Path]::GetTempPath()) ("dual_build_probe_{0}.dts" -f $PID)
Set-Content -LiteralPath $probe -Value "? `"DUALBUILD-PROBE-OK`"" -Encoding ascii

Write-Host "dual-build-check: $Root"

if (-not $SkipWindows) {
    try {
        if (-not (Test-Path -LiteralPath (Join-Path $BuildDir "CMakeCache.txt"))) {
            Invoke-Step "Windows configure ($WinPreset)" { Push-Location $Root; try { cmake --preset $WinPreset } finally { Pop-Location } }
        }
        Invoke-Step "Windows build" { cmake --build $BuildDir --target dottalkpp --config Release }
        $exe = Get-ChildItem -LiteralPath $BuildDir -Recurse -Filter dottalkpp.exe -ErrorAction SilentlyContinue |
               Where-Object { $_.FullName -match '\\Release\\' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $exe) { throw "built dottalkpp.exe not found under $BuildDir" }
        Push-Location (Join-Path $Root "dottalkpp")
        try { $out = & $exe.FullName --script $probe 2>&1 | Out-String } finally { Pop-Location }
        if ($out -notmatch 'DUALBUILD-PROBE-OK') { throw "Windows binary built but did not run the probe script" }
        $result.Windows = "PASS  ($($exe.FullName), $($exe.LastWriteTime))"
    } catch {
        $result.Windows = "FAIL  $($_.Exception.Message)"
    }
}

if (-not $SkipWsl) {
    try {
        if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) { throw "wsl.exe not available on this host" }
        $winForWsl = $Root -replace '\\', '/'
        $linuxRoot = (& wsl wslpath -a "$winForWsl").Trim()
        if ($LASTEXITCODE -ne 0 -or -not $linuxRoot) { throw "wslpath could not translate $Root" }
        $probeLinux = (& wsl wslpath -a ($probe -replace '\\', '/')).Trim()
        Invoke-Step "WSL build (wslbuild.sh, wsl-lean)" { wsl bash -lc "cd '$linuxRoot' && ./wslbuild.sh dottalkpp" }
        $out = & wsl bash -lc "cd '$linuxRoot/dottalkpp' && ./bin-wsl-lean/dottalkpp --script '$probeLinux'" 2>&1 | Out-String
        if ($out -notmatch 'DUALBUILD-PROBE-OK') { throw "WSL binary built but did not run the probe script" }
        $result.WSL = "PASS  ($linuxRoot/dottalkpp/bin-wsl-lean/dottalkpp)"
    } catch {
        $result.WSL = "FAIL  $($_.Exception.Message)"
    }
}

Remove-Item -LiteralPath $probe -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==== dual-build-check summary ====" -ForegroundColor Cyan
foreach ($k in $result.Keys) { Write-Host ("  {0,-8}: {1}" -f $k, $result[$k]) }
$failed = @($result.Values | Where-Object { $_ -like 'FAIL*' })
if ($failed.Count) {
    Write-Host "dual-build-check: FAIL" -ForegroundColor Red
    exit 1
}
Write-Host "dual-build-check: PASS" -ForegroundColor Green
exit 0
