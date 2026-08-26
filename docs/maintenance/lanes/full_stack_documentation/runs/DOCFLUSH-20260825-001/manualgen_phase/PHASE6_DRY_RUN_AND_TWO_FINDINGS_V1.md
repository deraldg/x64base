# v6 Phase 6 -- the dry run, and the useless alarm that was hiding a real one

    Run    : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Phase  : 6, manual candidate (Gate 6). Candidate-only. Nothing published,
             nothing promoted, no publication replaced.
    Status : review-needed. boundary_fail_rows=0. Two findings, section 4 and 5.

## 1. The harvest was stale, exactly as the cookbook warned

`FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V1.md` says: *"If the harvest predates
the Phase-4 rebuild, re-export it so the manual includes new commands."* It did,
and the gap is measurable rather than suspected:

    docs/manuals/developer/manualgen/harvested/   exported 2026-08-25 12:18
      HELP_COMMANDS        460      live store now  462
      HELP_HELP_TOPIC      665                      667
      HELP_HELP_LINE     29262                    29268

Two store rebuilds happened after that export -- 15:36 yesterday and 01:11
tonight. **Running Phase 6 against the canonical harvest would have built a
manual that does not know `DOT|BUILD`, `FOX|FILE`, or the corrected
`BUILD VECTORS` / `BUILD INFO` status.** This is rule 5b of the v6 plan --
*check the freshness stamp of a REF, not just a report* -- and it is the first
time in this lane the check was run before the harm rather than after.

Re-exported to a CANDIDATE workspace (the tool refuses to write `harvested/`
by design: `--out` is documented "NOT the canonical harvested/"):

    tools/fullstack_docs/export_help_meta_harvest.py --repo-root . --out \
      docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260825-001/manualgen_phase/harvest_candidate_v1

    14 tables, 62,570 rows
      HELP_COMMANDS  462   HELP_CMD_ARGS  2368   HELP_HELP_LINE  29268
      HELP_HELP_TOPIC  667   HELP_HELP_ARTIFACTS 14601   HELP_HELP_SECTION 14601
      META_SYSCMD  212   META_SYSARGS  249   META_SYSFUNC  75   (+5 more)

All six HELP counts match the live store read directly from the DBFs. **The nine
META rows are UNCHANGED from the 12:18 export, and that is correct, not
suspicious:** Phase 5's candidate import has not run, so the live metadata tables
have not moved.

## 2. The dry run

    manualgen.py --repo-root . --manual developer \
      --publication-workspace developer_manual_publication_v1_media_section_v1 \
      --harvest-workspace <candidate above>  {inventory,validate,export-manifest,build-dry-run}

    inventory        sections=25 media=19 appendices=13 manifests=5  harvest files=14/14
    validate         validation_fail_rows=1  validation_review_rows=0  boundary_fail_rows=0
    export-manifest  manifests_after_export=5
    build-dry-run    boundary_fail_rows=0
                     dry_run_hash_matches_current_combined=0
                     hash_comparison_status=REVIEW

**`boundary_fail_rows=0` is the cookbook's acceptance condition and it is met.**
All nine boundaries PASS: no publication rebuilt, no published workspace mutated,
no media touched, no x64base tables created, no C++ written, no HELP/META/
CMDHELPCHK mutation.

**The one validation FAIL is named, not counted.** Re-running
`validate_inventory` directly and printing every non-PASS row:

    FAIL  PYTHON_312   value=3.10.12  expected=>= 3.12      24 of 25 PASS

That is the sandbox's interpreter, not the manual -- the documented behaviour
("runs on sandbox 3.10 with only the version self-check failing"). Every harvest
check passed: `HARVEST_SELECTION_VALID`, `HARVEST_REQUIRED_FILES` 14/14,
`HARVEST_CSV_READABLE` 14/14, and `HARVEST_NONEMPTY_*` for every core table.

## 3. Why the hash mismatch had to be opened rather than accepted

`dry_run_hash_matches_current_combined=0` is easy to wave through -- "of course
it differs, the harvest is newer." A raw `diff` seemed to agree: **9,009 of 9,081
lines changed**, which reads as a total rewrite. Both readings are wrong, and the
reason is section 4.

## 4. FINDING ONE -- the two files disagree on LINE ENDINGS, so the hash can never match

    published combined .md   4,489 CRLF lines of 4,597
    build-dry-run .md            0 CRLF lines of 4,484

The published manual is CRLF; the assembler writes LF. **`dry_run_sha256` can
therefore never equal `current_combined_sha256`, whatever the content is.** The
9,009-line diff is almost entirely `\r`.

    diff <(tr -d '\r' < published) <(tr -d '\r' < dry_run)   ->  123 lines, 2 hunks

