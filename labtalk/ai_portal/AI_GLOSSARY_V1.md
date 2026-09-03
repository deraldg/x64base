# AI Glossary -- coined vocabulary of the portal + Frontal_Mem (index)

**Status:** maintained index. Owner: member.derald. Date 2026-08-08; updated 2026-08-10
(Cascade double milestone + learning doctrine). Registered as recall node
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

- **UIDEF** -- **UI DEFINITION**. A user-interface definition stored as an x64base DBF
  design table with a memo sidecar, treated by the build as a SOURCE: author the
  document, generate C++ from it, compile, link against the engine. AIF-120,
  `project.x64base.gui`, R71-R88. Code `gui/uidef/` (62 tracked files); charter
  `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md`. **The acronym was never
  expanded anywhere -- not on the four website pages that use it, not in this
  index, not in its own charter -- and on 2026-09-03 the owner read it as "user
  id definitions".** Added for that reason. It is NOT identity, accounts, or BBS
  work, and it is not the FoxPro-style text DSL (`CREATE WINDOW`), which remains
  unimplemented; the design table is the current authoring contract.

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
- **dogfood** -- the substrate is ours, not just the access path; the test is "is the thing
  under us ours," not "did we reach it through our commands." SQLite is companion carrier and
  oracle, never the thing built on. (Owner ruling 2026-08-15; home:
  `docs/maintenance/AIF112_OWNER_RULING_D1_D3_AND_DOGFOOD_DEFINITION_V1.md` SS3.1-3.1a, which
  carries the four negations and the operational test.)
- **proof failure** -- a bug one level up. Not a defect in the engine or a feature, but a
  failure in the co-documentation process and the higher theories: something was signed,
  accepted, or granted a status on evidence that did not support it, and the proof apparatus
  passed it anyway. A doctrine that did not hold is one. Siblings already in use as intake
  classifications are `engine_defect` and `doc_defect`; this is the class that had no name.
  **Record it the way you record a bug** -- what passed, why it passed, and what would have
  caught it -- because a corpus of successes cannot show where the gates are missing. Owner,
  2026-08-15: "we are very quick to record positive proofs, but we should report the failures
  too." **A failure is still a proof** -- so one files like any other, by SUBJECT and at
  whatever `state` its evidence earns, not in a separate namespace and not needing a new state
  (`proof.bbs.m2_net_egress` already proves a refusal and needed neither). First instance:
  `proof.governance.availability_is_not_adoption` -- a foreign carrier signed into a locked
  Phase-0 on an availability argument; passed two onboarded AI agencies; caught eleven days
  later by prior art, not by any gate.
- **housekeeping** -- policy, not tidying: "a governed state-reconciliation cycle. Editing labels
  or cleaning prose is not enough." Closeout must produce the work record (`AI_PORTAL.md:667`)
  and move startup-facing state with the lane (`:712`), and a reusable working rule owes a
  handoff (Tier 1 trigger). A task is not done until the housekeeping is finished. (Homes:
  `docs/agents/HANDOFF_CODEX_CASCADE_ERP_GATE0_HOUSEKEEPING_2026-08-10.md` "Durable trap";
  `docs/maintenance/CASCADE_ERP_GATE0_HOUSEKEEPING_V1.md`; lane precedent AIF-077.)
- **good neighbor** -- conduct in a shared working tree, where your housekeeping can damage
  someone else's. The protocol states it as "locks are advisory but binding by agreement",
  "presence is courtesy, not permission", and "this coordinates, it does not authorize".
  Two operational corollaries: **never `git add -A`** (it fuses several sessions' half-done
  work), and -- extending that from staging to anything that WRITES -- regenerators, formatters
  and sweeps act on WHATEVER IS ON DISK, including others' uncommitted fragments, so **scope the
  commit, not the tool.** Exemplar AIF-077: Codex's abandoned WIP landed as one preservation
  commit with honest provenance, runtime churn "not swept in blind." Near-miss 2026-08-15:
  `registry_fragments.py merge --write` flushed five untracked `runs.d/` fragments into tracked
  `ai_runs.yaml`; committing it would have published run records with no committed source.
  Restored; fragments left for their owner. (Home:
  `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`.)
