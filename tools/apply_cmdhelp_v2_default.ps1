param(
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path $ProjectRoot
$cmdhelp = Join-Path $root "src\cli\cmdhelp.cpp"
$snippetPath = Join-Path $root "src\cli\cmdhelp_v2_default_dispatch_snippet.cpp"

if (!(Test-Path $cmdhelp)) {
    throw "Cannot find $cmdhelp"
}
if (!(Test-Path $snippetPath)) {
    throw "Cannot find $snippetPath"
}

$text = Get-Content $cmdhelp -Raw
$snippet = Get-Content $snippetPath -Raw

$backup = "$cmdhelp.before_v2_default"
if (!(Test-Path $backup)) {
    Copy-Item $cmdhelp $backup
    Write-Host "Backed up $cmdhelp -> $backup"
}

if ($text -notmatch '#include\s+"helpdata_cmdhelp_bridge\.hpp"') {
    $text = $text -replace '#include\s+"edref\.hpp"', "#include `"edref.hpp`"`r`n#include `"helpdata_cmdhelp_bridge.hpp`""
    Write-Host "Inserted helpdata_cmdhelp_bridge.hpp include"
}

if ($text -notmatch '#include\s+<map>') {
    $text = $text -replace '#include\s+<iostream>', "#include <iostream>`r`n#include <map>"
    Write-Host "Inserted <map> include"
}

$start = $text.IndexOf("// === CLI")
$endMarker = "} // namespace cmdhelp"
$end = $text.LastIndexOf($endMarker)

if ($start -lt 0 -or $end -lt 0 -or $end -le $start) {
    throw "Could not find CLI dispatch block markers in cmdhelp.cpp. No changes written."
}

# Include namespace closing marker in replacement because snippet contains it.
$endAfter = $end + $endMarker.Length

$newText = $text.Substring(0, $start) + $snippet + $text.Substring($endAfter)

Set-Content -Path $cmdhelp -Value $newText -NoNewline
Write-Host "Updated $cmdhelp"
Write-Host "Next: cmake --build build --config Release --target dottalkpp"
