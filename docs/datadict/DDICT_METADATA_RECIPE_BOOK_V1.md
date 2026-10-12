# Data dictionary and metadata recipe book

Maintained manual chapter. Owner: member.derald. Reviewed: 2026-10-09.
Scope: development in `D:\code\ccode`; PowerShell 7 and the Release build.

DDICT reports catalog contents inside DotTalk++. There is no separate
`ddict.exe`, and no implemented `DDICT BUILD` command. Compiling the program,
harvesting metadata, and changing catalog rows are separate operations.
Follow the recipes in order for a new baseline; repeat only the affected steps
after a change. Workbench builds can wait; these recipes use the CLI.

## 1. Establish a fresh evidence directory

Run in PowerShell. Each invocation gets its own output directory.

```powershell
Set-Location D:\code\ccode
$repo = 'D:\code\ccode'
$run = Join-Path $repo ('docs\maintenance\reviews\ddict-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $run -ErrorAction Stop | Out-Null
$catalog = Join-Path $repo 'dottalkpp\data\datadict'
$cli = Join-Path $repo 'build\src\Release\dottalkpp.exe'
$probe = Join-Path $repo 'build\src\tests\Release\dottalkpp_ddict_catalog_view_test.exe'
$collector = Join-Path $repo 'build\Release\metacollect.exe'
```

Keep these variables in the same PowerShell session. Report files are new local
evidence; they are not automatically accepted or published. Record the exact
binary hash with each run, not just its modification time.

## 2. Build the consumers and their regression

For an already configured build:

```powershell
cmake --build "$repo\build" --config Release --target dottalkpp metacollect dottalkpp_ddict_catalog_view_test dottalkpp_ddict_catalog_dir_test
if ($LASTEXITCODE -ne 0) { throw 'Build failed; do not use an older executable as proof.' }
Get-FileHash -Algorithm SHA256 $cli,$collector,$probe | Export-Csv "$run\binaries.csv" -NoTypeInformation
```

If metacollect is not configured, enable `DOTTALK_BUILD_METACOLLECT=ON` in the
existing build configuration before building that target. Preserve its other
options. BBS consumers can be rebuilt with target `dottalk_bbsd`; stop the
specific running instance first if it holds the executable open. The maintainer
reported doing that after the October 9 build. `wb` and `wb_next` are separate
GUI targets; successful CLI tests do not certify their deployed executables.

## 3. Dogfood native x64base and check reporting does not write

```powershell
ctest --test-dir "$repo\build" -C Release -R '^dottalkpp_ddict_catalog_(dir|view)_test$' --output-on-failure -V --output-log "$run\regression.log"
if ($LASTEXITCODE -ne 0) { throw 'DDICT regression failed.' }
Select-String -Path "$run\regression.log" -Pattern 'FIXTURES|PASS TOTAL|tests passed'
```

The [native regression](../../src/tests/test_ddict_catalog_view.cpp) creates
disposable x64 DBFs with the engine's writer and native DTX memos. It checks a
long physical filename, a different long logical table name, long field names
sharing the first ten characters, wide values, both catalog families, qualified
identities, typed relations, invalid schemas and memo failures. CLI assertions
invoke the real DDICT handler and capture each command separately. They compare
every fixture catalog file's membership, bytes and write time before and after
reporting, then remove a fixture memo sidecar and assert that reports diagnose
it without recreating it. Fixtures remain under `build/ddict-dogfood/<run>` for
inspection; deliberate corruption there is test data, not live catalog damage.

## 4. Snapshot and inspect the maintained catalog

```powershell
Get-ChildItem -LiteralPath $catalog -File | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{ Name=$_.Name; Bytes=$_.Length; WriteUtc=$_.LastWriteTimeUtc.ToString('o'); SHA256=(Get-FileHash -LiteralPath $_.FullName).Hash }
} | Export-Csv "$run\catalog-before.csv" -NoTypeInformation
& $probe --inspect $catalog > "$run\catalog-inspection.txt"
$inspectionExit = $LASTEXITCODE
Get-Content "$run\catalog-inspection.txt"
```

Inspector exit 0 means its checks passed; 2 means review diagnostics; 1 means
failure. This is a read-only inspection, not a repair. Presence and row counts
do not establish freshness or valid references. The October 9 baseline found
missing memo payloads, space-filled native memo links, and unresolved relation
endpoints. See the [dated proof](../maintenance/reviews/DDICT_CATALOG_VIEW_IMPLEMENTATION_2026-10-09.md).
Re-measure these findings; do not bake those counts into a permanent test.