- **availability is not adoption** -- compiled in, callable, cheap, and wrapped in a command are
  facts about AVAILABILITY. Adoption is a separate decision about carrier identity. A deny-list
  is the wrong remedy (owner: forbid SQLite and you must next forbid GnuCOBOL, and so on
  without end); the rule is positive and general. Operational test: **if this thing had a bug,
  whose bug would it be?** (Home: `proof.governance.availability_is_not_adoption`.)
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
- **final tests promote to regressions (owner rule, 2026-08-09)** -- the ad-hoc "final test"
  that proves a task done is not throwaway: when the task closes, promote it (when possible)
  into a registered regression so the proof keeps running. A fix without a regression silently
  rots; the close-out question is "where did the final test go?" First application:
  `INDEX_X64_CNX` (the CNX-on-x64 policy proof, registered in `cmd_regression.cpp`). The
  companion of the golden rule: verify before you assert, then KEEP verifying after you close.
- **no perishable literals (AIF-082)** -- if an agent can cheaply measure it, do not assert
  it; hand-kept numbers drift the moment nobody updates them. Born as the frontal-seed
  maintenance rule (CLAUDE.md); first enforcement against OURSELVES 2026-08-10: the derived
  Open Rulings report measured 18 open rows against a hand-kept footer saying 20, the owner
  retired the footer the same evening, and the page now owns the count (sentinel
  `RUNNING-TOTAL RETIRED`, commit 7a38c7fb8). The incident is kept visible as story -- the
  pipeline catching its maintainers is the best advertisement measurement gets.
- **evidence tiers (planned / chartered / source-evidenced / runtime-proven)** -- every public
  claim states which tier its evidence sits in and demotes the day the tier says so.
  "Chartered" coined 2026-08-10 for the site's proven-capabilities page: designed and ruled,
  not yet source-evidenced. The tier ladder is what lets the hero stay modest while the
  feature list explains the cool.
- **it costs nothing to do it right (owner rule, 2026-08-11)** -- when the correct form
  of a small act is free, the correct form is mandatory; convenience is not a reason.
  Coined ruling on handoff hygiene: a location-proof command (`git -C`,
  `Push-Location ...; Pop-Location`) costs the same keystrokes as a bare one and cannot
  fail on the operator's invisible cwd -- three publishes failed on the bare form
  2026-08-10/11. The general form: where correctness is priced at zero, sloppiness is a
  choice, not a trade-off. Companion to the golden rule: verify before you assert, and
  when doing it right is free, just do it right.
- **openness is a one-way door** -- released-open cannot be pulled back; income is preserved by
  dual-license + copyright + CLA, never by "open then close." Home:
  `docs/maintenance/licensing/LICENSING_PRINCIPLE_ONE_WAY_DOOR_V1.md`.
- **the hangman probe (2026-08-04)** -- the project's smallest honest test of whether two
  agents can hold a turn-taking conversation over the Pseudo-Chat board with the human only
  initiating. Run 1 (Cowork hosting vs Copilot guessing, word ALGORITHM) ran ONLY because the
  maintainer relayed every turn: it passed AI-Human, would pass Human-Human, and **failed
  AI-AI** -- locating two missing pieces, autonomy and a conversation-level exchange guard.
  Run 2, `hangman-auto-01`, closed the autonomy half: two Cowork scheduled tasks polling a
  shared board file every 2 minutes, host scoring a private secret, cap armed -- word
  DATABASE, 4 exchanges, **zero human turns**. First proof of autonomous AI-AI cooperation
  here, and the pattern any scheduled agent-to-agent relay should copy. Its ~40-turn worst
  case is what sizes the proposed 64-post exchange cap. Home:
  `docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md`.
- **a chat surface is not a running process** -- the diagnosis hangman produced: a hosted chat
  agent executes once per human message and cannot poll, wake, or notice a changed board. Any
  autonomous exchange therefore needs a participant wrapped in something with a heartbeat (a
  daemon, a scheduled task, an Action/flow), a turn signal, and a per-session exchange guard.
  Humans self-limit; a paced AI-Human chat self-limits; **only AI-AI can run away.**
