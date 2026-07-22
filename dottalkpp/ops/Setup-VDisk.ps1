<#
.SYNOPSIS
    Provision (or tear down) the DotTalk++ in-memory virtual disk: a RAM-backed
    volume + the DBF/INDEXES/LMDB junctions that the `DO mem` flavor points at.

.DESCRIPTION
    Windows has no native tmpfs, so an in-RAM volume needs a driver. This script
    uses ImDisk Toolkit (free, scriptable): `imdisk -t vm` creates a RAM disk.
    It then creates <drive>:\dbf, \indexes, \lmdb and junctions
        <DataRoot>\dbf\mem      -> <drive>:\dbf
        <DataRoot>\indexes\mem  -> <drive>:\indexes
        <DataRoot>\lmdb\mem     -> <drive>:\lmdb
    so that `DO mem` (SET PATH DBF DBF/mem, etc.) lands entirely in RAM.

    Size defaults to the engine's Layer-1 auto clamp:
        clamp(25% * available RAM, 64 MB, 2048 MB)  capped at 50% of total RAM.
    Override with -SizeMB.

    PREREQUISITE: install ImDisk Toolkit -> https://sourceforge.net/projects/imdisk-toolkit/
    Driver mount/unmount requires an elevated (Administrator) PowerShell.
    Junction creation does not require admin, but mounting the RAM disk does.

    The RAM disk is volatile: it vanishes on reboot/detach. The junctions persist
    on disk but dangle until this script is re-run — which is the intended
    ephemeral behavior. Re-run after each boot to bring the mem volume back.

.PARAMETER DriveLetter
    Mount point for the RAM disk. Default 'M' (memory). 'X' aligns with the
    x64base brand if you prefer. One letter, no colon.

.PARAMETER SizeMB
    Fixed size in MB. 0 (default) = auto clamp algorithm.

.PARAMETER DataRoot
    The dottalkpp DATA folder (parent of dbf/indexes/lmdb).
    Default: D:\code\ccode\dottalkpp\data

.PARAMETER Remove
    Tear down: remove the junctions and detach the RAM disk.

.EXAMPLE
    # Elevated PowerShell — provision M: at auto size and wire the junctions
    .\Setup-VDisk.ps1

.EXAMPLE
    .\Setup-VDisk.ps1 -DriveLetter X -SizeMB 512

.EXAMPLE
    .\Setup-VDisk.ps1 -Remove
#>

[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z]$')]
    [string]$DriveLetter = 'M',

    [ValidateRange(0, 1048576)]
    [int]$SizeMB = 0,

    [string]$DataRoot = 'D:\code\ccode\dottalkpp\data',

    [switch]$Remove
)

$ErrorActionPreference = 'Stop'
$Drive = $DriveLetter.ToUpper()
$Mount = "${Drive}:"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-AutoSizeMB {
    $os  = Get-CimInstance Win32_OperatingSystem
    $cs  = Get-CimInstance Win32_ComputerSystem
    $availMB = [double]$os.FreePhysicalMemory / 1024.0          # FreePhysicalMemory is KB
    $totalMB = [double]$cs.TotalPhysicalMemory / 1MB
    $budget  = [Math]::Max(0.25 * $availMB, 64.0)               # PERCENT of available, FLOOR
    $budget  = [Math]::Min($budget, 2048.0)                     # CEIL
    $budget  = [Math]::Min($budget, 0.5 * $totalMB)             # HARDCAP: 50% of total
    return [int][Math]::Round($budget)
}

