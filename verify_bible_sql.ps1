$ErrorActionPreference = "Stop"

$Root = "D:\code\ccode\dottalkpp\data\bible_kjv_x64_rdbms"

$Required = @(
    "bible_kjv_x64.sqlite",
    "schema.sql",
    "manifest.json",
    "README.md",
    "checksums.sha256",
    "data"
)

Write-Host "Checking Bible seed layout:"
Write-Host "  $Root"
Write-Host ""

foreach ($Item in $Required) {
    $Path = Join-Path $Root $Item
    if (Test-Path $Path) {
        Write-Host "OK      $Item"
    } else {
        Write-Warning "MISSING $Item"
    }
}

$Db = Join-Path $Root "bible_kjv_x64.sqlite"

if (Test-Path $Db) {
    $Info = Get-Item $Db
    $Hash = (Get-FileHash $Db -Algorithm SHA256).Hash.ToLowerInvariant()

    Write-Host ""
    Write-Host "SQLite file:"
    Write-Host "  $Db"
    Write-Host "Size:"
    Write-Host "  $($Info.Length) bytes"
    Write-Host "SHA256:"
    Write-Host "  $Hash"
}

Write-Host ""
Write-Host "DotTalk++ smoke commands:"
Write-Host "  sqlite open data\bible_kjv_x64_rdbms\bible_kjv_x64.sqlite"
Write-Host "  sqlite status"
Write-Host "  sqlite tables"
Write-Host "  sqlite schema verses"
Write-Host "  sqlite select select count(*) as verse_count from verses"
Write-Host "  sqlite select select book_name, chapter_num, verse_num, verse_text from verses where book_name='John' and chapter_num=3 and verse_num=16"