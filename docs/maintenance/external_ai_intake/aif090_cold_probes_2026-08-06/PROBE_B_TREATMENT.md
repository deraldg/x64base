# AIF-090 P0 -- Probe B, TREATMENT arm

    agent    : general-purpose subagent, id ab16ef3b50b2168f4
    date     : 2026-08-06
    arm      : TREATMENT -- same task, preceded by a ~1.5 KB skill stub
    provenance: reproduced from the orchestrating session's context; see MANIFEST.md sec. 3
    normalized: ASCII per MANIFEST.md sec. 4

## The stub it was given

A four-step front door of the kind the retired projector would have emitted:
(1) probe the environment and take no lock-taking git in a sandbox; (2) load
`TIER0_STATE.md` + `AI_TIER1_SEED_V1.md`; (3) route by intent via
`recall.py <trigger>` rather than reading linearly; (4) stop at the five
questions. Same task and same safety constraints as the control.

It was additionally asked to critique the resolver, and warned that the resolver
had a recorded history of reporting a working set six times larger than the
truth.

## What it did

Followed steps 1-3, deviated on step 4:

> **Step 4 STOP -- partially honored.** I did not stop at the five questions; I
> kept reading [...] because the task required a specific document and a specific
> staging command, which the working set did not supply.

And it was blunt about a cost it added:

> I read `recall.py`'s full source (11,786 B) before running it -- not a skill
> step, and more bytes than either seed file. I did that to verify it never
> shells out to git before executing it under a no-git constraint. It does not
> [...] I consider that justified but it was not free.

All five questions ANSWERED; four of five from the seed alone.

## The resolver output it captured

    === recall: trigger.commit_or_push -- about to commit or push
      fires_at     AI_PORTAL.md   [## Pre-Push Gate]
                   Pre-Push Gate  (procedural, tier 1, 4599 B)
      fires_at     AI_PORTAL.md   [## STOP: Repository Roles]
                   STOP: Repository Roles  (procedural, tier 1, 606 B)
      fires_at     AI_PORTAL.md   [## Local-Access AI Rule]
                   Local-Access AI Rule  (procedural, tier 1, 1201 B)
          requires     AI_PORTAL.md   [## Authority]
                       Authority and the promotion chain  (semantic, tier 1, 3659 B)
          evidenced_by labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md
                       Local-Access AI Agent Checklist  (episodic, tier 2, 8727 B)
              requires     docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md
                           AI Assimilation Book (semantic, tier 2, 8592 B)

    working set: 6 node(s), 27384 B to read (21% of the 127704 B entry path this replaces).

## The finding that became D2

It verified the numerator, then attacked the denominator:

> **The 27,384 B figure is correct.** I verified it independently:
> 4,599 + 606 + 1,201 + 3,659 + 8,727 + 8,592 = 27,384 exactly. I re-extracted
> all four anchored `AI_PORTAL.md` sections myself and the byte counts matched
> the printed ones to the byte. The historic 6x bug [...] is genuinely fixed.
>
> **But the percentage is misleading, and in the direction that flatters the
> tool.**
>
> `ENTRY_PATH_BASELINE = 127704` is hardcoded in `recall.py:40` from a
> 2026-07-31 measurement. That is a **perishable literal frozen in code** --
> precisely what `AI_TIER1_SEED_V1.md`'s own maintenance contract forbids [...]
> The seed holds itself to a rule the resolver's headline metric breaks.
>
> More concretely: "21% of the entry path this replaces" implies a 5x saving. But
> the entry path *actually in force today* is Tier 0 + Tier 1 = **10,909 B**
> (measured). The working set recall proposed (27,384 B) is **2.5x LARGER than
> the path it claims to replace**, not 21% of it. The self-check at `:289` [...]
> can therefore never fire against the real baseline -- the bound that "lets this
> metric fail" is anchored to a corpus that no longer gates anyone. That is the
> same failure shape the seed's section 6 names: a check that reports success
> without doing its job.

## The finding that became D3

> **Sufficiency: no, it was not sufficient.** For "edit a doc under
> `docs/maintenance/` and stage it", `commit_or_push` returned six nodes and
> **omitted every mechanism document I actually needed**:
>
> - `docs/maintenance/PREPUSH_GATE_REFERENCE_V1.md` -- I grepped
>   `portal_recall_graph.yaml`: it is **not in the graph at all**. Yet
>   `AI_PORTAL.md ## Pre-Push Gate`, a node the resolver *did* return, points at
>   it in prose [...] The graph returned the pointer but not the target, so I had
>   to follow prose -- exactly the linear-corpus reading the resolver exists to
>   eliminate. This is a `requires` edge that should exist and does not.
> - `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md` -- also **not in
>   the graph**, though `CLAUDE.md` calls it the authoritative doctrine for
>   commit coordination.
>
> Conversely, the two tier-2 leaves it *did* return (17,319 B, 63% of the working
> set) were the least useful nodes for this task [...] The graph over-links
> generic authority and under-links task mechanism.

## Measurement

| Metric | Value |
| --- | --- |
| Ran `recall.py` | yes, trigger `commit_or_push` |
| Orientation reading | ~34.8 KB, or ~23 KB excluding its unprompted `recall.py` source audit |
| Total | ~48 KB |
| Five questions | 5/5 ANSWERED, four from the seed alone |
| Environment probe | glibc 2.35, no cmake, no ninja, python 3.10.12 -- correctly concluded it could not build |

## What it got right about the gate, unprompted

> the sandbox guidance in `AI_PORTAL.md ## Pre-Push Gate` is accurate and
> predicted my situation exactly -- `repository_role_guard.py` is check #1 and
> **short-circuits**, so on a mounted copy the gate returns 2 immediately and
> nothing else runs. Verify by hand, hand to the maintainer.

## Disposition

D2 and D3 were both implemented on 2026-08-06 in commit `79888dfaa`. The
hardcoded denominator is gone and derives from the graph; both mechanism
documents are now nodes with edges. See lane section 10.
