# Flush v6 -- the streamlined plan

    Run    : DOCFLUSH-20260825-001 (v6). Opened 2026-08-25.
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Lane   : full_stack_documentation (AIF-068)
    Status : **OPEN. Gate 0 has already failed once, correctly.** review-needed.
    Prior  : v5 = DOCFLUSH-20260812-001. Lessons in that run's V6_HINTS_V1.md.

---

## 1. Why v6 exists, in the owner's words

> "let us skip that step and start over with a whole new doc fullstack push
> from the beginning again, to see if we can improve. Improving the process
> from start to phase 6 through normalization and refactoring will improve the
> web phase by gigo."

**The website matrix and the website are DELIBERATELY OUT OF SCOPE.** They are
v5's remaining push and they stay unrun. The reasoning is garbage-in
garbage-out: the web phase consumes whatever the pipeline produces, so the
cheapest way to improve the website is to improve everything upstream of it and
run the web phase later against better inputs.

**v6 is therefore not a repeat. It is the same pipeline run again with the
checks that v5 had to learn.**

## 2. The whole improvement is that v6 STARTS by running a check

v5's cycles were lost to ORDERING facts -- what was built before what -- and
every one produced output that looked correct. Prose does not catch those.

    $py12 tools\fullstack_docs\docpush_preflight.py --root .     before starting
    $py12 tools\fullstack_docs\docpush_preflight.py --root .     after EVERY rebuild

**IT ALREADY EARNED ITS PLACE.** First run of v6, before any work:

    4. FAIL  exe newer than catalogs   exe 2026-08-25 02:44:18 is OLDER than
                                       1 catalog(s)

`include/foxref.hpp` gained the `FILE()` pointer entry in `6bcb5bb30` today.
**`dotref` and `foxref` are COMPILED IN**, so the current exe would rebuild the
store from the catalog as it was BEFORE that entry. That is the 2026-08-12
failure verbatim, caught before v6 touched anything.

**GATE 0 ACTION 1: rebuild the exe, then re-run the preflight.** No phase
starts until it is green or every FAIL is explained in writing.

Also reported on that run, and both are known:

    store integrity   665 topics reachable, every line row names one  -- AIF-126's
                      repair holding
    status coherence  167 rows STATUS=pending and CONFID=AUTHORITATIVE at once
                      -- open, carried from v5

## 3. What v6 does differently, phase by phase

