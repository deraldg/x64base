# Document Control / Inventory / Check-in-Check-out PDLC Lane v1

Status: chartered; Phase-0 decisions pending maintainer lock. Coordination + categorization only;
no source mutation proposed.
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

## Phase-0 decisions pending maintainer lock

These are the open questions Grok's first package should frame for the maintainer to lock:
1. **Substrate** -- where does control/inventory state live? (SQLite already in-tree; DBF/SYS*
   catalog; or a sidecar). Weigh against prior art and the dual-tree discipline.
2. **Inventory scope** -- exactly which item classes are under control at M1 (source vs docs vs
   samples vs capsules vs memo-resident schemas), and what stays out.
3. **Lock model** -- check-out/check-in semantics: advisory vs enforced, single vs multi-holder,
   how it interacts with Git as the publication path, and how a stale/abandoned checkout is
   recovered (cf. the cross-process cooperative locking already in the engine).
4. **Identity binding** -- who may check out/in; reuse the existing RBAC (`bbs`-style permissions,
   acting member, SYSGRANT) rather than a parallel scheme.
5. **Teaching surface** -- the HELP + contract shape, so the mechanism is documented, not hidden.

## PDLC gates (proposed)

- **P0** decision packet: the five decisions above locked by the maintainer.
- **P1** spike brief: a narrow proof over one item class, substrate chosen, no broad mutation.
- **P2+** implementation lane, gate by gate, each with runtime proof, per house PDLC.

## Current status

- Grok has formally accepted AIF-112 (acceptance package `AIPR-20260815-GROK-001`; transcribed in
  `docs/maintenance/external_ai_intake/aif112_document_control_acceptance_2026-08-15/`).
- Pseudo-Chat acceptance note is prepared for transcription onto the agent-sync return lane at
  closeout cadence.
- Phase-0 decisions are NOT yet locked. No source mutation is proposed.

## Next gate

Maintainer locks the Phase-0 decisions -> Grok produces the first real working package (a Phase-0
decision packet plus a Phase-1 spike brief). Nothing is built until then.

Owner `member.derald`; steward `member.ai.grok.xai`; scribe `member.ai.claude.cowork`;
`coordination/aif/AIF-112.claim`.
