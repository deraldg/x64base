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

    $all    = @($candidates)
    $newest = $all | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if ($newest) {
        # REPORT THE CHOICE, BECAUSE IT IS A CHOICE.
        #
        # This function picks by TIMESTAMP across several build roots and then
        # says nothing. Update-DotTalkRuntimeExe already quantifies staleness
        # when the copy FAILS -- that warning is loud, and it is the one the
        # working notes credit. A SUCCESSFUL copy of the wrong tree's exe
        # printed nothing at all, which is the case that actually costs a
        # session: the run works, the output looks right, and the binary is
        # from a preset built weeks ago.
        #
        # The shape is this tree's recurring one. An instrument reports on the
        # artifact it happened to find rather than on the source just written:
        # ctest did it on 2026-09-11 with test binaries built before fifteen of
        # their markers existed, and the build.ps1 target list exists because it
        # did it before that. Naming which tree won is the whole fix.
        #
        # Write-Host and Write-Warning ONLY. This function's return value is the
        # exe path -- a bare string here would join the output stream and the
        # caller would receive an array instead of a path.
        $ageMin = [math]::Round(((Get-Date).ToUniversalTime() - $newest.LastWriteTimeUtc).TotalMinutes, 1)
        Write-Host "datarun: staging $($newest.FullName)"
        Write-Host "         chosen by timestamp from $($all.Count) candidate(s); built $ageMin min ago."

        if ($newest.FullName -ne $Layout.BuildExe) {
            # NOT AN ERROR. Building a non-default preset and running it is a
            # legitimate thing to do, and refusing would break it. But the
            # DEFAULT preset is what nearly every session builds, so a winner
            # from anywhere else is worth a sentence rather than silence.
            Write-Warning "datarun: the staged exe is NOT the default pro-md build."
            Write-Warning "  staged : $($newest.FullName)"
            Write-Warning "  default: $($Layout.BuildExe)"
            Write-Warning "  This is correct IF you meant to run another preset. If you just built"
            Write-Warning "  the default, another tree holds a NEWER exe and you are about to run IT."
        }

        if ($all.Count -gt 1) {
            Write-Host "         other candidate(s), newest first:"
            $all | Sort-Object LastWriteTimeUtc -Descending | Select-Object -Skip 1 | ForEach-Object {
                Write-Host ("           {0}  ({1})" -f $_.FullName, $_.LastWriteTime)
            }
        }

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
            # Could not stage the fresh build (usually a running process holds the runtime exe:
            # the dottalk_bbsd daemon or another dottalkpp). Fall back to the existing copy, but
            # warn LOUDLY and quantify staleness so a stale run is never mistaken for a new build.
            $builtTime = (Get-Item -LiteralPath $builtExe).LastWriteTime
            $runTime   = (Get-Item -LiteralPath $Layout.RuntimeExe).LastWriteTime
            $stale = ""
            if ($builtTime -gt $runTime) {
                $mins = [math]::Round(($builtTime - $runTime).TotalMinutes, 1)
                $stale = " -- the copy being run is STALE ($mins min older than the build you just made)"
            }
            Write-Warning "datarun: could NOT copy the freshly-built exe into the runtime bin$stale."
            Write-Warning "  reason : $($_.Exception.Message)"
            Write-Warning "  built  : $builtExe  ($builtTime)"
            Write-Warning "  running: $($Layout.RuntimeExe)  ($runTime)"
            Write-Warning "  A running process is likely holding it (dottalk_bbsd daemon or another dottalkpp)."
            Write-Warning "  Stop that process and re-run datarun to actually test the new build."
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

    # ---- Runtime helper scripts (the TOOLS path slot) -----------------------
    # Some commands shell out to a helper rather than implementing a protocol
    # themselves -- SMTP invokes tools/notify/smtp_probe.py, as SFTP invokes the
    # system sftp client. The engine finds these through the TOOLS slot, which
    # resolves to <appRoot>/tools, NOT to the repository tools/ directory.
    #
    # The source of truth stays in the repository tools/ tree, because that is
    # what ships to the public repo (stage_dottalkpp_repo.ps1 IncludeRoots lists
    # "tools"; it does NOT list "dottalkpp"). Moving the helper into the runtime
    # tree would fix a local run and simultaneously delete it from the published
    # product. So it is COPIED here, exactly as the exe and DLLs are.
    #
    # Repo-relative paths; each is staged to the same relative location under
    # <appRoot>. Add a line to extend.
    $runtimeHelpers = @(
        "tools\notify\smtp_probe.py"
    )

    foreach ($rel in $runtimeHelpers) {
        $src = Join-Path $Layout.RepoRoot $rel
        $dst = Join-Path $Layout.AppRoot  $rel

        if (-not (Test-Path -LiteralPath $src)) {
            Write-Warning "Runtime helper not found in the repository: $src (the command that uses it will report it missing)."
            continue
        }

        $dstDir = Split-Path -Parent $dst
        if (-not (Test-Path -LiteralPath $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        }

        try {
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
        catch {
            # Same posture as the DLL stage: only complain if the destination is
            # ALSO absent. A locked-but-present helper is usable; a missing one
            # is not, and the command that needs it must not be the first to
            # discover that.
            if (-not (Test-Path -LiteralPath $dst)) {
                Write-Warning "Could not stage runtime helper $rel : $($_.Exception.Message)"
            }
        }
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

function Invoke-DotTalkWbRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryScriptPath,

        [Parameter(Mandatory = $true)]
        [string[]]$WbRelativeExeCandidates,

        [string[]]$AppArgs
    )

    $layout = Get-DotTalkLayout -EntryScriptPath $EntryScriptPath
    Set-DotTalkTraceDefaults

    $wbCandidates = @(
        $WbRelativeExeCandidates |
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

    $wbExe = $wbCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $wbExe) {
        throw "Workbench executable not found. Checked: $($wbCandidates -join ', ')"
    }

    if ($wbExe -like "*build-wx-fixed-local*") {
        Write-Warning "Using deprecated wx build root at $wbExe. Canonical GUI build root is $($layout.BuildRoot)."
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

    $wbDir = Split-Path -Parent $wbExe
    $env:DOTTALKPP_GUI_BIN = $wbDir

    $runtimePathParts = @($wbDir)
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
        & $wbExe @runtimeArgs
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
