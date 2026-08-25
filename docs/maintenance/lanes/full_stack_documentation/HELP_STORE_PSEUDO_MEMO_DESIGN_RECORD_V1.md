# The HELP store is a pseudo-memo, and it is the project's first system

    Recorded : 2026-08-25, run COWORK-20260824-001 (member.ai.claude.cowork)
    Told by  : member.derald, owner, in session
    Subject  : dottalkpp/data/help/* and src/help/helpdata_export_dbf.cpp
    Status   : **review-needed.** A design record and a ruling, not a change
               request. The store keeps running.

## Why this document exists

The reason the HELP store looks the way it does lived in exactly one place --
the owner's memory -- and he had forgotten it himself. He said so plainly:

> this help system was the first one I wrote so it was x32, also I had no real
> memo of any kind, so I made a pseudo memo with help lines. I didn't know
> whether to upgrade it or keep it for an artifact, then I forgot about it,
> because it works

An undocumented rationale is the live hazard here. Not the format.

## The design, stated

`HELP_LINE` carries unbounded help text the only way a fixed-width DBF can:
**one logical line is split into 240-byte PARTS across numbered rows**, and the
reader reassembles by `LINE_NO` + `PART_NO`. That is a memo field written in
the vocabulary the format had at the time, because the engine had no memo type
yet. The store is dBase III (`0x03`) for the same reason: it predates x64.

`split_parts(logical_line, 240)` in `helpdata_export_dbf.cpp` is the writer.

## It does not strain

Measured on the live store, 2026-08-25:

    PART_NO   1: 29,255 rows     2: 6 rows     3: 1 row
    rows at exactly 240 chars (the spill point)  : 6
    longest reassembled logical line             : 719 chars (DOT|VDISK line 1)

**Seven continuation rows out of 29,262.** The mechanism does exactly what it
was built for and almost never has to.

## The dogfooding exception, ruled

House rule: **documentation databases are x64.** Other flavours are supported
deliberately -- the `dbf/x32/*` fixtures, `V32_help/`, the VFP and Fox26 memo
specimens are all correctly not-x64, because covering those formats is the
point of them.

Live tables under `dottalkpp/data`, by format:

    0x64  224      0x03  38      0x30  19      0x83  2      0xf5  2

Of the 38 dBase III tables, all but one group are deliberate flavour coverage.
The exception is the documentation store itself:

    0x03  HELP_LINE  HELP_TOPIC  HELP_SECTION  HELP_ARTIFACTS  COMMANDS  CMD_ARGS

Manualgen's `MAN*` catalog **is** `0x64`. So the two documentation stores
disagree, and HELP is the one out of step.

**RULING: the exception stands, for now, and it stands deliberately.** HELP is
the subsystem every other lane measures itself through; converting it puts the
measuring instrument on the bench, to buy conformance in a store showing no
functional strain. "It works" is a real engineering argument and it is now
being made on purpose rather than by neglect. If the store is converted later,
that will be one decision with this record behind it rather than the same
decision taken twice.

## What WAS fixed, because it was a real loss and format-independent

`NAME` was `C40`. Measured before the change: **84 rows carried a NAME at
exactly 40 characters** -- real message keys losing their tails, e.g.

    SET_MESSAGE_CATALOG_VALIDATION_STATUS_TE|XT
    SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_TEX|T

Checked against source: **no two DISTINCT keys collided.** Nothing was
ambiguous. But nothing in the store could have said so either way, because
truncation destroys the evidence that anything was lost -- the row that fit
exactly and the row that was cut are indistinguishable afterwards. That is R6
in a DBF writer, and it is the same shape as AIF-126's blank `TOPICKEY`.

Two changes, both independent of the format question:

1. **`NAME` widened 40 -> 64.** Longest live message key measured 55.
2. **`write_fixed` now COUNTS truncations and the export reports them.**
   Identity-carrying columns pass their name; unnamed columns still count
   toward the total, so a new overflow can never be invisible.

The second matters more than the first. A width is a guess that will be wrong
again eventually; a counter makes the next overflow announce itself.

## The artifact question dissolves

"Upgrade it" and "keep it as an artifact" read as alternatives only while the
running store and the historical design share one name. They are two things:

- the **store** is live infrastructure and keeps running;
- the **design** is the artifact, and this document plus the comment block at
  `helpdata_export_dbf.cpp` is where it is preserved.

Same move as canonical-workspace versus session-state (AIF-124): the dilemma
was two things wearing one name.

**Owed to v6's website phase:** this belongs on the public
`/docs/dev/historical-source-lineage` surface. The project's first system,
still in production, carrying a memo it had to invent -- that is exactly what
that lane is for. It is not there today.

---

## Good Neighbor note

    WHAT CHANGED   : this record, plus src/help/helpdata_export_dbf.cpp --
                     a design comment at the pseudo-memo writer, NAME widened
                     40 -> 64 in three tables, and truncation counting with a
                     report. No store rebuild yet; the running store is
                     untouched until the next CMDHELP BUILD.
    WHOSE AREA     : subsystem help, owner member.derald. The file was CLEAN
                     against HEAD before the edit.
    AUTHORIZATION  : member.derald, in session 2026-08-25 -- the design history
                     in his own words, and "do all of that" against a proposal
                     of exactly these three items.
    VERIFY OR UNDO : after a rebuild, the export prints nothing about
                     truncation when there is none, and HELP_LINE.NAME reads 64
                     wide. Undo is reverting the three edits; the pre-change
                     store is kept at dottalkpp/data/help.bak-*.
