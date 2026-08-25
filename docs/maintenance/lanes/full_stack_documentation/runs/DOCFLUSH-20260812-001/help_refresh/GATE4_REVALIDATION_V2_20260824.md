# Gate 4 -- HELP refresh RE-validation (flush v5), capture v2

    Run       : COWORK-20260824-001 (member.ai.claude.cowork), for member.derald
    Lane      : full_stack_documentation
    Flush     : DOCFLUSH-20260812-001 (v5)
    Transcript: help_refresh/fullstack_post_refresh_runtime_v2_20260824.txt
                4,680 lines, ends DOCFLUSH-V5-POSTREFRESH-END, not truncated
    Compared  : help_refresh/fullstack_post_refresh_runtime_v1.txt (2026-08-21)
                runtime_baseline/fullstack_pre_refresh_runtime_v1.txt (2026-08-13)
    Status    : **review-needed.** The author does not self-approve.

The 2026-08-21 capture was preserved. This is a second file, not an overwrite.

---

## 0. What the run was actually bound to -- read this before the table

The banner carries the instrument that assertion 1 was withdrawn for lacking:

    dottalk++ v0.6 (2026-08-24, c39d966c dirty)  (Aug 24 2026 17:05:41)

Three facts, none of them inferred:

1. The exe was built from **`c39d966c`** -- R124, **three commits behind HEAD
   `a278b511e`**.
2. The tree was **`dirty`**. The engine says so itself.
3. `src/cli/cmdhelp.cpp` is one of the dirty files. Worktree blob
   `b0ba89fcb`, HEAD blob `c22125ab9`. That file belongs to the CONCURRENT
   session and its change is **uncommitted**.

**Consequence: the store this transcript describes is not reproducible from any
commit.** Everything below passed, and passed honestly, but it passed against a
working tree. Gate 4 may be recorded `runtime-proven against worktree
c39d966c+dirty`. It may NOT be recorded `runtime-proven against HEAD`, and it
must be re-bound once the concurrent session commits `cmdhelp.cpp`.

This is the 2026-08-12 failure class -- "a transcript that looks like evidence
and is not" -- caught this time by an instrument that did not exist then. The
version banner is the sound replacement for withdrawn assertion 1 and should be
written into the package.

---

## 1. Assertion-by-assertion

| # | Assertion | Result |
|---|-----------|--------|
| 1 | build stamp later than `358c14a8a` | **WITHDRAWN 2026-08-21** (unsound). Replacement (DOTHELP renders SMTP) is assertion 4. See section 0 for a better replacement. |
| 2 | `CMDHELPCHK` structural status PASS; blank artifact texts == 0 | **PASS / NOT INSTRUMENTED.** Transcript line 932: `OK no structural issues found`. The transcript carries **no blank-artifact-text counter at all**, so the second half of this assertion has never been measurable from this capture. Naming that rather than scoring it green. |
| 3 | `HELP SMTP`, `CMDHELP SMTP`, `HELP APPGUI`, `CMDHELP APPGUI` all resolve | **PASS, 4 of 4.** Zero occurrences of "No help found" anywhere in the transcript. On 2026-08-21 this was 3 of 4. See section 3. |
| 4 | `DOTHELP` renders `SMTP` with the syntax string from `include/dotref.hpp` | **PASS.** Transcript 2370-2371 renders `SMTP [USAGE\|STATUS\|PROBE\|SEND FROM <file> [TO <addr>] SUBJECT <text>]`, character-for-character `include/dotref.hpp:1152`. |
| 5a | `FOXREF` == 665; `DOTREF` >= 992 | **PASS.** FOXREF 665 (flat, as predicted). DOTREF 1,004. |
| 5b | `EDREF` != 786 | **WITHDRAWN 2026-08-21** as malformed -- an EDREF HELP_LINE row count cannot witness a change that lands in `HELP_TOPIC.TITLE`. EDREF is 786, and that number is not evidence either way. Finding 2 of the resume state (edref one-line titles reach nothing) is **still open** and still needs the direct `HELP_TOPIC.TITLE` read. |
| 6 | lines >= 28,827 and topics >= 528 | lines 29,206 **PASS**. topics 526 **fails the literal floor**. The floor is unsound; see section 2. |
| 7 | diff against the pre-refresh baseline | **DONE.** See section 4. |
| 8 | free of mojibake | **PASS.** `file(1)` reports `ASCII text`. The only non-printables are 14 lines of ANSI colour escapes in the startup banner. Zero mojibake. |

---

## 2. The topic count fell by four, and that is the fix landing

Do not read 530 -> 526 as loss. Read it as five inventions withdrawn and one
real topic gained.

The topic sets diff exactly, in both instruments (the `CMDHELP TOPICS` list and
the per-SOURCE bucket listings agree):

    LOST  (from DOTREF and REGISTRY, both):
      DOT|FILE  DOT|UDATE  DOT|UDATETIME  DOT|UNOW  DOT|UTIME
    GAINED (SOURCE_MINER):
      DOT|PALETTE STUB

Those five names are **exactly** the five diagnosed in
`GATE4_REFRESH_VALIDATION_V1.md` section 12b: expression functions that were
being promoted into DOT command rows because `is_expression_function_name()`
restated `function_catalog` by hand and the two lists had drifted. They are
functions. `src/cli/expr/function_catalog.cpp` is their only definition site;
they were never commands, and no command registry ever should have carried them.

The worktree `cmdhelp.cpp` now opens that predicate with

    // ASK THE FUNCTION CATALOG. DO NOT KEEP A SECOND COPY OF ITS CONTENTS HERE.

which is candidate ruling (b) implemented as delegation rather than as "add the
five". **This transcript is its runtime proof.** Exactly five rows left, the six
masked drifts (`PADC PADL PADR PROPER STRCAT STUFF`) were already claimed by
foxref keys and are untouched, and nothing else moved.

