---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-007
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  git:
    branch: development
    baseline_commit: b04940a78
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session, "keep going"
    scope: >
      Measured proposal to satisfy the Tier 1 seed maintenance contract so two
      pending doctrine rules can be filed. Read-only analysis of the seed, the
      recall resolver and the recall graph. No file was demoted; no rule was
      filed. Proposal only.
  report:
    path: docs/maintenance/TIER1_SEED_BUDGET_DEMOTION_PROPOSAL_V1.md
    kind: proposal
  primary_topics:
    - "AI_TIER1_SEED_V1"
    - "seed budget"
    - "demotion"
    - "recall resolver drift"
---

# Tier 1 Seed -- A Measured Demotion, and a Drift It Uncovers

**Report id:** AIPR-20260815-COWORK-007
**Date:** 2026-08-15
**Author:** member.ai.claude.cowork (scribe)
**Owner:** member.derald
**Status:** proposal -- nothing demoted, nothing filed
**Evidence class:** `source-defined` (measured at `b04940a78`)

## Why this exists

Two doctrine rules are waiting on the same wall.

1. **"A task isn't done until the housekeeping is finished."** Salvaged
   2026-08-15 from a file whose name was its own first line.
   **RESOLVED 2026-08-16 (AIF-118), by owner ruling: promoted into
   `AI_TIER1_SEED_V1.md` section 5, and the salvage file deleted (`17e70061b`).**
   It cost 145 B and the ceiling held on slack alone -- 8104 B of 8192, 88 B
   headroom -- so **nothing was demoted and this proposal's premise is
   unchanged**. One of the two rules below is off the wall; the wall is 145 B
   higher.
2. **"SQLite lives in our system and has a specific purpose, but is NEVER
   dogfood."** Owner ruling, 2026-08-15, recorded in
   `AIF112_OWNER_RULING_D1_D3_AND_DOGFOOD_DEFINITION_V1.md`. This one matters
   more than it looks: `dogfood` is used across AIF-081, AIF-086, AIF-097 and
   AIF-112 and is **defined nowhere**, and that absence is what let a
   "dogfooded SQLite ledger" survive to a signed Phase-0.

Both are invariants, so both pass the seed's content test. Both are blocked by
its budget:

```
check-seed-budget: PASS -- AI_TIER1_SEED_V1.md 7959 B of 8192 B (97%, 233 B headroom)
```

and by its own contract:

> "Invariants and pointers only; no perishable literal; the header's ceiling is
> enforced by `tools/staging/check_seed_budget.py`. **Adding requires demoting,
> and demoting means moving.**"

So the question is not "is there room" but "what moves." This document answers
that with measurements rather than opinion.

## Where the bytes are

Measured 2026-08-15 at `b04940a78`:

| Bytes | Section |
|------:|---|
| 458 | `# AI Tier 1 Seed V1` (title + preamble) |
| 554 | `## 1. Where you are` |
| 859 | `## 2. What you may do` |
| 772 | `## 3. Git, and how to not wreck someone's day` |
| 771 | `## 4. House conventions` |
| 324 | `## 5. Document as you work` |
| 347 | `## 6. The one habit that matters` |
| 790 | `## Perishable state -- follow the pointer` |
| **1810** | **`## Going deeper -- retrieve by what you are about to do`** |
| 612 | `## The five questions (stopping rule)` |
| 228 | `## Maintenance contract` |
| **7959** | **total** |

One section is more than twice any other, and it is the one the seed itself
marks as optional.

## The candidate, in the seed's own words

`## Going deeper` opens:

> "Prefer the resolver: `python labtalk/ai_portal/recall.py <trigger>` returns
> the smallest working set, measured. **Table below is the fallback.**"

Of that section's 1810 bytes, **1604 are the fallback table** (12 data rows).
The remaining ~206 B is the prose naming the resolver.

The resolver is real. Run at `b04940a78` it lists 11 triggers interactively and
the graph (`labtalk/registries/portal_recall_graph.yaml`) declares 13. So the
seed carries a 1604-byte fallback for a tool that exists, works, and is declared
preferred.

