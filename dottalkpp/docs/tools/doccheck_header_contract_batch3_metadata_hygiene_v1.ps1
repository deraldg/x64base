param()

$ErrorActionPreference = "Stop"

Write-Host "SelfDoc Header Batch 3 Metadata Hygiene Checkpoint v1"
Write-Host "Status: HYGIENE_CHECKPOINT_ONLY / REPORT_ONLY"
Write-Host "Permission level: REPORT_ONLY"
Write-Host "Source mutation authorized: no"
Write-Host "Header repair authorized: no"
Write-Host "DBF writes authorized: no"
Write-Host "HELP DATA rebuild authorized: no"
Write-Host "CMDHELPCHK mutation authorized: no"
Write-Host "C:/dottalkpp promotion authorized: no"
Write-Host "Deletion authorized: no"
Write-Host "Header Batch 4 authorized: no"
Write-Host "Working area: $PWD"
Write-Host ""

$DottalkRoot = (Get-Location).Path
$WorkspaceRoot = Split-Path $DottalkRoot -Parent

$OutCsv = ".\docs\generated\reports\header_contract_batch3_metadata_hygiene_v1.csv"
$OutMd = ".\docs\generated\reports\header_contract_batch3_metadata_hygiene_v1.md"
$CheckpointMd = ".\docs\generated\reports\header_contract_batch3_checkpoint_v1.md"
$ProposalMd = ".\docs\generated\proposals\header_contract_batch3_metadata_hygiene_v1.md"

New-Item -ItemType Directory -Force ".\docs\generated\reports" | Out-Null
New-Item -ItemType Directory -Force ".\docs\generated\proposals" | Out-Null

$Batch3Headers = @(
    "include/workspace/relation_state.hpp",
    "include/workspace/schema_area_state.hpp",
    "include/workspace/schema_workspace.hpp",
    "include/workspace/workarea_manager.hpp",
    "include/workspace/workarea_slot.hpp"
)

function To-WindowsRelPath {
    param([string]$Path)
    return ($Path -replace "/", "\")
}

function Get-LineNumber {
    param(
        [string[]]$Lines,
        [string]$Pattern
    )

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match $Pattern) {
            return ($i + 1)
        }
    }
    return ""
}

function Sha256Safe {
    param([string]$Path)
    try {
        if (Test-Path $Path -PathType Leaf) {
            return (Get-FileHash -Algorithm SHA256 $Path).Hash
        }
    } catch {
        return ""
    }
    return ""
}

$outRows = New-Object System.Collections.Generic.List[object]
$seq = 0

foreach ($rel in $Batch3Headers) {
    $seq++
    $src = Join-Path $WorkspaceRoot (To-WindowsRelPath $rel)

    $status = "PASS"
    $reason = ""
    $exists = Test-Path $src
    $hasContract = "False"
    $hasAuthority = "False"
    $hasMutation = "False"
    $hasNotes = "False"
    $hasProposalAuthority = "False"
    $hasSandboxAuthority = "False"
    $contractLine = ""
    $authorityLine = ""
    $mutationLine = ""
    $notesLine = ""
    $hash = ""

    if (-not $exists) {
        $status = "FAIL"
        $reason = "Missing Batch 3 header."
    } else {
        $hash = Sha256Safe $src
        $text = Get-Content $src -Raw
        $lines = @(Get-Content $src)

        if ($text -match "@dottalk\.contract") { $hasContract = "True" }
        if ($text -match "authority:\s*canonical-header-contract") { $hasAuthority = "True" }
        if ($text -match "mutation:\s*token-authorized") { $hasMutation = "True" }
        if ($text -match "notes:\s*canonical contract annotation inserted by guarded SelfDoc apply script") { $hasNotes = "True" }
        if ($text -match "batch3-canonical-mutation-proposal-only") { $hasProposalAuthority = "True" }
        if ($text -match "batch3-sandbox-preview-only") { $hasSandboxAuthority = "True" }

        $contractLine = Get-LineNumber $lines "@dottalk\.contract"
        $authorityLine = Get-LineNumber $lines "authority:\s*canonical-header-contract"
        $mutationLine = Get-LineNumber $lines "mutation:\s*token-authorized"
        $notesLine = Get-LineNumber $lines "notes:\s*canonical contract annotation inserted by guarded SelfDoc apply script"

        if ($hasContract -ne "True") {
            $status = "FAIL"
            $reason = "Missing @dottalk.contract."
        } elseif ($hasAuthority -ne "True") {
            $status = "FAIL"
            $reason = "Missing final canonical authority."
        } elseif ($hasMutation -ne "True") {
            $status = "FAIL"
            $reason = "Missing token-authorized mutation marker."
        } elseif ($hasNotes -ne "True") {
            $status = "FAIL"
            $reason = "Missing guarded apply script notes."
        } elseif ($hasProposalAuthority -eq "True") {
            $status = "FAIL"
            $reason = "Proposal-only authority text leaked into canonical header."
        } elseif ($hasSandboxAuthority -eq "True") {
            $status = "FAIL"
            $reason = "Sandbox-only authority text leaked into canonical header."
        } else {
            $reason = "Canonical metadata verified."
        }
    }

    $outRows.Add([pscustomobject]@{
        Sequence = $seq
        WorkspaceRelativePath = $rel
        Status = $status
        Reason = $reason
        Exists = if ($exists) { "True" } else { "False" }
        HasContract = $hasContract
        HasCanonicalAuthority = $hasAuthority
        HasTokenAuthorizedMutation = $hasMutation
        HasCanonicalNotes = $hasNotes
        HasProposalAuthorityLeak = $hasProposalAuthority
        HasSandboxAuthorityLeak = $hasSandboxAuthority
        ContractLine = $contractLine
        AuthorityLine = $authorityLine
        MutationLine = $mutationLine
        NotesLine = $notesLine
        Sha256 = $hash
        SourceMutationAuthorized = "False"
        HeaderRepairAuthorized = "False"
        DBFWriteAuthorized = "False"
        HelpRebuildAuthorized = "False"
        CmdHelpChkMutationAuthorized = "False"
        PromotionAuthorized = "False"
        DeletionAuthorized = "False"
        HeaderBatch4Authorized = "False"
    })
}

