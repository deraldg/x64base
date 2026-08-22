param(
    [ValidateSet('Debug','Release')]
    [string]$Config = 'Release',

    [string]$PythonExe = '',

    [string]$VcpkgRoot = $env:VCPKG_ROOT,

    [string]$VcpkgTriplet = 'x64-windows',

    # House default on Windows. NOT a hard requirement -- the module builds and
    # imports on other versions (proven on 3.10 under Linux, 2026-08-17). A
    # mismatch warns rather than blocks. Pass '' to silence.
    [string]$ExpectPythonVersion = '3.12',

    # Build directory for the LEAN configure. Deliberately NOT build-labtalk:
    # that tree belongs to the root build, and sharing it would mean this
    # configure and that one overwrite each other's cache.
    [string]$BuildDir = '',

    # Escape hatch. Uses the root build (build.ps1 -WithPyDotTalk), which also
    # builds dottalkpp.exe. Keep it for the case where a smoke needs the CLI.
    [switch]$ViaRootBuild,

    [switch]$Clean
)

# ============================================================================
# build_pydottalk.ps1 -- build the Python module, and ONLY the Python module.
#
# WHAT CHANGED 2026-08-17
#   This used to call build.ps1 -WithPyDotTalk, which configured the whole tree
#   and then ran `cmake --build --target dottalkpp pydottalk`. Producing a
#   4-source module therefore also built dottalkpp.exe (~400 cmd_*.cpp), plus
#   dottalk_tvui.lib and the tvision vcpkg package, because `tv` is on by
#   default in build.ps1 and this wrapper never passed -NoTV.
#
#   pydottalk links xbase, memo and xindex. It references dottalkpp, tvision
#   and dottalk_tvui zero times. So the default is now the lean standalone
#   configure in bindings/pydottalk/CMakeLists.txt, which builds those three
#   libraries and the module and nothing else.
#
#   -ViaRootBuild restores the old behaviour. It is kept rather than deleted
#   because some smokes may want dottalkpp.exe present; if one does, that is a
#   real dependency and should be found by running them, not assumed away.
# ============================================================================

$ErrorActionPreference = "Stop"

# Lives at the REPO ROOT, beside build.ps1 / build-labtalk.ps1 / build_help.ps1
# / build_website.ps1 -- every other build entry point is here, and this one sat
# in bindings\ only because that is where pydottalk was moved to. Moved
# 2026-08-17 so `.\build_pydottalk.ps1` works the same way as its siblings.
$RepoRoot    = Split-Path -Parent $MyInvocation.MyCommand.Path
$BindingsDir = Join-Path $RepoRoot "bindings"
$ProjectDir  = Join-Path $BindingsDir "pydottalk"

if (-not $BuildDir) { $BuildDir = Join-Path $RepoRoot "build-pydottalk" }