function Remove-JunctionLink([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            # rmdir removes the junction link only, never the target contents.
            cmd /c rmdir "`"$Path`"" | Out-Null
        } else {
            throw "Refusing to touch '$Path': it exists and is NOT a junction (real folder)."
        }
    }
}

# --- junction targets (subfolders of the RAM volume) and link paths (under DATA) ---
$pairs = @(
    @{ Link = Join-Path $DataRoot 'dbf\mem';     Target = "$Mount\dbf" },
    @{ Link = Join-Path $DataRoot 'indexes\mem'; Target = "$Mount\indexes" },
    @{ Link = Join-Path $DataRoot 'lmdb\mem';    Target = "$Mount\lmdb" }
)

# --- imdisk presence check ---
$imdisk = Get-Command imdisk.exe -ErrorAction SilentlyContinue
if (-not $imdisk) {
    Write-Warning "imdisk.exe not found. Install ImDisk Toolkit first:"
    Write-Host   "  https://sourceforge.net/projects/imdisk-toolkit/" -ForegroundColor Yellow
    Write-Host   "  (then re-open an elevated PowerShell and re-run this script)"
    return
}

# ============================ TEARDOWN ============================
if ($Remove) {
    Write-Host "Tearing down mem virtual disk on $Mount ..." -ForegroundColor Cyan
    foreach ($p in $pairs) {
        Remove-JunctionLink $p.Link
        Write-Host "  unlinked $($p.Link)"
    }
    if (-not (Test-Admin)) {
        Write-Warning "Detaching the RAM disk needs an elevated PowerShell. Junctions removed; run elevated to detach $Mount."
        return
    }
    & imdisk -D -m $Mount 2>$null | Out-Null
    Write-Host "  detached $Mount" -ForegroundColor Green
    Write-Host "Done." -ForegroundColor Green
    return
}

# ============================ PROVISION ============================
if (-not (Test-Admin)) {
    Write-Warning "Mounting a RAM disk requires Administrator. Re-run this in an elevated PowerShell."
    return
}

# Guard: DATA root and the three slot parents must exist (we create the mem links, not the tree).
if (-not (Test-Path -LiteralPath $DataRoot)) {
    throw "DataRoot not found: $DataRoot  (pass -DataRoot <path>)"
}
foreach ($slot in @('dbf','indexes','lmdb')) {
    $parent = Join-Path $DataRoot $slot
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
}

if ($SizeMB -le 0) {
    $SizeMB = Get-AutoSizeMB
    Write-Host "Auto size (clamp 25%*avail, floor 64, ceil 2048, <=50% total): $SizeMB MB" -ForegroundColor Cyan
} else {
    # Bound even an explicit override, per the [vdisk] floor/ceil rule.
    $SizeMB = [Math]::Min([Math]::Max($SizeMB, 64), 2048)
    Write-Host "Requested size (bounded to [64,2048]): $SizeMB MB" -ForegroundColor Cyan
}

# If the drive is already a mounted volume, reuse it; else create the RAM disk.
if (Test-Path -LiteralPath "$Mount\") {
    Write-Host "$Mount already present; reusing it (not remounting)." -ForegroundColor Yellow
} else {
    Write-Host "Creating $SizeMB MB RAM disk at $Mount ..." -ForegroundColor Cyan
    & imdisk -a -t vm -s "${SizeMB}M" -m $Mount -p "/fs:ntfs /q /y /v:DOTMEM" | Out-Null
    if (-not (Test-Path -LiteralPath "$Mount\")) { throw "RAM disk mount failed for $Mount." }
    Write-Host "  mounted $Mount" -ForegroundColor Green
}

# Create the target subfolders on the RAM volume.
foreach ($p in $pairs) {
    if (-not (Test-Path -LiteralPath $p.Target)) { New-Item -ItemType Directory -Path $p.Target | Out-Null }
}

# (Re)create the junctions DATA\<slot>\mem -> <drive>:\<slot>.
foreach ($p in $pairs) {
    Remove-JunctionLink $p.Link
    New-Item -ItemType Junction -Path $p.Link -Target $p.Target | Out-Null
    Write-Host "  junction $($p.Link)  ->  $($p.Target)" -ForegroundColor Green
}

Write-Host ""
Write-Host "mem virtual disk ready. In DotTalk++:  DO mem   (then CREATE X64 / USE land in RAM)" -ForegroundColor Green
Write-Host ""
Write-Host "Matching init.ini block:" -ForegroundColor Cyan
@"
[vdisk]
enabled  = 1
root     = $Mount\
mode     = fixed
size_mb  = $SizeMB
floor_mb = 64
ceil_mb  = 2048
warn_pct = 80
on_full  = warn
"@ | Write-Host
