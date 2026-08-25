# Gate 1 -- there was nothing to read, and Q1's hypothesis is refuted

    Run    : DOCFLUSH-20260812-001 (flush v5), Gate 1 / source comments and
             @dottalk contracts
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : review-needed. Q1 ANSWERED. Q2 and Q3 still open. Read-only.

---

## 1. Why there was nothing to read

The owner asked why Gate 1 could not be read. **It is not permissions.** Until
this file, `runs/DOCFLUSH-20260812-001/` held no `gate1/` directory and no Gate 1
artifact of any kind:

    CITED_PATH_WIDOW_TRIAGE_V1.md   gate0/          manualgen_phase/
    GATE0_RUN_ENVELOPE_V1.md        help_refresh/   runtime_baseline/
    TRIAGE_LOG_20260824_V1.md       V6_HINTS_V1.md  website_phase/

**Gate 1 was never executed for this run.** Its subject matter was carried
forward as three open questions in the Gate 0 envelope, section 4, and left
there. Every status this steward produced today -- Gate 4 closed, Gate 0
precondition closed, Phases 5 and 6 -- omitted Gate 1 entirely rather than
reporting it as open. **That omission is the finding the owner's question
surfaced**, and it is worse than a gap in the work: a status that silently drops
a gate reads as though the gate does not exist.

For reference, Gate 1 in the v4 handoff was
`1 -- comments/contracts | PASS | 1,032 files; 243 complete live SRCUSAGE
contracts after the coverage repair`.

## 2. Q1 -- ANSWERED, and the hypothesis is REFUTED

The envelope asked whether the contract miner is `src/cli`-shaped:

> 205 is close to the `src/cli` count (203), not the tree count (229). If the
> harvest is `src/cli`-shaped, then `src/edu/*` (16 contract files), plus
> contracts under `src/help`, `src/identity`, `src/xbase` and `src/security`,
> are not being mined at all. That would be a silent coverage gap in the
> authority the whole flush reconciles against.

**It is not `src/cli`-shaped. The miner scans `./src`, recursively.**

    src/cli/cmdhelp.cpp:2546          roots.push_back("./src");
    src/cli/command_help.hpp:51,60    source_roots = { "./src" }   (default)
    src/cli/cmdhelp.cpp:39            "the source-root list defaults to ./src"
    src/help/helpdata_source_miner.cpp:1773
                                      fs::recursive_directory_iterator

and a tree-wide search for a narrower root string -- `"src/cli"` or `./src/cli`
as a scan root anywhere in `src/**/*.cpp,hpp` -- **returns nothing.**

**So the predicted silent coverage gap does not exist.** `src/edu`, `src/help`,
`src/meta` and the rest are inside the scanned root.

### 2a. The number that pointed at the wrong cause

The envelope's reasoning rested on 205 being suspiciously close to `src/cli`'s
203, and it flagged the two-file difference as "unexplained either way".
Re-measured today with the marker the miner actually keys on:

    usage-contract .cpp tree-wide      231     (envelope 2026-08-12: 229)
    usage-contract .cpp + .hpp         235     (envelope: 233)
    usage-contract .cpp in src/cli     205     (envelope: 203)

**`src/cli` now holds exactly 205 -- the same number the ad-hoc build reported
mining.** The agreement is closer than it was when the question was written, and
it is a coincidence: the root is `./src` and cannot produce a `src/cli`-shaped
result. A numeric near-match invited a causal story, the story was checkable,
and checking it took one grep for the root string.

### 2b. What the 205-vs-231 gap actually is