# ---- Python ---------------------------------------------------------------
if (-not $PythonExe) {
    # The @( ) around the WHOLE pipeline is load-bearing, not style.
    #
    # Where-Object returns a bare STRING when exactly one item survives, and
    # indexing a string yields a CHARACTER. The previous version of this script
    # did `$candidates[0]` on that result and resolved $PythonExe to "D" -- the
    # first letter of D:\code\... . CMake was then handed
    # -D Python3_EXECUTABLE=D, silently ignored it, fell back to the system
    # Python 3.13.5, and failed with "Could NOT find Python3 (missing:
    # Development)" -- an error naming the wrong problem entirely.
    # Measured 2026-08-17.
    # ORDER MATTERS, and the first entry is the one that was missing.
    #
    # Measured 2026-08-17: build-labtalk\vcpkg_installed\x64-windows\tools\
    # contains ONLY pkgconf -- there is no python3 there. The interpreter this
    # project actually builds against lives in the vcpkg ROOT install, which
    # .venv312\pyvenv.cfg names outright:
    #
    #     home       = C:\Users\deral\vcpkg\installed\x64-windows\tools\python3
    #     version    = 3.12.9
    #
    # With that path absent from the list, the only survivor was the PATH
    # python (3.13.5), which is both the wrong version and -- being a single
    # survivor -- the reason the pipeline collapsed to a string.
    $pythonCandidates = @(
        @(
            $(if ($VcpkgRoot) { Join-Path $VcpkgRoot "installed\$VcpkgTriplet\tools\python3\python.exe" }),
            (Join-Path $RepoRoot "build-labtalk\vcpkg_installed\$VcpkgTriplet\tools\python3\python.exe"),
            (Join-Path $RepoRoot "build\vcpkg_installed\$VcpkgTriplet\tools\python3\python.exe"),
            $env:PYDOTTALK_PYTHON,
            $env:PY12,
            # 3.12.9, based on the vcpkg python above, so FindPython3 resolves
            # Development through its base prefix. Host-tool venv by charter, but
            # a valid fallback when the base install is not reachable directly.
            (Join-Path $RepoRoot ".venv312\Scripts\python.exe"),
            (Join-Path $RepoRoot "pycrud\.venv\Scripts\python.exe"),
            # LAST on purpose: whatever is on PATH is the 3.13 trap. The version
            # assertion below is what stops it rather than this ordering alone.
            (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    )

    if ($pythonCandidates.Count -gt 0) { $PythonExe = $pythonCandidates[0] }
}

# Assert the SHAPE of what we resolved, not merely that it is truthy. "D" is
# truthy. A path that does not exist, or is not a python executable, must fail
# here with a message that names the value -- not 80 lines later inside CMake.
if (-not $PythonExe) {
    throw "No Python executable resolved for pydottalk. Set PYDOTTALK_PYTHON, PY12, or pass -PythonExe."
}
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "Resolved PythonExe is not a file: '$PythonExe'. Pass -PythonExe with a full path to python.exe."
}
if ([IO.Path]::GetFileName($PythonExe) -notlike 'python*.exe') {
    throw "Resolved PythonExe does not look like a Python interpreter: '$PythonExe'."
}

# ---- Report the interpreter, and WARN on a surprise ------------------------
# The house default on Windows is 3.12 and the artifact ships as
# cp312-win_amd64.pyd -- but the module is NOT limited to 3.12. Corrected
# 2026-08-17 by the owner ("if it has run with 3.8 python, not a limitation"),
# and demonstrated the same day: a Linux build of this same source produced
# pydottalk.cpython-310-x86_64-linux-gnu.so, which imported and reported
# `pydottalk 0.4.0` under Python 3.10.
#
# So the danger was never "a version other than 3.12". It was a SILENT swap: a
# bad -D Python3_EXECUTABLE made CMake fall back to whatever python was on PATH
# (3.13.5, no Development component), and the error blamed the missing
# component rather than the wrong interpreter. The worse variant is a 3.13 WITH
# headers, which configures happily and emits a cp313 artifact that every 3.12
# caller then fails to import.
#
# A loud line fixes that. Blocking was an over-correction: it would refuse
# legitimate builds on any other interpreter, and the maintainer knows their
# environment better than this script does. Pass -ExpectPythonVersion '' to
# silence the warning entirely.
$pyVersion = (& $PythonExe -c "import sys; print('{}.{}'.format(*sys.version_info[:2]))" 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $pyVersion) {
    throw "Could not query the Python version from '$PythonExe'."
}
$pyVersion = $pyVersion.Trim()
Write-Host "PythonVer  : $pyVersion"

if ($ExpectPythonVersion -and $pyVersion -ne $ExpectPythonVersion) {
    Write-Warning ("Building against Python $pyVersion, not the house default " +
        "$ExpectPythonVersion. That is allowed -- the module is not pinned to one " +
        "version -- but the artifact will carry a cp$($pyVersion -replace '\.','') " +
        "tag and only that interpreter will import it. Resolved from: '$PythonExe'. " +
        "If this was not deliberate, pass -PythonExe explicitly.")
}

Write-Host "BindingsDir: $BindingsDir"
Write-Host "RepoRoot   : $RepoRoot"
Write-Host "PythonExe  : $PythonExe"

# ---- Escape hatch: the old, heavy path -------------------------------------
if ($ViaRootBuild) {
    Write-Host "Mode       : ROOT BUILD (also builds dottalkpp.exe)" -ForegroundColor Yellow
    $BuildScript = Join-Path $RepoRoot "build.ps1"
    & $BuildScript -Config $Config -WithPyDotTalk `
        -BuildDir (Join-Path $RepoRoot "build-labtalk") -PythonExe $PythonExe
    exit $LASTEXITCODE
}

# ---- Lean path -------------------------------------------------------------
Write-Host "Mode       : LEAN (module only -- no CLI, no TUI, no BBS)" -ForegroundColor Green
Write-Host "ProjectDir : $ProjectDir"
Write-Host "BuildDir   : $BuildDir"

if ($Clean -and (Test-Path -LiteralPath $BuildDir)) {
    Write-Host "Removing $BuildDir ..."
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

$cmakeArgs = @(
    '-S', $ProjectDir,
    '-B', $BuildDir,
    '-D', "CMAKE_BUILD_TYPE=$Config",
    '-D', "VCPKG_TARGET_TRIPLET=$VcpkgTriplet",
    '-D', "Python3_EXECUTABLE=$PythonExe"
)

# The toolchain carries pybind11 and lmdb. Without it the configure fails at
# find_package(pybind11) with a message that does not mention vcpkg, so say so
# here rather than letting the user decode it later.
if ($VcpkgRoot) {
    $toolchain = Join-Path $VcpkgRoot 'scripts\buildsystems\vcpkg.cmake'
    if (Test-Path -LiteralPath $toolchain) {
        $cmakeArgs += @('-D', "CMAKE_TOOLCHAIN_FILE=$toolchain")
        Write-Host "vcpkg      : $toolchain"
    } else {
        Write-Warning "vcpkg toolchain not found at $toolchain -- pybind11 and lmdb may not resolve."
    }
} else {
    Write-Warning "VCPKG_ROOT not set -- pybind11 and lmdb may not resolve. Pass -VcpkgRoot."
}

Write-Host ">>> Configuring (lean) ..."
& cmake @cmakeArgs
if ($LASTEXITCODE -ne 0) { throw "CMake configure failed ($LASTEXITCODE)." }

Write-Host ">>> Building target pydottalk ..."
& cmake --build $BuildDir --config $Config --target pydottalk
if ($LASTEXITCODE -ne 0) { throw "Build failed ($LASTEXITCODE)." }

$pyd = Get-ChildItem -Path (Join-Path $BuildDir "python") -Filter "pydottalk*.pyd" -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($pyd) {
    Write-Host ("Built OK: {0}" -f $pyd.FullName) -ForegroundColor Green
    Write-Host ("PYDOTTALK_BIN={0}" -f $pyd.DirectoryName)
} else {
    # Do not report success without the artifact. A zero exit code is not proof.
    throw "Build reported success but no pydottalk*.pyd was found under $BuildDir\python."
}
