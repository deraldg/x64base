# Concurrent AI-Session Coordination Protocol v1 (AIF-050 coordination component)

**Status:** candidate (dev-only; not promoted) · **Filed:** 2026-07-22
· **Owner:** member.derald · **Steward/author:** member.ai.claude.cowork · **Lane:** AIF-050.
· **Tool:** `tools/coordination/session_coordinator.py` · **State:** `coordination/`.

## Why (the proven failure)

Multiple AI/Cowork sessions run on one branch and one working tree with no coordination. The only
shared state is git (which stamps every commit with the maintainer, hiding the real author) and a
hand-edited intake queue that many agents append to at once. On 2026-07-22 four parallel sessions
collided on AIF-047 → 048 → 049 → 050 in a single sitting, and were caught only by reading `git log`.
Documentation cannot fix a coordination problem; an allocator and a presence surface can.

## The mechanism (filesystem-atomic, because that is the medium sessions actually share)

`coordination/` holds three things:

- `aif/AIF-NNN.claim` — **durable** allocation ledger. Claiming a number is an **atomic
  `O_CREAT|O_EXCL` create**: if two sessions race for the same number, exactly one wins the create;
  the loser sees "already claimed" and takes the next free. This is a real allocator, not a
  convention. Tracked + committed, so the ledger is shareable.
- `active_sessions/<run_id>.yaml` — **transient** presence (member, run, lanes, files, heartbeat).
  Gitignored. Lets a session *see* who else is live before it touches anything.
- `locks/<file>.lock` — **transient** advisory lock on a contested shared doc. Cooperative: check
  before you edit; stale locks (older than the reap window) are reapable. Gitignored.

## The protocol (every session, in order)

1. **Check in.** `session_coordinator.py checkin --member <m> --run <run> --lanes <...> --files <...>`
2. **Before opening a *new* lane, claim its number atomically** — never hand-pick from the intake:
   `session_coordinator.py claim-aif --member <m> --run <run> --lane "<name>"` → prints the number
   you own. (Use `--number N` only to formalize a number you already, verifiably, hold.)
3. **Before editing a contested shared doc** (the intake queue, dashboard, `CURRENT_TARGET.md`,
   `AI_PORTAL.md`), take the lock: `session_coordinator.py lock <path> --run <run>`. If it is held,
   coordinate or wait; do not edit under someone else's lock.
4. **Edit, then release**: `session_coordinator.py unlock <path> --run <run>`.
5. **Check the room anytime**: `session_coordinator.py status` (taken numbers, next-free, active
   sessions, held locks).
6. **Check out at end**: `session_coordinator.py checkout --run <run>`.

## Doctrine (the rules that make it hold)

- **Number assignment is single-writer** (AIF-050 contract invariant 6): the atomic claim, or the
  maintainer, allocates — never a free-for-all append to a shared file.
- **Locks are advisory but binding by agreement**: an AI partner honors a held lock the way it honors
  any gate. The maintainer (owner) is the tiebreaker.
- **Presence is courtesy, not permission**: checking in does not grant rights; it makes the room
  visible so work does not silently overlap.
- **This coordinates, it does not authorize**: coordination sits *beside* the identity/RBAC gates
  (AIF-045) and the promotion gates — it prevents collisions, it does not confer authority.

## Enforcement (the claim is not optional -- the commit chokepoint proves it)

The claim step above is coordination; this makes it binding. Every parallel session funnels through
one place: the maintainer's commit. So the duplicate-number check runs there, regardless of whether
any session bothered to run the coordinator.

- **Detector:** `tools/coordination/aif_collision_gate.py` -- HARD fails (exit 1) on a duplicate
  `AIF-NNN` in the intake queue; advisory reconciliation of the claim ledger vs intake (`--strict`
  promotes it to hard).
- **Gate:** `tools/staging/prepush_gate.py` runs the detector by default and folds a duplicate into
  its HARD-BLOCK lane (exit 2), alongside its build-tree/binary blocks and data-fixture warnings.
  Flags: `--strict-aif`, `--skip-aif`.
- **Automatic on every commit:** `python tools/staging/prepush_gate.py --install-hook` writes
  `.git/hooks/pre-commit`, so `git commit` runs the gate with no one having to remember.
  **Hooks are NOT version-controlled -- run `--install-hook` once per machine / clone / worktree.**
  Bypass a single deliberate commit with `git commit --no-verify`.

Proven: clean tree PASS; synthetic and full-root double-`AIF-048` FAIL (exit 1 -> block).

## Limits / honest reach

- Coordinates **local concurrent sessions on one machine/working tree** — the actual scenario. It is
  not a distributed lock service; cross-machine or cross-clone coordination would need the committed
  ledger + a fetch, not the transient presence files.
- Advisory locks depend on cooperation; a non-cooperating writer can ignore them (the maintainer is
  the backstop).
- Clock-skew affects stale-reaping windows; keep the reap window generous.

## Cross-references

- Lane: `AI_RUN_TRACEABILITY_LANE_V1.md` (AIF-050); contract invariant 6 in
  `AI_RUN_TRACEABILITY_CONTRACT_V1.md`.
- Run registry (presence's durable cousin): `labtalk/registries/ai_runs.yaml`.
- Portal doctrine: `AI_PORTAL.md` (Ownership and Authorship; Prove the Bottleneck First).