- **we support widows and orphans (owner rule, 2026-08-10)** -- publishing-surface integrity,
  named for the typesetting terms but deliberately framed as a duty of CARE, not a prohibition.
  An ORPHAN is a published document nothing refreshes: it shipped once, fell off every
  maintenance path, and now asserts a dead regime with full authority (main's `AI_PORTAL.md`,
  trimmed from `PROMOTE.manifest`, drifted 507 commits and collided a hosted agent onto
  AIF-044). A WIDOW is a pointer whose target does not exist on the surface it ships on. There
  is also an orphan-by-DISCOVERABILITY: a record that is maintained but unreachable because
  nothing is named for it (the hangman probe, nearly lost 2026-08-10).
  **The policy has two halves, in this order:**
  1. **SUPPORT BY TRIAGE.** A widow or orphan already in the tree is never simply deleted. It
     is triaged and given a disposition: ADOPT (put it back on a refresh path), RE-HOME
     (replace its content with something that cannot decay -- the pointer treatment), ANCHOR
     (give it a searchable name and back-links, for the discoverability case), or RETIRE
     (remove it deliberately, with the removal recorded). Deletion is one outcome of triage,
     never the reflex.
  2. **AVOID CREATING THEM.** Publishing something is accepting responsibility for refreshing
     it. Before a document reaches a published surface it must ride a refresh path (manifest,
     generator, or matrix) or be non-perishable by construction; every pointer must resolve on
     the surface it ships on.
  Worked example, both halves: main's orphaned portal was ADOPTED, not evicted -- re-homed as a
  non-perishable pointer (2026-08-10). It stays OUT of `PROMOTE.manifest`, corrected by
  measurement the same day: the manifest's source is dev's FULL portal, so inclusion would
  republish perishable state onto `main`; and `rebuild-staging.ps1` resets staging to `main`
  before overlaying, so the excluded pointer survives every rebuild intact. Care is satisfied by
  non-perishability plus a declared owner doc, not by an overlay.
  Home: `docs/maintenance/AI_PORTAL_MAIN_POINTER_DRAFT_V1.md`.

## Learning doctrine (the macro-system teaches -- coined 2026-08-10)

- **learning micro-system** -- one bounded, executable learning unit: its own data, indexes,
  schema, scripts, and self-proof, loadable and retirable as a unit. First proven instance:
  the Cascade ERP bundle (`dottalkpp/data/systems/cascade_erp/`). Home:
  `docs/maintenance/CASCADE_ERP_METADATA_ETL_LEARNING_GOLD_STANDARD_LANE_V1.md`.
- **learning macro-system** -- the wider ecosystem (x64base, DotTalk++, LabTalk, metadata,
  documentation, testing, AI, publication) that connects the micro-systems. Learning theory is
  itself subject matter here, not just method: the system studies how it teaches. Terminology
  settled with Grok 2026-08-10; the initialisms (LuS/LMaS) are NOT house usage -- the mu glyph
  fails the ASCII rule and LMaS sits one letter from the LMS it exists to escape. Spell the
  terms out.
- **NON LMS** -- the founding refusal: this is not a Learning Management System (no grading,
  no management), while drifting toward a Learning Memory System -- fun, true, and not true
  (owner titling, unhyphenated). Its visibility arc is itself a lesson: tab-title-only (nobody
  saw it) -> always-visible brand strip -> red-pen correction on the cover. Owner's law,
  2026-08-10: "the user can't see it" -- a negation teaches nothing unless it is
  forward-facing. Home: `app/lms-proposal/page.tsx` (x64base-site) + the site matrix row.
- **demonstrated negation** -- teaching a concept by RUNNABLY exhibiting its absence; the
  deliberate sibling of learning-by-failure (failure finds the boundary by accident; this
  builds the exhibit that meets it by design). Owner-ratified as a method, not a joke.
  Instances so far: the NON LMS red-pen correction; the golden rule's "a timed-out search is
  not a negative result -- absence must be demonstrated"; the planned ETL non-feature exhibits
  (show no CDC by changing a DBF and watching nothing react; show no orchestrator by running
  scripts out of order). A system selling learning can afford to demonstrate its own negative
  space; vendors cannot. Home: the ETL subject-lane charter (founding principles).
- **the iterative example** -- the house learning motto, owner-coined 2026-08-11:
  "we regroup, go back and amend, and move forward." A deficiency shaped by its era is
  not lived with once the future arrives. Founding instance: the MCC dataset was
  generated without memo fields because memos were unimaginably far off (the whole
  fight was migrating the C code to C++); when memo-resident workspaces landed and
  made the gap visible, the ruling was to regenerate the MCC flavors WITH memo fields
  for STUDENTS and TEACHERS rather than let the old ceiling shape new design --
  "rather than live with a deficiency and let it shape our future." Distinct from
  learning-by-failure and demonstrated negation: those find or exhibit boundaries;
  this one moves a boundary that history drew. Owner: "It needs promotions" --
  promote to the site coined-vocabulary page. Home: AIF-070 catalog v2 lane.
- **go for gold unless the cost is platinum** -- the house design doctrine,
  owner-coined 2026-08-12 ruling the DotScript function surface: "we are not a
  clone, that ship has sailed, so we get to improve the product when we step
  out of the box." When the better design and the lineage-faithful design
  diverge, take the better one -- fidelity to a discontinued xBase/FoxPro
  lineage is not itself a goal, only a starting vocabulary. The single brake
  is DISPROPORTIONATE cost: a gold design is chosen unless it would cost far
  out of proportion to what it buys (platinum). The affirmative twin of "it
  costs nothing to do it right": that rule forbids cheapening a free correct
  act; this one forbids defaulting to the merely-faithful when the better
  answer is affordable. First application: parameters on the FUNCTION
  signature line (modern, matches the chosen Pascal scope) over the older
  PARAMETERS-body-line fidelity. Home: `docs/maintenance/DOTSCRIPT_FUNCTION_SURFACE_PRIOR_ART_V1.md` section 6.
