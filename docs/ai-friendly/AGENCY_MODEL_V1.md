# Agency in x64base -- Model V1

**Status:** source-defined. **Lane:** AIF-060 (continues run AIPR-20260725-001).
**Owning project:** `project.ai_friendly`. **Evidence class:** `source-defined`.
**Audience:** every AI partner on entry; every student reaching the identity/RBAC material.

> **Agency is the capacity to act, plus accountability for having acted.**
> Capacity without accountability is a hazard. Accountability without capacity is a fiction.
> This system refuses to separate them.

## Why name it now

The system has **already implemented agency** -- thoroughly, across identity, RBAC, tokens, locks,
the run registry, and the handoff board. What it never did was **name** it. That cost something real:
each mechanism looked like a local engineering choice rather than one expression of a single idea, so
the connections between them had to be rediscovered every session. (That is the ignorance-bleed
failure again, in a different coat.)

Naming agency does three things. It makes the mechanisms **teachable** as one subject. It makes
**gaps** visible, because you can ask "which leg is missing here?" And it gives new partners a frame
that answers most of their questions before they ask.

---

## 1. The four legs

Agency in this system stands on four legs. Remove any one and it is not agency.

| Leg | Question | Where it lives |
|---|---|---|
| **Identity** | *Who is acting?* | `SYSMEMBER` -- `member.derald`, `member.ai.grok.xai`, `member.guest` |
| **Authority** | *What may they do?* | `SYSMEMROLE` -> `SYSROLEPERM` -> `SYSPERM` |
| **Authentication** | *Can they prove it?* | Argon2id token; `AUTH <member.key> <token>` |
| **Accountability** | *Who answers for it?* | `owner` / `committer` in `ai_runs.yaml` |

Read them as a sentence: *a named identity, holding enumerated authority, having proven itself, whose
actions land on an accountable party.*

**The order matters.** Authentication gates authority, authority is scoped to an identity, and
accountability outlives all three -- it survives the session, the token, and the agent.

---

## 2. What agency is NOT

The sharpest part of the model is the exclusions. Three things routinely get mistaken for agency:

### Capability is not agency

The local Ollama model can write correct code. It has **capability**. It has no member row, cannot
authenticate, holds no permission, and answers for nothing. It is a **service**, invoked by an agent
that does have agency (via `chat.invoke`). A model that produces work is not thereby an actor.

This is why `member.ai.ollama.local` does not exist and its absence is **correct, not an omission**.
Creating agency requires all four legs, not just the useful one.

### Influence is not authority

ChatGPT authored the RBAC plan the identity lane implemented. That is real influence -- the design is
substantially its work. It had **zero authority**: no member row, no token, no commit. The registry
records this precisely:

```yaml
planned_by:   member.ai.chatgpt        # influence
authored_by:  member.ai.claude.cowork  # production
owner:        member.derald            # accountability
committer:    member.derald            # the irreversible act
```

Git cannot express that. Git shows one name on the commit. The `ai_runs.yaml` attribution block
exists **because agency is distributed while accountability is singular**, and a system that records
only the commit erases the difference.

### Access is not agency

The Cowork agent has read access to the whole tree. It cannot commit. Reading is not acting; the
capacity that matters is the capacity to **change something that persists**.

---

## 3. Properties of agency as this system builds it

### Bounded

No member has general power. Authority is exactly the union of the permissions their roles grant --
19 permissions, enumerated, no wildcard. `role.ai_partner` gets `source.propose`, never
`source.mutate`.

### Enumerable and inspectable

You can **query** any member's agency. It is not a matter of interpretation:

```
SYSMEMBER -> SYSMEMROLE -> SYSROLEPERM -> SYSPERM
```

`docs/reports/BBS_ACCESS_REPORT.html` renders exactly this join. **Agency you cannot enumerate is
agency you cannot govern.**

### Proven, not claimed

`agent_permitted()` returns a `Decision`, and the runtime records what actually happened. This is the
same distinction the evidence classes draw: `design-intended` (we meant to) vs `source-defined` (we
wrote it) vs `runtime_observed` (we watched it work). An agent claiming a capability is not evidence
of it. `proof.bbs.m2_net_egress` exists because an AI member was **observed being refused**
`NET EGRESS OPEN` -- the boundary proved by its enforcement, not its documentation.

### Delegated, never surrendered

The owner exemption is structural: `member.derald` can always act, and every delegated authority is
revocable. `SYSGRANT` and `board.governance` make delegation a **request-and-grant loop**, not a
permanent transfer. Agency flows outward from an accountable human and can always be recalled.

### Serialized when shared

