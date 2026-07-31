param(
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path $ProjectRoot
$cmdhelp = Join-Path $root "src\cli\cmdhelp.cpp"

if (!(Test-Path $cmdhelp)) {
    throw "Cannot find $cmdhelp"
}

$backup = "$cmdhelp.before_no_v2_wording"
if (!(Test-Path $backup)) {
    Copy-Item $cmdhelp $backup
    Write-Host "Backed up $cmdhelp -> $backup"
}

$text = Get-Content $cmdhelp -Raw
$orig = $text

# Remove user-facing V2 wording in the current builder path.
# This keeps the existing code path intact but stops advertising "V2" as a user-visible mode.
$text = $text -replace 'CMDHELP V2 wrote:', 'CMDHELP wrote:'
$text = $text -replace 'CMDHELP V2', 'CMDHELP'

# If a previous experiment inserted deprecation warning strings, silence them.
$text = $text -replace 'CMDHELP: BUILD V2 is deprecated; V2 is now the default\.\r?\n?', ''
$text = $text -replace 'CMDHELP: use CMDHELP BUILD instead\.\r?\n?', ''

# Avoid accidental source-glob compilation of prior snippets.
Get-ChildItem (Join-Path $root "src\cli") -Filter "cmdhelp_*snippet*.cpp" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $destDir = Join-Path $root "tools"
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        $dest = Join-Path $destDir $_.Name
        Move-Item $_.FullName $dest -Force
        Write-Host "Moved accidental snippet source: $($_.FullName) -> $dest"
    }

if ($text -ne $orig) {
    Set-Content -Path $cmdhelp -Value $text -NoNewline
    Write-Host "Updated user-facing CMDHELP V2 wording in $cmdhelp"
} else {
    Write-Host "No V2 wording replacements were needed in $cmdhelp"
}

Write-Host "Next:"
Write-Host "  cmake --build build --config Release --target dottalkpp"
