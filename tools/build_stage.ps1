param(
    [switch]$Configure,
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$buildDir = Join-Path $repoRoot "build"
$cachePath = Join-Path $buildDir "CMakeCache.txt"

function Test-StaleCMakeCache {
    param(
        [string]$CacheFile,
        [string]$ExpectedSourceDir
    )

    if (-not (Test-Path -LiteralPath $CacheFile)) {
        return $false
    }

    $homeLine = Select-String -LiteralPath $CacheFile -Pattern '^CMAKE_HOME_DIRECTORY:INTERNAL=' -SimpleMatch:$false | Select-Object -First 1
    if (-not $homeLine) {
        return $false
    }

    $actual = $homeLine.Line.Substring("CMAKE_HOME_DIRECTORY:INTERNAL=".Length)
    try {
        $actualPath = [System.IO.Path]::GetFullPath($actual)
        $expectedPath = [System.IO.Path]::GetFullPath($ExpectedSourceDir)
    } catch {
        return $true
    }

    return $actualPath.TrimEnd('\') -ne $expectedPath.TrimEnd('\')
}

Push-Location $repoRoot
try {
    $staleCache = Test-StaleCMakeCache -CacheFile $cachePath -ExpectedSourceDir $repoRoot
    if ($staleCache) {
        Write-Host "Stale CMake cache detected in $buildDir"
        Write-Host "Removing copied build cache and reconfiguring for $repoRoot"
        if (Test-Path -LiteralPath $buildDir) {
            Remove-Item -LiteralPath $buildDir -Recurse -Force
        }
        $Configure = $true
    }

    if ($Configure -or -not (Test-Path -LiteralPath $cachePath)) {
        & cmake --preset stage
        if ($LASTEXITCODE -ne 0) {
            throw "cmake configure failed with exit code $LASTEXITCODE"
        }
    }

    & cmake --build --preset "stage-$Configuration"
    if ($LASTEXITCODE -ne 0) {
        throw "cmake build failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
