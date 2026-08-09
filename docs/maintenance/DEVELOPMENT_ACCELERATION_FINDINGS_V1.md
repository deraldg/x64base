# Findings: The July 14 Regime Change -- dating a development phase transition from the project's own records (AIF-101 M3)

**Status:** draft findings (review-needed; publication candidate). Owner: member.derald.
Steward: member.ai.claude.cowork. Date 2026-08-09. Lane: AIF-101
(`DEVELOPMENT_ACCELERATION_ANALYSIS_LANE_V1.md` -- method, series, timeline, confounds).
Evidence basis: the repository's own git history (regenerable via
`tools/analysis/acceleration_metrics.py`) and the owner's private financial ledger (off-repo;
dates extracted, amounts withheld). Language is correlational throughout, per the lane charter.

## 1. The question

The owner observed "exponential progress over the last 6 weeks" and named three candidate
factors: multi-AI combination, documentation-process maturation, and AI model upgrades -- with
an integrity condition attached: the observation must survive measurement, not flattery.

## 2. What the repository's own records show

Weekly series (ISO weeks, development branch; regenerable, bounded, rename-verified):

- **W26-W28** (late June): single-digit commits, ~1-5K lines/week. The quiet era.
- **W29** (Jul 13-19): 4 commits carrying ~180K lines of engine C++ -- one massive batch
  integration, old delivery style. Closeouts and lane docs appear for the first time.
- **W30** (Jul 20-26): commits jump ~20x (82); ~40K documentation lines; 96 new maintenance
  docs; 68 closeouts. The delivery process itself transforms to scoped, gated slices.
- **W31**: 178 commits; ~226K lines of operational tooling (catalog/automation machinery);
  the proof and claim registries ignite (66 proofs, 17 claims).
- **W32** (partial): the steady state -- the most commits yet (220+) at the lowest code volume:
  many small, proven, gated slices.

Two knees, one week apart: line volume takes off in W29; commit count in W30. The disagreement
is informative -- W29 produced at scale in the old style; W30 changed how production ships.
Sequential specialization follows: engine -> doctrine -> process -> tooling -> steady state,
approximately one week per layer.

## 3. The independent clock

The owner's financial ledger (dates only) resolves what git alone cannot:

- The first Claude subscription charge is **2026-07-14 -- the same day the closeout convention
  (AIF-006/008) was established.** Tier upgrades follow within ten days; the first in-repo
  Claude session is 07-21; the commit knee is the same week.
- An OpenAI usage-billing burst (the Codex-API working style) intensifies through early July
  and **stops ~07-13**; Anthropic billing **begins 07-14**. The spend, the doctrine, and the
  tool all pivot across a single day.
- Subscription is not adoption: Grok/xAI was billed monthly from January with first in-repo use
  in late July; ChatGPT Plus and Copilot billed continuously all year. Billing overcounts
  adoption; the repo undercounts access; each clock corrects the other. (Owner weighting:
  Grok and Copilot usage "trivial" -- held at negligible attribution weight.)

## 4. Findings

**F-A. The acceleration is real and is a phase transition, not a slope.** Every independent
metric -- commits, lines by category, new docs, closeouts, proofs, claims, regressions -- steps
by an order of magnitude or appears for the first time within a two-week window.

**F-B. The transition dates to a single deliberate act: 2026-07-14.** On one day the owner
acquired the new tool AND codified the documentation doctrine. The owner's factors F1
(multi-AI) and F2 (process maturation) are not competing explanations; on the evidence they
were one decision. F3 (model generation) is entangled with F1 by construction and cannot be
separated by any clock available.

**F-C. The mechanism visible in the data matches the Frontal_Mem thesis.** Doctrine (the
consolidation layer) precedes and accompanies the throughput jump; retrieval-infrastructure
weeks (portal, registries, gates) precede the highest-cadence weeks. A reachable, consolidated
corpus compounds: per-task overhead falls, so the same effort ships more, smaller, safer
slices. W32's signature -- maximum commits, minimum volume -- is what compounding looks like.

**F-D. A fourth factor the owner named late is a capability-class event:** granting AI
coworkers read access to the working tree ("prior a few weeks ago you and codex could not read
my harddrive"). It is dated only approximately; it belongs on the M1 timeline as the enabler
that made deep F1/F2 execution possible.

**F-E. The pre-history is the thesis origin.** The owner's description of the earlier era --
"short sessions of chatgpt desperately trying to scrap together a dozen or so files to stay
within the initial restrictive storage/memory limits" -- is the scarcity condition that
motivated building a human-side memory system at all. The system that measured this transition
exists because of the limits the transition escaped.

## 5. What is NOT claimed

No causal identification: C1 (owner fluency growth) is real, unmeasurable in-repo, and assumed
nonzero. F1/F2 cannot be ordered (same event); F3 cannot be isolated. Commit counts partially
measure the process change itself (priced: that is why eight denominators were used). The
result is a dated, multi-metric, two-clock CORRELATION with a mechanism consistent with prior
written theory -- strong for a self-study, and stated as exactly that.

## 6. Publication note

DRAFTED: `labtalk/ai_portal/whitepapers/WHITE_PAPER_JULY14_REGIME_CHANGE_V1.md` (2026-08-09,
review-needed). If approved, publication rides the matrix + flush pipeline (no hand-page);
a recall node (`doc.whitepaper_regime_change`) is wired at acceptance, per the coordination
paper's precedent. The financial ledger remains off-repo, dates-only, in the paper as in the
lane. Owner decision pending.