$outRows | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$passRows = @($outRows | Where-Object { $_.Status -eq "PASS" })
$failRows = @($outRows | Where-Object { $_.Status -ne "PASS" })

$applyReport = ".\docs\generated\reports\header_contract_batch3_canonical_apply_script_v1_report.md"
$applyCsv = ".\docs\generated\reports\header_contract_batch3_canonical_apply_script_v1_report.csv"
$applyRows = @()
if (Test-Path $applyCsv) {
    $applyRows = @(Import-Csv $applyCsv)
}
$appliedCount = @($applyRows | Where-Object { $_.Status -eq "APPLIED_CANONICAL_MUTATION" }).Count
$blockedApplyCount = @($applyRows | Where-Object { $_.Status -like "BLOCK_*" }).Count

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Header Contract Batch 3 Metadata Hygiene v1")
$md.Add("")
$md.Add("Status: HYGIENE_CHECKPOINT_ONLY / REPORT_ONLY")
$md.Add("")
$md.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$md.Add("")
$md.Add("Working area: $PWD")
$md.Add("")
$md.Add("Workspace root: $WorkspaceRoot")
$md.Add("")
$md.Add("## Safety Header")
$md.Add("")
$md.Add("Source mutation authorized: no")
$md.Add("Header repair authorized: no")
$md.Add("DBF writes authorized: no")
$md.Add("HELP DATA rebuild authorized: no")
$md.Add("CMDHELPCHK mutation authorized: no")
$md.Add("C:/dottalkpp promotion authorized: no")
$md.Add("Deletion authorized: no")
$md.Add("Header Batch 4 authorized: no")
$md.Add("")
$md.Add("## Verdict")
$md.Add("")
if ($failRows.Count -eq 0) {
    $md.Add("metadata_hygiene_status: PASS")
} else {
    $md.Add("metadata_hygiene_status: FAIL")
}
$md.Add("checked_headers: $($outRows.Count)")
$md.Add("pass_rows: $($passRows.Count)")
$md.Add("fail_rows: $($failRows.Count)")
$md.Add("applied_rows_from_apply_report: $appliedCount")
$md.Add("blocked_rows_from_apply_report: $blockedApplyCount")
$md.Add("")
$md.Add("## Rows")
$md.Add("")
$md.Add("| Seq | Status | Path | Contract | Authority | Mutation | Notes | Reason |")
$md.Add("|---:|---|---|---|---|---|---|---|")
foreach ($r in $outRows) {
    $path = ([string]$r.WorkspaceRelativePath).Replace("|","/")
    $reason = ([string]$r.Reason).Replace("|","/")
    $md.Add("| $($r.Sequence) | $($r.Status) | $path | $($r.HasContract) | $($r.HasCanonicalAuthority) | $($r.HasTokenAuthorizedMutation) | $($r.HasCanonicalNotes) | $reason |")
}
$md.Add("")
$md.Add("## Required Final Metadata")
$md.Add("")
$md.Add("authority: canonical-header-contract")
$md.Add("mutation: token-authorized")
$md.Add("notes: canonical contract annotation inserted by guarded SelfDoc apply script")
$md.Add("")
$md.Add("## Safety Confirmation")
$md.Add("")
$md.Add("- No source files were edited.")
$md.Add("- No header repairs were performed.")
$md.Add("- No DBFs were written.")
$md.Add("- HELP DATA was not rebuilt.")
$md.Add("- CMDHELPCHK was not modified.")
$md.Add("- Nothing was promoted to C:/dottalkpp.")
$md.Add("- No deletion occurred.")
$md.Add("- Header Batch 4 was not authorized.")
$md | Out-File $OutMd -Encoding UTF8

