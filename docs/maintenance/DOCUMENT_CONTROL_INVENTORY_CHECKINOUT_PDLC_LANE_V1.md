# Document Control / Inventory / Check-in-Check-out PDLC Lane v1

Status: chartered; Phase-0 decisions LOCKED (D1-D8, dogfood amendment on D1/D7), signed 2026-08-15
(maintainer + Grok). Coordination + categorization only; no source mutation proposed.
Baseline: `development` @ `23617ec67`.
Ticket: AIF-112.
Owner: member.derald.
Steward (primary, driving): member.ai.grok.xai (Grok / xAI, Outside-AI, access_mode: remote).
On-disk secondary + scribe (advisory): member.ai.claude.cowork (Cowork).
Parent projects: `project.x64base.runtime`, `project.labtalk.pdlc`, `project.ai_friendly`.

## Purpose

Bring a cross-platform **document control and inventory** surface to the large x64base / DotTalk++
inventory, with explicit **check-out / check-in** semantics, teaching-grade (HELP + contracts), and
respecting prior art. This lane owns the PDLC for that capability from Phase-0 decisions onward. It
is a coordination charter, not an implementation; Grok drives the design, the maintainer locks the
gates, and no source has been proposed yet.

## Working model (Outside-AI primary + on-disk scribe)

Grok is the driving steward but is Outside-AI: it cannot run `claim-aif`, `git`, or the build on the
host, and cannot read the private tree. Therefore:
- Grok produces review-needed packages (design, decision packets, spike briefs).
- Claude (on-disk, Cowork) transcribes, registers, files intake rows, and prepares scoped commits
  for the maintainer to run. Claude is advisory/secondary and does not drive the design.
- Every package notes the original claim text and the acceptance id for provenance.
- The maintainer (`member.derald`) confirms assignments and locks each PDLC gate.

## Scope (working definition, from Grok's acceptance)

- Cross-platform document control and inventory over the large x64base / DotTalk++ inventory.
- Explicit check-out / check-in semantics (a lock/version discipline for controlled items).
- Inventory includes: source, docs, samples, Workspace / Database Capsule, and memo-resident
  schemas.
- Teaching-grade: HELP surface plus contracts, not a hidden mechanism.

## Prior art to respect (do not reinvent)

- **Git remains the publication path.** This lane does not replace version control for the tree.
- **SQLite is already built into DotTalk++** and is a candidate substrate rather than a new
  dependency.
- Dual-tree discipline and the GitHub publication path remain unchanged.

## Fences / no-collision (stated explicitly)

- **AIF-055** (Workspace + Database Capsule / memo-resident): keep visible; the inventory will need
  to lock/version capsules, so coordinate, do not overwrite.
- **AIF-098** (Frontal_Mem persistent-memory): fenced. Do not absorb or duplicate it.
- No collision with Triggers, Identity, or the Tuple freeze.

## Phase-0 decisions -- LOCKED (signed 2026-08-15)

Signed by maintainer + Grok, 2026-08-15. Grok's formal decision packet:
`docs/maintenance/external_ai_intake/aif112_phase0_decisions_2026-08-15/` (AIPR-20260815-GROK-002).
The dogfood amendment (D1/D7) is the maintainer's and sits in the signed decisions themselves (not
only the spike brief), so it survives session rotation: the ledger must be exercised THROUGH x64base
/ DotTalk++, never a side-channel sqlite3 process.

- **D1 -- Primary substrate.** In-tree DotTalk++ SQLite ledger, created / queried / locked ONLY
  through x64base / DotTalk++ surfaces (the SQLITE command family, work areas, tables), never a
  side-channel sqlite3 process (dogfood). Git remains the publication path. **Fossil is considered,
  not adopted** unless the dogfooded spike proves a required property the runtime SQLite surface
  cannot express (this is the same experiment as the D7 spike).
- **D2 -- Inventory scope.** Source + docs + samples + Workspace / Database Capsule + memo-resident
  schemas.
- **D3 -- Lock model.** Hybrid: exclusive check-out for non-mergeable items (binaries, capsules),
  advisory for pure text (Git already merges text). Reuse the engine's cross-process cooperative
  locking; define stale/abandoned-checkout recovery.
- **D4 -- Publication boundary.** Private-tree authority only; GitHub remains the clean publication
  gate (dual-tree discipline unchanged).
- **D5 -- Teaching / SelfDoc.** Full HELP + contracts (AIF-025 / AIF-037). Because the spike is
  dogfooded, the spike itself becomes representative student-facing evidence.
- **D6 -- Fence.** Confirmed: no collision with Triggers, Identity, Tuple freeze, AIF-098, or the
  remaining site-and-guard-hardening work.
- **D7 -- First spike style.** pydottalk (or the CLI / runtime API) driving a LIVE x64base instance,
  so every check-out, inventory list, and release is exercised through the product under test.
  Lightweight, stays out of C++ `src/**` until the model is proven. NO naked sqlite3 script.
- **D8 -- Relationship to AIF-055.** Explicitly coordinated: the inventory must be able to lock /
  version Workspace / Database Capsules; coordinate, do not overwrite.

Carried from the charter (to confirm in the spike, not a separate D): identity binding reuses the
existing RBAC (acting member, `bbs`-style permissions, SYSGRANT), not a parallel scheme.

## PDLC gates (proposed)

- **P0** decision packet: the five decisions above locked by the maintainer.
- **P1** spike brief: a narrow proof over one item class, substrate chosen, no broad mutation.
- **P2+** implementation lane, gate by gate, each with runtime proof, per house PDLC.

## Current status

- Grok has formally accepted AIF-112 (acceptance package `AIPR-20260815-GROK-001`; transcribed in
  `docs/maintenance/external_ai_intake/aif112_document_control_acceptance_2026-08-15/`).
- Pseudo-Chat acceptance note is prepared for transcription onto the agent-sync return lane at
  closeout cadence.
- Phase-0 decisions are LOCKED (D1-D8, dogfood amendment on D1/D7), signed 2026-08-15. Grok drafts
  the Phase-1 spike package next. No source mutation is proposed.

## Next gate

Phase-0 locked (2026-08-15); the Phase-1 spike package is drafted and transcribed
(`docs/maintenance/external_ai_intake/aif112_phase1_spike_2026-08-15/`, AIPR-20260815-GROK-003).
Next: run the dogfooded spike per its `notes/EXERCISE_OUTLINE.md` against a LIVE x64base instance,
fill `notes/EVIDENCE_TEMPLATE.md`, and return the evidence. The evidence decides whether the runtime
SQLITE surface suffices (proceed to command-family design, still dogfooded) or a concrete gap
justifies reopening Fossil. No source mutation until proven.

Owner `member.derald`; steward `member.ai.grok.xai`; scribe `member.ai.claude.cowork`;
`coordination/aif/AIF-112.claim`.
