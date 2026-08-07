# Session Coordination -- Developer Manual V1

Status: proposal (review-needed), authored 2026-08-07, lane AIF-096.
Owner `member.derald`; steward `member.ai.claude.cowork`. ASCII (`--`, `->`).

Internals and extension guide for `tools/coordination/session_coordinator.py` and the
Tier-0 projection. For usage, see `COORDINATION_OPERATOR_MANUAL_V1.md`. For the design
model and its lineage, see `COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md` (AIF-096) and
`AI_SESSION_COORDINATION_PROTOCOL_V1.md` (same directory).

## 1. The model this implements

Two atoms. **chat** is mortal: it acts (claims, quips, edits) and forgets. **project** is
durable: it records and does nothing on its own. The acting atom cannot remember and the
remembering atom cannot act, so ALL identity and state live on the project, as files, and
a chat's first move is to read them. Everything below is the filesystem being the memory
the chat lacks. "session", "run", "presence", "member", "claim", "quip", "handoff",
"lineage", "aside" are derived terms over the two atoms -- none is itself an atom.

## 2. On-disk data model (`coordination/`)

The filesystem is the only medium concurrent local sessions reliably share, so every
primitive is a file, and durability is decided by `.gitignore`, not by code.

| Path | Meaning | Lifetime |
| --- | --- | --- |
| `aif/AIF-NNN.claim` | lane number allocation (aif, run_id, member, lane, claimed_utc) | DURABLE (tracked) |
| `lineage/<run>.yaml` | birth record (run_id, member, parent, born_utc) | DURABLE (tracked) |
| `active_sessions/<run>.yaml` | presence (run, member, lanes, files, heartbeat_utc, status) | transient (gitignored) |
| `quips/<run>/*.quip` | one ephemeral note per file (from, to, sent_utc, msg) | transient (gitignored) |
| `locks/*` | advisory file locks | transient (gitignored) |

The split is the point: what must survive a chat's death (allocations, lineage) is
tracked; what means nothing across time or machines (presence, quips, locks) is not.
`coordination/.gitignore` encodes this -- ignore `active_sessions/ locks/ quips/`,
negate (`!`) `aif/` and `lineage/`.

## 3. Constants and helpers

    COORD, AIF_DIR, SESS_DIR, LOCK_DIR, QUIP_DIR, LINEAGE_DIR   -- the paths above
    AIF_LO=6, AIF_HI=999   -- claim scan range
    STALE_MIN=240          -- presence/heartbeat older than this is reapable
    now()                  -- tz-aware UTC "...Z"; avoids utcnow() deprecation (py3.12)
    active_runs(root)      -- runs with a non-closed presence file
    holds(root, run)       -- AIF numbers whose claim cites this run (the aside chain)
    _age_min(stamp, now)   -- minutes since an ISO-Z stamp, or None if unparseable

## 4. Command surface (function : CLI)

    claim_aif(root, member, run, lane, want=None)   : claim-aif  --member --run --lane [--number]
    release_aif(root, number, run, force)           : release-aif --number --run [--force]
    checkin(root, member, run, lanes, files)        : checkin    --member --run [--lanes] [--files]
    checkout(root, run)                             : checkout   --run
    wake(root, member, run, parent=None)            : wake       --member --run [--parent]
    lock(root, target, run) / unlock(...)           : lock/unlock <target> --run
    status(root)                                    : status
    quip_send(root, frm, to, msg)                   : quip send  --from --to --msg
    quip_read(root, run, since=None, ack=False)     : quip read  --run [--since] [--ack]

## 5. Invariants (do not regress these)

- **Allocation is atomic, not hopeful.** `claim_aif` creates the claim file with
  `O_CREAT|O_EXCL`; if two sessions race for a number, exactly one wins the create. Grep
  is never an allocator -- a stale grep re-derives a taken number as free (AIF-078 scar).
- **Lineage is write-once.** `record_birth` uses `O_EXCL`; a resumed run re-waking keeps
  its original `born_utc` and `parent`. Re-waking never rewrites birth. It survives
  checkout, which is the whole reason it is a separate durable file from presence.
- **Report effects, not intentions.** `quip_read --ack` prints `acked N of M` and names
  any file it could NOT unlink; `checkout` reports when it cannot remove presence and
  marks the record closed instead. The bug both avoid: `except OSError: pass` on a mount
  that refuses unlink, then printing success. This shape recurs -- guard it.
- **Liveness is surfaced, not assumed.** `quip_send --to all` refuses when no peer is
  live; a direct quip to an absent run still delivers but WARNS (warn-and-deliver) and
  points to the durable board. The tool teaches the channel ladder at the point of use.

## 6. The Tier-0 projection (`labtalk/ai_portal/generate_tier0_state.py`)

The generator READS the coordination files and renders a small, can't-drift snapshot
(`TIER0_STATE.md`, target under 4096 B). Relevant readers:

    claimed_lanes(root)        -> (aif, lane, member) newest number first
    active_sessions(root, now) -> (run, member, stale) ; stale = age>STALE_MIN or unparseable
    lineage_records(root)      -> run -> {parent, born_utc, member}
    run_asides(root)           -> (run, member, [AIF-nnn ascending]) newest run first

`run_asides` is the horizontal structure -- a run's ordered claims. The
"Sessions, lineage, asides" section joins these: live check-ins (stale-marked, so an
abandoned straggler is never shown plainly live), and per run its parent, birth, and aside
chain. This is the identity model rising into the generated middle tier -- it rises by
REGENERATION (the pre-commit hook runs `--write`), never by hand.

## 7. Testing

`tools/coordination/test_session_coordinator.py` (stdlib, `python tools/coordination/test_session_coordinator.py`)
guards the primitives against silent rot. Cases: quip direct/broadcast/ack; ack honest
when unlink is refused (monkeypatches `Path.unlink` to raise -- exercise the FAILURE path,
not the happy one, or the test inherits the code's blind spot); quip warn-and-deliver to
an absent target; wake records durable lineage and survives checkout; wake whoami reads
identity from the record; claim atomic and unique. Add a case whenever you add a primitive.

## 8. Extension seams

- **New primitive:** add the function, wire an argparse subcommand + dispatch in `main`,
  decide durability (tracked vs gitignored) in `coordination/.gitignore`, and add a test
  that exercises its failure path.
- **New Tier-0 view:** add a reader that returns plain tuples/dicts, render it in
  `render()`, and keep the file under `SIZE_TARGET`. Never assert; the file is a
  projection of the ledger, regenerated, never authored.

## 9. Environment constraints

- **Sandbox (mounted Linux):** stdlib runs fine, but git must be read-only
  (`git --no-optional-locks`); a killed mutating git can leave a zero-byte `.git/index.lock`
  that blocks the maintainer. Cross-mount `unlink` may fail -- which is exactly why the
  honest-ack and honest-checkout paths exist. You cannot build or run the engine here;
  coordination is pure-python and needs neither.
- **Host:** the pre-commit hook regenerates `TIER0_STATE.md`; the pre-push gate blocks
  duplicate AIF numbers and non-ASCII in added lines. Register a claim's intake row in the
  same slice, or the collision gate and the Tier-0 "MISSING" mark will flag it.
