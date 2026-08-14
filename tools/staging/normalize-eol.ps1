# normalize-eol.ps1 -- one-time line-ending renormalization for D:\code\ccode.
#
# Flushes existing CRLF/LF churn so the working tree matches .gitattributes
# (source LF, Windows tooling CRLF, proof logs binary). Run on a CLEAN tree --
# commit or stash unrelated work first so this is an isolated "normalize" commit.
#
# DRY-RUN by default: it stages the renormalization and shows you what changed,
# but does NOT commit. Review, then re-run with -Execute to commit (or `git reset`
# to undo the staging).
#
#   .\tools\staging\normalize-eol.ps1            # dry run: stage + show
#   .\tools\staging\normalize-eol.ps1 -Execute   # stage + commit

param([switch]$Execute)
$ErrorActionPreference = 'Stop'

$repo = 'D:\code\ccode'
Set-Location -LiteralPath $repo

git rev-parse --is-inside-work-tree > $null
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host "repo   : $repo"
Write-Host "branch : $branch"

if (Test-Path (Join-Path $repo '.git\MERGE_HEAD')) { throw 'A merge is in progress -- resolve it first.' }

$before = (git status --porcelain | Measure-Object).Count
Write-Host "pending changes before renormalize: $before  (ideally commit unrelated work first)"

# 1) stop git from re-introducing CRLF on checkout (the real churn source)
git config core.autocrlf false
Write-Host "set core.autocrlf = false"

# 2) renormalize the whole tree to the .gitattributes policy
git add --renormalize .

# 3) summarize
$staged = @(git diff --cached --name-only)
Write-Host ("`nrenormalized + staged: {0} file(s)" -f $staged.Count)
git diff --cached --stat | Select-Object -Last 12

# 4) CAUTION: the ccode .gitattributes leaves .dts/.csv/.txt as text=auto, so a
#    renormalize can flip them. Verify none are SHA-256-bound before committing.
$data = $staged | Where-Object { $_ -match '\.(dts|csv|txt)$' }
if ($data.Count -gt 0) {
  Write-Host ("`nVERIFY: {0} .dts/.csv/.txt file(s) staged -- confirm none are checksum-bound" -f $data.Count) -ForegroundColor Yellow
  Write-Host "        (proof transcripts under labtalk/proofs/runs/ are already binary-guarded)."
  Write-Host "        If any are SHA-pinned, add a '-text' guard in .gitattributes and re-run."
}

if ($Execute) {
  git diff --cached --quiet
  if ($LASTEXITCODE -eq 0) {
    Write-Host "`nNothing to renormalize -- the index already stores LF." -ForegroundColor Green
    Write-Host "The real fix is done: core.autocrlf = false, so CRLF is no longer reintroduced on" -ForegroundColor Green
    Write-Host "checkout. Commit .gitattributes (and this script) to make the policy durable." -ForegroundColor Green
  } else {
    git commit -m "normalize line endings per .gitattributes; end CRLF/LF churn"
    Write-Host "`nCOMMITTED." -ForegroundColor Green
  }
} else {
  Write-Host "`nDRY-RUN: staged, NOT committed." -ForegroundColor Cyan
  Write-Host "  review : git diff --cached --stat"
  Write-Host "  commit : re-run with -Execute"
  Write-Host "  undo   : git reset"
}