Not scope. **26 files carry `@dottalk.usage` and sit outside `src/cli`**, all
inside the scanned root:

    src/dewey/cmd_hier.cpp                 src/ext/cmd/cmd_student_echo.cpp
    src/edu/edu_ascii_table.cpp            src/ext/cmd/cmd_student_hello.cpp
    src/edu/edu_bibletalk.cpp              src/help/helpdata_messages.cpp
    src/edu/edu_boolean.cpp                src/help/helpdata_source_miner.cpp
    src/edu/edu_case.cpp                   src/meta/metacollect.cpp
    src/edu/edu_christmas.cpp              src/tv/cmd_foxpro.cpp
    src/edu/edu_cobol.cpp                  src/tv/cmd_foxtalk.cpp
    src/edu/edu_edit.cpp                   src/tv/cmd_generic.cpp
    src/edu/edu_erp.cpp                    src/tv/cmd_recordview.cpp
    src/edu/edu_evaluate.cpp
    src/edu/edu_formula.cpp                (src/edu 16, src/tv 4, src/ext 2,
    src/edu/edu_hanukkah.cpp                src/help 2, src/dewey 1, src/meta 1)
    src/edu/edu_idx.cpp
    src/edu/edu_missing_shims.cpp
    src/edu/edu_normalize.cpp
    src/edu/edu_six.cpp
    src/edu/edu_text.cpp

**The reframed question for Phase 1 is therefore about BLOCK WELL-FORMEDNESS,
not roots:** the marker `@dottalk.usage` appears in 231 files, `@dottalk.end`
only 17 times tree-wide, and the miner reported 205. Whether a file with the
marker always yields a minable contract is now the open question, and it is a
different investigation from the one the envelope framed.

**NOT asserted as a defect**, for the same reason the envelope declined to: the
205 figure comes from an ad-hoc build transcript, not from a run made under
observation. **The next step is to mine and count, not to reason further.**

### 2c. Correction to a count this steward took first

An initial pass reported 578 contract-bearing `.cpp` tree-wide against the
envelope's 229 and nearly filed it as drift. The pattern was `@dottalk\.` --
which matches `@dottalk.file`, the FILE HEADER carried by 578 files, not a usage
contract. The vocabulary, measured:

    @dottalk.file 582   @dottalk.usage 266   @dottalk.subusage 49
    @dottalk.end 17     @dottalk.contract 11  @dottalk.location 6
    @dottalk.pdlc 5     @dottalk.external 2   @dottalk.locale 1

`@dottalk.usage` is the contract marker; `@dottalk.file` is provenance metadata.
**A near-miss of the same shape as 2a, caught one step earlier.**

## 3. Q2 and Q3 remain open, untouched

- **Q2 -- `foxref` and `FILE()`.** Decision needed: add a `foxref.hpp` entry
  recording the deliberate divergence from VFP, or leave foxref silent.
- **Q3 -- `risk:` blocks are not harvested.** Measured in the envelope: risk
  keys appear 0 times in built HELP DATA. A lane question, not a defect;
  recorded so nobody writes more expecting them to surface.

## 4. The comment collection system the owner asked for ALREADY EXISTS

On 2026-08-24 the owner asked for "a comment collection system -- collects and
compares comments changed in source file -- probably python", flagged minor
priority. It was never built, and it did not need to be:

    tools/comments/reharvest_source_comment_catalog.py
    tools/comments/build_source_comment_refresh_candidate.py
    tools/comments/audit_source_comment_escrow.py
    tools/comments/upsert_source_comment_contract.py
    tools/comments/tests/test_reharvest_source_comment_catalog.py

with a run corpus already on disk under
`runs/DOCFLUSH-20260716-001/comments_reharvest/` carrying inventory, delta,
review-queue and disposition CSVs across four dated passes.

**Prior art, found by looking rather than building** -- the lesson this session
paid for three times today.

## 5. Good Neighbour

    What changed      : this document, and the `gate1/` directory it sits in.
                        No code, no data, no contract, no source comment.
    Whose area        : the run record is this lane's. `src/**` was READ ONLY --
                        the miner, the bridge and the header defaults were read,
                        never modified.
    What authorization: the owner's question, "why can't you read g01".
    How to verify     : `grep -rn 'roots.push_back' src/cli/cmdhelp.cpp` shows
                        `./src`; a tree-wide search for a `src/cli` scan root
                        returns nothing; `grep -rl '@dottalk\.usage' src
                        --include=*.cpp | wc -l` returns 231, of which 205 are
                        under `src/cli`.
    How to undo       : delete this file.