Every counter corroborates and none dissents:

    topics       530 -> 526    (-4  = -5 +1)
    KIND STATUS 1563 -> 1558   (-5  : one REGISTRY STATUS row per withdrawn topic)
    KIND SUMMARY 2393 -> 2389  (-4)
    DOTREF   topics 261 -> 256 (-5)
    REGISTRY topics 460 -> 455 (-5)
    SOURCE_MINER topics 222 -> 223 (+1)
    line rows 29,075 -> 29,206 (+131)

**Assertion 6 is unsound, and it is the third of its class in this run.** A
count floor cannot distinguish content lost from miscategorised content
correctly removed; it scores a repair as a regression. Same shape as withdrawn
assertion 1 (a proxy that cannot move when its subject does) and withdrawn 5b (a
proxy in the wrong table).

**Proposed replacement, for the steward to rule on:** replace the topic floor
with a **topic-set diff against the previous capture**, with every departure
named and dispositioned. The line floor may stand -- lines are additive and a
fall there is a real signal. The set diff is what section 2 above is; it took
one pass and it answered a question the floor could only mis-answer.

---

## 3. Finding 10a is CLOSED -- `HELP APPGUI` resolves

2026-08-21 recorded `HELP APPGUI` returning "No help found" while the store held
68 rows for it: `HELP <verb>` reads the compiled dotref catalog, and APPGUI had
no dotref entry.

`859ef4548` added `{"APPGUI", ...}` and its alias `{"GUI", ...}` to
`include/dotref.hpp` (261 -> 263 entries). Transcript 3186-3188:

    . APPGUI
      APPGUI
      Launch the windowed Workbench GUI (dottalk_wb) as a separate process, ...

Resolved, with content. The operator-facing surface and the data surface now
agree for this command. The general question behind it -- what the other
uncurated commands should do -- is **not** closed by this; only APPGUI was
added, and it was added by hand.

---

## 4. Assertion 7 -- the diff against the pre-refresh baseline

    pre-refresh  (2026-08-13, 2,976 lines)   28,731 line rows,  527 topics
    post v1      (2026-08-21, 4,674 lines)   29,075 line rows,  530 topics
    post v2      (2026-08-24, 4,680 lines)   29,206 line rows,  526 topics

    pre -> v2 :  43 changed regions, 54 lines removed, 1,758 added
    v1  -> v2 :  39 changed regions, 49 lines removed,    55 added

By SOURCE, pre -> v2:

    CURATED_DOC       868 ->    868   flat
    DOTREF            896 ->  1,004   +108
    EDREF             786 ->    786   flat  (see 5b)
    FOXREF            665 ->    665   flat, as predicted
    REGISTRY          462 ->    460   -2
    SHARED_MSG      2,637 ->  2,637   flat
    SOURCE_MINER    7,503 ->  7,644   +141
    USAGE_CONTRACT 14,914 -> 15,142   +228

**Incidental finding -- the floor's provenance is wrong.** Assertion 6 quotes
28,827 lines / 528 topics as "the baseline". The baseline transcript reports
**28,731 / 527**. The floor was set from a number the baseline capture does not
contain, and was 96 lines and 1 topic adrift before anything was measured
against it. Whatever replaces assertion 6 should quote the transcript.

Also visible: the thousands separators are gone from the SOURCE table
(`2,637` in the baseline, `2637` in both post captures). That is Gate 2 s6
closing, already recorded 2026-08-21.

---

## 5. Disposition

Gate 4 re-closes on the seven live assertions -- 2 (status half), 3, 4, 5a, 7,
8 -- with assertion 6 held pending a ruling on its replacement, and with the
binding in section 0 recorded rather than papered over.

Nothing here is `runtime-proven against HEAD`. It is `runtime-proven against
worktree c39d966c+dirty`.

Owed, in order:

1. Steward ruling on assertion 6 -- topic-set diff replacing the topic floor.
2. Re-bind: once the concurrent session commits `src/cli/cmdhelp.cpp`, note the
   commit here. No re-run needed if the blob is unchanged.
3. Finding 2 (edref titles) still needs the direct `HELP_TOPIC.TITLE` read.
4. `FN_COVERAGE` still absent from the capture script -- the `FILE` 75/74 warn
   remains unverified by a run, and section 2 has just changed what `FILE` means
   to the roster, so this is now more interesting than it was.
5. The website matrix closing gate in `D:\dev\x64base-site`. Steward asked to
   regroup before that step and that pause still stands.

---

## Good Neighbor note

    WHAT CHANGED   : two new files under
                     runs/DOCFLUSH-20260812-001/help_refresh/ --
                     fullstack_post_refresh_runtime_v2_20260824.txt (the
                     capture, written by the steward's own run) and this
                     record. No source, no data, no store, no git mutation.
                     The 2026-08-21 capture and its record were not touched.
    WHOSE AREA     : lane full_stack_documentation, owner member.derald.
                     Section 2 reports on src/cli/cmdhelp.cpp, which belongs to
                     a CONCURRENT session -- READ ONLY, nothing was edited, and
                     the credit for the fix is theirs.
    AUTHORIZATION  : the standing "Full-Stack SelfDoc push v5" request plus the
                     in-session instruction to re-run the Gate 4 sequence
                     against today's build. Gate 3 was authorized 2026-08-21.
                     NOT authorized and NOT done: any commit, any promotion,
                     any pointer or website change.
    VERIFY OR UNDO : re-read the two files named above; the figures in every
                     table are line-addressable in the transcript. Undo is
                     deleting this record. The HELP store was backed up to
                     dottalkpp/data/help.bak-<stamp> before the run.
