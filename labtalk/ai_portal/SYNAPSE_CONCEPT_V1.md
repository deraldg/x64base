# Synapse -- a routed recall entry point (portal doctrine)

**Status:** hardened concept. Owner: member.derald. Date 2026-08-08. Procedural doctrine, not
legal or build advice. Registered as recall node `doctrine.synapse`; reached from
`trigger.understand_why`.

## Definition

Canonical (Frontal_Mem thesis, Appendix A): **a synapse is a typed, directed,
strength-weighted link between two memories -- the unit of the recall graph.** It decays with
disuse and reinforces on recall (thesis 5.3), so frequently walked paths harden into highways
and unused links fade.

In the portal, that graph is `labtalk/registries/portal_recall_graph.yaml` (resolver
`labtalk/ai_portal/recall.py`): nodes are memories, **edges are the synapses** (typed
`fires_at` / `requires` / `evidenced_by` / `supersedes`), and **triggers** are the entry
stimuli that fire the synapses hung off an intent. A memory with no synapse is **dark**: it is
on disk, it is correct, and no one reaches it when they need it -- thesis 5.1, "a memory that
cannot be reached is, functionally, a memory that does not exist." Filing is storage; a synapse
is retrieval at the right moment. Doing the first without the second is the failure this
concept names.

## Why it exists (the founding incident)

The editions/build/licensing facts -- a real CMake edition system, an education strip, package
manifests, an already-separated engine -- took **over an hour to rediscover** on 2026-08-08.
They were filed in the tree the whole time. They had no entry point, so from a cold session
they were dark. The fix was not another document. The fix was a **synapse**:
`trigger.release_or_license -> mechanism.editions_licensing`. One hop, from the intent ("I am
about to cut a release or decide licensing") to the knowledge.

## The rule that falls out of it

**When knowledge was hard to find, do not just file it -- synapse it.** The reflex "write it
down" is only half done. The second half is: give it a trigger entry point in the recall graph
so the next agent, or the next you, reaches it from the *intent* that needs it, not from
remembering the filename. This is the active form of the portal's older maxim "reachable, not
just filed."

Concretely, a synapse is complete when:
1. the knowledge lives in a maintained artifact (its own file), and
2. a `trigger.*` node names the intent that should surface it, and
3. an edge (`fires_at` / `requires`) connects them, and
4. `recall.py --validate` passes (no orphan, no dangling path).

## Relation to the two-atom model

Under the coordination ontology (`docs/maintenance/COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md`)
the **project** is the durable atom that holds memories; the **chat** is the acting atom that
must reach them within a bounded context. A synapse is how the acting atom reaches the durable
atom's memory *at the right moment*. A memory the chat cannot reach in one or two hops does not
functionally exist for that chat -- which is the recall graph's whole thesis.

## Frontal memory points; it does not host

The always-injected "frontal" layer -- the Tier-1 seed (`AI_TIER1_SEED_V1.md`) and its vendor
shims (`CLAUDE.md`, `AGENTS.md`) -- is under a hard byte ceiling (8192 B, enforced by
`tools/staging/check_seed_budget.py`) and the AIF-082 rule "invariants and pointers only, no
perishable literals" (`TIER1_MAINTENANCE_CONTRACT_V1.md`). So the frontal memory does not
*host* concepts like this one or the glossary -- it **points**, via the recall graph, which
costs the seed zero bytes. Synapses are precisely how the tiny always-read surface stays tiny
while everything remains reachable: the seed holds the triggers; the synapses route to the
bodies. Adding a body to the seed would blow the ceiling; adding a synapse does not.

## Lineage: this is Frontal_Mem's recall graph, made concrete

The synapse is not a new invention here -- it is the in-repo realization of the **Frontal_Mem**
persistent-memory thesis, whose "recall graph (typed links, decay-and-reinforce)" is still
listed there as design-only. The portal recall graph is that pillar wearing work clothes:
typed nodes + edges exist; decay-and-reinforce is the remaining thesis work. Building synapses
is building the thesis.

## See also

- `AI_GLOSSARY_V1.md` -- the coined-term index (this concept is one entry).
- `labtalk/registries/portal_recall_graph.yaml` -- the synapse network itself.
- `docs/maintenance/COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md` -- the two atoms.
- Frontal_Mem thesis (Cowork project, `thesis_persistent_memory.md`) -- the root work stream.
