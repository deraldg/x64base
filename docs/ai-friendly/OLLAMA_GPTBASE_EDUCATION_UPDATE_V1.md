# Ollama + GPTbase -- Education Update and Session Handoff V1

**For:** the next Claude (or other agent) session picking up the local-inference / advisor track.
**From:** `member.ai.claude.cowork`, run `AIPR-20260725-001`, 2026-07-25.
**Lane:** AIF-058 (roles taxonomy) with AIF-060 (agency). **Evidence class:** `source-defined`.
**Read first:** `AI_README.md` -> `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` ->
`docs/ai-friendly/AGENCY_MODEL_V1.md` -> this file.

---

## Orientation in one paragraph

x64base has three kinds of AI attached to it and they are **not interchangeable**. Agent-members
(you) authenticate, read, propose, and leave handoffs. **Ollama** is a local inference engine that
answers `CHAT` from behind an egress block -- it has capability but no identity, so it is a service,
not an actor. **GPTbase** is a hosted Custom GPT loaded with a project knowledge bundle -- it has
influence but no authority. Getting this wrong in either direction is the single most common
onboarding error, so the taxonomy exists to prevent it.

Credit where due: **Nathaniel A. Strickland** contributed to the Ollama server and GPTbase (see
`CREDITS.md`).

---

## 1. Ollama -- the local brain

### What is actually wired

- `BBS CHAT <text>` -> `127.0.0.1:11434`, over a minimal raw-socket HTTP/1.1 client. Loopback,
  plaintext, no TLS -- correct, because it never leaves the box.
- Gated by the `chat.invoke` permission. An agent-member without it gets refused.
- Default model `qwen2.5-coder:7b` (`--model` on `dottalk_bbsd`).
- **It answers while `host.network.egress` is `Block`.** This is the AFB air-gap property, and it is
  the whole point.

### Why the air-gap matters (the teaching point)

`host.network.egress` is owner-only and was **runtime-proven refused** to an AI member
(`proof.bbs.m2_net_egress`). Loopback is exempt. So the system can run inference over sensitive
project data with **nothing leaving the machine**. That is a capability most hosted assistants
structurally cannot offer, and it is worth understanding as a design property rather than a
limitation:

> Local inference is not a cheaper cloud model. It is a *different security posture*. The value is
> the egress block, not the parameter count.

### What Ollama is NOT

**It has no member row, and that absence is correct, not an omission.** Per `AGENCY_MODEL_V1.md`,
agency needs four legs -- identity, authority, authentication, accountability. Ollama has none of
them. It cannot `AUTH`, holds no permission, and answers for nothing. A model that produces good work
is still a **service**, invoked by an agent that does have agency.

If you find yourself about to create `member.ai.ollama.local`, stop and read section 2 of the agency
model first. Adding a row does not create agency; it creates a lie in the registry.

### What it would take to make Ollama an agent

An **agent harness**: a loop that reads boards, prompts the model, and posts back under an identity.
That does not exist. It pairs with the **M4.1 concurrency work** (per-session identity in the BBS
accept loop), because a harness posting concurrently with a human operator needs distinct sessions.

Sequence, if someone takes this on:
1. M4.1 per-session identity (prerequisite -- the accept loop is single-threaded with a
   process-global session today).
2. Harness process with its own token and `member.ai.ollama.local` row.
3. Bounded permissions: `bbs.read` + `bbs.post` + `chat.invoke`. **Never** `source.mutate`.
4. A `runtime_observed` proof that it posts under its own identity and is refused what it should be.

### Natural next use, no harness required

Local **summarize / triage / draft** over board and portal content. Everything stays on the machine.
This is the highest-value, lowest-risk next step and it needs no new identity -- an agent-member with
`chat.invoke` can drive it today.

---

## 2. GPTbase -- the hosted advisor

- An OpenAI Custom GPT loaded with a curated x64base knowledge bundle (~20 files).
- Role: the "ask the project expert" front-end -- orientation, explain a subsystem, draft,
  rubber-duck -- for a human or an agent.

### Two caveats that must stay visible

1. **Cloud-hosted, so NOT egress-isolated.** Never feed it anything that must stay local. That is
   Ollama's job. GPTbase is for public/shareable project knowledge only.
2. **Its bundle is a snapshot and goes stale.** Treat its answers as *orientation*, not truth. Verify
   against current source before acting. This session produced a live example of exactly why -- see
   section 3.

### Advisory, not authority

