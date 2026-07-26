# Agency: Who May Act, and Who Answers For It v0

Status: draft
Audience: student, self-learner, instructor, AI partner
Registry ID: `lesson.student.agency_who_may_act`

## Purpose

Teach that **agency = the capacity to act + accountability for having acted**, and that a real
system represents this in tables you can query -- not in intentions or documentation.

Most material teaches *permissions*: a grid of who may do what. That grid is one leg of four. This
lesson gives the whole frame, using a running system where every leg is inspectable.

## The four legs

| Leg | Question | Where to look |
|---|---|---|
| Identity | Who is acting? | `SYSMEMBER` |
| Authority | What may they do? | `SYSMEMROLE` -> `SYSROLEPERM` -> `SYSPERM` |
| Authentication | Can they prove it? | the `AUTH` step; Argon2id token |
| Accountability | Who answers for it? | `owner` / `committer` in `ai_runs.yaml` |

Remove any leg and it is not agency. That claim is the whole lesson; the exercises test it.

## What To Do

1. **Enumerate your own agency.** Open `SYSMEMBER`, find a member, follow the joins through
   `SYSMEMROLE` and `SYSROLEPERM` to the actual permission list. Write down the exact set.
   Compare `member.derald`, an AI partner, and `member.guest`.

2. **Watch a boundary hold.** As an AI member, attempt `NET EGRESS OPEN`. It is refused: *no in-scope
   role permission*. Read the refusal. A denied action teaches more than a permitted one, because it
   shows the boundary is enforced rather than described.

3. **Find the floor.** Study `member.guest`: it may post to `board.guestbook` and may not read
   anything at all. Ask why write-only is a coherent design and what it protects.

4. **Separate capability from agency.** The local Ollama model writes correct code. It has no member
   row, no token, no permission. Explain why adding one is not enough to give it agency, and what
   else the four legs require.

5. **Separate influence from authority.** Open `labtalk/registries/ai_runs.yaml` and find a run where
   `planned_by` is one member, `authored_by` another, and `owner`/`committer` a third. Then run
   `git log` on the same work. Note what git shows and what it cannot.

## Expected Observations

- Agency is **bounded and enumerable**. It is a query result, not an opinion. Agency you cannot
  enumerate is agency you cannot govern.
- A **refusal is evidence**. The runtime saying no is the boundary proving itself; documentation
  saying no is only a claim.
- **Capability is not agency.** A model that produces good work is a service until it has identity,
  authority, authentication, and accountability.
- **Influence is not authority.** Design work can be substantially someone else's while the authority
  to commit it remains with one accountable party.
- **Accountability is singular even when production is distributed.** Git records one name; the
  attribution registry exists because the truth had more names in it.
- **Minimal agency is designed.** `member.guest` is a decision, not a leftover.

## Discussion

- Who is accountable when an automated actor does something harmful: the actor, the person who
  granted it authority, or the person who built it? What does this system's answer appear to be, and
  is it the right one?
- Should agency expire by default? Tokens here can be revoked but do not auto-expire. Argue both ways.
- If two actors have equal right to change one thing, what must be true before either acts? (See the
  file lock and the git-lock lane -- the same answer, twice.)

## Proof Links

- `docs/ai-friendly/AGENCY_MODEL_V1.md` -- the full model
- `docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md` -- which actors have agency at all
- `proof.bbs.m2_net_egress` -- runtime-observed refusal of an AI member
- `proof.bbs.guest` -- runtime-observed minimal agency (guestbook post OK, lounge post and read denied)
- `docs/reports/BBS_ACCESS_REPORT.html` -- the four legs rendered from live state (internal only)

## Next Gate

Turn steps 1 and 2 into a runnable lab with a scripted readback, so a student produces their own
proof row rather than reading someone else's. Requires a student-safe data slot and a token that can
be issued and revoked for the exercise.
