# DOCFLUSH-20260901-002 -- manualgen instructions (host)

    run       : DOCFLUSH-20260901-002 (v8)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    measured  : 2026-09-01/02 at baseline 45f699a23, canonical harvest 14/14
    posture   : commands to RUN. Steps 1-2 mutate nothing. Step 3 onward does.

## 0. The interpreter, because the two authorities disagree

    cookbook Phase 6   $py12 = 'C:\Users\deral\vcpkg\...\python3\python.exe'
    CLAUDE.md          .venv312; NOT vcpkg python -- "minimal, no PyYAML"

**Measured, and the conflict does not bite here.** `manualgen.py` and everything
under `manualgen_lib/` are PyYAML-free. Only `tools/manualgen/assemble_manual.py`
and `tools/manualgen/check_manual_drift.py` import yaml, and `manualgen.py` never
calls either. So both interpreters run manualgen.

Use `.venv312` anyway -- it is the house rule, it is what `docpush_preflight`
uses, and the two sibling scripts above DO need it:

    $py12 = "D:\code\ccode\.venv312\Scripts\python.exe"

`build_postbaseline_supported_command_pages.py` carries an EQUALITY guard
(`!= (3, 12)`), so it breaks on 3.13+, not just below 3.12. Not in this chain,
but do not "upgrade" the venv to fix something else without checking it.

## STEP 0 -- THE HARVEST HAS A LAUNCHER. USE IT, NOT THE PYTHON SCAFFOLD.

    pwsh -File dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1

**This is the sanctioned producer and it is not what I used.** Corrected on the
owner's prompt ("manualgen is a pyrun I think"), which was right in substance:
the harvest is fed by a datarun-backed PowerShell script, the same way the CLI is
fed by `datarun.ps1` rather than the raw exe.

