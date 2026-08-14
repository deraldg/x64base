# regen_site_regression.ps1 -- regenerate the website regression catalog from the
# engine's OWN registry (src/cli/cmd_regression.cpp) so the published page cannot drift
# from what REGRESSION ALL runs. This is the wired doc-push step: run it after
# cmd_regression.cpp changes (or as part of the full-stack flush), then commit the site
# page as its own slice and publish. Idempotent -- it rewrites only the marked block.
#
# Cross-tree by design: the generator lives here (it reads the C++ registry), and writes
# into the site tree. The SITE build stays independent -- it just consumes the committed
# .mdx, so a site-only or CI build never needs this repo present.
#
# Run from D:\code\ccode. stdlib-only Python; no venv needed.
param(
  [string]$Site = 'D:\dev\x64base-site'
)
$ErrorActionPreference = 'Stop'
$sha  = (git rev-parse HEAD).Trim()
$page = Join-Path $Site 'content\docs\engine\regression-and-proof-testing.mdx'
if (-not (Test-Path $page)) { throw "site page not found: $page (pass -Site <path>)" }
python tools\reports\regression_index.py --write-mdx $page --sha $sha
Write-Host "regen: wrote regression catalog into $page  (pinned $sha)"
Write-Host "next: cd $Site; git add content/docs/engine/regression-and-proof-testing.mdx; commit; then npm run build + publish"
