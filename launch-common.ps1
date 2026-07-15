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

function Resolve-DotTalkBuiltExe {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Layout
    )

    # Different presets build to different roots:
    #   pro-md          -> build\src\Release
    #   windows-core    -> build\windows-core\src\Release
    #   core / index-*  -> build\<preset>\...
    #   pro-md-labtalk  -> build-labtalk\src\Release
    #   ansi-mt         -> build-ansi-mt\src\Release
    # Find the most recently built dottalkpp.exe across those roots so datarun
    # works regardless of which preset the user built.
    $searchRoots = @(
        $Layout.BuildRoot,
        (Join-Path $Layout.RepoRoot "build-labtalk"),
        (Join-Path $Layout.RepoRoot "build-ansi-mt")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    $candidates = foreach ($root in $searchRoots) {
        Get-ChildItem -LiteralPath $root -Recurse -Filter "dottalkpp.exe" -File -ErrorAction SilentlyContinue
    }

    $newest = @($candidates) | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if ($newest) {
        return $newest.FullName
    }

    # Nothing built yet; return the canonical pro-md path so the caller's
    # existence check produces a clear "build first" error.
    return $Layout.BuildExe
}

function Update-DotTalkRuntimeExe {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Layout
    )

    # Stage the freshly-built exe into dottalkpp/bin, then run it. Assert the
    # SOURCE (a build output); the destination must NOT be required to pre-exist
    # -- on a fresh clone dottalkpp/bin has no exe (*.exe is gitignored) and this
    # function's whole job is to create it.
    $builtExe = Resolve-DotTalkBuiltExe -Layout $Layout
    Assert-DotTalkPath -LiteralPath $builtExe -Label "Built executable"

    $runtimeDir = Split-Path -Parent $Layout.RuntimeExe
    if (-not (Test-Path -LiteralPath $runtimeDir)) {
        New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
    }

    try {
        Copy-Item -LiteralPath $builtExe -Destination $Layout.RuntimeExe -Force
    }
    catch {
        if (Test-Path -LiteralPath $Layout.RuntimeExe) {
            Write-Warning "Runtime executable is locked; running existing copy at $($Layout.RuntimeExe)"
        }
        else {
            throw "Could not stage runtime executable from $builtExe to $($Layout.RuntimeExe): $($_.Exception.Message)"
        }
    }

    # The exe is dynamically linked; it will not load without its runtime DLLs
    # (lmdb.dll, sqlite3.dll, tvision.dll, and any transitive deps). On a fresh
    # clone bin/ has none of these (*.dll is gitignored). Stage the FULL runtime
    # DLL set -- the union of whatever applocal deployed beside the exe and the
    # vcpkg dynamic bin -- so we never have to know which specific libraries are
    # DLLs vs statically linked. Copying extra DLLs is harmless; missing one is
    # a hard load failure.
    $buildDir = Split-Path -Parent $builtExe
    $dllSources = @(
        $buildDir,
        (Join-Path $Layout.BuildRoot "vcpkg_installed\x64-windows\bin"),
        (Join-Path $Layout.RepoRoot  "vcpkg_installed\x64-windows\bin")
    )
    if ($env:VCPKG_ROOT) {
        $dllSources += (Join-Path $env:VCPKG_ROOT "installed\x64-windows\bin")
    }
    $dllSources = @($dllSources | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)

    $staged = 0
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($dir in $dllSources) {
        foreach ($dll in @(Get-ChildItem -LiteralPath $dir -Filter *.dll -File -ErrorAction SilentlyContinue)) {
            # First source wins: the exe-adjacent (applocal) copy takes
            # precedence over the vcpkg bin copy.
            if ($seen.Add($dll.Name)) {
                $dest = Join-Path $runtimeDir $dll.Name
                try {
                    Copy-Item -LiteralPath $dll.FullName -Destination $dest -Force
                    $staged++
                }
                catch {
                    if (-not (Test-Path -LiteralPath $dest)) {
                        Write-Warning "Could not stage runtime dependency $($dll.Name): $($_.Exception.Message)"
                    }
                }
            }
        }
    }

    if ($staged -eq 0) {
        Write-Warning "No runtime DLLs staged into $runtimeDir. If the exe fails to load (lmdb.dll / sqlite3.dll / tvision.dll not found), build with a vcpkg preset first so vcpkg_installed is populated."
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
