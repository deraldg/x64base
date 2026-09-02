# Full-Stack Documentation Flush and Push -- Cookbook V2

    supersedes  FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V1.md
    written     2026-09-02, from DOCFLUSH-20260901-002 (v8) and -20260902-001 (v9)
    budget      2 HOURS MAXIMUM. GOAL: ONE HOUR.
    owner       member.derald
    steward     whoever is running it

## Read this page before you run anything

**The mechanical path takes about twenty minutes.** Measured across v8 and v9:
harvest export ~1 min, every manualgen step seconds, the website matrix check
~30s, the site build ~15s, the unit suite 0.2s.

v8 and v9 took a full day. **Not one minute of the overrun was the commands.**
It went to: four Gate 4 cycles where one was needed, diagnosing a gate that
reported a failure it had not found, and discovering that the accepted manual had
never been in version control. Every one of those is preventable, and the
prevention is in this document.

So the budget is not aspirational. If you are past two hours, you are not running
a flush -- you are debugging one, and you should stop and write down what you
found before continuing.

## THE FIVE RULES THAT KEEP IT UNDER AN HOUR

1. **CLASSIFY THE RUN FIRST.** Most phases are no-ops most of the time. Step 0
   below decides which phases apply. Skipping this is what makes a one-hour run
   take six.
2. **A GREEN GATE IS NOT A REVIEWED CHANGE.** Four Gate 4 plans reported
   `PASS_PLAN_ONLY findings=0` on 2026-09-02 and three of them would have damaged
   the manual. Diff staged against accepted and put EVERY difference in a named
   class. Zero unexplained, or you do not apply.
3. **FIX AT THE PRODUCER.** If the only way to satisfy a rule is to edit a
   generated file, the rule is pointed at the wrong bank. The next regeneration
   erases your fix.
4. **A COUNT THAT MOVES WITH YOUR FIX IS NOT A MEASUREMENT OF CORRECTNESS.**
   Pick a check that can distinguish right from wrong, not one that improves
   whenever you touch something.
5. **UNRUN IS NOT PASS.** Record what did not run as not-run. Never restate an
   inherited proof as a current one.

## Step 0 -- CLASSIFY THE RUN (5 minutes, saves hours)

