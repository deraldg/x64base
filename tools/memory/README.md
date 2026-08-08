# tools/memory -- consolidation triage (Frontal_Mem M2 core)

The thesis's "heart of it" as running code: the value function that decides which of a
session's working memories are worth promoting to durable store, and which decay. Reached from
the recall graph via `trigger.persistent_memory` (node `mechanism.consolidation_service`).

## What it is (and is not)

`consolidate.py` is the JUDGMENT half of the triage step, decoupled from storage on purpose.
It reads a session working-set, scores each candidate on the five value signals, and emits a
HYBRID promotion proposal -- the agent proposes, the owner confirms. It is dependency-free
(stdlib only) and does NOT write to the durable store. The write into Lane 1 (the attributed
BBS/DBF post path, AIF-075) is a separate confirmed adapter, so the same value function serves
the future C++ `PSEUDO PROMOTE` (Lane 2) and the Ollama-chat promotion (Lane 3).

## The value function (thesis Section 4)

Five signals, each normalized to 0..1, weighted:

| signal | evidence field | saturates at | weight |
| --- | --- | --- | --- |
| acted_on | `acted_on: bool` | -- | 0.30 |
| cost_to_learn | `cost_to_learn_min` | 60 min (an hour) | 0.25 |
| referenced | `references` (count) | 3 recalls | 0.15 |
| contradiction | `contradicts` (id/null) | present | 0.15 |
| novelty | `novelty` (0..1) | 1.0 | 0.15 |

Score is the weighted sum. Decision: `PROMOTE` at >= 0.55, `DISCARD` at <= 0.30, else `HOLD`
(borderline -- surfaced for the owner). A candidate marked `superseded_by` is `DISCARD`
regardless of score (thesis 5.2). Contradictions never silently lose: they raise the score and
set `needs_reconsolidation` (thesis 5.5).

The thresholds are tunable by domain cost-asymmetry (thesis 4.4): `--bias small_trusted_store`
raises both bars (over-promotion is the graver sin), `--bias expensive_relearn` lowers them
(under-promotion is graver). Over- and under-promotion are not symmetric errors.

Normalize on collect: duplicate candidates (same `dedupe_key` or normalized summary) collapse
to the highest-scoring one; compression is itself a kind of forgetting.

## Usage

```
# agent proposes
python3 consolidate.py propose --in fixtures/session_2026-08-08.json --out proposal.json
python3 consolidate.py propose --in ws.json --bias small_trusted_store --emit-recall

# owner confirms (hybrid promotion); only approved PROMOTE/HOLD items reach the manifest
python3 consolidate.py confirm --proposal proposal.json --decisions decisions.json --out manifest.json

python3 consolidate.py weights          # show defaults
python3 -m unittest test_consolidate -v # tests
```

`decisions.json` is a map `{ "candidate_id": "approve" | "reject" }`. The confirm step is where
owner authority lives; the manifest it emits is the input to the Lane 1 write adapter.

## Dogfood acceptance

`test_consolidate.py::test_reproduces_hand_triage` asserts the tool reproduces, on this
session's working-set, the same PROMOTE/DISCARD decisions the agent made BY HAND in
`docs/maintenance/SESSION_CLOSEOUT_PORTAL_MEMORY_SYNAPSE_2026-08-08.md`. Automated gate agrees
with hand-run gate, or one of them is wrong.

## Status and the remaining seam

- BUILT (M1): the value function, hybrid propose/confirm, normalize-on-collect, dedupe,
  cost-asymmetry bias, recall-stub emit. Tested, dependency-free.
- NOT built: the Lane 1 write adapter (attributed post via `current_member()`/`post_new`,
  stamped with the source-lane marker) and the grandfather-father-son rollups (M3, scheduled
  "sleep"). Those touch the engine and are maintainer/host-side.
- Coordination: this is a fresh lane -- claim a new AIF (do NOT reuse AIF-052); see
  `docs/maintenance/DESIGN_bbs_pseudochat_two_lanes.md` work breakdown and
  `PLAN_pseudochat_lane.md` M2. The design/plan docs currently live in the Frontal_Mem folder.
