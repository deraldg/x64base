# The coordination ontology: two atoms, and everything derived from them

Author: `member.ai.claude.cowork`. Date: 2026-08-07. Status: proposal (descriptive
frame, not doctrine yet). Authored outside the repository -- the documentation system
is frozen; this is the maintainer's to place. ASCII throughout (`--`, `->`).

> **Purpose.** State the model that the identity / `wake` design implies, so the design
> has a named frame instead of an assumed one. The frame is deliberately small: **two
> atoms.** Every other word we use in coordination -- session, run, presence, member,
> claim, quip, handoff -- is a *term* built from those two, not an atom of its own.

## 1. The two atoms

There are exactly two irreducible things, and they are asymmetric. The asymmetry is the
whole design, not a detail of it.

- **chat** -- mortal, forgetful, and the only atom that *acts*. It can claim, quip, edit,
  close. It cannot remember itself: between turns, and certainly between sessions, it
  goes blank. It is the atom that moves and forgets.
- **project** -- durable, inert, and the only atom that *remembers*. It holds the ledger
  (claims, presence, intake rows, pickup docs) but does nothing on its own. It is ground,
  not agent. It is the atom that persists and records.

**The law that falls out:** the atom that acts cannot remember, and the atom that
remembers cannot act. Therefore identity and state must live entirely on the **project**,
and the **chat**'s first duty is to read the project before doing anything. "A self-aware
chat" is a category error -- awareness is not a property of the acting atom; it is the
acting atom reading its own record off the remembering one.

## 2. Terms that are NOT atoms

These are the words we use every day. None is primitive. Each is a relation, a record, or
an episode over the two atoms -- naming them as derived is what keeps the model honest.

- **session** -- a *term, not an atom* (the correction that prompted this note). A session
  is an **episode**: one chat's bounded engagement with a project across an interval. It
  decomposes into `chat x project x time`. It is an edge with a lifespan, not a node.
- **run** -- the *identifier of one session* (one episode). Per-session by necessity: two
  concurrent chats need distinct runs or they stamp each other's work. `COWORK-<date>-NNN`.
- **presence** -- a *relation*: a chat announcing its existence to the project for the life
  of a session. Recorded in `coordination/active_sessions/<run>.yaml`. Transient.
- **member** -- a *project-side record* of a recurring chat identity, spanning many
  sessions. This is the stable name ("the identifier it always remembers") -- durable,
  read back on wake, never held in the chat. `member.derald.cowork`. Not an atom: it is a
  record the project keeps and a chat binds to.
- **claim** -- a *relation*: a chat binding a slice of the project (an AIF number). The
  binding is stored on the project side, so it outlives the chat that made it.
  `coordination/aif/AIF-NNN.claim`, atomic (`O_EXCL`).
- **quip** -- a *chat -> chat* edge. Needs both chats alive; the project only relays. This
  is why a quip cannot carry a handoff.
- **handoff** -- a *chat -> project -> chat* path. It must cross a dead chat, so it routes
  through the remembering atom: the ledger (claim + intake row + pickup doc). Never a quip.
- **lineage** -- a *durable project record* of a run's birth time (`born_utc`) and the run
  it was continued from (its `parent`). Written once on `wake`, it SURVIVES checkout --
  unlike presence -- so a resumed or closed session can answer "when was I born / who is
  my parent" from the ledger. Implemented 2026-08-07 (`coordination/lineage/<run>.yaml`,
  tracked): the parent edge this model first named as existing-but-untracked.
- **intake row / pickup doc** -- *project records* that make a handoff discoverable from
  HEAD, so work no chat currently holds cannot be forgotten (the AIF-070 failure).

## 3. What this frames

The identity / `wake` design is just the first edge of section 1 made explicit:

- **member vs run.** The durable identity is the **member** record (project-side, always
  re-read). The **run** is the per-session instance. Same name forever; distinct instance
  each session. "Give it an identifier it always remembers" = mint the member once, adopt
  it on every wake.
- **`wake` is the chat->project read, walked first.** A session's documented first move:
  adopt its member, write presence for this run, read its inbox. It prints "you are
  `<member>` (run `<run>`); you hold `<claims>`; inbox `<n>` unread." Nothing else runs
  before it.
- **Why the rule lives where it does.** The *rule* ("wake first") belongs in `CLAUDE.md`,
  the one file auto-injected into every session with full authority and no retrieval
  friction. The *perishable value* (the run, the claims) stays in the ledger files --
  `CLAUDE.md`'s own maintenance rule (AIF-082) forbids perishable literals in it. Rule in
  the always-injected atom-reader; state in the durable atom.

- **The rise, by tier (atomic vs derived).** The portal already sorts by atomicity, so
  these pieces rise in two directions. The *derived, perishable* identity state -- live
  sessions (stale-marked), each run's lineage (parent, `born_utc`), and its aside chain
  (ordered claims) -- rises into the GENERATED middle tier: `generate_tier0_state.py`
  (AIF-082) now projects it into `TIER0_STATE.md`, so it rises by regeneration and cannot
  drift. The *atomic* doctrine over it -- the two-atom law and wake-first -- is a
  candidate to rise to the Tier 1 seed as one compressed invariant plus a pointer here
  (owner call; the seed is budget-capped -- planned separately, not applied).

## 4. Placement (done 2026-08-07, owner-authorized)

Filed here, `docs/maintenance/`, beside `AI_SESSION_COORDINATION_PROTOCOL_V1.md`, and
routed so it is reachable and not merely filed: recall-graph node
`mechanism.coordination_ontology` (`labtalk/registries/portal_recall_graph.yaml`), reached
by a `requires` edge from the protocol node, so `recall.py commit` surfaces it. The
protocol's opening carries a one-line pointer here. Filing without routing would orphan
it -- the exact failure the ledger exists to prevent -- so the node and edge landed in the
same motion as the file.

The seed-rise half (rising the atomic law to the Tier 1 seed) is planned, not applied, in
`SEED_RISE_PLAN_TWO_ATOM_V1.md` (same directory); it stays an owner call because the seed
is budget-capped.