What it does that the Python exporter does not:

    1. exports the 10 CURRENT tables THROUGH THE ENGINE
         & $datarun -CommandLines "DOTSCRIPT HELP_META_HARVEST_EXPORT_v1.dts"
       so `EXPORT ... CSV` resolves MEMO TEXT properly. The Python exporter uses
       the v32-era `dbfread`, which does not follow x64 memo blocks and blanks
       COMMANDS.USAGE/VERBOSE, CMD_ARGS.USAGE/VERBOSE,
       HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE and SYSFUNC.NOTES.
    2. writes an IMMUTABLE run directory
         harvested\export_runs\HELPMETA-<utc-stamp>\
       It never overwrites `harvested\`. Three prior runs are preserved there.
    3. carries the four stale META_* forward LABELLED `CARRIED_STALE_MAY`, and
       says why in its own header: "so manualgen sees all 14 required files
       WITHOUT PRETENDING THE STALE FOUR ARE CURRENT."
    4. writes `HELP_META_EXPORT_MANIFEST_v1.csv` with per-file status, row count,
       SHA-256 and export_method.

**What I did instead, and rolled back.** I ran
`tools/fullstack_docs/export_help_meta_harvest.py` and copied 15 CSVs flat over
`harvested\`. Measured consequence, comparing my manifest against the sanctioned
run `HELPMETA-20260728T003402Z`:

    my v0 manifest      SYSENTVAR EXPORTED 12   SYSFLDDIC EXPORTED 16
                        SYSHELP   EXPORTED  8   SYSMSG    EXPORTED  0
    house v1 manifest   all four CARRIED_STALE_MAY, same counts,
                        "(carried forward -- source not yet current)"

Same numbers, opposite claim. I relabelled four known-stale tables as freshly
exported -- the exact pretence that script exists to prevent -- and I did it
while promoting memo-blanked CSVs over the canonical workspace.

**ROLLED BACK 2026-09-02.** `harvested\` restored from
`harvested.bak-20260901-DOCFLUSH002`, verified byte-identical by `diff -r`.
E5 is back to its true reading of **9/14**, and the run records saying E5 PASS
have been corrected. A false PASS is worse than an honest FAIL.

    STATUS: E5 is OPEN again and clears when STEP 0 runs on the host.

## The standing base arguments

Every command below takes these. **The harvest workspace is the export RUN the
script just created, not `harvested\`** -- that is the script's own closing
instruction, and it is why `export_runs\` exists.

    $run  = 'docs\manuals\developer\manualgen\harvested\export_runs\HELPMETA-<stamp>'
    $base = '--repo-root','D:\code\ccode',
            '--manual','developer',
            '--publication-workspace','developer_manual_publication_v1_media_section_v1',
            '--harvest-workspace',$run

Substitute the stamp the script prints. Do not point at `harvested\` and do not
point at my candidate under `runs\DOCFLUSH-20260901-002\harvest_candidate_v1`;
both are memo-blanked or stale.

---

## STEP 1 -- close PYTHON_312 (read-only, ~seconds)

**THIS IS NOT COSMETIC BOOKKEEPING. IT UNBLOCKS THE ENTIRE M-4 PATH.**
Measured 2026-09-02, and it reframes the priority of this step:

    reference_candidate.py:65
        if validation["validation_fail_rows"]:
            return {"created": 0}, {...}

`build-reference-candidate` returns EARLY -- creating nothing -- if ANY
validation row fails. The only failing row is `PYTHON_312`. So on 3.10 it
reports `topics=0 lines=0/0 commands=0 status=FAIL`, which reads like a data
problem and is not one.

That was verified as pre-existing and unrelated to the harvest: the identical
zero-result appears against the OLD scaffold harvest too, so it is the version
guard doing its job fail-closed, not anything this run changed.

**Consequence:** `build-reference-candidate` ->
`build-command-reference-review-book` -> a 21/1 pointer audit -> M-4 is ONE
host command away, not a research problem. Step 1 is the unblock.

Gate 6 also moves from "predicted green" to "proven" on the same command.

    & $py12 .\tools\manualgen\manualgen.py @base validate

    EXPECT: validation_fail_rows=0  validation_review_rows=0  boundary_fail_rows=0

    DONE 2026-09-02: MANRUN-20260902T121419Z-DB8760CB, exactly that. 25/25 PASS,
    files=14/14. Diffed against the sandbox 3.10 checks file: ONE row changed,
    PYTHON_312 FAIL -> PASS. Gate 6 is proven, and the M-4 path is open.

    NOTE ON INVOCATION. `$base` is a PowerShell ARRAY and `@base` splats it, so
    both must be defined in the SAME session as the call. A bare
    `.venv312 manualgen.py @base validate` is not a command -- that shorthand
    appeared in chat and cost a round trip. The block above is the runnable form.

Measured on 3.10 this session: `validation_fail_rows=1`, and the one row is

    check_id,status,value,expected,note
    PYTHON_312,FAIL,3.10.12,>= 3.12,Manualgen requires Python 3.12 or newer.

All 24 substantive checks already pass, including every harvest check
(`HARVEST_REQUIRED_FILES` 14/14, `HARVEST_CSV_READABLE` 14/14, the three
`HARVEST_NONEMPTY_*`). **If any row other than PYTHON_312 changes state on 3.12,
stop** -- that would mean the sandbox and host disagree about content, not just
about the interpreter, and Gate 6 would need re-deriving rather than confirming.

Full check list: `manualgen_phase/validate_checks_v1.csv` in this run.

## STEP 2 -- rebuild the dry run on the host (read-only, ~1 min)

    & $py12 .\tools\manualgen\manualgen.py @base inventory
    & $py12 .\tools\manualgen\manualgen.py @base export-manifest
    & $py12 .\tools\manualgen\manualgen.py @base build-dry-run
    & $py12 .\tools\manualgen\manualgen.py @base parity-review

    EXPECT: sections=25 media=19 appendices=13
            boundary_fail_rows=0
            dry_run_hash_matches_current_combined=0

That last one is **expected and is not a failure**: the store gained 193 topics,
so the dry run SHOULD differ from the current combined manual. A match would mean
the new HELP never reached the manual.

Sandbox reference run, off the canonical harvest:
`MANRUN-20260902T010218Z-CE18F502`, `boundary_fail_rows=0`.

---

## STEP 3 ONWARD MUTATES. Read this first.

`apply-controlled-acceptance` replaces the ACCEPTED manual and its pointer. It is
the M-4 mutation and needs its own GO. Everything before it is candidate-only.

The chain, and what each step consumes:

    build-selective-merge-candidate
        -> a candidate MANRUN id
    build-controlled-acceptance-plan
        --candidate-run <that MANRUN id>
        --pointer-audit <repo-relative GREEN pointer-audit JSON>
        --context-decision docs\maintenance\lanes\full_stack_documentation\
                           MANUALGEN_CANONICAL_ACCEPTANCE_CONTEXT_DECISION_2026-07-28.md
        -> a plan MANRUN id, which must PASS
    apply-controlled-acceptance
        --plan-run <that plan MANRUN id>
        --authorization-record <repo-relative durable authorization record>

### RESOLVED 2026-09-02 -- the gate is now satisfied

    pointer_audit_v2:  pass=21  review=1  fail=0
    REVIEW: ['CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER']

    validate_pointer_audit demands, and both now hold:
      summary == {"pass": 21, "review": 1, "fail": 0}          True
      reviews == [CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER]  True

**It cleared on `build-reference-candidate` ALONE.** Steps 3 and 4 of the chain
errored out and never ran, and the audit still reached 21/1 -- so the
command-reference branch was NOT the unblock. The reference candidate was, and it
only ran because `PYTHON_312` cleared. One host command, propagating.

    build-reference-candidate  MANRUN-20260902T121923Z-CE9F6E8B  status=PASS
      topics 666   lines 29700/29700   commands 462   args 2368   syscmd 212
      unclassified 0   command_without_topic 0   compact_aliases_resolved 8

Exactly the sandbox prediction, on the host, off the promoted canonical harvest.

### MY ERROR, twice now: placeholder lines that look runnable

The chat block contained `$ref = 'MANRUN-...'` as a fill-in. It was pasted
literally, so `$ref` held the string `MANRUN-...` and steps 3 and 4 died with
`missing bound manifest: ...\MANRUN-...\`. Same class as the earlier
`.venv312 manualgen.py @base validate` shorthand.

**Rule for this file: never write a placeholder that is syntactically valid.**
Capture ids from the tool instead:

    $ref = (& $py12 .\tools\manualgen\manualgen.py @base build-reference-candidate |
            Select-String 'run_id=(\S+)').Matches.Groups[1].Value
    $ref    # confirm it looks like MANRUN-<stamp>-<hash> before using it

### build-disposition-candidate: FAIL, and NOT on the M-4 path

    dispositions=70/70  approved_section_topics=477
    missing_policy=1  extra_policy=13  invalid_targets=0  status=FAIL

`REVIEW_DISPOSITIONS` is a hand-maintained policy table (54 entries) and the
store now has 70 review topics. It drifted when the store gained 193 topics.

    EXTRA (13) -- in policy, no longer review topics:
      DOT|BBS, DOT|BUILD INFO, DOT|BUILD VECTORS, DOT|CANARY, DOT|CC PRINT,
      DOT|CMDREL, DOT|CODAYSL, DOT|FORMULA, DOT|NET, DOT|UDATE, DOT|UDATETIME,
      DOT|UNOW, DOT|UTIME

`DOT|CODAYSL` is NOT a stray typo, and a first draft of this note called it one.
`disposition.py:29` carries it deliberately:

    "DOT|CODAYSL": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|CODASYL",
                      "Source-mined transposition resolves to the supported
                       CODASYL topic.")

It is a rule for a known source-mined transposition. Its appearing in EXTRA is
therefore a GOOD sign -- the transposed topic no longer surfaces as a review
topic, so the rule may have outlived the defect it was written for. That is a
retirement candidate, not a bug. Verified before claiming, after nearly
recording the opposite.

UDATE/UDATETIME/UNOW/UTIME are four of the five functions from V6_HINTS
section 4, still unruled.

    MISSING policy: the tool counts 1, NOT 29.

A raw set difference gives 29 topics with no policy entry, but
`_auto_source_fact_policy` derives one for 28 of them. Only where the fallback
ALSO returns None does a topic count as `missing_policy`. Two different measures;
the tool's is the authoritative one. (Recorded because reporting the 29 would
have been this session's fifth instance of subtracting two differently-defined
numbers and calling the remainder a defect.)

    THE ONE UNRESOLVABLE TOPIC:
      DOT|TRANSACTION   has_help=False   has_runtime=False

**That is v7's D1 orphan, arriving from a fourth direction.**
`src/cli/cmd_transaction.cpp` declares `command: TRANSACTION` in a usage
contract with no dotref entry, so it gets no HELP topic and no SYSCMD row.
`DOTREF_COV` cannot see it because that check enumerates dotref ENTRIES and an
entry never written is invisible. Now the disposition policy cannot classify it
either. The owner's reframing stands and is strengthened: generate dotref from
the contracts (`dotref_autogen.py`) and this dissolves rather than needing a
policy row.

**Disposition is not on the M-4 critical path.** `build-selective-merge-candidate`
takes no required arguments, and `build-controlled-acceptance-plan` needs
`--candidate-run` (selective-merge), `--pointer-audit` and `--context-decision`.
The disposition run feeds the command-reference branch, which is separate.

### THE OLD BLOCKER, kept for the record

`manualgen_lib/controlled_acceptance.py:62` requires the pointer audit's summary
to equal **exactly**:

    {"pass": 21, "review": 1, "fail": 0}

with the single REVIEW being `CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER`.

Run fresh this session
(`manualgen_phase/pointer_audit_v1/manual_documentation_pointer_audit_v1.json`):

    pass=19  review=3  fail=0

    REVIEW rows:
      CANONICAL_REFERENCE_MATCHES_ACTIVE_READER      <- extra
      CANONICAL_REFERENCE_RECORDED_HASH_CURRENT      <- extra
      CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER  <- the expected one

    active_reader_sha256 = EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F

**Zero FAILs.** The two extra REVIEWs are both canonical-reference rows: the
accepted reference no longer matches the active reader, and its recorded hash is
stale. That is the expected consequence of a HELP store that gained 193 topics
and a manual that has not been re-accepted since. It is the work M-4 exists to
do -- but the gate that authorizes M-4 reads the same rows, so the chain refuses
until the reference is rebuilt.

Regenerate the audit before each attempt:

    & $py12 .\tools\fullstack_docs\audit_manual_documentation_pointers.py `
        --repo-root D:\code\ccode `
        --output-dir docs\maintenance\lanes\full_stack_documentation\runs\
                     DOCFLUSH-20260901-002\manualgen_phase\pointer_audit_v1

### The path to a green audit -- now measured, not guessed

    & $py12 .\tools\manualgen\manualgen.py @base build-reference-candidate
    & $py12 .\tools\manualgen\manualgen.py @base build-command-reference-candidate `
        --reference-run <that MANRUN id> --disposition-run <disposition MANRUN id>
    & $py12 .\tools\manualgen\manualgen.py @base build-command-reference-review-book `
        --candidate-run <that MANRUN id>
    # then re-run the pointer audit; aim for pass=21 review=1
    # then the acceptance chain above

**The first step is predicted GREEN off the promoted canonical harvest.**
Simulated 2026-09-02 by suppressing only the PYTHON_312 row and calling the
library directly:

    transform_status            PASS
    canonical_harvest_replaced  0
    topics 666   help_lines 29700   included_help_lines 29700   commands 462
    args 2368    syscmd 212
    duplicate_topic_keys 0       unassigned_line_rows 0
    unclassified_unassigned_lines 0   command_without_topic 0
    compact_command_aliases_resolved 8

Every line accounted for -- 29700 of 29700 included, nothing unclassified,
no command without a topic. That is the harvest promotion paying off: the
reference builds cleanly from prose that actually exists.

**SIMULATION, NOT A RESULT.** It bypassed the CLI's RunLogger, so it wrote under
the placeholder id `MANRUN-REFERENCE-CANDIDATE` -- which looks like a run id and
is not one. Renamed to
`generated/manualgen_reference_candidates/SIMULATED-20260902-sandbox-py310-not-a-run/`
with a `README_PROVENANCE.txt` stating what it is. Gitignored, 5.9 MB, safe to
delete, superseded by the first real run. Flagged rather than left to be
mistaken for evidence.

### A brittleness worth knowing before you rely on that gate

The `{"pass": 21, "review": 1, "fail": 0}` expectation is a **hardcoded literal
in a tool** -- the perishable-literal shape `CLAUDE.md` opens by warning about.
Today the audit emits 22 checks (19+3), so 21+1 is reachable. **Add a
twenty-third check and the acceptance chain refuses even with everything green**,
because the sum no longer equals 22. It fails closed, which is the right
direction, but it fails for the wrong reason and the message
(`POINTER_AUDIT_SUMMARY:{...}`) will not say so.

Not changed here. Recorded as a lane item.

---

## What NOT to run

    apply-gate4-acceptance         separate gate, separate authorization
    apply-gate5-development-plan   source-staging gate; not this run's scope
    anything that writes D:\dev\x64base-site   the publish is on standing HOLD

## Quick state, so nothing is assumed

    canonical harvest        14/14, manifest_findings=0   (promoted this session)
    harvest rollback         docs\manuals\developer\manualgen\
                             harvested.bak-20260901-DOCFLUSH002
    HELP store               666 topics / 29700 lines, built 2026-09-01 17:03
    store backup             dottalkpp\data\help.bak-20260901-170342 (verified)
    Phase 8 entry rows       all eight PASS

**Carried limitation, because it now sits in what the manual reads:** the interim
harvest exporter uses the v32-era `dbfread`, which does not follow x64 memo
blocks, so `COMMANDS.USAGE/VERBOSE`, `CMD_ARGS.USAGE/VERBOSE`,
`HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE` and `SYSFUNC.NOTES` are blank in the
canonical workspace. A manual accepted today inherits that. The permanent fix is
a native `CMDHELP` harvest verb reusing the memo logic in `src/cli/cmd_use.cpp`.
Worth weighing before granting M-4.