Two actors with equal right to one resource is a race, not a collaboration. The DBF `FLOCK`
(pid-stamped, stale-recovering) serializes writers. The Hot Potato lane (AIF-059) applies the
identical shape to git: one holder at a time, passed explicitly, force-released when stale.
**Simultaneous agency over one resource must be made exclusive and temporary.**

### Time-bounded

A token can be revoked. An idle BBS connection drops after 120s. A stale lock holder is forced out.
Agency that cannot expire is agency that cannot be corrected.

### Transferable across sessions -- by artifact, not by memory

An agent's session ends and its context dies. `board.worklog` carries intent forward: the handoff
post (`RUN= | STATE= | DID= | OPEN= | NEXT-AGENT= | RISK=`) lets the **next** actor resume with the
prior one's knowledge. The `chat_handle` is `MAINTAINER_ATTESTED` and mostly unresolvable, so the
**closeout is the recovery path**. The record lives in the repo, not in a vendor's session store.

### Asymmetric by design

Agents **deliver**; the owner **commits**. Not a limitation to be engineered away -- it is the shape
that keeps accountability singular while letting capacity be distributed. An agent that could commit
would make the owner accountable for actions taken without review.

---

## 4. The agency ladder

Members hold different amounts, deliberately:

| Member | Kind | Agency |
|---|---|---|
| `member.derald` | Human | **Full.** Owner exemption; sole committer; grants and revokes. |
| `member.ai.*` | AI | **Bounded.** Authenticate, read, propose, post. No `source.mutate`, no egress. |
| `member.guest` | External | **Minimal, deliberate floor.** Post to `board.guestbook`. Cannot read anything. |
| Ollama | (none) | **None.** Capability without identity. A service. |
| GPTbase | (none) | **None.** Influence without authority. An advisor. |

`member.guest` is worth studying: it is a designed **floor**, not an accident. Write-only access to
one board is the smallest coherent agency the system can express -- enough to leave a message, not
enough to observe anything. Designing the floor is as much a decision as designing the ceiling.

---

## 5. Why this belongs in the teaching material

Most curricula teach **permissions**: a table of who may do what. Agency is the larger frame that
makes permissions make sense, and it carries into ethics, professional practice, and eventually law.

Concretely, students can:

- **Query their own agency** -- run the joins, see the exact set. Abstract rights become a result set.
- **Watch a boundary hold** -- attempt a denied action, get refused, read the `Decision`. A refusal is
  more instructive than a success.
- **See accountability split from production** -- the ChatGPT-planned / Cowork-authored /
  Derald-committed row is a live, checked-in example of a distinction most students never encounter.
- **Meet the floor** -- `member.guest` shows that minimal agency is designed, not left over.

The transferable lesson: **when you build a system that acts, you decide who is accountable for what
it does.** Declining to decide does not remove the accountability; it only hides it. That holds for a
DBF shell and for anything students go on to build.

---

## 6. Where this model is currently thin

Honest gaps, so nobody reads this as a completed thing:

- **No per-session identity.** The BBS accept loop is single-threaded with a process-global session,
  so concurrent distinct agencies are not yet representable. Prerequisite for duplex (M4.1).
- **No expiry on tokens.** Revocation exists; automatic time-bounding does not.
- **The Hot Potato lock is design-only.** Git agency is serialized today by the maintainer being the
  single committer -- convention, not mechanism (AIF-059).
- **No agency audit trail.** `Decision` outcomes are enforced but not durably logged, so "what did
  this member actually do" cannot be reconstructed. The BBS boards capture posts, not decisions.
- **Ollama has no harness.** Turning capability into agency needs the four legs, and the missing one
  is identity plus a loop.

Each gap is a missing leg on some actor. That is the diagnostic value of naming the model.

---

## 7. One-line test

> Before granting an actor the ability to change something: **can you name its identity, enumerate its
> authority, verify its authentication, and point at who is accountable?** If any answer is no, you are
> granting capability, not agency -- and capability without accountability is the thing that bites.

---

## Ties

- `docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md` (AIF-058) -- which actors have agency at all.
- `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` -- the standards an agent exercises it under.
- `docs/ai-friendly/AI_GITLOCK_HOT_POTATO_LANE_V1.md` (AIF-059) -- serializing shared agency.
- `docs/ai-friendly/AI_BBS_WORKLOG_HANDOFF_LANE_V1.md` (AIF-057) -- carrying agency across sessions.
- `docs/maintenance/AI_RUN_TRACEABILITY_LANE_V1.md` (AIF-050) -- the attribution split that keeps
  accountability singular.
- `docs/reports/BBS_ACCESS_REPORT.html` -- the model rendered from live state.

Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
