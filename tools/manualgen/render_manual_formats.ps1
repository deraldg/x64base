[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'

$assembled = Join-Path $RepositoryRoot 'docs\manuals\developer\manualgen\generated\assembled'
$markdown = Join-Path $assembled 'developer_manual_assembled_v1.md'
$html = Join-Path $assembled 'developer_manual_v1.html'
$pdf = Join-Path $assembled 'developer_manual_v1.pdf'
$css = Join-Path $RepositoryRoot 'tools\manualgen\manual_render.css'

foreach ($required in @($markdown, $css)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required manual-render input is missing: $required"
    }
}

$pandoc = (Get-Command pandoc -ErrorAction Stop).Source
& $pandoc $markdown `
    '--from=gfm' `
    '--to=html5' `
    '--standalone' `
    '--embed-resources' `
    "--css=$css" `
    '--metadata=pagetitle:DotTalk++ / x64base Developer Manual' `
    "--output=$html"
if ($LASTEXITCODE -ne 0) {
    throw "Pandoc HTML render failed with exit code $LASTEXITCODE"
}

$edgeCandidates = @(
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
)
$edge = $edgeCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1
if (-not $edge) {
    throw 'Microsoft Edge is required for the PDF render but was not found.'
}

$profile = Join-Path $RepositoryRoot '.tmp\edge-manual-render'
New-Item -ItemType Directory -Force -Path $profile | Out-Null
$htmlUri = [Uri]$html
& $edge `
    '--headless' `
    '--disable-gpu' `
    '--no-pdf-header-footer' `
    "--user-data-dir=$profile" `
    "--print-to-pdf=$pdf" `
    $htmlUri.AbsoluteUri
if ($LASTEXITCODE -ne 0) {
    throw "Edge PDF render failed with exit code $LASTEXITCODE"
}

foreach ($artifact in @($markdown, $html, $pdf)) {
    $item = Get-Item -LiteralPath $artifact
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $artifact).Hash
    Write-Output "$($item.Name)`t$($item.Length)`t$hash"
}
