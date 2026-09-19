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

function Select-DotTalkNewestExisting {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string[]]$Candidates
    )

    # NAMING WHICH TREE WON IS THE WHOLE FIX -- the same sentence
    # Resolve-DotTalkBuiltExe carries, applied to the other two selections in
    # this file. Until 2026-09-15 both of them were
    # `Where-Object { Test-Path } | Select-Object -First 1`: FIRST THAT EXISTS,
    # not newest, and silent about it. So the workbench path could run a stale
    # binary purely because a staler tree sat earlier in a hardcoded list, and
    # the run would look identical to a correct one.
    #
    # Resolve-DotTalkBuiltExe already picked by timestamp and reported both the
    # winner and every loser. This tree contained the right answer and the wrong
    # answer in one file.
    #
    # Write-Host and Write-Warning ONLY -- this function returns a PATH, and a
    # bare string would join the output stream and hand the caller an array.
    $found = @(
        $Candidates |
        Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
        ForEach-Object { Get-Item -LiteralPath $_ }
    )
    if ($found.Count -eq 0) { return $null }

    $newest = $found | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    Write-Host ("{0}: using {1}" -f $Label, $newest.FullName)
    Write-Host ("         chosen by timestamp from {0} candidate(s) present; built {1}." -f
                $found.Count, $newest.LastWriteTime)

    if ($found.Count -gt 1) {
        $first = $Candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
        if ($first -ne $newest.FullName) {
            # The old rule would have run this one. Say so, because a silent
            # change of winner is how a fix becomes a new surprise.
            Write-Warning ("{0}: list order would have chosen {1}, which is NOT the newest." -f $Label, $first)
        }
        Write-Host "         other candidate(s) present, newest first:"
        $found | Sort-Object LastWriteTimeUtc -Descending | Select-Object -Skip 1 | ForEach-Object {
            Write-Host ("           {0}  ({1})" -f $_.FullName, $_.LastWriteTime)
        }
    }

    return $newest.FullName
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

    $wbExe = Select-DotTalkNewestExisting -Label "wb" -Candidates $wbCandidates
    if (-not $wbExe) {
        throw "Workbench executable not found. Checked: $($wbCandidates -join ', ')"
    }

    if ($wbExe -like "*build-wx-fixed-local*") {
        Write-Warning "Using deprecated wx build root at $wbExe. Canonical GUI build root is $($layout.BuildRoot)."
    }

    $cliExe = Select-DotTalkNewestExisting -Label "wb-cli" -Candidates $cliCandidates
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

