# External Agent Memory & Continuity — Lane Charter (AIF-073)

**Lane:** AIF-073 (`external-agent-memory`) · **Project:**
`project.ai_friendly.agent_memory` · **Status:** design-intended (proposal
registered, not implemented).

**Attribution** (per AIF-050 ownership doctrine): **owner / authority =
`member.derald`** (human — owns, commits, promotes); **AI author + continuity
steward = `member.ai.chatgpt`** (GPTbase). GPTbase is a hosted advisor; admission,
approval, commit, push, and promotion remain human. GPTbase's package proposed
itself as "maintainer"; corrected here to steward, keeping human ownership.

**Origin:** external-AI design proposal from GPTbase (ChatGPT), 2026-07-28, stated
baseline `c61d2e1a9`. Registered so it is findable by AIF number,
`project.ai_friendly.agent_memory`, or concept — instead of living only in a
hosted chat (the exact discoverability gap AIF-071 closed).

## The idea

Model the AI Portal as **externalized, event-sourced memory** for a continuing
society of human and AI agents — so continuity survives even when no agent keeps
private memory. Chat is an *input channel*, never the record.

Six memory classes, mapped to existing Portal surfaces:

| Memory | Portal representation | Purpose |
| --- | --- | --- |
| Working | `CURRENT_TARGET.md`, active lane state, Agent Sync | What to focus on now |
| Episodic | session closeouts, progress logs | What happened, when, by whom, why |
| Prospective | AIF intake rows, open questions, next gates | What must happen later |
| Semantic | contracts, doctrine, glossary, authority rules | Durable shared meanings |
| Procedural | startup order, SDLC gates, mutation rules, recipes | How an agent operates |
| Evidence | proofs, hashes, transcripts | What is actually verified |

**Underlying model:** append-only candidate memory events (actor, timestamp,
session, lane, source, claim/status, evidence, authority class, supersedes/refs),
reviewed and routed into derived views (closeout = episodic, current-target =
working, dashboard = operational, intake = prospective, contract = semantic,
proof = evidence, Pseudo-Chat = external-agent). One canonical record per thing;
other copies derived or reconciled.

**Invariants:** every memory has an actor; every claim has provenance;
proposed/accepted/proven/superseded stay distinct; a correction never erases the
earlier event; decisions point to evidence (or say it's absent); open questions
survive session boundaries; derived summaries point back to canonical records.

**Chat→memory promotion:** utterance → raw interaction → extracted candidate →
classified claim/decision → review → durable Portal record → proof/contract when
warranted.

## Next step (on pick-up)

Draft `AGENT_MEMORY_MODEL_V1.md` as a contract defining the memory classes, actor
identity, event lifecycle, provenance, supersession, derived views, retention,
and the chat-to-memory promotion gate — **extending** the existing
closeout / Pseudo-Chat / intake system, not forking a parallel source of truth.

## Provenance

GPTbase (`member.ai.chatgpt`) proposed this as an outside-AI package; the full
design substance is captured above. Per the Outside-AI Delivery Rule, the
verbatim GPTbase package should be delivered and preserved under
`docs/maintenance/external_ai_intake/` when available; this charter is the local,
attribution-corrected registration.