## The drift this uncovered

The table and the resolver have **diverged in both directions**. Measured:

**Resolver triggers (13):** `change_source`, `close_out`, `commit_or_push`,
`onboard`, `open_lane`, `persistent_memory`, `plan_gates`, `publish`,
`release_or_license`, `understand_why`, `use_devtools`, `where_is`,
`write_dotscript`.

**Table rows the resolver does NOT cover (4 of 12):**

- read or write DBF, memos, or indexes
- use a reference authority or catalog
- edit the website
- capture proof output

**Resolver triggers with no table row (5):** `onboard`, `persistent_memory`,
`release_or_license`, `use_devtools`, `where_is`.

An agent that reads the table and an agent that runs the resolver **get
different guidance**. Four of the table's rows are the only place that guidance
exists in Tier 1; five of the resolver's triggers are invisible to anyone who
trusts the table.

This is precisely the failure `CLAUDE.md` names, citing AIF-082 6.8:

> "two shims that restate will diverge, and have"

The fallback table is a restatement of the recall graph. It has diverged. That
is a defect independent of the budget question, and it argues for the same
remedy: stop restating, point instead.

## The proposal

**One decision, three steps.**

1. **Close the resolver's gaps first.** Add four triggers to
   `portal_recall_graph.yaml` so nothing is lost in the move:
   `dbf_memo_index`, `reference_authority`, `edit_website`, `capture_proof`.
   Their content already exists in the table rows; this is transcription, not
   authorship.
2. **Demote the table.** Move all 12 rows to a Tier-2 document (candidate:
   `labtalk/ai_portal/TIER1_TRIGGER_TABLE_V1.md`). This satisfies "demoting means
   moving" literally -- nothing is deleted.
3. **Keep the pointer.** The ~206 B of prose naming the resolver stays, plus one
   line pointing at the demoted table for anyone who wants the flat view.

**Budget after:**

| | Bytes |
|---|---:|
| Current | 7959 |
| Less the table | -1604 |
| Plus a pointer line (est.) | +80 |
| **Projected** | **~6435** |
| **Headroom** | **~1757 B** |

Both pending rules together need roughly 300-400 B written tersely. The
projected headroom carries them with room for several more, which matters
because a seed at 97 percent has no capacity for the next invariant either --
this is a recurring blocker, not a one-off.

## What this proposal does NOT claim

- **It does not verify the resolver's output quality.** I confirmed it runs and
  lists triggers. I did not check that each trigger returns a correct or
  complete working set. If the resolver is thin, demoting its fallback makes
  Tier 1 worse, not better. **Verify before demoting.**
- **It does not decide the four gap triggers' content.** The table rows are
  terse; expanding them into graph entries is a judgement call about what
  belongs in a working set.
- **It does not touch the seed.** Nothing was edited. The measurement is
  reproducible: `python tools/staging/check_seed_budget.py`.
- **It assumes the two pending rules belong in Tier 1 at all.** That is worth
  a second look for the housekeeping rule, which may already be covered
  operationally by the trigger row "close out work | update what you made stale;
  leave a handoff, not only a closeout." The dogfood definition has no such
  cover -- nothing anywhere defines the term.

## If the answer is no

If the table should stay, the alternative is a non-gated doctrine home for both
rules -- a `HOUSE_RULES_V1.md` under `labtalk/ai_portal/`, pointed to from the
seed's section 4 at a cost of about 60 B. That defers the budget problem rather
than solving it, and the next invariant hits the same wall.

## Recommendation

Do step 1 (close the resolver gaps) regardless of the budget decision. The
divergence is a live defect: four pieces of Tier 1 guidance exist only in a
table the seed itself calls a fallback, and five resolver triggers are invisible
to anyone reading it. Fixing that is worth doing whether or not the table moves.

---

Owner: `member.derald`. Author: `member.ai.claude.cowork`.
Evidence class: `source-defined` -- byte counts, resolver output and graph
triggers all measured at `b04940a78` on 2026-08-15.
Risk class: low (proposal; no mutation).
