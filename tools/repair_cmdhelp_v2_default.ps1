param(
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path $ProjectRoot

# The previous drop-in accidentally placed a snippet file under src\cli with a
# .cpp extension.  The project glob compiles src\cli\*.cpp, so that snippet was
# built as a standalone translation unit.  It is not standalone source.
$bad = Join-Path $root "src\cli\cmdhelp_v2_default_dispatch_snippet.cpp"
$keep = Join-Path $root "tools\cmdhelp_v2_default_dispatch_snippet.inc"

if (Test-Path $bad) {
    New-Item -ItemType Directory -Force -Path (Split-Path $keep) | Out-Null
    Move-Item $bad $keep -Force
    Write-Host "Moved non-standalone snippet out of src\cli:"
    Write-Host "  $bad"
    Write-Host "  -> $keep"
} else {
    Write-Host "No stray src\cli\cmdhelp_v2_default_dispatch_snippet.cpp found."
}

# Ensure no other accidental cmdhelp snippet .cpp files remain in src\cli.
Get-ChildItem (Join-Path $root "src\cli") -Filter "cmdhelp_*snippet*.cpp" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $dest = Join-Path (Join-Path $root "tools") $_.Name
        Move-Item $_.FullName $dest -Force
        Write-Host "Moved accidental snippet source: $($_.FullName) -> $dest"
    }

Write-Host "Now rebuild:"
Write-Host "  cmake --build build --config Release --target dottalkpp"