This is the family this lane keeps naming: **a proxy that cannot answer the
question put to it.** `dry_run_hash_matches_current_combined` was built to answer
"would a rebuild change the manual?" and it answers "do these two files use the
same newline?" -- with the answer permanently no. It joins the build stamp, the
EDREF row count, and the banner's two halves.

It is worse than useless, because of section 5.

## 5. FINDING TWO -- behind the permanent red light, a real 117-line loss

With `\r` removed the diff is two hunks, and only one of them matters:

    3c3,7          header comment block (created_utc, harvest selection) -- expected
    4481,4597d4484 117 lines present in the PUBLISHED manual, ABSENT from the rebuild

Those 117 lines are two whole H1 sections, inserted into the combined file by
marker:

    <!-- MDO-261 MAN* CLI visibility reference insertion start -->
    # MAN* Catalog and Manualgen CLI Visibility Reference
    <!-- MDO-270 MANUAL_MUTATION_CYCLE_REFERENCE_START -->
    # Manual Mutation Cycle and Guarded Publication Workflow

The published manual has 26 H1s; the rebuild produces 24. **A real Phase 6 build
would silently drop both sections.**

**The sources are NOT lost, which makes this a manifest gap rather than data
loss.** Both exist in the publication workspace and neither is in the assembler's
input set:

    manualgen_man_catalog_visibility_reference.md          34 lines, workspace ROOT
    references/manual_mutation_cycle_reference_v1.md       68 lines, references/

The assembler reads `sections/` (1 file), `sections/sections/` (24 files),
`appendices/` (3), media and manifests. It does not read `references/`, and it
does not read loose markdown at the workspace root. 34 + 68 lines of source plus
insertion markers and separators is the 117.

**The two findings compound, and that is the lesson.** An alarm that is red for a
trivial reason is not merely noise -- it is CAMOUFLAGE. Anyone who looked at
`dry_run_hash_matches_current_combined=0`, remembered the newline mismatch, and
moved on would have shipped a rebuild missing two sections. The check was
red for the wrong reason and right for a reason nobody had found.

Two smaller observations inside that tail, recorded and not acted on:

- The MDO-270 block emits `## Manual Mutation Cycle` BEFORE its own
  `# Manual Mutation Cycle and Guarded Publication Workflow` -- an H2 above its H1.
- It carries `Status: DRAFT INSERTION CANDIDATE` in the published manual.

## 6. Phase 6 status

    harvest freshness          FAIL on canonical -> re-exported to candidate, PASS
    inventory                  PASS   25 / 19 / 13 / 5, harvest 14/14
    validate                   PASS   except PYTHON_312 (sandbox interpreter)
    boundary_fail_rows         0      -- the acceptance condition
    build-dry-run              DONE   MANRUN-20260826T012054Z-B9F8B8BD
    hash comparison            REVIEW -- sections 4 and 5

Owner-blocked, and the reason is the same one Phase 5 hit -- `$py12`:

    tools/manualgen/build_postbaseline_supported_command_pages.py:391
        if sys.version_info[:2] != (3, 12): raise SystemExit("Python 3.12.x is required")

An EQUALITY test, so 3.13 would fail it too. The R127 allow-list page generator
and `build_complete_command_reference_index.py` must run on the owner's machine:

```powershell
$py12 = 'C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe'
& $py12 .\tools\manualgen\build_postbaseline_supported_command_pages.py --dry-run
```

**Run the dry run first, always** -- it classifies without writing.

## Good Neighbor

    What changed  : one directory and one document in this run, plus a candidate
                    harvest workspace (14 CSVs) written INSIDE it. The dry-run
                    artifact landed under
                    docs/manuals/developer/manualgen/generated/manualgen_build_dry_runs/
                    MANRUN-20260826T012054Z-B9F8B8BD, which is where the tool's
                    own boundary contract says dry runs write.
                    No published workspace, no media, no HELP, no META, no
                    catalog, no source was touched.
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
                    Section 5 concerns the publication workspace's assembly
                    manifest -- reported, not edited.
    Authorization : the owner's standing instruction to run v6 to the end.
    Verify        : diff <(tr -d '\r' < published.md) <(tr -d '\r' < dry_run.md)
                      expect 2 hunks: 3c3,7 and 4481,4597d4484
                    grep -c $'\r' on each file: 4489 and 0
                    grep -rl 'MDO-261\|MDO-270' on the workspace: the combined
                      .md, and references/manual_mutation_cycle_reference_v1.md
    Undo          : delete manualgen_phase/. The generated dry-run directory is
                    disposable by its own contract.
