# AI Glossary -- coined vocabulary of the portal + Frontal_Mem (index)

**Status:** maintained index. Owner: member.derald. Date 2026-08-08. Registered as recall node
`doc.ai_glossary`; reached from `trigger.onboard`. This is a **pointer index**, not a corpus:
each term gets one line and a home. Definitions live in the homes; this file just makes the
vocabulary reachable in one hop. It is not hosted in the frontal seed (byte budget + AIF-082);
it is reached by trigger.

**Root project.** These terms serve **Frontal_Mem** -- Derald's persistent-memory thesis: the
model is stateless, so long-term memory lives human-side in the owner-controlled store (git,
DBF, curated docs), and a session's job is to consolidate the worthy, attributed, normalized
fraction into that store before it decays. The full thesis lives in the **Frontal_Mem** project
folder (standalone, outside the ccode repo: `thesis_persistent_memory.md`,
`thesis_memory_architecture.svg`, the two-lane design, the pseudo-chat plan); its in-repo faces
are the ontology, the seed-rise plan, and the recall graph named below.

## A note on "atom" (two senses -- do not conflate)

- **Ontological atom** -- one of the two irreducible entities, *chat* and *project*. In this
  sense a quip is a relation, not an atom.
- **Registered primitive ("atom" of the toolset)** -- a first-class, implemented, registered
  building block (has an AIF, code, and a test). In THIS sense **quip is an atom** -- it is an
  established primitive, not a loose coinage. Both senses are valid on different axes.

## The two atoms (ontology)

- **chat** -- the acting atom: a bounded-context session that does work and must reach memory.
- **project** -- the durable atom: the owner-controlled store that holds memory across sessions.
- Home: `docs/maintenance/COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md`;
  `docs/maintenance/SEED_RISE_PLAN_TWO_ATOM_V1.md`.

## Registered primitives (implemented -- AIF + code + test)

- **quip** -- an ephemeral heads-up between concurrent sessions; the lightest coordination rung.
  Registered (AIF-050), implemented in `tools/coordination/session_coordinator.py`
  (`quip send`/`quip read`), tested in `test_session_coordinator.py`. Not a fresh coinage --
  an established primitive.
- **claim-aif** -- the atomic lane-number allocator (`O_EXCL`); the allocator, not grep.
  Same coordinator; ledger at `coordination/aif/AIF-NNN.claim`.
- Coordination surface home: `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`,
  `docs/maintenance/COORDINATION_DEVELOPER_MANUAL_V1.md` (+ operator manual).

## Recall / memory mechanism

- **synapse** -- a typed, directed, strength-weighted link between two memories; the unit of the
  recall graph (Frontal_Mem thesis, Appendix A). In the portal, the typed recall-graph edge;
  triggers are the entry stimuli. Home: `SYNAPSE_CONCEPT_V1.md`.
- **recall graph** -- the portal's synapse network: typed nodes + edges + triggers. This is the
  in-repo realization of Frontal_Mem's "recall graph (typed links, decay-and-reinforce)," which
  the thesis still lists as design-only. Home: `labtalk/registries/portal_recall_graph.yaml`,
  resolver `labtalk/ai_portal/recall.py`.
- **trigger** -- an intent ("about to cut a release") that fires the synapses hung off it.
- **frontal memory** -- the always-injected layer: Tier-0 generated state, the Tier-1 seed, and
  the vendor shims. Points, never hosts. Homes: `labtalk/ai_portal/AI_TIER1_SEED_V1.md`,
  `TIER0_STATE.md`, `CLAUDE.md`, `AGENTS.md`.
- **seed budget / gate** -- 8192 B hard ceiling on the Tier-1 seed; adding requires demoting.
  Gate: `tools/staging/check_seed_budget.py`; contract:
  `labtalk/ai_portal/TIER1_MAINTENANCE_CONTRACT_V1.md`.

## Durable principles (Frontal_Mem doctrine)

- **human-side memory locus** -- the model is stateless; durability lives in the store, not the
  model. (Thesis SS1.5; in-repo face: the two-atom ontology.)
- **action now or demote** -- unreasoned deferral is the agent scoring the work low; it then
  decays. If you defer, name the reason. (Thesis SS4.6.)
- **normalize on collect** -- atomic, deduped, linked by default; costed rollups (grandfather
  pattern) only when a full rebuild is too dear.
- **reachable, not just filed** -- filing is storage; a synapse is retrieval at the right
  moment. The active form is: when something was hard to find, synapse it.
- **provenance is mandatory** -- an unattributed record poisons a trust-based store
  (made concrete by AIF-075).
- **the recurring defect pattern** -- something reports success without doing its job
  (author-zero posts, a consumer committed without its definition, a handoff written where a
  clone cannot see it). **Verify before you rely; trust the measurement, not the success
  message.**
- **openness is a one-way door** -- released-open cannot be pulled back; income is preserved by
  dual-license + copyright + CLA, never by "open then close." Home:
  `docs/maintenance/licensing/LICENSING_PRINCIPLE_ONE_WAY_DOOR_V1.md`.

## Derived / conceptual terms

- **session / run / member** -- terms over the chat atom (an acting instance / its run id / the
  identity acting); not atoms themselves. Home: coordination protocol.
- **handoff** -- a session's consolidated close-out to the next session; must be placed where a
  clone can see it (versioned), not in an untracked dir.
- **pseudo-chat** -- the short-term-to-long-term consolidation channel; a live exchange
  consolidates into an attributed BBS post through the value gate. Home:
  `docs/maintenance/PSEUDO_CHAT_RETURN_LANE_V1.md`.
- **Good Neighbor policy** -- the external-AI conduct rule. Home:
  `docs/maintenance/GOOD_NEIGHBOR_POLICY_V1.md`.
- **Class A / Class B partner** -- capability tiers for an acting agent (file/shell/tools vs
  chat-only); capability is a property of the deployment, not the brand. Home:
  `labtalk/ai_portal/EXTERNAL_CALL_CONTRACT_V1.md`.

## Reached by

`trigger.onboard -> doc.ai_glossary`; `doctrine.synapse -> doc.ai_glossary` (requires). Add a
term by adding a line here and, if it needs its own entry point, a trigger + synapse in the
recall graph. Do not inline definitions into the seed.