## 5. Report tables, fields and objects

Start the exact built CLI from its data directory:

```powershell
Push-Location "$repo\dottalkpp\data"
try { & $cli } finally { Pop-Location }
```

At the DotTalk++ prompt:

```text
DDICT HELP
DDICT STATUS
DDICT TABLES
DDICT FIELDS DATA_DICTIONARY_OBJECTS
DDICT OBJECTS FAMILY LEGACY
DDICT OBJECTS FAMILY X64
DDICT OBJECTS TYPE COMMAND PROFILE ENGINE FAMILY X64
```

Verify the displayed active catalog directory. `FIELDS` prints physical field
names and widths for recognized catalog tables, then curated field objects.
`FAMILY` means catalog schema origin; a LEGACY catalog can itself use x64 DBF
storage. The supplemental `DATA_DICTIONARY_*` family is not a replacement copy
of the legacy `DD*` rows. Object listings are bounded to 80; an absent row in a
bounded listing does not prove absence from the database.

For a reproducible DDICT-only report, the test executable exposes the same
handler without starting the full shell. PowerShell:

```powershell
Push-Location "$repo\dottalkpp\data"
try {
    & $probe --command 'STATUS' > "$run\ddict-status.txt"
    & $probe --command 'TABLES' > "$run\ddict-tables.txt"
    & $probe --command 'FIELDS DATA_DICTIONARY_OBJECTS' > "$run\ddict-fields.txt"
    & $probe --command 'OBJECTS FAMILY X64' > "$run\ddict-objects-x64.txt"
} finally { Pop-Location }
```

This proves the linked command handler, not full-shell dispatch. Read the
reports: the handler harness does not make diagnostic text a failing exit code.

## 6. Follow relations, evidence and index metadata

Copy an exact object ID from the object listing. Substitute it for the
placeholder below, including its `x64:` qualification when present.

```text
DDICT REL <object-id> BOTH
DDICT EVIDENCE <object-id>
DDICT TAGS DATA_DICTIONARY_OBJECTS
```

Relations are bounded to 40 per direction; evidence to 20 per section.
`HAS_CATALOG_ATTRIBUTE` edges target attributes, not objects. Source-artifact
IDs and legacy DDSOURCE IDs occupy different identity domains. Memo failure
markers are findings, not decoded prose. `TAGS` separates catalog tag rows from
physical CDX/LMDB presence; a DBF alone is not proof of an index. Neither artifact
presence nor catalog tag prose proves that a physical index is healthy.

## 7. Harvest a small source area into candidate reports

Run the standalone collector from PowerShell, not inside DotTalk++. Start with
one bounded directory; repeat into distinct files for other needed subtrees.

```powershell
& $collector $repo --source-root src/datadict --no-skeleton-marker > "$run\datadict-facts.csv" 2> "$run\datadict-harvest.log"
if ($LASTEXITCODE -ne 0) { throw 'Harvest failed.' }
Get-Content "$run\datadict-harvest.log"
$facts = @(Import-Csv "$run\datadict-facts.csv")
$facts | Group-Object evidence_kind | Select-Object Name,Count
```

For command contracts, repeat using `--source-root src/cli` and a different
output name. Empty results can mean that this subtree has no matching contracts;
check the source and collector warnings. Do not interpret an empty harvest as
an instruction to empty live tables.

For a bounded comparison against metadata:

```powershell
& $collector $repo --source-root src/cli --metadata-root "$repo\dottalkpp\data\metadata" --compare --compare-out "$run\cli-compare.csv" > "$run\cli-facts.csv" 2> "$run\cli-compare.log"
if ($LASTEXITCODE -ne 0) { throw 'Comparison failed.' }
if (!(Test-Path "$run\cli-compare.csv")) { throw 'Comparison output missing.' }
Get-Content "$run\cli-compare.log"
Import-Csv "$run\cli-compare.csv" | Format-Table -AutoSize
```

A partial source slice compared with broader metadata naturally has coverage
gaps. Label its scope and compare members, not totals. Collector exit 0 can
accompany comparison issues or output-write warnings; inspect both artifacts
and stderr. These CSVs are evidence candidates, never automatic deletions.

