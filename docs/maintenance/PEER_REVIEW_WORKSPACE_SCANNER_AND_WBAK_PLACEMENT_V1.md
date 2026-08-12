# Peer review: the WORKSPACE OPEN scanner, and where WRITEBACK's backups live

Owner: `member.derald`. Status: **review-needed, nothing built.**
Steward/author: `member.ai.claude.cowork`. Lane: AIF-070 (coworker).
Companion: `RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md` (operations),
`MEMO_RESIDENT_MINIDB_V1.md` (mechanism).

Written for a **one-way review session**: it assumes no back-channel, so every
claim below carries the measurement that produced it and the command that
reproduces it. Where something is unmeasured it says so.

**Nothing in the scanner or the writeback backup path has been changed.** Work
was stopped deliberately at the point a ruling is needed. The regression that
exposed the first finding (`workspace_wbak_scan.dts`) is written and green but
UNREGISTERED, pending the same ruling.

---

## 1. What is being reviewed, and why it is ONE review

Two symptoms were found on 2026-08-12. They look like separate bugs and are
not: both live in `WORKSPACE OPEN`'s directory scanner, and a fix for either
lands in the same function.

- **A. The scanner admits backup sidecars as tables.** `WORKSPACE OPEN DBF`
  over a root containing `.__wbak` / `.__fldbak` files opens them as work
  areas.
- **B. `WORKSPACE OPEN <dir>` resolves CWD-relative and fails silently.**

Reviewing them separately risks two rulings that do not compose -- a filter
decision and a resolution decision arriving in the same function from different
reviews, in either order.

There is also a third question the maintainer raised that reframes A entirely
(section 5): the backups need not be in that directory at all.

---

## 2. Finding A -- backups become tables

### What was measured

The maintainer's own console, a routine open over the x64 root:

    Area 5: opened 'FMGRTST.__fldbak.dbf'

Then, deliberately, with writeback's backups present
(`workspace_wbak_scan.dts`, 4/4 markers green, Linux g++ Release):

    Area 12: opened 'ROOMS.__wbak.dbf'  [index: ROOMS.cdx, attached]
    ...
    WORKSPACE: 26 table(s) opened into area(s) 0..25.

**26 areas for a workspace whose posture declares 13.**

### Why it is worse than a count

Each backup **attached the live table's index**. `ROOMS.__wbak.dbf` is bound to
`ROOMS.cdx`, an index built over different records. An ordered read or `SEEK`
on that area follows an ordering that was never built for it and reports
success while doing so. This is the house's most-hunted failure shape, arrived
at by two correct components meeting.

### Why it compounds

`WORKSPACE SAVE <name> MEMO MINIDB` walks every OPEN area. So:

    WRITEBACK ... CONFIRM  ->  OPEN DBF  ->  SAVE MEMO MINIDB

mints a container whose **posture declares the backups as members**, and the
next cycle backs those up in turn. The contamination reaches the manifest,
which is the one place this subsystem cannot tolerate it: the posture is the
enumeration authority, and the entire writeback design rests on that.

### Scope, stated fairly

The scanner's blindness PREDATES writeback -- `.__fldbak` comes from
`FIELDMGR APPEND`. Writeback did not create the defect. What writeback changes
is the frequency: every `CONFIRM` mints N backups into the exact directory an
operator then points `SET PATH DBF` at.

---

## 3. Finding B -- OPEN &lt;dir&gt; resolves against the process CWD

### What was measured

From `cwd = dottalkpp`, with `DO x64` in effect:

| Spelling | Result |
|---|---|
| `WORKSPACE OPEN <absolute path>` | 15 tables |
| `WORKSPACE OPEN data/DBF/x64` (CWD-relative) | 15 tables |
| `WORKSPACE OPEN DBF/x64` (DATA-relative) | **0 tables, no message** |
| `WORKSPACE OPEN DBF` (the slot) | 14 tables |
| `WORKSPACE OPEN students` (bare stem) | opens via the slot |

### Why it matters

The runtime usage text **already promises the opposite**:

    - Relative targets resolve from SETPATH/INIT slots, primarily DBF.

`DBF/x64` is the DATA-relative spelling every other verb uses, and the one
`SET PATH DBF` itself takes. The scanner takes the raw token instead. A miss
prints nothing -- the operator sees an empty workspace and no reason for it.

### Relationship to the fix that landed today

Commit `5a4f9b3ec` closed exactly this split for three other surfaces
(`WORKSPACE WRITEBACK TO`, `ERASE DIR`, `FILE()`), routing them through
`paths::resolve_in_slot`: absolute stays absolute, a token containing
separators is DATA-root-relative, a bare name sits in its slot. That commit's
message records what the split cost -- a regression that wrote to one directory
and asserted against another, producing six green markers off a directory it
had never written.

`WORKSPACE OPEN <dir>` is the **fourth surface**, found after the commit, and
it is the only one that fails silently. It was deliberately left untouched
pending this review rather than folded in.

---

## 4. Retention facts for `.__wbak`, measured

The maintainer asked what the retention period is, and whether it is
session-scoped. Neither was documented. Measured (three writebacks, two
confirmed, against the 13-table MCC posture):

| Question | Answer |
|---|---|
| Does a backup exist after CONFIRM? | yes |
| Does a second CONFIRM chain `.__wbak.__wbak`? | **no** |
| Does the backup hold the immediately-prior content? | yes |
| Does it still hold the generation before that? | **no -- silently discarded** |
| File census after 3 writebacks | 15 live + 15 backups, stable |

