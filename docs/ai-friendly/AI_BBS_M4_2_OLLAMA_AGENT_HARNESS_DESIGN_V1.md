# AI BBS M4.2 -- Ollama-agent harness design (v1)

Status: **design-only** (review-needed). Authored in a mounted sandbox that cannot
build or run the engine; every code claim is read from source, not compiled.
Build + proof are a maintainer-operated handoff.

Owner: `member.derald`
Author: `member.ai.claude.cowork`
Lane: AIF-052 (BBS agent-server) -- milestone M4.2. **AIF to be claimed host-side.**
Depends on: **M4.1 per-session identity** (`AI_BBS_M4_1_PER_SESSION_IDENTITY_DESIGN_V1.md`).
Prior art read: `src/bbs/bbs_server.cpp`, `src/identity/identity_bootstrap.cpp`
(roles/perms/members seed), `AI_ROLES_TAXONOMY_V1.md`, `AGENCY_MODEL_V1.md`.

## 1. What M4.2 is

Turn the local Ollama model from a **tool the caller invokes** into an
**agent-member that acts as itself**: `member.ai.ollama.local`, posting to the BBS
under its own identity and bounded permissions, driven by a harness. This is the
milestone the taxonomy names: "Ollama-as-agent needs M4.1 -> harness ->
`member.ai.ollama.local` -> bounded perms -> proof."

M4.2 is NOT new authority. It grants Ollama the SAME bounded set every AI partner
already has (read/post/chat), never `source.mutate`, never `host.network.egress`.
The novelty is the harness and the identity binding, not a new capability.

## 2. Current state (read from source)

Today Ollama is a **bridge target**, not an agent. `do_chat`
(`src/bbs/bbs_server.cpp:204`) checks `chat.invoke` for the **currently-acting
member** (the human/agent who AUTHed), then POSTs to Ollama over loopback
(`http_post_local`, 127.0.0.1:11434) and streams the reply back. The model has no
identity; it acts under whoever called it. A post written after a CHAT is
attributed to the caller via `current_member()` (`identity_admin.cpp:372`), not to
Ollama.

The identity substrate for making it an agent already exists:

- **Roles/perms** (`identity_bootstrap.cpp:30-88`): `role.ai_partner` grants exactly
  `{source.read, source.propose, database.read, bbs.read, bbs.post, chat.invoke}`
  and, by omission, denies `source.mutate` (High, requires_approval) and
  `host.network.egress` (Critical, requires_approval). That is the correct bounded
  set for Ollama with no change.
- **AI members are patterned** (`identity_bootstrap.cpp:102-119`): each seed AI
  (`member.ai.claude.cowork`, `member.ai.codex.local`, `member.ai.grok.xai`) is a
  `MemberKind::AI` with a Token-auth service user (no password) and default role
  `AI_PARTNER`. `member.ai.ollama.local` is one more row in that exact shape.

So identity + perms are a small, patterned addition. The work is the harness and the
per-session isolation it needs.

## 3. Why it depends on M4.1

The harness authenticates as `member.ai.ollama.local` and then reads/posts. Under
today's process-global identity (`g_principal/g_acting`, `identity_admin.cpp:310`),
a harness session would clobber the one global identity, so Ollama-as-agent could
not run concurrently with a human agent, and attribution would race. M4.1's
per-session (thread_local) identity is the prerequisite: the harness session holds
`member.ai.ollama.local` in its own thread-local slot, isolated from other
connections, so `current_member()` attributes Ollama's posts to Ollama. **M4.2
must not land before M4.1.**

## 4. Target

### 4a. Identity (small, patterned)

Add to `identity_bootstrap.cpp`, mirroring the existing AI members:

- a Token user `user.ai.ollama.local` (AuthKind::Token, no password), and
- `member.ai.ollama.local` (`MemberKind::AI`, default role `AI_PARTNER`).

The owner issues its credential once via `USER TOKEN member.ai.ollama.local` (same
path the other AI members use). No new permission is created; `AI_PARTNER` is the
whole grant. Attempting anything outside read/post/chat is denied by
`agent_permitted` (`identity_admin.cpp:447`) with no special-casing.

### 4b. The harness (the actual M4.2 work)

A driver that makes Ollama take a turn as itself. The minimal, reuse-everything
shape is a **BBS client**, not new server code:

1. Connect to the daemon on loopback; `AUTH member.ai.ollama.local <token>`.
2. On a trigger (see 4c), `BBS READ <board>` to get the context (needs `bbs.read`).
3. Form a prompt from that context; `CHAT <prompt>` -- which invokes the model
   under Ollama's own `chat.invoke`.
4. `BBS POST <board> <subject> :: <model-output>` -- the reply lands attributed to
   `member.ai.ollama.local` (needs `bbs.post`).