Answer these three, in order, and stop at the first YES:

    Did src/** or include/** change since the last run?
        YES -> FULL RUN. Phases 1-7, then PUSH.
        NO  -> Gates 1-6 are CORRECTLY NOT RUN. Say so in the envelope. This is
               not negligence and the record must not read as though it were.

    Did the HELP store or the harvest change?
        YES -> Phases 4-7, then PUSH.
        NO  -> the manual candidate can be rebuilt from the existing harvest.

    Is this website-only reconciliation?
        YES -> skip to PUSH. This is the v9 shape and it is a ONE-HOUR run.

Measure it, do not remember it:

```powershell
cd D:\code\ccode
git --no-optional-locks log --oneline -1
git --no-optional-locks status --porcelain -uall src include | Measure-Object -Line
```

## Step 1 -- OPEN THE ENVELOPE (5 minutes)

Create `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-<date>-<nnn>/`
and write `GATE0_RUN_ENVELOPE_V1.md` containing, at minimum:

- the run's SCOPE and, explicitly, what is NOT in scope;
- the baseline: ccode HEAD, site HEAD, store counts, accepted manual state;
- the E1-E8 entry rows, each marked PROVEN, INHERITED (with the condition that
  makes inheriting valid), or OPEN.

**The INHERITED marking is the point.** A website-only run legitimately inherits
E2-E5 and E7 from the previous flush, but ONLY while it performs no source or
HELP mutation. State that condition. If the run later touches either, the
inheritance is void and those rows must be re-proven.

## Step 2 -- THE FLUSH (skip per Step 0)

### Harvest (only if HELP changed)

Use the SANCTIONED engine-backed exporter. There is a Python scaffold that
produces a similar-looking harvest; it leaves memo text BLANK and relabels stale
tables as fresh.

```powershell
.\dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1
```

> **WARNING -- the scaffold looks like the exporter and is not.** On 2026-09-02 a
> harvest promoted with the scaffold relabelled four stale tables `EXPORTED` where
> the house says `CARRIED_STALE_MAY`. That is the exact pretence the sanctioned
> script exists to prevent. It was rolled back and verified byte-identical before
> being redone. **If the argument-row count drops by a few hundred after an
> exporter run, that is the fix landing, not data loss:** the engine resolves memo
> text the scaffold left blank.

### Manual candidate and acceptance

```powershell
$py12 = "D:\code\ccode\.venv312\Scripts\python.exe"
$base = @("--repo-root","D:\code\ccode","--manual","developer")
$rx   = [regex]'run_id=(MANRUN-\S+)'

& $py12 .\tools\manualgen\check_harvest_ascii.py --repo-root D:\code\ccode

$o1 = & $py12 .\tools\manualgen\manualgen.py @base build-reference-candidate 2>&1; $o1
$ref = $rx.Matches(($o1 -join "`n")) | Select-Object -Last 1 | % { $_.Groups[1].Value }

$o2 = & $py12 .\tools\manualgen\manualgen.py @base build-disposition-candidate 2>&1; $o2
$disp = $rx.Matches(($o2 -join "`n")) | Select-Object -Last 1 | % { $_.Groups[1].Value }

$o3 = & $py12 .\tools\manualgen\manualgen.py @base build-command-reference-candidate `
        --reference-run $ref --disposition-run $disp 2>&1; $o3
$cand = $rx.Matches(($o3 -join "`n")) | Select-Object -Last 1 | % { $_.Groups[1].Value }

$o4 = & $py12 .\tools\manualgen\manualgen.py @base build-publication-structure-candidate 2>&1; $o4
$struct = $rx.Matches(($o4 -join "`n")) | Select-Object -Last 1 | % { $_.Groups[1].Value }

"ref=$ref  disp=$disp  cand=$cand  struct=$struct"
```

> **`build-publication-structure-candidate` TAKES NO ARGUMENTS.** It builds from
> the accepted reader, not from the command candidate. Passing `--command-run`
> fails with "unrecognized arguments".
>
> **CAPTURE RUN IDS FROM THE OUTPUT.** Never hand-type a MANRUN id and never leave
> a `<placeholder>` in a PowerShell command -- `<` is a reserved operator and the
> line will not parse. The `$rx` capture above exists for this reason.
>
> **READ `tools/manualgen/manualgen_lib/commands.py` BEFORE INVENTING A FLAG.** It is 120 lines.
> Three wrong commands were handed to the owner on 2026-09-02 by guessing at an
> interface that could have been read: `--manual-id` (it is `--manual`), a
> placeholder, and `--command-run` on a parser that takes none.

### THE REVIEW THAT ACTUALLY CATCHES THINGS (do not skip; 10 minutes)

Build the Gate 4 plan, then **partition every planned mutation before applying**:

```powershell
$o5 = & $py12 .\tools\manualgen\manualgen.py @base build-gate4-acceptance-plan `
        --command-run $cand --structure-run $struct `
        --status-approval <path to gate4_status_approval_v1.json> 2>&1; $o5
$plan = $rx.Matches(($o5 -join "`n")) | Select-Object -Last 1 | % { $_.Groups[1].Value }
```

Then, for every row in `gate4_planned_mutations.csv`, diff `target` against
`staged_path` and assign a class. **Required outcome: zero unexplained.** Also
assert whole-file text preservation -- normalised for whitespace, bullet markers
and provenance lines, the text before and after must be IDENTICAL for a rendering
change.

A clean v9-shaped partition looks like:

    164  byte-identical
      3  non-md artifacts
      1  marker change (3 lines)
      0  unexplained
      0  text added or lost

> **THIS STEP IS THE WHOLE DEFENCE.** The gate said `findings=0` for a plan that
> joined text across a byte boundary mid-word ("not the command name" became "not
> the comm and name") and for another that welded list items into sentences on
> eight pages. The fragment count fell in both cases, exactly as it would for a
> correct fix. **Counting is not partitioning.**

Then write the apply authorization bound to the REAL hashes, pre-validate it, and
let the OWNER run the apply.

```powershell
$o6 = & $py12 .\tools\manualgen\manualgen.py @base apply-gate4-acceptance `
        --plan-run $plan --authorization <path to gate4_apply_authorization_v1.json> 2>&1; $o6
```

**Verify by reading the accepted pages on disk afterwards.** Not by trusting
`PASS_APPLIED`.

## Step 3 -- COMMIT THE FLUSH (10 minutes)

```powershell
git add --pathspec-from-file=<explicit path list>
git status --short -uall
git commit -F <message file>
```

> **NEVER `git add -A`, `git add .`, OR A DIRECTORY.** Adding
> `command_reference_v1/` on 2026-09-02 swept in 47 orphan pages the change never
> touched. Staging a previously untracked file makes EVERY line an added line, so
> the house-style gate then blocked on pre-existing characters. **The prepush
> gate's "> 60 paths staged" warning was the accurate complaint; the ASCII failure
> was its symptom.**
>
> **KEEP `-uall`.** This repo sets `status.showUntrackedFiles=no`, so a bare
> `git status` shows nothing at all for a file you just created.
>
> Build the path list from the plan ledger, not by hand.

## Step 4 -- THE PUSH (30 minutes, and it is mostly checking)

### 4a. Read the website matrix FIRST. It is the entry gate.

`D:\dev\x64base-site\content\docs\dev\website-documentation-matrix.mdx`. Classify every
page you will touch before touching it. The matrix is also the CLOSEOUT gate: the
run does not close until it is re-audited.

### 4b. Run the hard publication gate

```powershell
& $py12 .\tools\fullstack_docs\website_matrix_check.py --root D:\code\ccode --site-root D:\dev\x64base-site
```

> **IF IT SAYS "catalog drifted from source", CHECK WHETHER THE TOOL RAN.**
> `command_catalog_sync` exits 2 for "Python 3.12+ required" AND exits 2 for real
> drift. The caller cannot tell them apart and prints the alarming one. On
> 2026-09-02 this gate reported FIVE failures against a site that was current on
> every relationship it tests; four were the guard. **Use `.venv312`, never the
> vcpkg python** -- the guard exists because the vcpkg interpreter is minimal and
> has no PyYAML. See `GATE_CORRECTIONS_REQUIRED_V1.md`.

### 4c. Update the ONE authority, not the eleven pages

`D:\dev\x64base-site\public\artifacts\documentation-progress-v1.json` is the single
authority behind ELEVEN of the thirteen freshness contracts. Derive the drift:

```powershell
& $py12 .\tools\fullstack_docs\build_documentation_progress.py `
    --repo-root D:\code\ccode `
    --catalog D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx `
    --check D:\dev\x64base-site\public\artifacts\documentation-progress-v1.json
```

> **`--out` IS A COMPARISON CANDIDATE, NOT A REPLACEMENT.** Its field set differs
> from the live artifact: it omits `website_function_core_rows`,
> `canonical_harvest_*`, `run_id`, `state` and others, and renames
> `help_arguments` to `help_cmd_args`. Copying it over the live file deletes
> fields that pages and contracts read. **Update the drifted fields IN PLACE.**
>
> **DO NOT REWRITE FIGURES THAT DID NOT MOVE.** Re-measure them, confirm, leave
> them. Churn destroys the signal that the changed ones are real.
>
> **THE SITE TRACKS THREE DISTINCT MANUAL IDS** and they are not interchangeable:
> the newest DRY RUN (this is what "Manual candidate" means), the command-reference
> candidate, and the Gate 4 apply. **No gate will catch a plausible id in the wrong
> row**, because every contract checks that a marker matches its authority, not
> that the right authority was chosen.

### 4d. Make the bound markers match, then verify

```powershell
cd D:\dev\x64base-site
node scripts/check-site-freshness.mjs
node scripts/check-site-freshness.mjs --self-test
```

> **RUN THE SELF-TEST AFTER THE WORK, NOT BEFORE.** It corrupts one required
> marker in every contract and demands each still fail. A contract made to pass by
> loosening it is worse than one that fails, and the self-test is the only thing
> that tells them apart.
>
> **FIVE OF THE THIRTEEN ARE ATTESTATIONS, NOT MEASUREMENTS** -- "FAQ reviewed
> <date>", "reconciled through <date>". **A date typed to satisfy a checker is a
> fabricated attestation.** Do the review, then date it; never the reverse.
>
> **IF A CONTRACT FAILS ON A VALUE YOU JUST CHANGED ON A PAGE, YOU EDITED THE FAR
> BANK.** Contracts interpolate from the authority. Change the artifact.

### 4e. Build, then review what you built

```powershell
npm run build
powershell -ExecutionPolicy Bypass -File D:\code\ccode\start-ai.ps1 -Built
```

`-Built` because search needs a Pagefind index and dev mode has none. The site is
on **:3002**; **:3000** is the reports gateway that proxies to it. Hydration
through :3000 works (fixed 2026-08-16, AIF-118).

The build measures two fields nothing else does: `website_static_pages_built` and
`website_pagefind_pages_indexed`. **Update them from the build output.**

## Step 5 -- CLOSE (10 minutes)

- Re-audit the website matrix and record the sweep with the current `as_of_date`.
- Write the run closeout: what was proven, what was DELIBERATELY not done and
  why, what open items the run produced.
- `Last audited` in the matrix moves ONLY after the owner reviews a rendered site
  revision. Not on a local build.
- Publication is a DISTINCT MUTATION requiring its own authorization. A manual
  acceptance grant does not cover it.
- Gate 9 is live verification: read the DEPLOYED routes. **A green build is not
  live-site proof.**

## Time budget

    Step 0  classify                    5 min
    Step 1  envelope                    5 min
    Step 2  flush (skipped if no-op)   20 min
    Step 3  commit                     10 min
    Step 4  push                       30 min
    Step 5  close                      10 min
                                       -------
                                       80 min

Website-only runs skip Step 2 and land near forty minutes.

## When something fails

**Read what the check actually compared before believing its message.** Three
times on 2026-09-02 a claim in this repo's own records turned out to be prose
mistaken for evidence: a grep that matched a sentence ABOUT a contract, a run
record asserting unit tests that did not exist, and a gate reporting drift it had
not measured. The pattern is not carelessness. A grep matching discussion of a
thing looks identical to a grep matching the thing.

**Record null results.** "I tried the obvious fix and it changed nothing, here is
why" is worth more than the fix, because it stops the next reader spending the
same hour.

## Companion documents

- `FULL_STACK_DOCUMENTATION_NORTH_STAR_V1.md` -- why the chain exists.
- `GATE_CORRECTIONS_REQUIRED_V1.md` -- gate defects found and not yet fixed.
- `FLUSH_FIELD_NOTES_V1.md` -- the diagnoses behind the warnings above, kept out
  of this page so it stays runnable.
