<#
.SYNOPSIS
  Generate the Pinocchio DIMENSION tables (Phase 3c, AIF-167): classes.csv and
  majors.csv, by ENUMERATING the same closed universe gen_pinocchio_data.ps1
  draws CLS_ID from -- 3 terms x 11 majors x 300 numbers = 9,900 classes.

.WHY ENUMERATION, NOT DERIVATION
  The fact generator builds CLS_ID as $term + $major + (100..399), so the
  class universe is CLOSED and known without reading the 5.5M-row ENROLL at
  all: FK integrity (every ENROLL.CLS_ID appears in CLASSES) holds by
  construction, and this script is safe to run WHILE a timed battery holds
  the fixtures -- it touches nothing but tmp CSVs. At ~555 expected
  enrollments per class, the probability any class has zero enrollments is
  vanishingly small; the star battery MEASURES the actual number via the
  LEFT JOIN left-extended report rather than assuming it.

.USAGE
  .\gen_pinocchio_dims.ps1              # writes classes.csv + majors.csv
  Same OutDir convention as gen_pinocchio_data.ps1 (data\tmp\pinocchio).
  Next: run pinocchio_build_dims.dts (CREATE X64 + IMPORT + CDX + LMDB).
#>
param(
  [string] $Root,
  [string] $OutDir
)

if (-not $Root) {
  # scripts live at <root>/dottalkpp/scripts/pinocchio -> three parents up
  $Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
}
if (-not $OutDir) { $OutDir = Join-Path $Root 'dottalkpp\data\tmp\pinocchio' }
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$classesCsv = Join-Path $OutDir 'classes.csv'
$majorsCsv  = Join-Path $OutDir 'majors.csv'

# EXACTLY the fact generator's lists -- change one, change both.
$majors = 'CSCI','MATH','ENGL','HIST','BIOL','CHEM','PHYS','ARTS','BUSN','PSYC','COMM'
$terms  = 'F25','W26','S26'
$names  = @{
  CSCI='Computer Science'; MATH='Mathematics';   ENGL='English';
  HIST='History';          BIOL='Biology';       CHEM='Chemistry';
  PHYS='Physics';          ARTS='Fine Arts';     BUSN='Business';
  PSYC='Psychology';       COMM='Communications'
}

Write-Host "Pinocchio dims generator: enumerating the closed CLS_ID universe"

$swC = [System.IO.StreamWriter]::new($classesCsv, $false, [System.Text.Encoding]::ASCII)
$swC.WriteLine('CLS_ID,TERM,MAJOR,CNUM')
$classTotal = 0
foreach ($term in $terms) {
  foreach ($mj in $majors) {
    for ($num = 100; $num -le 399; $num++) {
      $swC.WriteLine("$term$mj$num,$term,$mj,$num")
      $classTotal++
    }
  }
}
$swC.Flush(); $swC.Close()

$swM = [System.IO.StreamWriter]::new($majorsCsv, $false, [System.Text.Encoding]::ASCII)
$swM.WriteLine('MAJOR,MNAME')
foreach ($mj in $majors) { $swM.WriteLine("$mj,$($names[$mj])") }
$swM.Flush(); $swM.Close()

Write-Host ""
Write-Host "Done."
Write-Host "  classes.csv : $classTotal rows (expect 9900 = 3 terms x 11 majors x 300)  ($classesCsv)"
Write-Host "  majors.csv  : $($majors.Count) rows  ($majorsCsv)"
Write-Host ""
Write-Host "Next: ./datarun.ps1 with pinocchio_build_dims.dts (safe alongside a running battery: new tables only)."
