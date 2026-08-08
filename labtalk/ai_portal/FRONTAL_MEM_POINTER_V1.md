# Frontal_Mem -- persistent-memory thesis (root project pointer)

**Status:** in-repo pointer to a folder-side artifact. Owner: member.derald. Date 2026-08-08.
This is a stub, not the thesis. It exists so the root project is reachable in one hop from the
portal; the body stays human-side and owner-promoted (thesis SS1.5 human-side memory locus,
SS4.5 hybrid promotion). Registered as recall node `root.frontal_mem`.

## What Frontal_Mem is

The ROOT project this repo's memory work serves: Derald's thesis and design for AI memory that
persists across sessions. Claim: persistent knowledge between sessions is achievable now,
without advancing the model, by a human-memory-shaped pipeline -- hold experience briefly,
triage it by value, promote the valuable, let the rest decay, and recall through typed
associative links ("synapses"). The model is stateless; long-term memory lives human-side in
the owner-controlled store. The aim is selective forgetting with reliable recall of what
mattered, not total memory.

## Where the body lives (not in this repo, by design)

The standalone Frontal_Mem project folder, sibling to ccode. Key files:
- `thesis_persistent_memory.md` -- the thesis (SS1-8 + appendices; SS1.5 memory is human-side,
  SS4.6 the value gate also runs on the agent's own work: unreasoned deferral is demotion).
- `thesis_memory_architecture.svg` -- consolidation pipeline + recall graph + BBS substrate.
- `DESIGN_bbs_pseudochat_two_lanes.md`, `PLAN_pseudochat_lane.md` -- the realization path
  (a live exchange consolidates into an attributed BBS post through the value gate).
- `PLAN_bbs_shell_provenance_fix.md` -- AIF-075 provenance (the trust layer), implemented.
- `AI_Portal_schemas.md` -- the 12 SYS* DBF tables. Contains real member keys; kept OUT of the
  tracked/deployable tree deliberately (exposure control).
- `AI_PORTAL_ONBOARDING_SUMMARY.md`, `SESSION_HANDOFF_2026-07-31.md`.

Status: working draft, review-needed. Importing it into the repo is a human-owned promotion
decision; this pointer is the reversible, zero-exposure alternative that still makes the root
reachable.

## In-repo faces (what already realizes the thesis here)

- **The recall graph is the thesis's recall graph.** Typed edges are realized; the
  strength-weight / decay / reinforce dimension (thesis 5.3) is still design-only.
  `labtalk/registries/portal_recall_graph.yaml`, resolver `labtalk/ai_portal/recall.py`.
- `SYNAPSE_CONCEPT_V1.md` -- synapse doctrine (defers to the thesis's Appendix A definition).
- `AI_GLOSSARY_V1.md` -- coined vocabulary, including the thesis's durable principles.
- `docs/maintenance/COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md`,
  `docs/maintenance/SEED_RISE_PLAN_TWO_ATOM_V1.md` -- the two-atom ontology.
- Substrate: the AI-BBS (durable store), AIF-075 provenance (trust layer), the pseudo-chat lane
  (short-term-to-long-term consolidation channel).

## Open thesis work (not started here)

The consolidation / triage service (the value function: acted-on, costly-to-learn,
re-referenced, contradiction, novelty; hybrid promotion; grandfather rollups) is SPECIFIED, not
built. The recall graph's decay-and-reinforce is design-only. These are the genuinely new work;
storage, locking, and the bus already exist.

## Reached by

`trigger.persistent_memory -> root.frontal_mem`; also `trigger.onboard -> root.frontal_mem`.
From here the synapse concept and glossary are one more hop.