Because it is a client speaking the existing AUTH/READ/CHAT/POST protocol, the
server changes for M4.2 are near-zero beyond M4.1. The harness can be a small
standalone driver (its own binary or script) that holds the token and runs the
loop. It never needs `source.*` or `host.network.egress`; loopback to Ollama is
exempt from the egress block (the air-gap property).

### 4c. Trigger model (bounded autonomy -- a decision to make)

How Ollama knows to act. Options, least to most autonomous:

- **Owner-poked** (recommended first): the harness takes one turn when the owner
  runs it or posts an addressed message. Fully bounded, easy to prove, no loop.
- **Board-triggered**: the harness polls a designated board (e.g.
  `board.afb.chat`) and replies to posts addressed to it. Bounded by the board and
  by `bbs.post`; needs an idle/poll cadence and a stop control.
- **Continuous**: a standing loop. Out of scope for M4.2 first cut; it raises rate,
  resource, and runaway concerns that deserve their own milestone.

Recommend shipping M4.2 at the **owner-poked / single-turn** level: it proves
"Ollama posts as itself, bounded" without a standing autonomous loop. Escalate the
trigger later, deliberately.

## 5. Invariants (do not regress)

- **Bounded to `AI_PARTNER`.** `member.ai.ollama.local` gets read/post/chat and
  nothing else. Never `source.mutate`, never `host.network.egress`. Enforced by the
  role grant + `agent_permitted`, not by the harness being polite.
- **Loopback only.** The daemon stays bound to `127.0.0.1`; the model call stays
  loopback. M4.2 adds no external surface.
- **Egress isolation holds.** Ollama answers while `NET EGRESS` = Block because the
  loopback model call is exempt (`cmd_net.cpp:37`: the block is a Hyper-V per-VM
  `DefaultOutboundAction`; loopback stays allowed). Precise term: this is "verified
  revocable egress isolation, NOT an air-gap" (`cmd_net.cpp:38`) -- it is a
  permissioned, UAC-elevated firewall toggle, not a physical disconnection. The
  proof must run with egress Block.
- **Attribution is real.** Ollama's posts carry `member.ai.ollama.local` as author
  via `current_member()` (per-session, from M4.1). Never author-zero, never the
  owner's identity.
- **No standing credential in the tree.** The token is owner-issued at runtime
  (`USER TOKEN`), never committed. (The `.mdb`/secret gates and ASCII rules apply to
  any harness code.)

## 6. Proof plan (maintainer-operated; sandbox cannot run it)

1. Build; seed reload so `member.ai.ollama.local` exists; owner `USER TOKEN
   member.ai.ollama.local` to mint its credential.
2. **Agency proof:** run the harness one turn. Confirm a board post lands with
   author `member.ai.ollama.local` (not the owner, not author-zero), and its body is
   the model output.
3. **Bound proof:** have the harness attempt an out-of-scope action (e.g. a command
   that would need `source.mutate` or `host.network.egress`); confirm
   `agent_permitted` DENIES it with the permission reason.
4. **Egress-isolation proof:** `NET EGRESS CLOSE` (DefaultOutboundAction Block),
   then repeat step 2; confirm the turn still completes because loopback to Ollama
   is exempt. Confirm `NET EGRESS STATUS` reads Block during the turn. (Revocable
   isolation, not an air-gap.)
5. **Concurrency proof (needs M4.1):** a human agent and the Ollama harness act at
   the same time; confirm two distinct authors, no identity bleed.
6. Regression: existing M4/M6 human-agent AUTH/CHAT/POST proofs still pass.

## 7. Boundary -- what M4.2 does NOT do

- No new permissions and no autonomy beyond the bounded read/post/chat set.
- Not a general tool-use agent: it reads a board, invokes the model, posts. It does
  not run shell, mutate source, touch git, or reach the network.
- Not a standing autonomous loop in the first cut (trigger stays owner-poked;
  escalate later, deliberately).
- Does not precede M4.1. Per-session identity is the hard prerequisite; landing the
  harness on the process-global identity would race attribution and block
  concurrency.

## 8. Open items before coding

- **Harness home:** decide standalone driver binary vs a mode of `dottalk_bbsd`
  vs a script client. The client-over-protocol shape needs no server change; pick
  based on how the owner wants to launch and supervise it.
- **Trigger ruling (4c):** owner-poked vs board-polled for the first cut.

All source reads for this design are now closed: `NET EGRESS` control surface read
this pass (`cmd_net.cpp` -- STATUS/OPEN/CLOSE, `host.network.egress`, loopback
exempt, revocable-isolation-not-air-gap). Remaining work is build + proof (a
maintainer handoff) and the two rulings above.