## 8. Generate metadata import candidates

```powershell
& $collector $repo --no-source --source-root src/cli --sysargs-include-keywords --syscmd-import-out "$run\syscmd-candidate.csv" --sysfunc-import-out "$run\sysfunc-candidate.csv" --sysargs-import-out "$run\sysargs-candidate.csv" > "$run\seed-facts.csv" 2> "$run\seed-export.log"
if ($LASTEXITCODE -ne 0) { throw 'Candidate export failed.' }
foreach ($name in 'syscmd','sysfunc','sysargs') {
    $path = Join-Path $run ($name + '-candidate.csv')
    if (!(Test-Path $path)) { throw "Missing candidate: $path" }
    $rows = @(Import-Csv $path)
    if ($rows.Count -eq 0) { throw "Empty candidate requires investigation: $path" }
    [pscustomobject]@{ Candidate=$name; Rows=$rows.Count }
}
Get-Content "$run\seed-export.log"
```

Scope caveat: seed exporters have independent collection paths. SYSCMD now
honors explicit `--source-root` values for both registrations and contracts.
The example is a CLI slice; include other specific source roots only when
their coverage is needed, and label the scope. SYSARGS reads `src/cli`; SYSFUNC
uses its compiled registry. `--no-source` suppresses the ordinary fact harvest,
not the seed export work. The source-root filter does not constrain SYSARGS or
SYSFUNC. Validate SYSARGS with `validate_sysargs_candidate.py` and pass the
SYSCMD candidate from the same invocation using `--syscmd-candidate`.
Review the [metacollect runbook](../maintenance/lanes/full_stack_documentation/METACOLLECT_RUNBOOK_V1.md)
before importing. SYSCMD/SYSFUNC/SYSARGS describe command/function/argument
metadata; they do not populate DDICT object and evidence tables automatically.

## 9. Build a HELP candidate and validate it

In a fresh CLI session, substitute a NEW absolute candidate directory for the
example path. This writes HELP candidate DBFs and sidecars; it is not read-only.

```text
CMDHELP USAGE
CMDHELP BUILD D:\code\ccode\build\help-ddict-candidate-UNIQUE D:\code\ccode\src\cli
CMDHELPCHK ARTIFACTS D:\code\ccode\build\help-ddict-candidate-UNIQUE 20
```

Use explicit output and source roots. Do not reuse `UNIQUE` literally or target
`dottalkpp/data/help`. This is a partial CLI-source candidate, not a complete
replacement HELP catalog. Validate generated members and representative DDICT
usage text. `CMDHELP BUILD LEGACY` produces the compatibility surface and is not
the normal HELP DATA build. Source syntax and deployed HELP can disagree until
their separately reviewed update has happened.

Read/report commands in the normal CLI:

```text
HELP DDICT
CMDHELP DDICT
CMDHELPCHK REF
MANUAL STATUS
MANUAL TABLES
MANUAL COUNTS
MANUAL SECTIONS
```

The MANUAL command reads its runtime catalog. Adding this chapter to the source
manual does not rebuild MAN* tables or generated Word/PDF/publication bundles.

## 10. Rebuild or repair the dictionary deliberately

There is no verified single end-to-end DDICT refresh command. The historical
orchestrator can emit planned or blocked stages; those reports do not mean it
rebuilt a catalog. Use the [tool guide](../../tools/datadict/README.md) to choose
the exact extractor, reconciliation or promotion stage needed for a specific
source and destination.

1. Name the input revision, accepted schema, source scope, row identities and
   destination family. Preserve long names in native x64 DBF/X64M metadata.
2. Produce candidates outside the live directory. Use native x64base creation
   and memo APIs; never squeeze long fields into classic ten-character names.
3. Validate required fields, duplicate identities, typed edge endpoints, memo
   payloads and representative values. Run recipes 3-6 against the candidate
   using the inspector's explicit path and an isolated `data/datadict` home.
4. Compare candidate and live members. Review additions, updates, deletions,
   evidence lineage and index consequences. Snapshot matched DBF/DTX pairs and
   all affected index artifacts, with a concrete restore procedure.
5. Apply only the approved candidate using its reviewed loader, then close and
   reopen with native x64base and re-read the same values and memo payloads.
   Rebuild only the affected indexes and verify known-key lookup/order behavior.
