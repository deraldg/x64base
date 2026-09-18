param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "launch-common.ps1")

$layout = Get-DotTalkLayout -EntryScriptPath $MyInvocation.MyCommand.Path
$dataDir = $layout.RuntimeData
$bibleDb = "bible_kjv_x64_rdbms\bible_kjv_x64.sqlite"
$biblePath = Join-Path $dataDir $bibleDb

Write-Host "DotTalk++ launch directory:"
Write-Host "  $dataDir"
Write-Host ""

if (Test-Path -LiteralPath $biblePath) {
    $info = Get-Item -LiteralPath $biblePath
    Write-Host "Bible SQLite seed found:"
    Write-Host "  $bibleDb"
    Write-Host "  $($info.Length) bytes"
} else {
    Write-Warning "Bible SQLite seed NOT found at: $biblePath"
}

Write-Host ""
Write-Host "Recommended DotTalk++ smoke commands:"
Write-Host "  sqlite cwd"
Write-Host "  sqlite biblecheck"
Write-Host "  sqlite books"
Write-Host "  sqlite verse John 3:16"
Write-Host "  sqlite list verses 5"
Write-Host "  sqlite columns verses"
Write-Host "  sqlite select select count(*) as verse_count from verses"
Write-Host "  sqlite select select ref, text from verses where ref='John 3:16'"
Write-Host "  sqlite select select ref, text from verses where text like '%kingdom of heaven%' limit 10"
Write-Host ""
Write-Host "Note: SQLITE SEARCH uses FTS5 and may require SQLite runtime support."
Write-Host "      The SELECT/LIKE command above is the portable search smoke test."
Write-Host ""

$exitCode = Invoke-DotTalkCliRuntime -EntryScriptPath $MyInvocation.MyCommand.Path -AppArgs $AppArgs
if ($exitCode -ne 0) {
    exit $exitCode
}

# Was a hardcoded build\vcpkg_installed\x64-windows\tools\python3\python.exe --
# a path that has never existed in this tree (that directory holds only Lib,
# measured 2026-09-18), and not the interpreter CLAUDE.md binds to the name
# $py12 in any case.
# One shared resolver now, in launch-common.ps1, which is already dot-sourced
# above.
$py12 = Resolve-DotTalkPython -RepoRoot $layout.RepoRoot -Label 'run-bible pydottalk smoke'
$smoke = Join-Path $layout.RepoRoot "bindings\pydottalk_smoke.py"

Write-Host ""
Write-Host "Running pydottalk smoke:"
Write-Host "  $smoke"
& $py12 $smoke
exit $LASTEXITCODE