So retention is **not session-scoped**. It is **generation-scoped at depth one,
kept on disk indefinitely**. Nothing expires it, nothing sweeps it, and nothing
announces that the previous backup was discarded. Two confirmed writebacks and
your first undo is gone. Walk away and the last one sits in the DBF root
forever.

Memo sidecars ARE preserved (`STUDENTS.__wbak.dtx`), so a recovery is complete
as far as depth one goes.

**Unmeasured, stated as unknown:** whether depth one is sufficient for the
recovery scenarios the owner has in mind. That is a requirements question, not
an engineering one, and it belongs to the reviewer and the owner.

---

## 5. The option the maintainer raised, which changes the shape

> "have you considered the house tmp, also we can add new paths with add path"

Measured:

- **`TMP` is a real, settable slot** -- `SET PATH TMP <path>`, listed in the
  live `SETPATH` slot list. The `Slot` enum additionally carries `TMP_OUT` and
  `TMP_SYSTEM`, which `SET PATH` does not currently expose.
- **`SET PATH ADD` does not exist.** The grammar is
  `SETPATH <slot> [TO|=] <path>` -- single-valued, one path per slot, no list
  and no append form. Multi-path slots would be new grammar, not a new
  argument.

Routing backups to a TMP-rooted location **dissolves finding A for `.__wbak`
without touching the scanner at all** -- the files simply leave the DBF root.
It also gives retention somewhere to live: a tmp area can be aged out, and the
current scheme has no expiry story whatsoever.

The tension to rule on: the undo of last resort would no longer sit beside the
thing it undoes, and if TMP is ever swept, the undo goes with it. **A depth-one
backup that can be swept is a materially thinner guarantee than one that
cannot.** Note this does NOT address `.__fldbak`, which has its own producer.

---

## 6. Options

### For A (backups as tables)

| # | Option | For | Against |
|---|---|---|---|
| A1 | Filter `*.__wbak.*` / `*.__fldbak.*` in the scanner | one place, fixes both producers, fixes existing trees already carrying backups | encodes a naming convention into the scanner; a future producer with a different suffix is missed again |
| A2 | Writeback writes backups to a sibling directory | scanner stays naive | changes a landed-file layout now proven and documented; does not fix `.__fldbak`; existing trees still carry backups |
| A3 | Writeback writes backups under a TMP-rooted path | dissolves the symptom AND gives retention a home | undo separated from its subject; sweepable; does not fix `.__fldbak`; existing trees still carry backups |
| A4 | A1 + (A2 or A3) | belt and braces: existing trees cleaned by the filter, new backups out of the way | two changes, two review surfaces |

**Steward's note, offered as opinion not conclusion:** A1 is the only option
that repairs trees that ALREADY contain backups, and the only one that covers
`.__fldbak`. A3 is the only one that answers retention. They solve different
halves, which is why A4 exists.

### For B (silent CWD-relative OPEN)

| # | Option | For | Against |
|---|---|---|---|
| B1 | Route through `paths::resolve_in_slot`, matching the four surfaces fixed in `5a4f9b3ec`, and make a miss LOUD | one rule everywhere; honours what the usage text already promises | changes behaviour for any caller relying on CWD-relative today |
| B2 | Keep resolution, only make the miss loud | smallest change; no behavioural break | leaves the usage text lying, and leaves the fifth surface out of step with the other four |
| B3 | Leave it, document it | zero risk | a silent zero-table open stays a silent zero-table open |

---

## 7. What is NOT claimed

- No claim that `.__wbak` recovery is broken. It is proven to work
  (`WB_T9`, both toolchains): the backup opens as a 200-record table holding
  the prior content.
- No claim that finding A is writeback's fault. It predates writeback.
- No claim about what depth of retention is CORRECT. Only what it currently is.
- No claim that the Windows run discriminated the path fix. It could not --
  `datarun.ps1` sets cwd = DATA, which makes both resolutions identical. The
  fix was discriminated on Linux, where they diverge.

---

## 8. Decisions requested

1. **A:** which of A1 / A2 / A3 / A4.
2. **B:** which of B1 / B2 / B3, and whether B rides with A or lands separately.
3. **Retention:** is depth one, kept forever, the intended contract? If not,
   what is -- and does it need an expiry, a depth, or an explicit
   "your previous backup was discarded" notice?
4. **Registration:** does `workspace_wbak_scan.dts` become a registered
   regression (`kRegressionSpecs`), stay an unregistered candidate, or get
   folded into `workspace_writeback.dts`?
5. **Numbering:** does this get its own AIF? It is not AIF-070's -- the scanner
   predates that lane -- and any verb taking a relative directory is exposed.

---

## 9. Reproduce

    REGRESSION RUN WORKSPACE_WRITEBACK        # 12 markers, the writeback contract
    dottalkpp --script data/scripts/workspace_wbak_scan.dts   # finding A, 4 markers
    REGRESSION FIND memo ram                  # locate related specs

Finding B, by hand from a cwd that is not DATA:

    DO x64
    WORKSPACE OPEN DBF/x64                    # opens nothing, says nothing
    WORKSPACE OPEN DBF                        # opens the slot, works

Retention, by hand: writeback to a scratch root, mutate a landed table, write
back with CONFIRM, repeat, then look for `*.__wbak.__wbak.*` (absent) and read
the sentinel out of `*.__wbak.dbf` (holds only the last generation).
