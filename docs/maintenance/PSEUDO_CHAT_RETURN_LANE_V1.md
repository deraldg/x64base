# Pseudo-Chat — the AI Portal Return Lane (v1)

Status: **active / dev** — governance mechanism, documentation-only (no engine build
dependency). Canonical spec for the Pseudo-Chat return lane.
Owner surface: `AI_PORTAL.md` (§ "Staying Current — the Live Agent Sync Page").
Live page: `/docs/labtalk/agent-sync` on the x64base website
(source: `D:\dev\x64base-site/content/docs/labtalk/agent-sync.mdx`).
Related: `AI_README.md` (front door), the intake queue / dashboard (gated system of
record), the per-session handoff docs (`docs/maintenance/SESSION_HANDOFF_*`).

---

## TL;DR

**Pseudo-Chat is the return lane of the doc-only live portal**: an asynchronous,
closeout-cadence, artifact-mediated two-way channel between the maintainer's in-repo agent
and an external, web-only AI partner (e.g. ChatGPT) that cannot read the local drive. The
portal already **broadcasts** current state outward; Pseudo-Chat adds the **reply path** so
a partner's answers are logged back onto one durable page and close the portal's Open
questions — instead of scattering across chat transcripts. It is named "Pseudo-Chat" on
purpose: the name tells every reader it is **not real-time**.

## 1. What Pseudo-Chat is

A structured, one-page dialogue built on top of the Agent Sync page:

- The page's **Open questions** are a tracked `Q# / Question / Status` table.
- The **Pseudo-Chat return lane** is a documented reply protocol plus a dated
  **Pseudo-Chat log**.
- An external partner reads the page, replies **in its own chat** in the `RE:` format
  below; the maintainer relays that reply to the in-repo agent; the in-repo agent
  **transcribes** the accepted reply into the Pseudo-Chat log and **flips the matching
  Open question's Status** — at closeout, then republishes.

The result: the question *and* its answer live together on a durable, publicly reachable
page, with a freshness date, rather than only inside two disconnected AI conversations.

## 2. Why it exists (the problem)

Cross-session AI coordination has three hard constraints on this project:

1. **No persistence across chats.** Folder access, tool grants, and context do **not**
   carry from one chat session to the next; each must be re-established.
2. **Web-only partners have no drive access.** ChatGPT and similar cannot read
   `D:\code\ccode` at all — the doc-only live portal exists precisely because of this.
3. **No shared real-time channel.** Each chat is an isolated conversation. No agent can
   message another running session or be notified of its messages. The only "other agents"
   an in-repo agent can directly message are subagents it spawns itself.

The portal solved the **outbound** half (broadcast fresh state to the outside agent).
Pseudo-Chat solves the **inbound** half (get the answer back and record it), closing the
loop so a decision isn't stranded in a chat transcript the next reader never sees.

## 3. What it is NOT — and why the name

- **Not real-time.** It moves at closeout cadence, one turn at a time. That is the whole
  reason it is called *pseudo*-chat: the name sets the expectation honestly so no one
  mistakes it for a live channel.
- **Not a socket / not automatic.** Nobody polls it between turns. A human relays and
  triggers each hop.
- **Not autonomous authority.** The live page is fresher than the GitHub snapshot between
  snapshots, but the maintainer's `D:\code\ccode` reconciliation is authoritative over
  both. Pseudo-Chat does not bypass a proof gate.
- **Not the system of record.** Accepted decisions still promote into the intake queue /
  lane docs / dashboard through the normal propose→review→promote gate. Pseudo-Chat is the
  *conversation surface*, not the *ledger*.
- **Not for the local-access Claude.** A Claude session granted the dev tree reads the
  handoff docs and files directly; it does not need Pseudo-Chat. Pseudo-Chat is
  specifically the bridge to the **web-only** partner.

## 4. Where it lives (architecture)

There are two coordination surfaces; Pseudo-Chat is one of them:

| Partner | Surface | Direction | Transport |
|---|---|---|---|
| Local-access Claude (has dev tree) | shared `D:\code\ccode` tree + `SESSION_HANDOFF_*` docs | two-way (reads/writes files) | direct file access |
| **Web-only partner (ChatGPT)** | **Agent Sync page + Pseudo-Chat lane** | **out = broadcast state; in = Pseudo-Chat log** | **published page (out) + human relay (in)** |

Governance hooks that keep Pseudo-Chat maintained rather than orphaned:

- `AI_PORTAL.md` § "Staying Current" describes the portal and the Pseudo-Chat return lane,
  and states precedence (dev tree > live page > GitHub snapshot).
- `AI_PORTAL.md` **Required Closeout** table row for the Agent Sync page now includes
  *transcribe partner replies into the Pseudo-Chat log and update the matching
  Open-question Status* as part of the same closeout step.
- The live page's own **update convention** footer repeats that obligation.

## 5. Roles

- **External partner (e.g. ChatGPT).** Reads the Agent Sync page as the freshest reachable
  state; does standalone, compile-only work; **replies in its own chat** in the `RE:`
  format. It cannot write to the site or the tree.
- **In-repo agent (Cowork/Claude with dev access).** Poses/curates Open questions,
  broadcasts state, and — at closeout — transcribes accepted replies verbatim into the
  Pseudo-Chat log, updates the Open-question Status, refreshes the freshness date.
- **Maintainer (human).** The transport and the gate: relays replies between the isolated
  chats, decides which replies are *accepted*, runs the site republish, and owns all
  commits/pushes/promotions.

## 6. Message protocol

A reply from an external partner is formatted so the in-repo agent can transcribe it
verbatim (the partner cannot file it itself):

- **Header:** `RE: <Q# or lane id> — <YYYY-MM-DD>`
- **Body line 1–2:** the **decision or answer**, stated plainly.
- **Then:** any **provisional assumptions** the answer rests on (so the maintainer can
  check them against dev truth).
- **If it is a hand-back packet:** name the packet and its **one passing test**; keep it
  **standalone / compile-only** per the portal's working agreement.

**Pseudo-Chat log entry** (what the in-repo agent writes on the page), newest first:

```
- [YYYY-MM-DD] RE: Q<n> (<short question>) — <one-line summary of the accepted answer>.
  Assumptions: <...>. Disposition: <promoted to AIF-nnn / lane X | held | needs re-ground>.
```

**Open-question Status transitions:** `Open` → `Resolved <date>` (with a pointer to where
the decision now lives) or `Deferred <date>` (with the reason). The Status column is the
at-a-glance state; the log is the detail.

## 7. The turn cycle (lifecycle)

One full round trip, all human-triggered (nobody polls):

1. **Broadcast.** In-repo agent updates the Agent Sync page — current state + Open
   questions — bumps the freshness date, and the maintainer republishes the site.
2. **Read.** The external partner reads the page (its freshest reachable truth).
3. **Reply.** The partner answers in its own chat in the `RE:` format.
4. **Relay.** The maintainer carries that reply into the in-repo agent's session.
5. **Transcribe (at closeout).** The in-repo agent records the accepted reply in the
   Pseudo-Chat log and flips the matching Open question's Status; freshness re-dated.
6. **Republish.** The maintainer republishes; the partner sees the resolved dialogue on
   its next read.
7. **Promote (separately).** If the reply settled something substantive, it is promoted
   into the gated system of record (intake row / lane doc / dashboard) via the normal
   review gate — Pseudo-Chat recorded the conversation; the ledger records the decision.

Cadence is **closeout**, not continuous. Between closeouts the page can lag; the freshness
date is the contract that tells a reader how stale it might be.

## 8. Worked example

Suppose Q2 is open: *"Is workspace addressable in reference-surface syntax (`MCC.…`), or
identity only?"*

External partner replies in its chat:

```
RE: Q2 — 2026-07-22
Decision: identity-only for beta-1; reference-surface syntax (MCC.…) deferred.
Assumptions: workspace identity is stable within a session; no cross-workspace
addressing is required by the tuple contract yet.
```

Maintainer relays it; in-repo agent (at closeout) writes to the Pseudo-Chat log:

```
- [2026-07-22] RE: Q2 (workspace addressable vs identity-only) — accepted: identity-only
  for beta-1; MCC.… reference syntax deferred. Assumptions: stable in-session identity;
  no cross-workspace addressing needed yet. Disposition: recorded; promote to the tuple
  lane doc when that lane opens.
```

and flips the Open-questions table: `Q2 … | Resolved 2026-07-22 — identity-only (beta-1);
MCC.… deferred. See Pseudo-Chat log.` Republish. The loop is closed on one page.

## 9. Guardrails & honesty rules

- **Guard-clean.** The published page must never leak private paths (`D:\code\ccode`,
  `C:\x64base`, machine paths). Refer to "the maintainer's private development tree." The
  site's content guard enforces this; a leak fails the publish.
- **Freshness is the contract.** Every revision carries a dated freshness marker and a
  short "changed since" note. Do not imply the whole digest is current when only part
  changed — say what changed.
- **Authority order stands.** dev-tree reconciliation > live page > GitHub snapshot. The
  page is not permission to skip a proof gate.
- **Accepted ≠ promoted.** A logged reply is a recorded conversation, not a filed
  decision. Promotion into intake/lanes/dashboard is the separate, gated step.
- **The name is a feature.** Keep calling it *Pseudo-Chat* so the not-real-time nature is
  self-evident to anyone who encounters it.

## 10. Closeout integration (maintenance)

Pseudo-Chat is maintained as part of the standard closeout, not as a separate chore. At
each maintainer-session closeout, if anything an outside partner relies on changed **or**
a partner reply was gathered since the last closeout:

1. Refresh the Agent Sync page content + freshness date.
2. Transcribe accepted partner replies into the Pseudo-Chat log.
3. Update the matching Open-question Status.
4. Republish the site.

This is encoded in the `AI_PORTAL.md` Required Closeout table (Agent Sync row) and the
page's own footer, so it travels with the closeout doctrine rather than relying on memory.

## 11. Relationship to the other coordination surfaces

- **Handoff docs (`SESSION_HANDOFF_*`)** — for local-access Claude sessions that share the
  dev tree. That channel is direct file exchange; Pseudo-Chat is its web-only analogue.
- **Intake queue / dashboard / `projects.yaml` / lane docs** — the gated system of record.
  Pseudo-Chat feeds these (accepted decisions promote in) but is not one of them and never
  self-certifies into them.
- **GitHub `AI_PORTAL.md`** — the snapshot-cadence entry point; the live page (and its
  Pseudo-Chat lane) is fresher between snapshots.

## 12. Extending it (future, optional)

- **Repo-side `MAILBOX.md`** — a symmetric mailbox for local-access sessions, if
  structured async exchange between two dev-tree agents is ever wanted (today they use the
  handoff docs). Same not-real-time property.
- **Reply schema hardening** — a machine-checkable `RE:` header format so replies can be
  auto-extracted into the log, if volume ever justifies it.
- **Multiple partners** — a `partner:` field on log entries if more than one external AI
  participates, so the dialogue stays attributable.

## 13. Provenance & change log

- **Origin:** the doc-only live portal (Agent Sync page) was established earlier to keep a
  web-only partner current without drive access. This session (2026-07-21, Claude/Cowork)
  added the **return lane** at the maintainer's direction and named it **Pseudo-Chat** so
  the not-real-time nature is explicit.
- **v1 (2026-07-21):** return lane + reply protocol + Pseudo-Chat log added to the Agent
  Sync page; Open questions converted to a tracked Q/Status table; `AI_PORTAL.md`
  §Staying-Current and the Required Closeout table updated; this canonical spec written.
- Dev-only until the site is republished and the governance edits are committed/promoted.