function Resolve-DotTalkPython {
    # ONE interpreter resolver for the launchers. Until 2026-09-18 there were
    # four, and three of them were a single hardcoded path that had stopped
    # resolving -- or had never resolved:
    #
    #   run-bible.ps1      build\vcpkg_installed\x64-windows\tools\python3\python.exe
    #   pydottalk.ps1      build-labtalk\vcpkg_installed\...\tools\python3\python.exe
    #   run-pydottalk.ps1  the same build-labtalk path
    #
    # Measured 2026-09-18: build\vcpkg_installed\x64-windows\tools\python3\
    # holds only Lib, no python.exe. build-labtalk was reclaimed 2026-09-17,
    # and build_pydottalk.ps1 had already measured on 2026-08-17 that its
    # tools\ directory held only pkgconf. So all three named a path that could
    # not answer, and each one threw at its own Test-Path a line later instead
    # of trying anything else.
    #
    # ORDER MATTERS, and it depends on WHAT THE INTERPRETER IS FOR:
    #
    #   HostTools (default) -- running this repo's .py, and importing a built
    #       pydottalk module. CLAUDE.md pins these to the repo venv .venv312
    #       and NOT to the vcpkg python, which is minimal and carries no PyYAML
    #       (-> ModuleNotFoundError: yaml).
    #
    #   BuildExtension -- configuring CMake for the module itself. There the
    #       vcpkg install wins, because FindPython3 needs Development (headers
    #       plus lib), which a venv only resolves through its base prefix.
    #       .venv312\pyvenv.cfg names that base outright:
    #           home    = C:\Users\deral\vcpkg\installed\x64-windows\tools\python3
    #           version = 3.12.9
    #       build_pydottalk.ps1 keeps its own copy of that ordering and is
    #       deliberately NOT changed here: it is the one resolver that was
    #       already correct, and it runs without loading this file.
    #
    # The @( ) around the whole pipeline is load-bearing, not style. When
    # exactly one candidate survives, Where-Object returns a bare STRING, and
    # [0] on a string yields a CHARACTER: build_pydottalk.ps1 once resolved its
    # interpreter to "D" that way, and CMake then reported a missing Python3
    # rather than a bad path.
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        # An explicit answer from the caller wins over every candidate below.
        # Empty means "resolve it for me".
        [string]$PythonExe = '',

        [ValidateSet('HostTools', 'BuildExtension')]
        [string]$Purpose = 'HostTools',

        [string]$VcpkgRoot = $env:VCPKG_ROOT,

        [string]$VcpkgTriplet = 'x64-windows',

        [string]$Label = 'Python'
    )

    if (-not $PythonExe) {
        $vcpkgRootPython = $null
        if ($VcpkgRoot) {
            $vcpkgRootPython = Join-Path $VcpkgRoot "installed\$VcpkgTriplet\tools\python3\python.exe"
        }

        $venv312     = Join-Path $RepoRoot ".venv312\Scripts\python.exe"
        $buildTree   = Join-Path $RepoRoot "build\vcpkg_installed\$VcpkgTriplet\tools\python3\python.exe"
        $labtalkTree = Join-Path $RepoRoot "build-labtalk\vcpkg_installed\$VcpkgTriplet\tools\python3\python.exe"
        $pydTree     = Join-Path $RepoRoot "build-pydottalk\vcpkg_installed\$VcpkgTriplet\tools\python3\python.exe"
        $pycrudVenv  = Join-Path $RepoRoot "pycrud\.venv\Scripts\python.exe"

        if ($Purpose -eq 'BuildExtension') {
            $ordered = @($vcpkgRootPython, $pydTree, $labtalkTree, $buildTree,
                         $env:PYDOTTALK_PYTHON, $env:PY12, $venv312, $pycrudVenv)
        } else {
            $ordered = @($env:PYDOTTALK_PYTHON, $env:PY12, $venv312, $vcpkgRootPython,
                         $pydTree, $labtalkTree, $buildTree, $pycrudVenv)
        }

        $candidates = @($ordered | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) })

        # Whatever is on PATH is deliberately NOT in that list. It is the 3.13
        # trap, and a launcher that silently runs the wrong interpreter is the
        # failure this function exists to stop. Name the venv instead.
        if ($candidates.Count -eq 0) {
            throw ("${Label}: no Python interpreter resolved under $RepoRoot. " +
                   "Expected the repo venv .venv312\Scripts\python.exe -- build it, " +
                   "set PY12 or PYDOTTALK_PYTHON, or pass -PythonExe.")
        }

        # Write-Host only: this function returns a PATH, and a bare string
        # would join the output stream and hand the caller an array.
        $PythonExe = $candidates[0]
        Write-Host ("{0}: using {1}" -f $Label, $PythonExe)
        if ($candidates.Count -gt 1) {
            Write-Host ("         chosen by order from {0} candidate(s) present; the rest, in order:" -f $candidates.Count)
            $candidates | Select-Object -Skip 1 | ForEach-Object { Write-Host ("           {0}" -f $_) }
        }
    }

    # Assert the SHAPE of what we resolved, not merely that it is truthy. "D"
    # is truthy.
    if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
        throw "${Label}: resolved interpreter is not a file: '$PythonExe'."
    }
    if ([IO.Path]::GetFileName($PythonExe) -notlike 'python*.exe') {
        throw "${Label}: resolved interpreter does not look like a Python interpreter: '$PythonExe'."
    }

    return $PythonExe
}

