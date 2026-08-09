# Development Acceleration Analysis -- measuring the six-week exponential

**Status:** charter (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-09. **AIF-101** (claimed 2026-08-09, run `COWORK-20260809-001`).
Parent: `project.ai_friendly` (process analysis) with a Frontal_Mem seam.

## Owner statement of record (2026-08-09, verbatim intent)

> "I have noticed an exponential progress over the last 6 weeks. Factors I considered:
> 1. Using more combinations of AI together.
> 2. Maturation of the documentation process.
> 3. AI upgrades themselves."

Recorded at the owner's direction, with his own integrity check attached: the observation must
not rest on an AI's flattery ("unless you are feeding me crap"). Ruling adopted by this lane:
**praise is an unproven assertion; the golden rule applies to compliments too.** The lane exists
to replace the feeling with a measurement.

## First reading (2026-08-09, development branch, commits per ISO week)

```
W26:   3      W27:   5      W28:   9      W29:   4     <- single digits, four weeks
W30:  82      W31: 178      W32: 217*                  <- ~20x step, still climbing
                                          (*W32 partial -- measured mid-week)
```

Not a slope -- a **phase transition** at W30 (week of 2026-07-20). The owner's six-week window
and the measured knee agree. One metric is not an analysis; it is the reason to run one.

## The question, stated honestly

Which of the owner's three factors -- and which confounds -- explain the knee and the sustained
climb? Attribution will be correlational, not causal; the lane says so up front and compensates
with a dated factor timeline and multiple independent metrics rather than one.

Candidate factors (owner's three + confounds that must be priced):

- **F1 Multi-AI combination.** Coworker lanes (Codex site refactor, Grok Lane 1, ChatGPT
  planning, Ollama harness design, cross-provider peer review). Datable via lane docs,
  ai_runs.yaml, assignment records.
- **F2 Documentation-process maturation.** The closeout convention (2026-07-14, AIF-006/008),
  AIF lane discipline, the portal/recall graph, the gate estate, promote-final-tests. Datable
  via the docs themselves -- and note the candidate mechanism: **the Frontal_Mem thesis
  predicts exactly this shape** (a reachable, consolidated corpus compounds; retrieval replaces
  re-derivation, so per-task overhead falls toward zero). W30 sitting on the doctrine cluster
  is the thesis's own predicted signature.
- **F3 AI upgrades.** Model generation changes in the same window. Datable externally; effect
  entangled with F1/F2.
- **C1 Owner fluency (confound).** The maintainer's own process mastery grew over the same
  weeks; sessions steer faster. Hard to separate from F2 -- name it, do not bury it.
- **C2 Measurement artifact (confound).** Scoped per-path slices (the pre-push gate era) mean
  MORE commits per unit work than the old style; commit count partially measures the process
  change itself. This is why M0 uses multiple denominators, not commits alone.

## Milestones

| M | Delivers | Gate |
|---|---|---|
| M0 | **Metric extraction (measure first, bounded).** Weekly series from the repo's own records: commits; AIF lanes claimed AND closed; closeouts written; proofs/lessons registered; regressions added; gates added; docs/maintenance files created; lines added (source vs docs split). Each metric bounded/cross-checked (C2 rule). Extraction script committed so the series regenerates. | series reproduce from one command; no hand-counted numbers |
| M1 | **Factor timeline.** Dated event list per F1/F2/F3/C1: first coworker lane, closeout convention, recall graph, gate wirings, model changes. Every date cites a commit or doc. | timeline rows all cite evidence |
| M2 | **Attribution analysis.** Knee location vs factor dates; per-metric knees compared (do docs metrics lead source metrics?); honest confound accounting; explicitly correlational language. | findings state what CANNOT be concluded as clearly as what can |
| M3 | **Report + publication candidate.** A findings doc; optionally a site page/whitepaper (the Frontal_Mem thesis validation angle: "documented from month eleven onward" meets "the eleventh month is when it went vertical"). Publication rides the matrix + flush pipeline, not a hand-page. | owner review; matrix row if published |

## M1 seed -- agent-adoption timeline (first evidence in the record, extracted 2026-08-09)

First-mention / first-file-add dates from `git log` (adoption PROXIES -- lower bounds; the
owner's financial audit of subscription starts, reaching back to 2025-08, is the precision
source and M1's next input):

| Agent / era | First evidence | What it was |
|---|---|---|
| ChatGPT (pre-repo era) | predates the record | Owner (verbatim): "prior to that most dev was simple short sessions of chatgpt desperately trying to scrap together a dozen or so files to stay within the initial restrictive storage/memory limits in early AI." The context-window scarcity that era imposed is the ORIGIN CONDITION of the Frontal_Mem thesis -- the memory system exists because the limits did. First in-repo doctrine mention 2026-07-25 (AIF-060 agency model, `e3bae587b`). |
| Codex / Copilot footprint | **2025-08-29** (first path-adds; branch `rename-cli-to-dli-20250829`) | Matches the owner's billing recollection "back to 08/25" independently -- two sources, days apart. |
| Codex (named in commits) | 2026-07-21 (`e68ccf1af`) | DEF family / security doctrine era. |
| **Claude (Cowork)** | **2026-07-21/22** (session dir `2026-07-21_claude_recno64_indextxn_onboarding`; first commit mention `be021e8b7` 2026-07-22) | **Arrives IN the knee week (W30, week of 2026-07-20).** |
| Ollama | 2026-07-25 (`596f6b7d1`) | AI-BBS agent-server bundle (AIF-052..059). |
| Grok | 2026-07-30 intake (`2e1b1c548`); first lane files 2026-08-08 | Virtual-workspaces intake, then the Lane 1 coworker assignment. |
| Copilot (named in commits) | 2026-08-03 (`09bcaeb21`) | Remote-agent branch-baseline hardening. |
| Disk access for Claude/Codex (owner factor 4) | owner-dated "a few weeks ago" -- to be pinned in M1 | Capability-class change: read access to the working tree; the enabler that made F1/F2 executable at depth. |

**The bracket, stated plainly:** the closeout convention lands W29 (2026-07-14); Claude arrives
W30 (2026-07-21); the commit knee IS W30. F2 leads by one week; F1/F3 (a new agent, on a then-new
model generation) lands exactly at the knee. The two candidate causes BRACKET the transition --
which is precisely why M2 must stay correlational and why the financial audit's exact
subscription dates matter: they are the only independent clock that can order F1 against F3.

## Rules inherited

Prove-the-bottleneck / measure-first (M0 before any narrative); bounded metrics only (an
unbounded number cannot fail); no perishable literals in this charter (the data lives in M0's
regenerable series, not here -- the first-reading table above is dated evidence, not maintained
state); asides follow the aside rule.

## Registration (on pickup, host-side)

`claim-aif` fresh number; intake row citing it; stamp here.