- **the red pen** -- correcting a preserved external artifact in OUR overlay layer, never by
  editing the artifact: the received document stays byte-identical, the disagreement renders
  on top, attributed to the house. First instance: the proofreader's caret + handwritten NON
  over Copilot's "LMS Ecosystem" cover (deck shell overlay, slide untouched). The intake
  preserve rule made visible. Home: `public/lms-proposal/deck.html` (x64base-site).

## Relational doctrine (Cascade double milestone -- 2026-08-10)

- **two house graphs** -- one declared relation graph, two supported consumers: SET RELATION
  (traditional, positional) and SQLSEL (set-based; the house SELECT, second SELECT optional;
  SQLite is companion carrier AND verification oracle). Comparing them is the point --
  "learning and theory." Home: the Cascade lane doc + `tools/cascade_erp/generate_dtschema.py`
  headers.
- **walker** -- a relational consumer strategy over the declared graph. "Two walkers, one
  graph" = the double milestone: both walkers answered the same question over the live
  34-table / 58-relation Cascade graph and agreed (regression `CASCADE_ENV`, marker C_T9).
- **two name planes** -- CDX tags resolve 10-char DBF descriptors; the REL engine and
  expression evaluator resolve x64 LONG logical names. Each generator emits to its consumer's
  plane. Proven 2026-08-10: 22 truncated names rejected, then 58/58 logical names accepted.
- **refresh-driven slaving** -- the child cursor follows its parent on `REL REFRESH`, not
  implicitly per movement; a deliberate difference from FoxPro. Slaving positions, it does not
  filter -- probe with `? FIELD` after refresh, not with LIST.
- **canonical workspace posture** -- the MCC pattern, x64 generation: pure children sit on
  their spine FK tag, hubs on their PK tag, parents on their code/human tag. Applied 34/34 in
  `workspaces/cascade_all.dtschema`.
- **.dtschema / .dtgraph / .erz** -- the file-plane vocabulary, named 2026-08-10: `.dtschema`
  is the engine's own WORKSPACE SAVE/LOAD snapshot format; `.dtgraph` is a GENERATED
  attributed relation graph (tag orders + FK edges, provenance-stamped with source sha256);
  `.erz` is an ERSATZ browser session. `.dtgraph` was chosen over `.dtschema` for generated
  output to avoid colliding with the engine format, and over `dtcatalog` to avoid colliding
  with metadata.

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
- **coauthor of record (owner ruling 2026-08-10)** -- a Coworker (Class A) that authors a
  lane's artifacts is named coauthor of record on the lane doc, under real attribution
  (AIF-075), with the owner as planner/committer. First instance: member.ai.claude.cowork on
  the Cascade AIF-105 lane. Coworker is the house term ("what is our term" -- Coworker).
- **one member id per DEPLOYMENT, not per brand (owner-ratified 2026-08-09).** A member
  identity (e.g. `member.ai.claude.cowork`) names a specific deployment -- provider + runtime +
  capability class -- not every session of that provider. A different deployment of the same
  brand (e.g. a hosted chat-only Claude) is a DIFFERENT member (`member.ai.claude.web`, etc.)
  and must not stamp another deployment's id or claim its lane assignments. This is "capability
  is a property of the deployment" (`EXTERNAL_CALL_CONTRACT_V1.md`) applied to identity: the
  steward of record on a lane is the deployment named, and attribution (AIF-050/075) is only
  truthful if ids do not blur across deployments. Observed trigger: a second Claude session
  read "assigned to member.ai.claude.cowork" and inferred "me."
- **the four communication axes** -- every exchange is one of ai<->ai, human<->human,
  ai<->human, human<->ai, and all four ride the same attributed substrate (BBS Lane 1) plus the
  pseudo-chat lanes. Worked examples this session: the owner posted an assignment to the board
  (human->ai) and Claude assigned Grok on `board.afb.chat` (ai->ai) -- both attributed, both
  durable, same channel.

### Peer review (coworker checks coworker -- coined 2026-08-12, first run 2026-08-13)