function Resolve-DotTalkPyModuleDir {
    # Where the BUILT pydottalk module lives. pydottalk.ps1 and
    # run-pydottalk.ps1 both hardcoded build-labtalk\python, a tree reclaimed
    # 2026-09-17 -- and build_pydottalk.ps1's default build directory has been
    # build-pydottalk since 2026-08-17 in any case, so the hardcoded answer was
    # already the wrong tree before it was deleted.
    #
    # Measured 2026-09-18: no build*\python directory exists in this tree at
    # all. The module is simply not built right now, so the honest return is
    # $null, and the CALLER names the builder. Throwing a path that was never
    # going to be there is how these launchers looked broken instead of unbuilt.
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        [string]$ModuleDir = ''
    )

    if ($ModuleDir) { return $ModuleDir }
    if ($env:PYDOTTALK_BIN -and (Test-Path -LiteralPath $env:PYDOTTALK_BIN)) {
        return $env:PYDOTTALK_BIN
    }

    # Newest, not first: two stale trees can each hold a .pyd, and picking by
    # list order is the bug Select-DotTalkNewestExisting was written for.
    return Select-DotTalkNewestExisting -Label "pydottalk module" -Candidates @(
        (Join-Path $RepoRoot "build-pydottalk\python"),
        (Join-Path $RepoRoot "build-labtalk\python"),
        (Join-Path $RepoRoot "build\python")
    )
}

function Test-LabTalkPythonModule {
    # One module, one process, one answer. Two probes cost two process starts
    # and are worth it: a single combined probe cannot say WHICH import failed,
    # and which one failed is the whole diagnostic here.
    param(
        [Parameter(Mandatory = $true)] [string]$Exe,
        [Parameter(Mandatory = $true)] [string]$Module
    )

    # find_spec is NOT enough for _tkinter: the spec can resolve while the
    # import still fails on a missing tcl/tk DLL. Import it for real.
    #
    # ErrorActionPreference IS FORCED TO Continue FOR THE DURATION, and that is
    # load-bearing rather than defensive. A caller running under 'Stop' -- which
    # every launcher here does -- turns a NATIVE command's stderr into a
    # TERMINATING error. This function's whole job is to let an import fail, so
    # under Stop the failing probe threw a NativeCommandError whose message is
    # python's first traceback line, and the refusal upstream reported
    # "Traceback (most recent call last):" instead of naming the missing module.
    # Measured 2026-09-19: the verification arm asserted that the refusal NAMES
    # the module, and that assertion is the only reason this surfaced.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Exe -c "import $Module" 1>$null 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        $ErrorActionPreference = $prev
    }
}

