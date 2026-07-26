# DD-series data-dictionary specs -- closed generation (archive)

**Status:** historical record. **Not an active lane.** Committed 2026-07-25 under AIF-062.

## What this is

545 spec, `_AUTOLOG_v0`, and `_NEXT_ACTIONS_v0` documents from the DD-series data-dictionary
work, written **2026-05-27 through 2026-05-30** -- a four-day burst. Nothing in the directory has
been modified since (one file, `DD-004_DD004_NEXT_ACTIONS_v0.md`, was touched 2026-07-14).

## Why it is committed rather than ignored

It was untracked for two months and was nearly gitignored as scratch. One line stopped that:
`AIF-015` (2026-07-14, in `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`) cites **DD-001 / DD-002 /
DD-004** among the sources it consulted when separating the engine/index and lean/education product
axes.

A live lane citing these specs as its evidence base means a reader of AIF-015 must be able to follow
the citation. An uncommitted citation target is the same failure this session found in the proof
registry: **the record claims support from an artifact nobody else can see.** See
`docs/maintenance/AI_EVIDENCE_LAYER_VERSIONING_LANE_V1.md` (AIF-062).

Committing 545 markdown files is cheap. A broken citation trail is not.

## How to read it

- **Closed generation.** Treat every file here as historical unless a current lane doc says
  otherwise. Do not resume a `_NEXT_ACTIONS_v0` from this directory without checking whether the work
  landed elsewhere -- much of it did.
- **`_AUTOLOG_v0` files** are generated run logs from that period, not hand-authored specs.
- **Naming** (`DD096ZD2ZU`, `DD-004`) is that generation's sequencing scheme and does not map onto the
  current `AIF-###` lane numbering.
- If you need a fact from here, **verify it against current source** before relying on it. Two months
  of engine work sit between these documents and `development` as it stands.

## If this ever becomes active again

Give it a lane number in `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` and a lane doc, the
same as any other work. Do not reactivate it by editing files in place -- that would leave the
archive and the active work indistinguishable, which is the condition this README exists to prevent.

Owner: `member.derald`.
