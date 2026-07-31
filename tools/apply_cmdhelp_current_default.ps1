param(
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path $ProjectRoot
$cmdhelp = Join-Path $root "src\cli\cmdhelp.cpp"

if (!(Test-Path $cmdhelp)) {
    throw "Cannot find $cmdhelp"
}

$backup = "$cmdhelp.before_current_default"
if (!(Test-Path $backup)) {
    Copy-Item $cmdhelp $backup
    Write-Host "Backed up $cmdhelp -> $backup"
}

$text = Get-Content $cmdhelp -Raw

# The current build path needs the HELP DATA bridge.
if ($text -notmatch '#include\s+"helpdata_cmdhelp_bridge\.hpp"') {
    if ($text -match '#include\s+"edref\.hpp"') {
        $text = $text -replace '#include\s+"edref\.hpp"', "#include `"edref.hpp`"`r`n#include `"helpdata_cmdhelp_bridge.hpp`""
        Write-Host "Inserted helpdata_cmdhelp_bridge.hpp include"
    } else {
        throw "Could not find edref.hpp include anchor."
    }
}

# The report helper uses std::istringstream. Some local versions may already get this indirectly,
# but keep the include explicit.
if ($text -notmatch '#include\s+<sstream>') {
    $text = $text -replace '#include\s+<regex>', "#include <regex>`r`n#include <sstream>"
    Write-Host "Inserted <sstream> include"
}

$replacementPath = Join-Path $root "tools\cmdhelp_current_default_cli_block.inc"
if (!(Test-Path $replacementPath)) {
    throw "Cannot find $replacementPath"
}
$replacement = Get-Content $replacementPath -Raw

$start = $text.IndexOf("// === CLI")
if ($start -lt 0) {
    throw "Could not find // === CLI marker in cmdhelp.cpp"
}

$newText = $text.Substring(0, $start) + $replacement
Set-Content -Path $cmdhelp -Value $newText -NoNewline

# Avoid source-glob compilation of old snippets.
Get-ChildItem (Join-Path $root "src\cli") -Filter "cmdhelp_*snippet*.cpp" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $destDir = Join-Path $root "tools"
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        $dest = Join-Path $destDir $_.Name
        Move-Item $_.FullName $dest -Force
        Write-Host "Moved accidental snippet source: $($_.FullName) -> $dest"
    }

Write-Host "Updated CMDHELP dispatch to current HELP DATA default."
Write-Host "Next:"
Write-Host "  cmake --build build --config Release --target dottalkpp"
