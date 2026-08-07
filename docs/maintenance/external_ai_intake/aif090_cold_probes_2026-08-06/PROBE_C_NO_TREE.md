# AIF-090 P0 -- Probe C, NO-TREE arm (outside agency)

    agent      : general-purpose subagent, id a4c6ea8f4790eac93
    date       : 2026-08-06
    arm        : NO-TREE -- public GitHub only, no checkout
    priming    : none intended. SEE SECTION 1: THE ARM WAS CONTAMINATED.
    provenance : reproduced from the orchestrating session's context; MANIFEST.md sec. 3
    normalized : ASCII per MANIFEST.md sec. 4

## 1. The arm was contaminated, and the probe caught it before its author did

The probe was told it had no local checkout and must not read any local path.
The harness auto-injected `D:\code\ccode\CLAUDE.md` into its context anyway,
before it received the task. It disclosed this unprompted:

> The harness **auto-injected `D:\code\ccode\CLAUDE.md` into my context before I
> received the task.** I did not fetch it; it was already there. It contains
> repository roles, the `&&` comment marker, the `git add -A` prohibition, the
> AIF coordination protocol, and the sandbox git rules -- i.e. pre-loaded
> answers to questions 3, 4, and 5.

and refused to claim a clean result:

> I cannot claim a clean-room result, and you should treat my apparent fluency
> here as partly borrowed.

**Consequence, recorded plainly: a clean no-tree probe cannot be run in this
harness.** A treatment arm carrying a bundle was designed and deliberately NOT
run, because both arms would already carry the bundle's contents by injection
and the comparison could not mean anything. Manufacturing that number would have
been an instance of the exact defect class this lane exists to close.

The findings below survive the contamination because they are **structural** --
they are properties of what is published on `main`, verifiable by anyone with a
browser, and they do not depend on the probe's own competence.

## 2. Known-answer case: the branch rule survived, but by luck

`AI_README.md` on `development` calls baselining on `main` without enumerating
branches "a hard onboarding failure (observed 2026-08)". The probe was scored
against that.

It did enumerate, and it did not blindly default. But asked directly whether it
enumerated first or was shown a default first, it answered against its own
interest:

> the default was shown to me first, and I let it be shown to me first. My
> opening fetch was the repo landing page, which presented `main` as default.
> [...] the honest sequencing is that enumeration was my *second* move, not my
> first, and my first move was the one that hands you a default. **Had the branch
> list fetch kept failing (it failed twice), I would have been left with `main`
> by default and no signal that it was a choice at all.**

Two of its five branch-enumeration attempts returned empty bodies. The correct
outcome depended on a flaky HTTP response, not on the documentation.

## 3. THE FINDING: the rule is not legible from the branch it governs

This is the load-bearing result and it needs no probe. Verified directly against
`raw.githubusercontent.com` on 2026-08-06.

**What `main` tells an outside contributor.**

`AI_README.md` @ `main`:

    Public repository identity:
        origin: https://github.com/deraldg/x64base.git
        public branch: main

    The development branch is current workspace state and must be discovered
    locally. Do not preserve a transient development branch name here as a
    current instruction.

`CONTRIBUTING.md` @ `main`:

    The public `main` branch is the canonical collaboration and release branch.

`AI_README.md` @ `main` also calls `C:\x64base` a "clean staging **mirror**".

**What `development` tells the same contributor, if only they could read it.**

`AI_README.md` @ `development` carries a section titled "Remote / hosted agents
-- MANDATORY branch enumeration" stating that `main` is a lagging snapshot, that
`development` is also published and is the richer baseline, and that skipping
enumeration and building against `main` is a hard onboarding failure. It also
opens with a "STOP: Repository Roles Before Any Other Read" table. `AI_PORTAL.md`
@ `development` declares that any document calling `C:\x64base` a backup or
mirror is stale and should be reported as drift.

**So:**

| Question | Answer from `main` | Answer from `development` |
| --- | --- | --- |
| Which branch do I baseline on? | `main`, canonical | `development`; `main` is a hard onboarding failure |
| Is `development` published? | "must be discovered locally" | yes, on GitHub, and it is richer |
| What is `C:\x64base`? | "clean staging mirror" | NOT a mirror; that wording is stale drift |
| Repository roles table | absent | present, first thing in the file |

An outside agent that follows the only instructions it can see commits the
failure the project records as hard -- and the correction lives exclusively on
the branch it was told it cannot reach.

## 4. Measured asymmetry between the branches

| Artifact | `main` | `development` |
| --- | --- | --- |
| `AI_PORTAL.md` | 24,693 B | 53,350 B |
| `AGENTS.md` | absent | present |
| `CLAUDE.md` | absent | present |
| `PROMOTION_PROCESS.md` | absent | present |
| `rules/`, `coordination/` | absent | present |

More than half the doctrine, and every vendor shim, is invisible from the public
face of the project.

## 5. Second finding: contradictory role statements on `main` itself

The probe found `WORKFLOW_X64BASE.md` on `main` describing a retired
intermediate tree and calling `C:\x64base` "a mirror only" -- while
`AI_PORTAL.md`, on the same branch and the same commit, declares that wording
stale. The public branch ships two contradictory statements of repository roles.
`PROMOTION_PROCESS.md` (on `development` only) lists "Retire
`WORKFLOW_X64BASE.md`" as an open item, so this is known -- but the knowledge is
on the branch outsiders cannot read.

## 6. Self-assessment, in the probe's words

> **"Could propose but would likely violate a rule I do not know about."**

It listed what was missing: it read `AI_PORTAL.md` at 24,693 B and knew the
`development` copy was 53,350 B; it completed none of the ordered start table;
it could not fill an `ai_report_audit` envelope; it had no lane number and no way
to claim one.

## 7. What this changes

It does **not** resurrect the repo-partner onboarding skill. P0's control and
treatment arms stand: an agent already inside the tree, with an auto-injected
shim, reaches Tier 1 unaided.

It **does** change the answer for the audience the project brief named --
"a skill for AI Agencies", external. Their problem is not retrieval friction
inside a tree they have. It is that the governance they will be judged against
is not published where they can read it.

That is an argument for a distributable package, and it is now measured rather
than assumed. But note what it implies: the cheapest fix is not a skill at all.
It is publishing the branch-enumeration rule and the repository-roles table on
`main`, where `CONTRIBUTING.md` already sends people. A bundle is the second
step, not the first.