6. Capture the resulting dictionary, HELP and MANUAL reports and their hashes.
   Report development, staging and publication states separately.

A missing DTX payload cannot be reconstructed from its numeric memo link.
Recover a matched backup or regenerate from traceable original evidence.
Space-filled native M8 links are invalid; do not silently turn them into NULL.
Do not copy legacy rows into supplemental tables or remove nested duplicate
directories as a substitute for schema-aware reconciliation.

## 11. Close the reporting run

After read-only reporting, snapshot again and compare all properties:

```powershell
Get-ChildItem -LiteralPath $catalog -File | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{ Name=$_.Name; Bytes=$_.Length; WriteUtc=$_.LastWriteTimeUtc.ToString('o'); SHA256=(Get-FileHash -LiteralPath $_.FullName).Hash }
} | Export-Csv "$run\catalog-after.csv" -NoTypeInformation
$changes = @(Compare-Object (Import-Csv "$run\catalog-before.csv") (Import-Csv "$run\catalog-after.csv") -Property Name,Bytes,WriteUtc,SHA256)
if ($changes.Count) { $changes; throw 'Catalog changed during reporting; investigate ownership and cause.' }
```

This covers direct catalog files only. Record separate evidence for any indexes
you intentionally changed. Closeout should name binaries, source revision,
catalog paths, scopes, diagnostics, test results, retained candidates and any
unverified stages. An unchanged catalog can still contain pre-existing defects.

## 12. Build the native Portal/manual/website feed

Run this complete PowerShell block from any directory. It writes a new candidate
workspace, without changing live catalogs. Exit 2 means a valid report with
review findings, not a clean catalog. Reusing an output directory is refused.

```powershell
Set-Location D:\code\ccode
$repo = 'D:\code\ccode'
$py12 = "$repo\.venv312\Scripts\python.exe"
$out = "$repo\docs\maintenance\reviews\ddict-feed-" + [guid]::NewGuid().ToString('N')
cmake --build "$repo\build" --config Release --target ddict_export
if ($LASTEXITCODE -ne 0) { throw 'Native exporter build failed.' }
& $py12 "$repo\tools\datadict\catalog\ddict_feed.py" build --repo-root $repo --executable "$repo\build\src\Release\ddict_export.exe" --catalog "$repo\dottalkpp\data\datadict" --out $out
if ($LASTEXITCODE -eq 1) { throw 'Feed generation failed.' }
& $py12 "$repo\tools\datadict\catalog\ddict_feed.py" check --repo-root $repo --out $out
```

`DDICT_MANIFEST.json` binds native JSON, identity crosswalk, classified
diagnostic disposition, Markdown and HTML to source members, hashes, binary and
producer versions. The Portal's current
feed pointer selects one workspace. Manualgen recognizes this optional companion
inside an explicitly selected HELP/META harvest directory. The assembled manual
reads the current pointer and includes both the maintained recipe and the
validated dictionary candidate; it does not accept or publish either.

The website candidate producer is
`tools/fullstack_docs/build_ddict_website_candidate.py --out <new-directory>`.
It reads the current dictionary pointer and produces internal candidates only.
See the [feed contract](contracts/DDICT_FEED_CONTRACT_V1.md) for identity, memo,
freshness and promotion rules. SYSARGS candidate v2 now uses
`ARG:COMMAND:<owner>:<KEYWORD|PLACEHOLDER>:<name>`; existing live IDs are unchanged.

## Source and proof map

- [DDICT command](../../src/cli/cmd_ddict.cpp), `cmd_DDICT` and report functions.
- [Shared catalog view](../../src/datadict/ddict_catalog_view.cpp), schema and memo adapter.
- [Collector entrypoint](../../src/tools/metacollect_main.cpp) and
  [collector](../../src/meta/metacollect.cpp), flags and independent export scopes.
- [CMDHELP](../../src/cli/cmdhelp.cpp) and
  [CMDHELPCHK](../../src/cli/command_helpchk.cpp), candidate build and validation.
- [MANUAL](../../src/cli/cmd_manual.cpp), runtime catalog reports.
- [October 9 regression evidence](../maintenance/reviews/DDICT_RECIPE_REGRESSION_2026-10-09.json).

Commands are source-evidenced unless a linked proof records their execution.
Candidate generation and live catalog promotion were not performed to write
this chapter. The regression runs native x64base against disposable fixtures.
