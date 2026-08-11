# Memo Zoo Orthogonality Stress Charter V1 -- the zoo proves the cage

**M1 SOAKED (2026-08-11, same day as chartering).** `src/memo/memo_zoo.cpp`
(target `memo_zoo`), six driver personas, shadow oracle, embedded-NUL and
high-byte payloads, Temporal Collapse reopens, steady-state settle, final
reopen sweep. Four seeds green: 20260811 (500 gens / 1,584 ops),
7 (5,000 / 22,353), 42 (5,000 / 29,648, genesis population 200),
1993 (10,000 / 50,459, reopen every 50). Totals: 20,500 generations,
104,044 ops, ~215 reopen cycles, ZERO divergences. Payload-agnosticism,
cross-memo isolation, and reopen durability: RUNTIME-PROVEN at the store
level. Emergent ecology finding, replicated across all seeds: predation
(Hawk merge + Otter erase) drives every population to the floor (8) --
Merge-Hawks are apex predators in every world; a Turtle-bias rebalance is a
tuning note, not a proof gap. M2 (Sentinel as a second process, FLOCK) and
the hibernation window remain open.

**Status:** review-needed charter (authored 2026-08-11). Owner: member.derald.
Coauthor of record: member.ai.claude.cowork (Coworker, Class A).
Parent claim under test: **memos are payload-agnostic and orthogonal** --
status board tier today: source-evidenced (`src/memo/memo_ref.cpp`); this
charter's harness promotes it to runtime-proven, or finds out it should not.
Provenance: external stimulus ("Quantum Memo Zoo"), an AI-generated stress
spec supplied by the owner 2026-08-11; MAPPED into house terms below, not
adopted verbatim (intake-style: received ideas are source material, not
authority).

## 1. The reframe that makes it rigorous

The Zoo describes memos WITH behavior. x64base memos HAVE NO behavior --
and that is precisely the claim under test. So: species are DRIVER PERSONAS,
not memo properties. A seeded harness performs each species' chaotic
operation pattern AGAINST the store through the public API
(`put_text` / `update_text` / `get_text`; delete verb: M0 discovery). The
store passes if it remains a passive, byte-faithful cage no matter what the
animals do:

- no operation on memo A ever changes the bytes of memo B (isolation);
- every readback byte-matches what was last written (fidelity), including
  deliberately corrupted, binary-ish, and empty payloads (agnosticism);
- close/reopen mid-chaos loses nothing (durability -- the memo_smoke
  reopen precedent, at scale);
- concurrent driver processes serialize via FLOCK without corruption
  (the Sentinel's real job).

## 2. Oracle design (the house discipline, applied)

- **Shadow model:** the harness keeps an in-memory map ref->bytes and
  mirrors every operation. After each generation, full sweep: store readback
  byte-compares against the shadow. First divergence = hard fail with the
  seed, generation, and op log printed. (The dual-carrier pattern: shadow as
  oracle, exactly as SQLite referees SQLSEL.)
- **Determinism:** one PRNG, one seed, printed in the banner. Any failure is
  replayable with `--seed N`. No wall-clock dependence in op selection.
- **Event log:** the driver records every op (species, ref, op, byte count)
  -- ancestry and mutation history are DRIVER bookkeeping, not a store
  requirement (the store owes bytes, not genealogy).

## 3. Species -> API-verb mapping (v1 cast chosen to cover every verb)

| Species | Driver behavior | Verb class it stresses |
| --- | --- | --- |
| Entropy-Fawn | mutate random chars in own payload, update | update_text, fidelity of corrupted text |
| Pointer-Beetle | overwrite first 64 bytes of a RANDOM OTHER memo | update_text cross-memo; isolation of neighbors |
| Stack-Serpent | grow on access; shed oldest half past threshold | update_text large/growing/shrinking payloads |
| Fork-Turtle | duplicate self (new put of copied bytes) | put_text under population growth |
| Merge-Hawk | concat two payloads into one, retire sources | put + retire (delete verb or empty-update; M0) |
| Null-Otter | empty a payload | zero-length payloads (agnosticism edge) |
| Chrono-Slug | churn catalog metadata only, never the memo | store indifference to sidecar-table churn |
| Sentinel-Ram | second PROCESS: FLOCK, verify sweep, log | cross-process locking + concurrent oracle |

Echo-Moth folds into Fork-Turtle (duplicate with mutation); ecosystem
events are batch modes of the above (Fork Bloom = all turtles fork one
generation; Entropy Winter = fawn rate x10; Temporal Collapse = close and
reopen the store mid-run). Population cap is a DRIVER rule; at the cap the
harness measures store behavior at scale, it does not expect the store to
police reproduction.

Two stressors from the spec's earlier draft (owner FYI, 2026-08-11), added:

- **Hibernation:** a memo is declared immutable for an interval. The driver
  enforces the vow; the Sentinel holds the table FLOCK across the window --
  proving other writers block cleanly and the sleeper's bytes are identical
  on wake (a quiet-period durability probe).
- **Steady state:** after the chaos phases end, N quiet generations of
  read-only sweeps must show ZERO divergence drift -- the ecosystem settles
  and the oracle stays green with nobody writing. Catches deferred-write
  and cache-flush ghosts that only surface after the noise stops.

Population range 50-500 per the spec; "evolving new fields" is catalog/
driver bookkeeping, not a store behavior (the store owes bytes, not
schema).

## 4. Placement and shape

A standalone C++ harness beside the existing smoke test
(`src/memo/memo_smoke.cpp` is the template and precedent): links the memo
lib only, no CLI dependence. Flags: `--seed`, `--generations`,
`--population-cap`, `--reopen-every`. Success output ends with one line:
`MEMO-ZOO: N generations, M ops, 0 divergences, seed S` -- the transcript
checkpoint. A second entry point (or flag) runs the Sentinel as the
concurrent process for the FLOCK phase.

## 5. Milestones (proofs named in advance)

- **M0 Discovery:** does the backend expose a delete/retire verb, or is
  retirement empty-update by convention? Practical payload ceiling? Confirm
  memo_smoke's build wiring as the harness's CMake template.
- **M1 Solo zoo:** single process, full v1 cast, shadow oracle,
  10k+ generations across several seeds, reopen-every included. Green =
  agnosticism + isolation + fidelity + durability runtime-proven.
- **M2 Sentinel:** two processes (zoo + ram) against one store; FLOCK
  serializes; oracle stays green. Green = concurrency claim proven at the
  memo layer (bbs_store's append discipline, generalized).
- **M3 Promotion:** status board's payload-agnostic entry advances to
  runtime-proven citing the harness line; the WORKSPACES catalog inherits
  the confidence (its snapshots are just one well-behaved animal in a
  proven cage).

## 6. What this deliberately does not claim

No transactional guarantees beyond what the ACID page already scopes; no
claim that the store polices content (it must NOT -- policing would violate
agnosticism); no simulation-for-its-own-sake -- every species exists to
stress a verb, and a species that stresses nothing new is zoo decoration
and stays out of v1.