The phases are unchanged. What changed is that each now opens with a check that
runs instead of a paragraph that has to be remembered.

    Gate 0   preflight GREEN, or every FAIL written down. Plus: the exe's own
             banner names a commit and is NOT `dirty` (V6_HINTS 8c, assertion
             1'). One grep.
    Gate 1   mine and count UNDER OBSERVATION -- and READ THE COUNTERS THE
             MINER ALREADY PRINTS before designing any new measurement.
             "Usage contracts mined directly: N row(s) from M file(s)" is
             emitted by every CMDHELP BUILD and lands in the run transcripts.
    Gate 2   baseline captured, with the store's own generation stamp recorded.
    Gate 3   package + authorization. ONE `datarun.ps1` INVOCATION PER
             HELP-MUTATING COMMAND. Never an array. It cost v5 two cycles, the
             second time inside a script written by the steward who had just
             documented it.
    Gate 4   execute + validate. Adopt 1' and 6' (topic-SET diff, not a count
             floor); 5b stays retired.
    Phase 5  metadata. Count discipline applies: see section 4.
    Phase 6  manualgen. The page generator now has an ALLOW-LIST selector and a
             `--dry-run` that classifies without writing. USE THE DRY RUN FIRST,
             ALWAYS.
    Web      OUT OF SCOPE for v6.

## 4. The rules v5 paid for, stated as checks rather than warnings

Each of these is now either a tool, a gate line, or a one-command test. Prose
that has no runnable form is marked so.

| rule | how it runs |
|---|---|
| Name what is in a count | `stack_audit_v1.py` check G (COUNT_KINDS) -- findings-free, cannot move the ratchet |
| Guard the authority you NAME, not the working set | AIF-128; `refcheck_v1.py` tests `commands_reg`, not the union |
| An identity number is an INTEGER; padding is display | R126; nine readers match `AIF-0*(\d+)` and normalise |
| What composes a command page | R127; `--compose-catalog`, cross-references recorded |
| Quote an identity without spending it | `id-cite:ignore` (`tools/coordination/idcite.py`) |
| A marker that suppresses nothing is noise | `check_cited_paths.py` advisory |
| An unescaped inline pipe splits a table cell | `check_house_style.py` advisory |
| Predict the gate before handing over a command | `is_data_fixture` / `is_hard_block` are importable |
| Prior art before building | `docpush_preflight.py --prior-art "<subject>"` |
| **A substring grep is not a count of the thing you named** | NO RUNNABLE FORM YET -- see section 5 |
| **Check the freshness stamp of a REF, not just a report** | NO RUNNABLE FORM YET -- see section 5 |
| **Derive numbers and INCIDENTS; do not assert them** | NO RUNNABLE FORM -- it is a habit |

## 5. The three that have no gate, and are the likeliest to bite v6

**These are the ones to watch, precisely because nothing will stop them.**

### 5a. A substring grep is not a count of the thing you named

v5 made this error TWICE, and the second time was two sections below the
correction recording the first.

    `@dottalk\.`        matched `@dottalk.file`         -> 578, not 229
    `@dottalk.usage`    matched `@dottalk.usage.voluntary`
                        AND prose mentions              -> 231, when 209 are real

The second one is what kept Gate 1's Q1 open for thirteen days behind a
coverage gap that did not exist. **Before quoting a count, print the DISTINCT
MATCHED STRINGS, not just the number.**

### 5b. Check the freshness stamp of a REF, not just a report

v5 caught a twenty-day-old inventory report about to be quoted as proof. It did
NOT catch a NINE-DAY-STALE `origin/main`, because a ref does not look like a
report. Nine hours of measurement ran against a 2026-08-16 snapshot; the drift
audit it produced said CHANGED 29 / NEW 70 when the truth was 9 / 64.

**AN AUDIT AGAINST A STALE BASELINE DOES NOT MERELY MISS THINGS; IT INVENTS
WORK.** Before reading a remote ref: `git log -1 --format=%ad origin/main`.

### 5c. Derive numbers and incidents; do not assert them

Four times in v5 a figure was stated without being computed, and once an
INCIDENT was asserted without being checked -- a "real widow" that git showed
never existed, which reached a commit message and a source docstring before it
was caught. **A false incident in a docstring is worse than a false number in
a report: the next reader inherits it as settled fact.**

## 6. What v6 inherits that v5 did not have

    tools/coordination/idcite.py                 id-cite:ignore
    tools/fullstack_docs/stack_audit_v1.py       check G, COUNT_KINDS
    tools/fullstack_docs/dbfread.py              x64 false-terminator fixed (AIF-127)
    tools/fullstack_docs/refcheck_v1.py          three-state guards, honest labels
    tools/fullstack_docs/normcheck_v1.py         FN_IDENTITY that can fail
    tools/manualgen/build_postbaseline_supported_command_pages.py
                                                 allow-list selector + --dry-run
    tools/manualgen/build_complete_command_reference_index.py
                                                 declared provenance layers
    tools/staging/check_cited_paths.py           inert-marker advisory
    tools/staging/check_house_style.py           inline-pipe advisory
    rulings                                      R126, R127
    lanes                                        AIF-128 closed, AIF-129 chartered

## 7. Carried into v6 from v5, unfinished

1. **AIF-129** -- contract sub-block vocabularies (`status=`, `risk:`).
   Coordination-blocked on the session that owns the HELP store.
2. **167 rows `pending` + `AUTHORITATIVE`** -- the preflight's standing WARN.
3. **56 owner topics that can never render** (AIF-126 open item).
4. **OI-010 item 2** -- purge `docs/getting-started/BUILDING.md` from `main`.
   Item 1 is DONE; it was carried by the 2026-08-21 promotion.
5. **OI-017 remainder** -- 11 of 14 files unexamined, and the first three split
   1 defect / 1 demo / 1 transcript, so the headline count overstates the work.
6. **OI-018** -- the overlay still publishes from the FILESYSTEM. Undecided.

## 8. Good neighbour

    What changed:      opens run DOCFLUSH-20260825-001 with this plan. No code.
    Whose area:        full_stack_documentation / AIF-068.
    Authorization:     member.derald, 2026-08-25 -- "we are in fullstack 5 go to
                       6", website step deliberately skipped.
    How to verify:     section 2's FAIL reproduces by running the preflight
                       before the exe is rebuilt.
    How to undo:       delete the run directory. Nothing else references it yet.
