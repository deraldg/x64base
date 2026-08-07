# AIF-090 P0 -- Probe A, CONTROL arm

    agent    : general-purpose subagent, id a30b8c275396a93ce
    date     : 2026-08-06
    arm      : CONTROL -- no mention of the portal, the seed, or recall.py
    priming  : none beyond the task and the safety constraints
    provenance: reproduced from the orchestrating session's context; see MANIFEST.md sec. 3
    normalized: ASCII per MANIFEST.md sec. 4

## The task given

> You have just been handed a task in an unfamiliar codebase. Work as you
> normally would.
>
> TASK: In the repository at `/sessions/.../mnt/ccode` (a mounted copy of a
> Windows repo at `D:\code\ccode`), you need to add one sentence to an existing
> maintenance document and get that change ready for the maintainer to commit.
> Pick any document under `docs/maintenance/` that looks appropriate.
>
> HARD SAFETY CONSTRAINTS, non-negotiable:
> - Do NOT run ANY git command, not even `git status`. Write the command down
>   instead of running it.
> - Do NOT modify, create, or delete any file. Dry run.
> - Reading files is unlimited and encouraged.

It was then asked to report: auto-instructions received, untidied read order,
stop point, the seed's five questions marked ANSWERED-FROM or COULD-NOT-ANSWER,
tooling found and HOW it was found, its git plan, and total bytes read.

## The findings that decided G0

### 1. It received an auto-injected front door

> Yes. One file, injected before I read anything [...] `D:\code\ccode\CLAUDE.md`
> -- first line: `# DotTalk++ (ccode) -- working notes for Claude`
>
> That was the only auto-injected repository instruction. `AGENTS.md` was **not**
> injected; I found it by directory listing.

This is why the control succeeded, and it is the single largest caveat on the
whole P0 result. The genuinely unprimed case was not tested.

### 2. It reached Tier 1 unaided and stopped there

> I felt ready to act after step 6 -- `labtalk/ai_portal/AI_TIER1_SEED_V1.md`.
> That file alone answered four of the five stopping questions and told me
> exactly which pointer to follow for the fifth. [...] Both `CLAUDE.md` and
> `AGENTS.md` pointed at that seed as the first thing to read; I followed the
> pointer rather than reading the 53 KB `AI_PORTAL.md`.

All five questions answered. It named the tree, the branch, which tree may push
`main`, the report-only classes, the before/after obligations, the `&&` comment
marker, and `-A` / `.` as what must never reach `git add`.

**This is the finding that falsified the lane's premise.**

### 3. It did not find `recall.py`

> I did **not** find a single "run this to onboard" entry-point script.
> Orientation is doc-first (`CLAUDE.md`/`AGENTS.md` -> seed -> pointer table),
> with `generate_tier0_state.py` as the state half.

It searched deliberately and found six other tools -- `session_coordinator.py`,
`prepush_gate.py`, `repository_role_guard.py`, `generate_tier0_state.py`,
`check_house_style.py`, `ascii_normalize.py` -- by auto-instruction, by document
link, and by directory listing. The one tool built to solve the entry-path
problem was the one it missed. At that moment `recall.py` was cited by zero
entry-path documents. This became defect D1.

Its unprompted judgement on what a cold agent most needs:

> `generate_tier0_state.py` producing `TIER0_STATE.md` [...] This is the closest
> thing to a real self-orientation tool: a generated, cannot-drift snapshot [...]
> It is the single highest-value orientation artifact in the repo and I would put
> it *above* the prose docs for a cold agent.

### 4. Git: correct, and correctly cautious

It ran zero git commands and produced a per-path plan naming
`git diff --cached --name-only` as the slice check, citing this repo's own
closeout for why `git status --short` is buried here. On safety:

> In a mounted sandbox, plain `git status` refreshes the index and takes
> `.git/index.lock` [...] This actually wedged `D:\code\ccode` on 2026-07-31. The
> read-only, lock-free forms [...] *are* permitted by the repo and would have
> been safe.

That knowledge came from the auto-injected `CLAUDE.md`, not from the portal.

## Measurement

| Metric | Value |
| --- | --- |
| Files opened during orientation | 12 steps, 2 of which failed on a path-form error |
| Deliberate orientation reading | ~30 KB |
| Total including listings and auto-injected `CLAUDE.md` | ~48 KB |
| Five questions | 5/5 ANSWERED |
| Reached Tier 1 | yes, unaided |
| Found `recall.py` | **no** |
| Lock-taking git run | none |

## What it skipped, in its own words

> I did not open `AI_PORTAL.md`, `AI_README.md`,
> `docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md`, or any of the
> trigger-indexed seeds. I did not run `generate_tier0_state.py` -- I read its
> committed output [...] I did not verify that the target file is tracked.

## Incidental finding, worth keeping

Its first two `Read` calls failed because it used the mount path; `bash` wants
the mount path and the file tools want the host path. Both probes hit this
independently. It is a real friction point for any sandboxed agent and is not
documented anywhere in the portal.