$ck = New-Object System.Collections.Generic.List[string]
$ck.Add("# SelfDoc Header Batch 3 Checkpoint v1")
$ck.Add("")
$ck.Add("Status: CLOSED_CHECKPOINT_CANDIDATE / BUILD-PASSED-PENDING-DOCS-REFRESH")
$ck.Add("")
$ck.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$ck.Add("")
$ck.Add("## Summary")
$ck.Add("")
$ck.Add("SelfDoc Header Batch 3 applied canonical @dottalk.contract annotations to five workspace headers after proposal, sandbox preview, canonical proposal, guarded dry-run, token-authorized apply, metadata verification, and pro-md-Release build.")
$ck.Add("")
$ck.Add("## Files")
$ck.Add("")
foreach ($h in $Batch3Headers) {
    $ck.Add("- $h")
}
$ck.Add("")
$ck.Add("## Verified State")
$ck.Add("")
$ck.Add("Metadata hygiene pass rows: $($passRows.Count)")
$ck.Add("Metadata hygiene fail rows: $($failRows.Count)")
$ck.Add("Apply report applied rows: $appliedCount")
$ck.Add("Apply report blocked rows: $blockedApplyCount")
$ck.Add("")
$ck.Add("## Build Evidence")
$ck.Add("")
$ck.Add("Observed build command:")
$ck.Add("")
$ck.Add("    cmake --build --preset pro-md-Release")
$ck.Add("")
$ck.Add("Observed output artifacts:")
$ck.Add("")
$ck.Add("    D:/code/ccode/build/src/Release/dottalkpp.exe")
$ck.Add("    D:/code/ccode/build/src/tests/Release/dottalkpp_lmdb_backend_smoke.exe")
$ck.Add("")
$ck.Add("## Boundaries Preserved")
$ck.Add("")
$ck.Add("- No header repairs were performed.")
$ck.Add("- No DBFs were written.")
$ck.Add("- HELP DATA was not rebuilt.")
$ck.Add("- CMDHELPCHK was not modified.")
$ck.Add("- Nothing was promoted to C:/dottalkpp.")
$ck.Add("- No deletion occurred.")
$ck.Add("- Header Batch 4 was not authorized.")
$ck.Add("")
$ck.Add("## Next Action")
$ck.Add("")
$ck.Add("Run the documentation pipeline and record final Batch 3 acceptance. Do not start Batch 4.")
$ck | Out-File $CheckpointMd -Encoding UTF8

$prop = New-Object System.Collections.Generic.List[string]
$prop.Add("# Header Contract Batch 3 Metadata Hygiene v1")
$prop.Add("")
$prop.Add("Status: REPORT_ONLY / HYGIENE_CHECKPOINT")
$prop.Add("")
$prop.Add("## Result")
$prop.Add("")
$prop.Add("| Metric | Value |")
$prop.Add("|---|---:|")
$prop.Add("| checked headers | $($outRows.Count) |")
$prop.Add("| pass rows | $($passRows.Count) |")
$prop.Add("| fail rows | $($failRows.Count) |")
$prop.Add("")
$prop.Add("## Safety")
$prop.Add("")
$prop.Add("This report does not edit source files, repair headers, write DBFs, rebuild HELP DATA, modify CMDHELPCHK, promote to C:/dottalkpp, delete files, or authorize Header Batch 4.")
$prop | Out-File $ProposalMd -Encoding UTF8

Write-Host "Header Contract Batch 3 metadata hygiene wrote $OutCsv"
Write-Host "Header Contract Batch 3 metadata hygiene wrote $OutMd"
Write-Host "Header Contract Batch 3 checkpoint wrote $CheckpointMd"
Write-Host "Header Contract Batch 3 metadata hygiene proposal wrote $ProposalMd"
Write-Host "Checked headers: $($outRows.Count)"
Write-Host "Pass rows: $($passRows.Count)"
Write-Host "Fail rows: $($failRows.Count)"
Write-Host "Applied rows from apply report: $appliedCount"
Write-Host "Blocked rows from apply report: $blockedApplyCount"
Write-Host "No source files were edited."
Write-Host "No header repairs were performed."
Write-Host "No DBFs were written."
Write-Host "HELP DATA was not rebuilt."
Write-Host "CMDHELPCHK was not modified."
Write-Host "Nothing was promoted to C:/dottalkpp."
Write-Host "No deletion occurred."
Write-Host "Header Batch 4 was not authorized."