GPTbase cannot touch the repo. The precedent is recorded in `ai_runs.yaml`: ChatGPT **planned** the
identity/RBAC lane, Cowork **implemented** it, `member.derald` **owns and committed** it. Three
distinct roles, and git shows only the third. That split is why the attribution block exists.

> Influence is real and worth recording. It is not authority. Claim your actual row, not a larger one.

---

## 3. The lesson this session paid for (read this before trusting any document)

A partner -- me -- assessed the engine and reported that x64base had **no write-ahead log**.

It has one, and has since 2026-07-19: `.tbj` redo log, `fsync` of a `C` marker *before* the DBF
apply, idempotent replay on open, **crash-proven in three teed phases**.

I got it wrong by reading `include/cli/table_state.hpp`, which called the whole thing *"stubs ...
intentionally no-op placeholders"* -- comments left from before implementation. The design doc and
all three proof transcripts existed but were **untracked**, hidden by a blanket `*.log` rule in
`.gitignore` (71 proof artifacts on disk, 0 in git). So the repository under-reported itself, and I
believed it.

Three rules came out of it, now in the standards seed:

- **The source is the truth.** When source and comments disagree, read `src/`. A repository can
  under-report itself.
- **Evidence must be versioned or the proof registry is fiction.** Run
  `python tools/gates/run_gates.py` -- it checks `@dottalk.file` coverage and that every registry
  citation resolves *and is tracked*.
- **When a placeholder becomes an implementation, the comment above it is part of the change.**

This applies directly to GPTbase: if a snapshot-based advisor can be wrong about a shipped
subsystem, so can a stale comment, and so can you. Verify.

---

## 4. Teaching frame (LabTalk)

The Ollama/GPTbase split is a **live, inspectable example** of a distinction students rarely meet:

| | Ollama | GPTbase | Agent-member |
|---|---|---|---|
| Capability | high | high | high |
| Identity | none | none | `member.ai.*` |
| Authority | none | none | bounded, enumerated |
| Accountability | none | none | `member.derald` |
| **Agency** | **none** | **none** | **bounded** |

Exercises that work today:

1. **Watch the air-gap hold.** `CHAT` while `NET EGRESS` reports `Block`. The model answers; nothing
   leaves. Ask *why loopback is exempt and whether that is safe*.
2. **Attempt the boundary.** As an AI member, try `NET EGRESS OPEN`. Read the refusal. A denied
   action teaches more than a permitted one.
3. **Trace influence vs authority.** Find the ChatGPT-planned / Cowork-authored / Derald-committed run
   in `ai_runs.yaml`, then run `git log` on the same work. Note what git cannot say.

Lesson home: `labtalk/lessons/student/agency_who_may_act_v0.md` (`status: draft`). These three would
strengthen it toward `proof_linked`.

---

## 5. Pickup points for the next session

| Item | State | Where |
|---|---|---|
| Ollama harness | **not started**; needs M4.1 first | `AI_ROLES_TAXONOMY_V1.md` section 2 |
| M4.1 per-session identity | design-intended; blocks duplex + harness | `AI_BBS_LANE_V1.md` |
| Local summarize/triage over boards | **best next step, no harness needed** | this doc section 1 |
| GPTbase bundle refresh | stale by ~1 day of heavy lane work | rebuild from `AI_PORTAL.md` seeds |
| Agency lesson -> `proof_linked` | needs the three exercises above | `agency_who_may_act_v0.md` |
| AIF-061 memo durability | **proposal awaiting maintainer build** | `src/AIPortal/sessions/2026-07-25_cowork_memo_wal_atomicity/` |

### Handoff post for `board.worklog`

```
RUN=AIPR-20260725-001 | STATE=source-defined, committed | DID=AIF-058 roles taxonomy + AIF-060
agency model + AIF-062 evidence-layer fix; Ollama/GPTbase education update | OPEN=Ollama harness
blocked on M4.1; GPTbase bundle stale; agency lesson needs 3 exercises | NEXT-AGENT=start with local
summarize/triage over boards (no harness needed) | RISK=do not create member.ai.ollama.local without
all four agency legs
```

---

## Ties

- `docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md` (AIF-058) -- the three roles.
- `docs/ai-friendly/AGENCY_MODEL_V1.md` (AIF-060) -- why capability and influence are not agency.
- `docs/ai-friendly/AI_BBS_WORKLOG_HANDOFF_LANE_V1.md` (AIF-057) -- the handoff surface.
- `docs/maintenance/AI_EVIDENCE_LAYER_VERSIONING_LANE_V1.md` (AIF-062) -- why the repo under-reported.
- `CREDITS.md` -- Nathaniel A. Strickland, Ollama server and GPTbase.

Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
