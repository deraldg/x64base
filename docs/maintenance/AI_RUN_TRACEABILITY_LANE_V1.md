# PROJECT LANE — AI Run Traceability & True-Author Attribution

**Type:** governance lane (large) · **Status:** **STAGED (chartered; not started; M0 owed)**
· **Filed:** 2026-07-22
· **Owner / authority:** Derald Grimwood (maintainer) — final say, authorization, and the only party
who commits/pushes. Ownership is **not** delegated by the assignment below.
· **Assigned member (lane steward / author):** `member.ai.claude.cowork` (Cowork / Claude, Anthropic)
— assigned 2026-07-22 by the owner to steward this lane and author its work. This is a stewardship
assignment under the owner's authorization, not a transfer of ownership; *the header is itself a
small demonstration of the owner-≠-author model the lane proposes.*
· **Parent:** `project.x64base.identity` (extends the run/session entity AIF-045's model already
posits; may promote to `project.x64base.governance` if it grows).
· **Extends:** AIF-020 (AI report-audit envelope) + AIF-045 (identity / RBAC; *member ≠ session/run*)
+ AIF-042 (contract system: one harvester, discriminate by KIND — the universal `@dottalk.file` block
is a new KIND).
· **AIF:** candidate **AIF-050** (next-free; maintainer assigns final).
· **Last agent:** `member.ai.claude.cowork` · run `AIPR-20260722-007` · chat `""` (MAINTAINER_ATTESTED)
· 2026-07-22 — *the return-path pointer this lane defines, applied to itself; resolvable via
`labtalk/registries/ai_runs.yaml` → `current_by_lane[AIF-050]`.*

## Why this lane exists (the finding)

Ask "which AI worked on the `USER` command?" and the honest answer today is *"Cowork/Claude, per the
audit envelope — but I can't tell you the model, the session, or how to get back to it."* Three
gaps, all provable:

1. **Attribution collapses onto the maintainer.** Every identity/`USER` commit — `0d4b9b407`,
   `2a89cc5c3`, `bfa6bb0fd`, and the rest — is authored *and* committed by
   `Derald Grimwood <derald@grimwood.ws>`. That is correct mechanically (the maintainer is the only
   one who commits and pushes) and **wrong as a record of who did the work**. Git blame attributes
   100% of AI-authored code to the human. The maintainer's name on everything is not credit — it is
   **noise that buries the real contributor.** (Maintainer's own words: *"stamping my name all over
   the place is a distraction from the truth."*)
2. **The agent is traceable only to the product level.** The AIF-020 envelope records
   `provider: Anthropic, product: Cowork, model: not_exposed` and leaves `session.id` /
   `chat_reference` = `not_exposed`. So you can name "Cowork/Claude" but cannot return to the
   *specific session* that holds the live context.
3. **Planning vs implementing authors are conflated.** Identity/RBAC (AIF-045) was *planned* by an
   external AI (ChatGPT/OpenAI, "external-AI plan evaluated and endorsed with caveats") and
   *implemented* by Cowork/Claude. The record does not distinguish the two contributions; "who
   worked on it" silently merges a design author and a code author.

### Live proof — a collision during this lane's own drafting (2026-07-22)

This lane could not keep a stable AIF number while it was being written, because **at least four
Cowork/Claude sessions were editing the same branch and the same intake queue at once**, each
claiming numbers with no coordination:

- It was first chartered **AIF-047** — and collided with a parallel session's committed
  "HELP command UX" AIF-047 (`9e14918a8` → `cc0761e8f`, HEAD, tagged *"owner: Claude/Cowork"*). Caught
  by reading `git log`. Renumbered to 048.
- **AIF-048** collided too — the *working tree* already held a parallel session's uncommitted
  AIF-048 ("Full-stack documentation flush II") plus an AIF-049 ("ArcticTalk retro TUI"). Renumbered
  to **AIF-050**.

Four sessions, one branch, one intake file, three number collisions in the span of a single lane's
drafting — none visible to each other, because the only shared state is git (which shows every commit
authored by the maintainer, hiding the real actors) and a hand-edited intake queue that multiple
agents append to concurrently. This is not a hypothetical in the "why": it is the exact failure the
lane removes, observed live, *while describing it.*

**Finding (a required design constraint for this lane): AIF-number assignment must be a single-writer
operation.** A shared file that many agents append to is a race by construction. The RUN registry
(M1) is the natural home for an atomic "claim next-free" — or the maintainer is the sole assigner —
but a free-for-all intake queue cannot allocate unique ids. This is added to M0's contract as an
open requirement.

## Thesis: separate *who owns/commits* from *who did the work*, and make each run addressable

The system already keeps **one owner** (Derald) and **one authoritative tree** (`D:\code\ccode`).
This lane adds the missing axis: **who actually authored a unit of work, in which run, reachable
how** — recorded as first-class data, so the owner's necessary roles (authorize, commit, own) never
overwrite the record of the contributor.

Two hard rules the design serves:

- **Owner ≠ author; committer ≠ contributor.** Record them in separate fields, each once. Do not
  repeat the owner's name as ceremony; record it where it is load-bearing (authorization, ownership)
  and nowhere else. Attribution serves *truth*, not credit.
- **The closeout stays the system of record; the chat handle is warm-resume convenience.** Per the
  portal's own rule (*"the chat is never the record; the closeout is"*), durable knowledge lives in
  closeouts + lane docs. A resolvable chat handle is *additive insurance* — reopen the live agent if
  the session still exists; lose nothing that matters if it does not, because the knowledge is
  already written down. Traceability-to-chat must never become a single point of failure.

## The four-part traceable key

Every unit of AI work resolves to: **(member) × (project/lane) × (run) × (chat handle)** —
with authorship split from ownership.

- **member** — the identity-catalog key (`member.ai.claude.cowork`), not a free-text product string;
  ties work to a real AIF-045 entity with a role.
- **project / lane** — already tracked (`AIF-NNN` + `projects.yaml`).
- **run** — a new first-class entity (the *session/run* AIF-045 already separates from *member*):
  `{run_id, member, project, lane, started, last_closeout, status, continues_run}`.
- **chat handle** — the resumable pointer + a **binding** (`SELF_REPORTED | MAINTAINER_ATTESTED`),
  because the platform stamps IDs `not_exposed`, so the maintainer attests what the run cannot
  self-report. Precedent is in-tree: the Pinocchio machine profile is `MAINTAINER_ATTESTED` for
  exactly this reason.

## The source spine — the universal `@dottalk.file` contract

Attribution at *lane* granularity (runs, closeouts) is not enough — a change touches specific files,
and the source itself does not record who authored what. The source-side carrier is a **universal
per-file contract, `@dottalk.file`**: one block on **every** source file, holding file demographics
plus a **provenance pointer** — never embedded change history (that would duplicate what the closeout
and run registry already hold; the single-source-of-truth doctrine forbids it). Only *commands* carry
the behavior contract `@dottalk.usage`; **every** file carries `@dottalk.file`. That universality is
what turns the tree into a harvestable object graph and unlocks a cheap algebra:

- `census = files carrying @dottalk.file` — the complete node set (today the harvest sees only commands).
- `@dottalk.file ∖ @dottalk.usage = non-command files`; `@dottalk.file ∩ @dottalk.usage = commands`.
- `git ls-files ∖ census = uncovered files` — a **coverage gate** (advisory first; see M3).
- `group @dottalk.file by layer / subsystem` = the architecture map, harvested from source.

One block, scope-named (so the field set can grow without renaming), with demographics and a
maintenance/provenance pointer as field-groups:

```
// @dottalk.file v1
// path: src/cli/cmd_area.cpp
// subsystem: cli
// layer: command            # command | helper | engine-core | glue | test | header
// owns: DOT|AREA            # empty on non-command files → the ∖ set
// project: project.x64base.runtime
// status: supported
// provenance: prov://src/cli/cmd_area.cpp   # POINTER into the provenance catalog; no history in source
```

It is a new **KIND** in the AIF-042 one-harvester model — a KIND every file has — not a new pipeline.
Most fields are **derivable** (`path` is the path; `subsystem`/`layer` from the directory + a
heuristic; `owns` from the existing `@dottalk.usage owner`), so a generator writes the first pass and
review only adjudicates the judgment fields — the backfill of hundreds of files is cheap.

The **provenance catalog** is the maintained source the pointer resolves to: a harvested DBF (SelfDoc
"reported" class), one row per change — `{unit/path, run_id, member (true author), planned_by,
committer/owner, date, change_ref → closeout § / commit, summary}` — fed from the RUN registry (M1) +
closeouts + commits. The who/when/why lives there **once**; source carries only the key + pointer.
This is the "pointers to a maintained source" model, and it encapsulates cleanly if source ever
becomes objects/records: the unit key is the foreign key, the provenance catalog is a related table.

## Milestones (large lane; each report-first, maintainer-gated)

- **M0 — inventory + attribution contract.** ✅ **landed (candidate, 2026-07-22).** The RUN + CHANGE
  entities, the five roles (**owner / committer / author / planner / attestor**), the `handle_binding`
  states, and the invariants are fixed in `docs/maintenance/AI_RUN_TRACEABILITY_CONTRACT_V1.md`. It
  leads with the census measurement below.
- **M1 — RUN registry.** ✅ **landed (candidate, 2026-07-22).** `labtalk/registries/ai_runs.yaml`
  (schema `ai-runs-v1`) seeded with the real runs: this session (`AIPR-20260722-007`, Cowork,
  AIF-046+047), and the identity runs (`-004`/`-005`, Cowork-implemented, **ChatGPT-planned**,
  Derald-owned). Every seeded run is `MAINTAINER_ATTESTED` — a live demonstration of the central case
  (the platform stamps the session id `not_exposed`, so the owner attests the handle; the run is fully
  recovered from its closeout regardless). Validator fields declared; runs chain via `continues_run`.
- **M2 — universal `@dottalk.file` contract + provenance catalog.** ✅ **spec + harvester landed
  (candidate, 2026-07-22); backfill pending.** Contract shape fixed (a new AIF-042 KIND: demographics
  + provenance pointer, no embedded history); `tools/fullstack_docs/source_census.py` harvests the
  census and derives first-pass blocks (`--sample` proves it: command → `owns: DOT|AREA`, helper →
  `layer: helper`). **Measured (real repo, git-tracked):** 1009 source files, **227 carry `@dottalk.usage`
  (22%)**, **782 carry neither (78%, invisible to the harvest today)** — the motivation, grounded.
  **Backfill capability landed (2026-07-25):** `source_census.py --write [--only <prefixes>]` inserts
  the derived `@dottalk.file` block at the top of each uncovered file (idempotent; skips files that
  already carry one) -- the missing "generator-driven backfill" tool. **Dogfooded:** the AI-BBS lane's
  12 new source files now carry hand-classified blocks (accurate `layer`: `glue` / `engine-core` /
  `command` / `header`, not the heuristic default). Remaining: the provenance DBF, and the
  **maintainer-gated full-tree sweep** (`--write` whole tree, then review the heuristic `layer` fields)
  that takes census 0% -> covered.
- **M3 — coverage gate (advisory).** ✅ **landed (candidate, 2026-07-22).** `source_census.py`
  reports `git ls-files ∖ census`; **advisory** by default (exit 0), `--strict` fails (exit 1) — proven
  to flip cleanly (strict exits 1 at today's 0% coverage). Promotable to a hard drift gate (sibling of
  the AIF-033/035 gates) once backfill completes, on maintainer decision.
- **M4 — audit envelope v2 (`ai-report-audit-v2`).** ✅ **spec landed (candidate, 2026-07-22).**
  `docs/maintenance/AI_REPORT_AUDIT_V2_SPEC.md`: adds `agent.member`, an `attribution` block splitting
  `authored_by` / `planned_by` from `owner` / `committer` (recorded once), and
  `session.run_id` / `chat_handle` / `handle_binding` / `continues_run`. Additive + version-gated
  (validator accepts v1 and v2; `run_id` cross-checked against `ai_runs.yaml`). Worked example uses
  this session's real run; the identity row shows the ChatGPT-planned/Cowork-implemented split v1 could
  not express. Wiring the validator + closeout adoption is M6.
- **M5 — the "Last agent" pointer (the return path).** ✅ **core landed (candidate, 2026-07-22).**
  The registry carries the index — `ai_runs.yaml` `current_by_lane` / `current_by_project` (lane →
  newest run → chat handle), the queryable "return to the last agent"; and the human-readable
  `Last agent: …` line is on the AIF-050 and AIF-046 lane docs. **Pending (maintainer-gated):** the
  dashboard Current-Lane rows + a `current_run:` on the `projects.yaml` project — proposed, not swept
  in.
- **M6 — closeout-convention wiring + validator.** ✅ **validator landed (candidate, 2026-07-22).**
  `tools/fullstack_docs/run_attribution_check.py` scans every closeout, reports v2-attributed vs v1,
  cross-checks `run_id` against the registry, and flags `author ≠ owner`. Run on the real tree: **68
  closeouts, all v1, 3 registry runs** — v2 adoption starts here. Advisory (exit 0); `--strict`
  promotes it to a gate. **Convention delta (proposed):** new closeouts stamp `run_id`, record
  `author ≠ owner`, and attest `chat_handle` — a one-line addition to the AIF-006 closeout convention
  (AIF-024 fixes *when* to document; this fixes *whose*).
- **M7 — attribution-truth backfill + doctrine.** ✅ **doctrine + recent-lane backfill landed
  (candidate, 2026-07-22).** The **"Ownership and Authorship (AIF-050)"** doctrine section is in
  `AI_PORTAL.md` (owner ≠ author; committer ≠ contributor). The recent lanes' true authors are in
  `ai_runs.yaml`: scan-evaluator (AIF-046) = Cowork/Claude; identity (AIF-045) = **ChatGPT-planned,
  Cowork-implemented, Derald-owned/committed**. Backfilling the older 60+ pre-v2 closeouts (the
  validator lists them) is optional follow-on, best done as those lanes are next touched.
- **M8 — outside-AI reflection + peer review.** Publish the attribution model on the Agent-Sync page
  so ChatGPT/Codex are recorded and can self-report `planned_by`/`authored_by` in returned packages;
  human + cross-AI peer review (Outside-AI Delivery Rule).
- **M9 — concurrent-session coordination (the anti-collision mechanism).** ✅ **core landed
  (candidate, 2026-07-22).** Traceability *records* who did what; coordination *prevents* two sessions
  from colliding in the first place — the deeper need the live AIF-047→050 race exposed.
  `tools/coordination/session_coordinator.py` provides three filesystem-atomic primitives:
  **atomic AIF-number claim** (`O_CREAT|O_EXCL` — proven: a second session claiming a held number is
  refused; next-free correctly skips all taken), **session presence** (`checkin`/`status`/`checkout`),
  and **advisory file locks** for the contested AI-facing docs. Durable claim ledger under
  `coordination/aif/*.claim` (tracked); presence/locks transient (gitignored). Protocol:
  `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`. **This session's AIF-050 is now claimed
  through the tool** (`coordination/aif/AIF-050.claim`). *Pending:* wiring the protocol into
  `AI_PORTAL.md` (deliberately deferred — the portal was being co-edited by another session while this
  landed; editing it under contention is exactly what the lock discipline forbids), and a `--strict`
  pre-edit hook. **Contract invariant 6** (single-writer id assignment) is the doctrine this enforces.

## Falsifiable success criteria

- **Resolvable:** given any closeout or lane, one can name the AI **member**, the **run_id**, the
  **chat handle** + its **binding**, and — if resolvable — reopen the exact session. Verified by
  picking three past lanes and resolving each.
- **True author, not committer:** the actual contributor is recorded in a field that does **not**
  require reading git, and the maintainer's name appears only where it is load-bearing
  (authorization, ownership, commit), not as blanket attribution.
- **Plan ≠ implementation:** for a lane authored across AIs (identity is the live example), the
  record distinguishes `planned_by` from `authored_by`.
- **No new single point of failure:** losing a chat session does not lose lane knowledge — the
  closeout still fully transfers it (re-proven by a "resume from closeout only" dry run).
- **Complete census:** every source file carries `@dottalk.file`; `git ls-files ∖ census` is empty
  (or every exception is explicitly listed). The `∖ @dottalk.usage` classification and the
  layer/subsystem architecture map both fall out of the same harvest, at a couple-of-lines-per-file
  cost.

## Governance / boundary

Docs + registries + schema only; no engine source unless the RUN entity later earns a runtime home
(e.g. an identity-catalog `SYSRUN` table under AIF-045). Maintainer-gated at every step; AI-facing
doc changes are proposed/reviewed, never self-certifying. The maintainer is the **attestor** for
handles the platform will not expose — a role the model names explicitly rather than leaving
implicit. Minimize ceremonial owner-name stamping by design.

## Cross-references

- Extends: AIF-020 report-audit (`labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md`,
  `labtalk/registries/ai_report_audit.yaml`), AIF-045 identity
  (`docs/maintenance/IDENTITY_RBAC_MANAGEMENT_LANE_V1.md` — *member ≠ session/run*), and AIF-042
  contract system (`docs/maintenance/SCRIPT_HEADER_CONTRACT_LANE_V1.md` — one harvester, KIND column;
  `@dottalk.file` joins `@dottalk.usage`/`@x64base`/`@script.usage` as a KIND).
- Precedent for `MAINTAINER_ATTESTED` binding: `PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json`.
- Portal doctrine touched at M5: `AI_PORTAL.md` (committer ≠ author).
- Registration when filed: intake AIF-050; dashboard Current Lane State; session index.
