# Candidate — new-chat onboarding trigger + AI_README Cowork-access insert

**Status:** `review-needed` candidate (NOT applied). AI-facing doc changes are proposed/reviewed/promoted, never self-certifying (`AI_PORTAL.md` → Closeout Updates Startup). I'm report-only.
**Baseline:** worded against `AI_README.md` / `AI_PORTAL.md` as read from `D:\code\ccode` on 2026-07-21 — confirm the commit before promoting.
**Orthogonality principle:** the repo (public `AI_README`) stays the single source of doctrine; the project layer carries *only* the irreducible pre-read bootstrap (the trigger + how to get access + posture). No doctrine is copied — Part A points, Part B single-sources the one Cowork-specific mechanism into the repo.

---

## Part A — Project-global trigger (goes in the Claude Project custom instructions / `memory.md`)

The one thing that can't live in the repo: the trigger that makes a new chat read the public front door *before* it starts working. Deliberately thin — pointer + the three facts that must exist before the README is read.

```text
x64base — do this FIRST in every new chat, before any analysis or code:
1. GitHub is a public SNAPSHOT, not truth. Do not ground work on it.
2. Fetch and follow the public front door (works with no file access):
   https://raw.githubusercontent.com/deraldg/x64base/main/AI_README.md
   Live lane state:  https://x64base.com/docs/labtalk/agent-sync
3. Request a mount of D:\code\ccode (your directory-request tool) and ground
   all real work on that DEV tree. You are a local-access, REPORT-ONLY partner
   until the maintainer authorizes a mutation; write access is not authorization.
```

Everything after that — authority chain, SDLC gates, source-mutation preflight, local-access checklist, closeout rules — is reached *through* `AI_README`, not restated here. If any of it changes, only the repo changes; this block does not.

---

## Part B — Proposed `AI_README.md` insert (single-source the Cowork access mechanism)

The file-access mechanism is the only genuinely runtime-specific bit; put it in the one front door so it doesn't become a separate drifting copy.

**Placement:** immediately after the "Start here, in this order" table (the mandatory-start table), before `## Start Here (legacy list — superseded…)`.

```markdown
### Local-access agents on Cowork / Claude (no file access at start)

Some agents (e.g. Claude in Cowork) begin a session with **no disk access** and must
request it. If that's you:

1. You can already read this front door, `AI_PORTAL.md`, and the live Agent Sync page
   from the public GitHub/website surfaces — do that first; they need no mount.
2. Gain disk access by requesting a mount of `D:\code\ccode` through your
   directory-request tool; the maintainer approves it.
3. Ground all source and lane-state work on the mounted **DEV** tree. The public
   GitHub snapshot is onboarding doctrine, not source truth (see **Authority**) —
   never present a snapshot read as current dev state.
4. Then resume the table above at Step 3 (`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md`).
```

**Optional companion:** the same four lines could instead (or also) live in `docs/agents/AI_BABY_BOOTSTRAP_CARD.md`, with `AI_README` linking to it — your call on which is the canonical home. Keep it in exactly one place.

---

## Why this closes the gap (and stays orthogonal)

- **Bootstrap paradox dissolved:** the public portal is reachable with zero file access, so doctrine never needs duplicating into the project. `AI_README` was already built for "when memory/history is unavailable."
- **Two public, mount-free surfaces already exist:** GitHub `AI_README` (stable doctrine) + Agent Sync page (fresh lane state). The trigger just points a new chat at both.
- **Two surfaces, two uses:** public GitHub = *how to work*; dev tree = *what's true*. The project layer only supplies the trigger.
- **Drift-proof:** Part A rarely changes (it's a pointer); all doctrine lives once, in the repo, under the same review gate as any contract (AIF-006/037, Rule of Three).

## Suggested follow-through (maintainer-gated)
- Place Part A in the project's persistent surface; place Part B via the normal AI-facing-doc review, updating `AI_FRIENDLY_DASHBOARD` Session Log + a closeout per AIF-006/024, with an AIF intake row if you want it tracked as a lane.