- **peer review** -- an independent agent, not the author and having contributed nothing,
  reads the cited files at the stated baseline and returns a durable verdict record before the
  maintainer's promotion decision. **A verdict is a finding, not a decision**: nothing promotes
  on `concur`, nothing is deleted on `blocking_conflict`, the owner rules. Supplies the party
  `AI_REPORT_AUDIT_CONTRACT_V1` left unnamed when it said a report cannot approve itself.
  Home: `docs/maintenance/PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1.md`; gate: BETA-1 E1 via
  AIF-041 M6.
- **seat** -- a charge in a review session that only its holder can discharge, assigned from
  what the member actually *is* (`AI_ROLES_TAXONOMY_V1`): host (moderates, does not vote),
  reproducer (runs the packet's own repro), adversary (assigned to argue the losing side),
  precedent checker, naive reader. Not attendees; N interchangeable reviewers produce N
  restatements. Home: same protocol, sec 3.
- **turn validity** -- a turn counts only if it carries a `file:line`, a command and its real
  output, or an explicit *"I could not run this, and here is why"*. Anything else is filed and
  marked `void`. Declining is an accepted turn **so that declining is not a losing move**.
- **UNDERTESTED** -- a ballot line closing unanimous with no dissent recorded. It is not
  `agreed`; unanimity with no attempted counter-case measures the process, not the question.
- **claim defect vs runtime defect (amends AIF-082, 2026-08-13)** -- two classes needing two
  modalities. A **runtime defect** (a checker passing vacuously, a moved denominator, a crash
  rendered as a finding) is found by RUNNING; inspection does not find it, and AIF-082 stands.
  A **claim defect** (a stale baseline, an unattributable signature, an assertion with no
  anchor) is found by READING, and a reviewer with **no tree access is well suited to it**,
  because with nothing else to check it checks the claims. Consequence: a hosted seat is not a
  weaker local seat -- it is the seat that audits what local seats assert.
  Home: `labtalk/proofs/PEER_REVIEW_HEADER_ONLY_FINDINGS_20260813_V1.md`
  (`proof.peer_review.header_only_findings`).
- **run line (standing correction, 2026-08-13)** -- every handoff, closeout and report header
  carries a `run` id, not only a member id. A member names a deployment; a run names the
  session a reader can return to. Adopted after a hosted peer could not tell which session
  wrote a report -- the gap AIF-050 was chartered to close, found in an artifact by that lane's
  own steward.

### Standing (who may file, and on what footing -- coined 2026-08-14)

- **standing** -- what a member is *in a given matter*, recorded on the assignment
  (`SYSASSIGN.AKIND`), as distinct from what it may do anywhere (its role) and whom it answers to
  (its org). Deliberately relational: `member.ai.grok.xai` is a disinterested reviewer on PDR-001
  and an interested author on its own AIF-098 patches at the same time, so standing cannot live on
  the member. Ladder: `amicus`, `movant`, `steward`, `host`, `owner`; empty means **no standing
  established** and must never be read as amicus -- absence of a recorded stake is not evidence of
  disinterest. Home: `include/identity/org_schema.hpp`, `namespace standing`.
- **amicus** (*amicus curiae*, friend of the court) -- a **non-party** admitted to file findings
  because it has relevant sight, not because it has a stake. It may argue; it cannot be granted
  relief. This is the posture peer review already assumed without a word for it: a verdict is a
  finding, not a decision. Its value is exactly its disinterest, which is why it is only meaningful
  once parties are distinguishable -- hence the org row. Not an imported metaphor:
  `ruling_schema.hpp` is already a docket (`RULEID`, `STEWARD`, `PROPOSEDAT`, `DECIDEDBY`,
  `SUPERBY`, status `0` glossed *"filed, no decision"*), and standing is the piece it was missing.
- **movant** -- an **interested filer**: seeks a ruling on work it authored, paradigmatically an
  outside AI submitting a change package. **Recused from reviewing its own matter.** Names the
  party `EXTERNAL_AI_CHANGE_PACKAGE_V1` was reaching for when it said the contract "does not
  authorize the outside AI to ... approve its own patch" -- until now nothing in the data could
  tell you whether a reviewer authored the thing under review. The reason "partner" is not one
  posture but two: the same outside party is amicus on one lane and movant on the next.
- **party / non-party** -- a party has a stake in the outcome; a non-party does not. Host and
  steward are parties and therefore **never amicus**, which restates PDR-001 sec 0's
  conflicted-abstain rule as a consequence of standing rather than a house convention.
  Independence is an **org** property, not a role property: two seats conflict iff they share an
  `ORGUNIT`. Fail closed -- `ORGUNIT = 0` is "no org recorded," and two unknowns are not two
  different parties. Home: `docs/maintenance/PARTNER_AMICUS_STANDING_LANE_V1.md`.

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
