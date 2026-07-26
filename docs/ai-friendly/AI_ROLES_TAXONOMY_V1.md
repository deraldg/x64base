# AI Roles in x64base -- Taxonomy V1

**Status:** source-defined. **Lane:** AIF-058 (continues run AIPR-20260725-001).
**Owning project:** `project.ai_friendly`. **Evidence class:** `source-defined`.

Purpose: name the kinds of AI in the system and what each can and cannot do, so nobody confuses an
**advisor** with an **agent**, or a **local model** with a **member**. This is the first entry in the
portal's capability inventory (bleeds ignorance -- see `AI_PORTAL_HARDENING_LANE_V1.md`).

There are three roles. They are not interchangeable.

## 1. Doers -- agent partners (members)

Grok (`member.ai.grok.xai`), Claude/Cowork (`member.ai.claude.cowork`), Codex (`member.ai.codex.local`).

Agentic. They **authenticate** with owner-issued tokens, read the seeds, propose and deliver **source
changes** (as change packages, Outside-AI Delivery Rule), and leave **worklog handoffs**. Bounded by
RBAC: `role.ai_partner` never gets `source.mutate` or `host.network.egress`. **These are the ones that
do the work.** They have member rows and identities.

## 2. Local brain -- Ollama (AFB isolated)

*Credit: **Nathaniel A. Strickland** -- the Ollama local model. See `CREDITS.md`.*

**Not a member; no identity row** (that is correct, not an omission). It is the CHAT backend:
`BBS CHAT` -> `127.0.0.1:11434`, gated by `chat.invoke`, and -- the whole point of the AFB air-gap --
it answers **while egress is Blocked** (loopback exempt).

Role: the **isolated local inference engine.** Today: conversation behind `CHAT`. Natural next:
local **summarize / triage / draft** over board and portal content -- with nothing leaving the
machine. Its value is exactly that privacy: inference you can run over sensitive project data
egress-blocked.

Not autonomous. To become a posting member (`member.ai.ollama.local`) it needs an **agent harness** (a
loop that reads boards, prompts the model, posts back) -- which does not exist, and which pairs with
the M4.1 concurrency / duplex work. The raw model is a service, not an agent.

## 3. Hosted advisor -- GPTbase (OpenAI Custom GPT)

*Credit: **Nathaniel A. Strickland** -- GPTbase. See `CREDITS.md`.*

**Not a member; cannot touch the repo.** A hosted GPT loaded with a curated x64base knowledge bundle
(~20 files). Role: the **"ask the project expert" front-end** -- orientation, explain a subsystem,
draft, rubber-duck -- for a human or an agent.

Advisory, not authority. Two caveats that must stay visible:

- **Cloud-hosted, so NOT egress-isolated.** Do not feed it anything that must stay local -- that is
  Ollama's job. GPTbase is for public/shareable project knowledge.
- **Its knowledge is a SNAPSHOT** of the bundle at load time. It goes stale ("ether") unless the
  bundle is refreshed. Treat its answers as informed suggestions to verify against source, never as
  the source of truth.

## Boundaries to keep (ignorance-bleeding)

- An **advisor (GPTbase) is not an agent**: it cannot authenticate, act, or deliver a change package.
  Route its output through a real agent-member + the change-package contract.
- A **local model (Ollama) is not a member**: it needs a harness before it can post or act.
- Only the **agent-members** deliver change under the Outside-AI Delivery Rule.

## Where each fits the workflow

| Need | Use |
|---|---|
| Orientation / explain a subsystem | GPTbase (hosted, knows the bundle) or the portal seeds (authoritative, in-repo) |
| Private inference over board / lane content | Ollama (egress-blocked, local) |
| Actually change source / leave handoffs | the agent-members (Grok, Cowork, Codex) |

## Capture-while-hot

GPTbase's knowledge bundle is a snapshot; **refresh it when the project moves or it goes ether.** Same
discipline that produced this taxonomy -- write it down while it is fresh, or the boundary is lost and
the next person makes a local model a member, or trusts a stale hosted advisor as truth.

## Provenance

AIF-058, 2026-07-25, continues run AIPR-20260725-001. Companion lanes: AFB/Ollama isolated runtime
(`app.labtalk.afb`), GPTbase hosted GPT, AI-BBS worklog/handoff (AIF-057). First artifact of the
portal capability inventory called for in `AI_PORTAL_HARDENING_LANE_V1.md`.
