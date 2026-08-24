# AIF-120 Application UI DSL -- Lane Seed v1

Status: **durable seed for anyone resuming lane `application-ui-dsl`**
Authority: `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md` (the charter)
Steward: member.derald. Lane agent: ALPHA (member.ai.claude.cowork).

This is the smallest sufficient start. It does not restate the charter, the
contract or the rulings -- it says which one answers which question, and it
records the failure modes this lane has actually hit, so the next agent does not
have to rediscover them at the same price.

## What the lane is, in one paragraph

Give the existing GUI a language: a portable UI description other people can
generate frontends from. The deliverable is a **design table** -- a DBF with a
memo sidecar, sixteen fields, three record kinds -- and any DSL *text* is a
convenience over it. That choice is not fashion: FoxPro's own screen designer
stored its work as a DBF, so a DBF engine wanting a portable UI description has
thirty-year-old prior art with the same shape.

## Authority chain -- ask the right document

| Question | Document |
|---|---|
| Why does this lane exist, what are its gates | `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md` |
| What does a field/kind/property MEAN | `docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md` |
| Why is a specific decision the way it is | `docs/maintenance/AIF120_*_V1.md` -- one ruling per unit |
| What is settled, open, and owed to whom | the newest `SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_*.md` |
| Which ruling lives in which file | the closeout's index table |
| What outside sources describe VFP formats | `docs/manuals/developer/dev/dev-23-external-references.md` |

**Read the closeout first.** It is the only one of these that tells you what is
currently false.

## Three facts that govern everything else

1. **Geometry is INTENT.** `FLOW` and `ORDINAL` are the model; absolute
   coordinates are quarantined in `ORIGIN` with their unit attached. A pixel does
   not travel to a character grid.
2. **Four backends, and each must SAY what it cannot do.** wx, Tk, HTML,
   character cell. A target that silently drops something the document states is
   the defect -- not the target that reports a loss.
3. **VFP is the source of the DOCUMENT FORMATS only.** Runtime semantics come
   from x64base, measured. Never cite VFP for behaviour.

## The corpus regenerates -- never hand-edit a fixture

    cd gui/uidef
    python3 author_cases.py        # the refusal/acceptance fixtures
    python3 author_frame.py ...    # five other author scripts

The `.DBF`/`.FPT` pairs are BUILD PRODUCTS and are untracked by design; the
prepush gate blocks `.dbf` outright. If a fixture is wrong, fix the author
script.

## Standing constraints -- these are not suggestions

- **Never `git add -A`, `git add .`, or a bare directory.** The rule is about
  BREADTH, not spelling. Stage explicit paths. Hand all mutating git to the
  steward as PowerShell.
- **No `git status` in any form from a sandbox or across the device mount** -- it
  takes `.git/index.lock`, which cannot be unlinked across the mount. Read-only
  `log`, `ls-files`, `cat-file`, `grep`, `show` are fine.
- **One authoritative copy.** Edit the working tree. Do not build in a scratch
  directory and push whole files over the tree afterwards.
- **The author does not self-approve.** Every ruling ships `review-needed`.
- **ASCII only.** Use `--` and `->`.
- **Agents do not write to `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`** -- hand a
  Good Neighbor note to the steward to transcribe.
- **Always look for prior art before building.** Twice this lane has written a
  procedure for a mechanism that already existed.

## Failure modes this lane has actually hit

Recorded because each one cost real time and each one is repeatable:

- **A search shaped by the object you have cannot find an object with a different
  schema.** Hit three times: a widow sweep with an extension whitelist that
  missed `.csv` and `.mjs`; a property scan matching `pr.get()` that could not
  see fonts and could not tell a DOC row from an OBJ row; a grep for
  `localtime_r` that could not see the `#ifdef _WIN32` guard three lines above
  it. Every flat grep over-reports. Group by the schema before concluding.
- **A caveat is not a control.** A comment saying a thing is unproven does not
  stop an earlier section claiming it is proven.
- **A fix that lands at a SITE instead of at the RULE comes back.** Corrections
  49, 51, 52, 54 and 55 are all this shape.
- **A working tree that already contains a file hides the fact that a clone does
  not.** Fixtures (R75) and then the VFP reader (R87) both failed this way, and
  the second one had a comment describing the first.
- **A generated projection can be regenerated at the wrong moment.** Do not
  hand-manage `TIER0_STATE.md`; a pre-commit hook owns it.
- **Markdown wrapping moves a citation away from its `cite-check:ignore`
  marker.** The marker suppresses only its own physical line.

## Where the proof is

Screenshots and transcripts live in `docs/maintenance/evidence/`. A ruling that
says "built and run" names its evidence file. If a ruling claims a measurement
and points at nothing, treat the claim as unproven and say so -- that has
happened here and the correction is in the record.