function Resolve-LabTalkPython {
    # The portal needs an interpreter this repo does NOT otherwise use, and
    # that is the whole finding. Measured 2026-09-18 on this machine:
    #
    #   vcpkg python3  -- what bare `python` resolves to here    tkinter NO   yaml NO
    #   .venv312       -- based on the vcpkg python              tkinter NO   yaml yes
    #   Anaconda 3.12.7                                          tkinter yes  yaml yes
    #
    # Both copies of launch_portal.ps1 said `python`, which on this box is the
    # one interpreter of the three that can do neither, so the portal window
    # has not opened from its own launcher for as long as PATH has resolved
    # that way. The failure was also unhelpful: the portal caught the
    # ImportError and printed "GUI unavailable" WITHOUT naming the interpreter
    # it was running under, so the same line appeared no matter which python
    # you tried, and trying another one looked like it had changed nothing.
    #
    # tkinter CANNOT be pip-installed -- it comes from the base install's
    # tcl/tk. So this resolver PROBES rather than assuming, and a miss names
    # every candidate and the module each one lacked.
    #
    # NOT the same question as Resolve-DotTalkPython, deliberately kept apart:
    # that one resolves an interpreter to BUILD or IMPORT the pydottalk
    # module and prefers the venv CLAUDE.md pins host tooling to. This one
    # needs a desktop GUI toolkit, which that venv structurally cannot have.
    # One function answering both would have to rank Anaconda above .venv312
    # for every caller, and that contradicts the house rule.
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        # An explicit answer from the caller wins, but is still PROBED -- an
        # interpreter that cannot import what the portal needs is not an
        # answer just because someone named it.
        [string]$PythonExe = '',

        # Headless --audit / --audit-write / --run-item need yaml only. The
        # venv serves those today and refusing it over a toolkit the run will
        # never load would be a refusal for its own sake.
        [bool]$RequireTk = $true,

        [string]$Label = 'LabTalk portal'
    )

    $wanted = if ($RequireTk) { @('_tkinter', 'yaml') } else { @('yaml') }

    # AN INSTRUCTION IS NOT A PREFERENCE, corrected 2026-09-19 when this
    # function's own falsification arm caught it. -PythonExe used to sit at the
    # head of the candidate list and FALL THROUGH when it failed the probe, so
    # naming an interpreter that could not do the job quietly ran a different
    # one. That is the precise substitution this resolver exists to prevent,
    # reintroduced by the resolver itself.
    #
    # The two inputs are NOT the same kind of statement and are no longer
    # treated alike. -PythonExe is per-invocation intent: someone typed it for
    # this run, so a failure REFUSES and names what was missing. LABTALK_PYTHON
    # is ambient configuration that can go stale in a shell profile, so a
    # failure WARNS BY NAME and continues -- a stale variable should not make
    # the portal unlaunchable, but it must never fail silently either.
    if ($PythonExe) {
        if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
            throw "${Label}: -PythonExe names no file: '$PythonExe'."
        }
        $lack = @($wanted | Where-Object { -not (Test-LabTalkPythonModule -Exe $PythonExe -Module $_) })
        if ($lack.Count -gt 0) {
            throw ("${Label}: the interpreter you named cannot run this -- '$PythonExe' " +
                   "is missing " + ($lack -join ', ') + ".`n" +
                   "           _tkinter cannot be pip-installed; it comes from the base install's tcl/tk.`n" +
                   "           Name one that has it, or drop -PythonExe to let the launcher choose.")
        }
        Write-Host ("{0}: using {1}" -f $Label, $PythonExe)
        return $PythonExe
    }

    if ($env:LABTALK_PYTHON -and (Test-Path -LiteralPath $env:LABTALK_PYTHON -PathType Leaf)) {
        $lack = @($wanted | Where-Object { -not (Test-LabTalkPythonModule -Exe $env:LABTALK_PYTHON -Module $_) })
        if ($lack.Count -gt 0) {
            Write-Warning ("{0}: LABTALK_PYTHON is set to {1}, which is missing {2}. Ignoring it." -f
                           $Label, $env:LABTALK_PYTHON, ($lack -join ', '))
        }
    }

    $ordered = @(
        $env:LABTALK_PYTHON,
        (Join-Path $env:USERPROFILE "anaconda3\python.exe"),
        (Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python312\python.exe"),
        (Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python313\python.exe"),
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
        (Join-Path $RepoRoot ".venv312\Scripts\python.exe")
    )

    $present = @($ordered | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique)
    $report = @()

    foreach ($exe in $present) {
        $missing = @($wanted | Where-Object { -not (Test-LabTalkPythonModule -Exe $exe -Module $_) })
        if ($missing.Count -eq 0) {
            # Write-Host only: this function returns a PATH.
            Write-Host ("{0}: using {1}" -f $Label, $exe)
            return $exe
        }
        $report += ("           {0}  -- missing {1}" -f $exe, ($missing -join ', '))
    }

    if ($present.Count -eq 0) {
        throw "${Label}: no Python interpreter found at all. Set LABTALK_PYTHON to one that has tkinter and PyYAML."
    }

    # NAME EVERY CANDIDATE AND WHAT IT LACKED. The portal's own message said
    # only that tkinter was missing, which is true of most of this list and
    # tells a reader nothing about what to do next.
    throw ("${Label}: no interpreter has " + ($wanted -join ' + ') + ". Tried:`n" +
           ($report -join "`n") + "`n" +
           "           _tkinter cannot be pip-installed -- it comes from the base install's tcl/tk.`n" +
           "           Set LABTALK_PYTHON to a full CPython (Anaconda or python.org) and re-run.")
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
