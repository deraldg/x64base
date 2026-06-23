param(
    [string]$OutputPath = "MANIFEST.txt"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$outputFile = Join-Path $repoRoot $OutputPath
$outputRelative = [System.IO.Path]::GetRelativePath($repoRoot, $outputFile).Replace('\', '/')
$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Push-Location $repoRoot
try {
    $trackedFiles = & git -c safe.directory='D:/code/ccode/x64base' -C $repoRoot ls-files
    if ($LASTEXITCODE -ne 0) {
        throw "git ls-files failed with exit code $LASTEXITCODE"
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("Repo manifest: $repoRoot")
    $lines.Add("Generated: $generatedAt")
    $listedFiles = @($trackedFiles | Where-Object { $_ -ne $outputRelative })

    $lines.Add("Tracked file count: $($trackedFiles.Count)")
    $lines.Add("Manifest entry omitted from listing: $outputRelative")
    $lines.Add("")
    $lines.Add("RelativePath => SizeBytes => LastWriteTime")

    foreach ($relativePath in $listedFiles) {
        $fullPath = Join-Path $repoRoot $relativePath
        if (-not (Test-Path -LiteralPath $fullPath)) {
            $lines.Add("$relativePath => (missing) => (missing)")
            continue
        }

        $item = Get-Item -LiteralPath $fullPath
        $stamp = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        $lines.Add("$relativePath => $($item.Length) => $stamp")
    }

    [System.IO.File]::WriteAllLines($outputFile, $lines)
    Write-Host "Wrote manifest: $outputFile"
}
finally {
    Pop-Location
}
