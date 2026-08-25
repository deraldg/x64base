# Gate 1 Q1 -- CLOSED. There is no coverage gap; there was a counting artifact.

    Run    : DOCFLUSH-20260812-001 (flush v5) / COWORK-20260825-001
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : **Q1 CLOSED. Both hypotheses refuted.** review-needed.

---

## 1. The two hypotheses, both refuted

**H1, the envelope's (2026-08-12): the miner is `src/cli`-shaped, so contracts
outside `src/cli` are silently missed.** Refuted earlier today by one grep --
`cmdhelp.cpp:2546 roots.push_back("./src")`, scanned recursively.

**H2, the reframe (this session): the gap is BLOCK WELL-FORMEDNESS**, on the
evidence that `@dottalk.usage` appears in 231 files while `@dottalk.end`
appears 17 times tree-wide.

**H2 IS ALSO REFUTED, and more cheaply than H1.** `@dottalk.end` does not
appear anywhere in `src/help/helpdata_source_miner.cpp`. It is not part of this
grammar. `extract_usage_contract_blocks` (:1061) runs a block from the marker
line to the first line that is not a `//` comment, or to the next marker:

    while ((pos = text.find("@dottalk.usage v1", pos)) != npos) { ... }
    if (clean.rfind("//", 0) != 0) break;

`@dottalk.end` terminates the `@dottalk.location` block instead -- a different
block, in the same header, with its own grammar. **The reframed question was
built on a terminator the miner never reads.**

## 2. What the 231 actually is

    209  @dottalk.usage v1              real contracts -- the literal the
                                        extractor searches for
     16  @dottalk.usage.voluntary v1    a DIFFERENT, DELIBERATE category,
                                        matched only because it CONTAINS the
                                        substring. Created by
                                        tools/fullstack_docs/convert_subcmd_to_voluntary.py
                                        (2026-07-27). The contract miner does
                                        not read voluntary contracts, on purpose.
      6  prose mentions                 not markers at all. Five are the same
                                        boilerplate sentence -- "handler and a
                                        @dottalk.usage contract IN THE SAME
                                        COMMIT as the handler" -- and one is
                                        "no source file, so no @dottalk.usage
                                        contract, so no SYSCMD".
    ---
    231

**THE 231 WAS NEVER A CONTRACT COUNT.** `grep -rl "@dottalk\.usage"` substring-
matches `.voluntary` and matches prose. There is no coverage gap to explain.

**AND THIS IS THE SECOND TIME IN ONE DOCUMENT.** Section 2c of
`GATE1_OPENING_AND_Q1_ANSWERED_V1.md` records the identical mistake caught
earlier the same day: `@dottalk\.` matched `@dottalk.file` and put the count at
578. **The reframed question was then built on a count made the same way, two
sections below the correction.** A marker vocabulary was even written out there
-- `usage 266` occurrences against `file 582` -- and the 231 FILE count was
still taken with a substring grep.

## 3. "Mine and count under observation" ALREADY HAPPENED

The instrument exists and has existed throughout. `helpdata_cmdhelp_bridge.cpp`
computes `usage_contract_files`, `usage_contract_rows`, `source_files_scanned`,
`source_files_skipped` and a `source_artifact_cap_hit` flag, and `cmdhelp.cpp`
:2378 prints:

    Usage contracts mined directly: {rows} row(s) from {files} file(s)

**Two independent captures on 2026-08-21, taken during GATE 4's refresh
validation, four days before Gate 1 was opened:**

    help_refresh/GATE4_REFRESH_VALIDATION...   3499 row(s) from 207 file(s)
    help_refresh/step6_alone.txt               3499 row(s) from 207 file(s)

The measurement Q1 asked for was already on disk, in this run's own directory,
in a phase this steward had already validated twice. **Nobody asked the
instrument the question it was already answering** -- the AIF-126 lesson,
repeated in the same lane five days later.

Earlier captures for shape: 247 files (2026-07-17, isolated rebuild), 224 and
223 (2026-07-23), and the envelope's own quoted 205 / 3459 rows.

## 4. The residual, and it is not a defect

    209  files carrying the v1 literal today
     -3  carry it as a STRING LITERAL, not on a `//` line
    ---
    206  expected today          vs 207 measured 2026-08-21

The three are `helpdata_messages.cpp`, `helpdata_source_miner.cpp` and
`metacollect.cpp` -- **the tools that process contracts, containing the marker
in their own source.** The extractor's `clean.rfind("//", 0) != 0` check skips
them, which is exactly right; a miner must not mine itself.

`helpdata_messages.cpp` is 672,623 bytes and also exceeds the 512 KB
`kEffectiveMaxFileBytes` scan cap -- belt and braces on the same file.

**206 today against 207 four days ago is corpus drift, not a discrepancy.** The
counts are from different dates and are reported as such rather than
reconciled. No file is outside the scan root; none of the 209 exceeds the cap
except the one already excluded.

## 5. Q1 is closed

There is no silent coverage gap, by roots or by well-formedness. The miner
scans what it says it scans, mines the marker it says it mines, and its own
counters have been reporting the answer since at least 2026-08-21.

**What would have been needed to see this at any point: read the miner, and
read the transcript already sitting in the run directory.** Neither required a
build, a store rebuild, or coordination with the concurrent session.

## 6. Gate 1 status after this

    Q1  CLOSED. Both hypotheses refuted; no gap exists.
    Q2  ANSWERED and implemented (6bcb5bb30) -- foxref pointer entry.
    Q3  ANSWERED; implementation coordination-blocked; AIF-129 chartered.

**Gate 1's questions are now all closed, and the one that was blocking
execution turns out to have had nothing behind it.** Whether Gate 1 is
"executed" is now a bookkeeping question for the steward rather than a
measurement question: the phase it was meant to validate has been measured,
twice, under observation, and recorded.

## 7. Good neighbour

    What changed:      this record only. No code, no contract, no store.
    Whose area:        full_stack_documentation. The miner was READ, not
                       modified or run.
    Authorization:     flush v5 Gate 1, "next on the knock out list".
    How to verify:     `grep -c "dottalk.end" src/help/helpdata_source_miner.cpp`
                       returns 0; the 209/16/6 split reproduces with two greps;
                       the 2026-08-21 captures are in this run's help_refresh/.
    How to undo:       delete this file.
