Set-StrictMode -Version Latest

function Get-DotTalkLayout {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryScriptPath
    )

    $scriptDir = Split-Path -Parent $EntryScriptPath
    $scriptLeaf = (Split-Path $scriptDir -Leaf).ToLowerInvariant()

    if ($scriptLeaf -eq "bin") {
        $appRoot = Split-Path -Parent $scriptDir
        $repoRoot = Split-Path -Parent $appRoot
    } else {
        $repoRoot = $scriptDir
        $appRoot = Join-Path $repoRoot "dottalkpp"
    }

    return @{
        RepoRoot    = $repoRoot
        AppRoot     = $appRoot
        RuntimeData = Join-Path $appRoot "data"
        RuntimeExe  = Join-Path $appRoot "bin\dottalkpp.exe"
        BuildRoot   = Join-Path $repoRoot "build"
        BuildWslRoot = Join-Path $repoRoot "build-wsl"
        BuildExe    = Join-Path $repoRoot "build\src\Release\dottalkpp.exe"
    }
}

function Assert-DotTalkPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $LiteralPath)) {
        throw "$Label not found: $LiteralPath"
    }
}

function Set-DotTalkTraceDefaults {
    $env:DOTTALK_APPEND_TRACE = "0"
    $env:DOTTALK_INDEX_TRACE = "0"
}

function Get-DotTalkAppArgs {
    param(
        [string[]]$AppArgs
    )

    return @($AppArgs | Where-Object { $_ -ne $null -and $_ -ne "" })
}

function Set-DotTalkLastExitCode {
    $lastExit = Get-Variable -Name LASTEXITCODE -Scope Global -ErrorAction SilentlyContinue
    if ($null -ne $lastExit) {
        $global:LASTEXITCODE = [int]$lastExit.Value
    } else {
        $global:LASTEXITCODE = 0
    }
}

function Update-DotTalkRuntimeExe {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Layout
    )

    Assert-DotTalkPath -LiteralPath $Layout.BuildExe -Label "Built executable"
    Assert-DotTalkPath -LiteralPath $Layout.RuntimeExe -Label "Runtime executable path"

    try {
        Copy-Item -LiteralPath $Layout.BuildExe -Destination $Layout.RuntimeExe -Force
    }
    catch {
        Write-Warning "Runtime executable is locked; running existing copy at $($Layout.RuntimeExe)"
    }
}

function Invoke-DotTalkCliRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryScriptPath,

        [string[]]$CommandLines,

        [string[]]$AppArgs
    )

    $layout = Get-DotTalkLayout -EntryScriptPath $EntryScriptPath
    Set-DotTalkTraceDefaults

    Assert-DotTalkPath -LiteralPath $layout.AppRoot -Label "Application root"
    Assert-DotTalkPath -LiteralPath $layout.RuntimeData -Label "Runtime data path"

    Update-DotTalkRuntimeExe -Layout $layout

    $runtimeArgs = Get-DotTalkAppArgs -AppArgs $AppArgs

    Push-Location $layout.RuntimeData
    try {
        if ($CommandLines -and $CommandLines.Count -gt 0) {
            $commandStream = @($CommandLines)
            if ($commandStream.Count -eq 1 -and $commandStream[0] -match "(\r\n|\n|\r)") {
                $commandStream = @(
                    ($commandStream[0] -split "\r\n|\n|\r") |
                    Where-Object { $_ -ne $null -and $_ -ne "" }
                )
            }

            $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("dottalk-codex-" + [System.Guid]::NewGuid().ToString("N") + ".dts")
            try {
                [System.IO.File]::WriteAllLines($tempScript, $commandStream)
                & $layout.RuntimeExe --script $tempScript @runtimeArgs
            }
            finally {
                if (Test-Path -LiteralPath $tempScript) {
                    Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
                }
            }
        } else {
            & $layout.RuntimeExe @runtimeArgs
        }
        Set-DotTalkLastExitCode
    }
    finally {
        Pop-Location
    }
}

function Invoke-DotTalkWxRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryScriptPath,

        [Parameter(Mandatory = $true)]
        [string[]]$WxRelativeExeCandidates,

        [string[]]$AppArgs
    )

    $layout = Get-DotTalkLayout -EntryScriptPath $EntryScriptPath
    Set-DotTalkTraceDefaults

    $wxCandidates = @(
        $WxRelativeExeCandidates |
        Where-Object { $_ -ne $null -and $_ -ne "" } |
        ForEach-Object { Join-Path $layout.RepoRoot $_ }
    )

    $cliCandidates = @(
        (Join-Path $layout.RepoRoot "build\src\Release\dottalkpp.exe"),
        (Join-Path $layout.RepoRoot "build\src\Debug\dottalkpp.exe"),
        (Join-Path $layout.RepoRoot "build-wx-fixed-local\src\Release\dottalkpp.exe"),
        $layout.RuntimeExe
    )

    Assert-DotTalkPath -LiteralPath $layout.AppRoot -Label "Application root"
    Assert-DotTalkPath -LiteralPath $layout.RuntimeData -Label "Runtime data path"

    $wxExe = $wxCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $wxExe) {
        throw "wx executable not found. Checked: $($wxCandidates -join ', ')"
    }

    if ($wxExe -like "*build-wx-fixed-local*") {
        Write-Warning "Using deprecated wx build root at $wxExe. Canonical GUI build root is $($layout.BuildRoot)."
    }

    $cliExe = $cliCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $cliExe) {
        throw "DotTalk++ CLI executable not found. Checked: $($cliCandidates -join ', ')"
    }

    $env:DOTTALKPP_GUI_CLI = $cliExe
    $env:DOTTALKPP_EXE = $cliExe
    $env:DOTTALKPP_ROOT = $layout.AppRoot
    $env:DOTTALKPP_DATA = $layout.RuntimeData
    $env:DOTTALK_DATA = $layout.RuntimeData

    $wxDir = Split-Path -Parent $wxExe
    $env:DOTTALKPP_GUI_BIN = $wxDir

    $runtimePathParts = @($wxDir)
    if ($env:VCPKG_ROOT) {
        $runtimePathParts += (Join-Path $env:VCPKG_ROOT "installed\x64-windows\bin")
    }
    $runtimePathParts += @(
        (Join-Path $layout.BuildRoot "vcpkg_installed\x64-windows\bin"),
        (Join-Path $layout.RepoRoot "vcpkg_installed\x64-windows\bin")
    )
    $runtimePathParts = $runtimePathParts | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
    $env:PATH = "$($runtimePathParts -join ';');$env:PATH"

    $runtimeArgs = Get-DotTalkAppArgs -AppArgs $AppArgs

    Push-Location $layout.RuntimeData
    try {
        & $wxExe @runtimeArgs
        Set-DotTalkLastExitCode
    }
    finally {
        Pop-Location
    }
}

function Invoke-PydotTalkStarterSmokes {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryScriptPath,

        [string[]]$AppArgs
    )

    $layout = Get-DotTalkLayout -EntryScriptPath $EntryScriptPath
    $runner = Join-Path $layout.RepoRoot "bindings\run_pydottalk_smokes.ps1"

    Assert-DotTalkPath -LiteralPath $runner -Label "pydottalk smoke runner"
    $argList = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $runner
    )
    if ($AppArgs) {
        $argList += $AppArgs
    }

    & powershell @argList
    Set-DotTalkLastExitCode
}
