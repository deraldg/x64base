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
- **the golden rule (verify before you assert)** -- never report a change as "done" unless you
  verified it. For anything you cannot test in-session -- a host-only build, an engine run, a
  live service -- get ground truth first (run it, read the actual error) or hand the
  verification off explicitly; do NOT assert done. The sharpened form of "trust the measurement,
  not the success message," earned 2026-08-08 when three host-only changes were each asserted
  working and each broke. Evidence: `proof.golden_rule_verify_before_assert`.
- **openness is a one-way door** -- released-open cannot be pulled back; income is preserved by
  dual-license + copyright + CLA, never by "open then close." Home:
  `docs/maintenance/licensing/LICENSING_PRINCIPLE_ONE_WAY_DOOR_V1.md`.

## Derived / conceptual terms

- **session / run / member** -- terms over the chat atom (an acting instance / its run id / the
  identity acting); not atoms themselves. Home: coordination protocol.
- **handoff** -- a session's consolidated close-out to the next session; must be placed where a
  clone can see it (versioned), not in an untracked dir.
- **aside** -- a side trip taken during a task in progress to correct or check out a side issue,
  then return to the main task. **Rule (standing, owner 2026-08-08): an aside does not need its
  own PDLC or AIF unless it is promoted** into standing work; a promoted aside graduates to a
  claimed lane like anything else. This keeps the main task moving without ceremony for every
  small detour, while still catching the ones that turn out to matter.
- **recursion / recurse back** -- the call-stack view of stepping back: stepping out of the current
  task to handle a side issue is a push (a new frame), "recurse back" is the pop (return to the
  frame underneath). An aside is one such frame. Home: `RECURSION_MARKERS_V1.md`.
- **recursion marker** -- a short greppable breadcrumb (`RECURSED OUT -> / IN <- / BACK <-`) placed
  in the SDLC/PDLC artifact at each push/pop so the movement pattern is trackable and an
  un-returned step-back (an `OUT` with no `BACK`) surfaces as a leak instead of vanishing. The
  temporal/movement complement to the recall graph's semantic edges. Home: `RECURSION_MARKERS_V1.md`.
- **pseudo-chat** -- the short-term-to-long-term consolidation channel; a live exchange
  consolidates into an attributed BBS post through the value gate. Home:
  `docs/maintenance/PSEUDO_CHAT_RETURN_LANE_V1.md`.
- **Good Neighbor policy** -- the external-AI conduct rule. Home:
  `docs/maintenance/GOOD_NEIGHBOR_POLICY_V1.md`.
- **Class A / Class B partner** -- capability tiers for an acting agent (file/shell/tools vs
  chat-only); capability is a property of the deployment, not the brand. Home:
  `labtalk/ai_portal/EXTERNAL_CALL_CONTRACT_V1.md`.

## The team model (AI agencies as coworkers -- reinforced 2026-08-08)

Each AI agency (Claude, Grok, Codex, Ollama) is accepted as a **team-member entity**: a
first-class member in the identity system, not a tool. An agency holds an AI/service login token
(`USER TOKEN`), acts under real attribution (`current_member()`, AIF-075) exactly as a human
member does, and is assigned lanes as a coworker (see the Grok Lane 1 assignment). Human and AI
members are the same kind of entity in the store; only `author_kind` differs. This is the
lightweight member layer -- the store's answer to "manage the users," an attributed identity
sitting under the BBS.

- **team-member entity / coworker** -- an AI agency holding a member identity + service token.
  Home: `src/cli/cmd_user.cpp` (`USER LOGIN`/`AS`/`TOKEN`), `src/identity/identity_admin.cpp`
  (`current_member`, `login`); conduct rule: `docs/maintenance/GOOD_NEIGHBOR_POLICY_V1.md`.
- **the four communication axes** -- every exchange is one of ai<->ai, human<->human,
  ai<->human, human<->ai, and all four ride the same attributed substrate (BBS Lane 1) plus the
  pseudo-chat lanes. Worked examples this session: the owner posted an assignment to the board
  (human->ai) and Claude assigned Grok on `board.afb.chat` (ai->ai) -- both attributed, both
  durable, same channel.

### Joining a lane (acceptance workflow)

An AI member joins a lane by: (1) **accepting the assignment** (the coworker takes the lane),
then (2) **picking up the project frontal memory** -- the always-loaded entry context for that
project, retrieved by its recall trigger (e.g. `trigger.persistent_memory` returns the
Frontal_Mem working set). General onboarding (`trigger.onboard`) may run **before or after** that
pickup, whichever is more efficient: a coworker already onboarded to the repo goes straight to
the project frontal memory; a cold agency onboards first. The order is an efficiency choice, not
a fixed gate.

- **project frontal memory** -- the per-project always-loaded entry context: its pointer plus the
  recall working set its trigger returns. The project-scoped analog of the Tier-1 seed.

### Leaving a lane (exit workflow) -- the symmetric other half

On the way out (session end / checkout) the member **updates the project frontal memory**: it
writes back what it learned so the next member picks up the advanced state, not the stale one.
The exit is where consolidation runs -- a triage program promotes the session's short-term
working memories into long-term store (semantic / episodic) through the value gate, and the rest
decays. Entry and exit are symmetric: **pick up** the frontal memory coming in, **update and
triage to long-term** going out. Triage engine: `tools/memory/consolidate.py` (score + hybrid
propose/confirm) -> `promote.py` (attributed write). See `mechanism.consolidation_service`.

## Reached by

`trigger.onboard -> doc.ai_glossary`; `doctrine.synapse -> doc.ai_glossary` (requires). Add a
term by adding a line here and, if it needs its own entry point, a trigger + synapse in the
recall graph. Do not inline definitions into the seed.
