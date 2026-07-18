#requires -Version 5.1
<#
  Pinocchio stress-test data generator.

  Emits MCC-shaped CSVs at arbitrary scale into the Pinocchio lane's tmp dir.
  Deterministic (seeded) and streamed, so 1M+ rows generate quickly with flat
  memory. Record 1 is the MCC canary (SID 50000000, Taylor Quinn) so the same
  freshness assertion holds at scale.

  Output (derived, gitignored -- never published):
    <root>/dottalkpp/data/tmp/pinocchio/students.csv
    <root>/dottalkpp/data/tmp/pinocchio/enroll.csv

  Usage:
    .\gen_pinocchio_data.ps1                       # 1,000,000 students
    .\gen_pinocchio_data.ps1 -Students 100000      # 100k warm-up
    .\gen_pinocchio_data.ps1 -Students 1000000 -EnrollMin 3 -EnrollMax 8
#>
param(
  [string] $Root,
  [int]    $Students   = 1000000,
  [int]    $EnrollMin  = 3,
  [int]    $EnrollMax  = 8,
  [int]    $Seed       = 64,
  [string] $OutDir
)

if (-not $Root) {
  # scripts live at <root>/dottalkpp/scripts/pinocchio -> three parents up
  $Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
}
if (-not $OutDir) { $OutDir = Join-Path $Root 'dottalkpp\data\tmp\pinocchio' }
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$studentsCsv = Join-Path $OutDir 'students.csv'
$enrollCsv   = Join-Path $OutDir 'enroll.csv'

$rng = [System.Random]::new($Seed)

$last   = 'Anderson','Brown','Davis','Garcia','Johnson','Martin','Miller','Ramirez','Rodriguez','Smith','Taylor','White','Williams','Wilson'
$first  = 'Alex','Avery','Casey','Drew','Evan','Jordan','Liam','Mason','Mia','Noah','Olivia','Quinn','Reese','Rowan','Skyler','Sophia'
$majors = 'CSCI','MATH','ENGL','HIST','BIOL','CHEM','PHYS','ARTS','BUSN','PSYC','COMM'
$gender = 'M','F','X'
$terms  = 'F25','W26','S26'

Write-Host "Pinocchio generator: $Students students -> $studentsCsv"
$swS = [System.IO.StreamWriter]::new($studentsCsv, $false, [System.Text.Encoding]::ASCII)
$swE = [System.IO.StreamWriter]::new($enrollCsv,   $false, [System.Text.Encoding]::ASCII)
$swS.WriteLine('SID,LNAME,FNAME,DOB,GENDER,MAJOR,ENROLL_D,GPA,EMAIL')
$swE.WriteLine('SID,CLS_ID')

$enrollTotal = 0
for ($i = 0; $i -lt $Students; $i++) {
  $sid = 50000000 + $i
  if ($i -eq 0) { $ln = 'Taylor'; $fn = 'Quinn' }   # canary
  else {
    $ln = $last[$rng.Next($last.Length)]
    $fn = $first[$rng.Next($first.Length)]
  }
  $dob   = '{0:0000}{1:00}{2:00}' -f $rng.Next(1985,2007), $rng.Next(1,13), $rng.Next(1,28)
  $g     = $gender[$rng.Next($gender.Length)]
  $maj   = $majors[$rng.Next($majors.Length)]
  $endt  = '{0:0000}{1:00}{2:00}' -f $rng.Next(2023,2026), $rng.Next(1,13), $rng.Next(1,28)
  $gpa   = '{0:0.00}' -f (2.0 + $rng.NextDouble() * 2.0)
  $email = ('{0}.{1}{2}@student.mcc.edu' -f $fn, $ln, ($i % 100)).ToLower()
  $swS.WriteLine("$sid,$ln,$fn,$dob,$g,$maj,$endt,$gpa,$email")

  $k = $rng.Next($EnrollMin, $EnrollMax + 1)
  for ($j = 0; $j -lt $k; $j++) {
    $term = $terms[$rng.Next($terms.Length)]
    $mj   = $majors[$rng.Next($majors.Length)]
    $num  = 100 + $rng.Next(0, 300)
    $swE.WriteLine("$sid,$term$mj$num")
    $enrollTotal++
  }

  if (($i % 100000) -eq 0 -and $i -gt 0) { Write-Host "  ...$i students" }
}
$swS.Flush(); $swS.Close()
$swE.Flush(); $swE.Close()

Write-Host ""
Write-Host "Done."
Write-Host "  students.csv : $Students rows  ($studentsCsv)"
Write-Host "  enroll.csv   : $enrollTotal rows  ($enrollCsv)"
Write-Host ""
Write-Host "Canary: record 1 must build to SID 50000000 = Taylor Quinn."
Write-Host "Next:  .\run_pinocchio.ps1   (builds x64 + CDX + LMDB, then measures)"
