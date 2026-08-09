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

## M0 finding 2 -- the outliers are CODE, and the two knees disagree by a week (2026-08-09)

The suspected `src_add` artifacts (W29 182K, W31 241K) were provenance-checked and the
"vendored/generated" hypothesis was FALSIFIED: ~99% of both spikes are code-extension lines.
W29 is real engine C++ (`fox_standard_catalog.cpp`, `cmdhelp.cpp`, `cmd_workspace.cpp`, ...);
W31 is dozens of ~600-line Python OPERATIONAL scripts (the phase22 message-catalog machinery) --
a category M2 should name separately: single-use operational code vs durable engine code.

The corrected reading: **the LINE knee is W29; the COMMIT knee is W30.** W29 delivered 183K
lines in only 4 commits (batch-drop style); W30 delivered 20x the commits at far lower
lines-per-commit (scoped slices, the gate era). Confound C2 runs INVERTED from the charter's
guess: commits UNDERCOUNT the early takeoff rather than inflating the late one. Sequence as now
measured: doctrine lands W29 AND output takes off W29 in the old delivery style; the delivery
process itself transforms W30, where Claude arrives. Caveat CLOSED 2026-08-09: the rename-aware pass (`-M`) reproduces both spikes to the line
(W29 eng 179,009 = 179,009; W31 tool 224,010 = 224,010) -- no moved-file inflation. **M0 is
complete**: every series value is regenerable, bounded, provenance-checked, rename-verified.

## M2 seed -- per-metric knees and the honesty ledger (2026-08-09)

| Metric | Knee week | Character |
|---|---|---|
| eng_code lines | **W29** | one massive batch integration (4 commits, 180K C++) |
| doc lines + new docs + closeouts | **W29 onset, W30 surge** | doctrine lands W29, applied at scale W30 |
| commits (granularity) | **W30** | delivery style transforms to scoped slices |
| tool_code lines | **W31** | operational automation (phase machinery) |
| proofs + aifclaims | **W31** | the registries/allocator era |
| steady state | **W32** | most commits, least code -- small proven slices |

Sequential specialization: engine -> doctrine -> process -> tooling -> steady state, one week
per layer. What CANNOT be concluded (M2's standing honesty ledger): F1 vs F3 cannot be ordered
from git alone (Claude's arrival and its model generation are one event in this record -- the
owner's financial audit is the only independent clock); C1 (owner fluency) is unmeasurable
in-repo and is assumed nonzero; correlation language only, throughout.

## M1/M2 -- the financial clock (owner ledger audit, 2026-08-09; DATES ONLY)

Privacy rule, standing: the source ledger is OWNER-HELD, OFF-REPO. This section records dates
and patterns only -- no amounts, no accounts. The ledger is the evidence of record; this is its
extraction.

- **Claude subscription first charge: 2026-07-14 -- the SAME DAY as the closeout convention
  (AIF-006/008 date).** Tier-upgrade charges follow on 07-21, 07-22, 07-24 (the climb to the
  Cowork-capable tier); first in-repo Claude session 07-21; commit knee W30. F1 and F2 are not
  merely bracketing the knee -- they are ONE EVENT: a single regime change on 2026-07-14, the
  process codified the day the tool was acquired.
- **Spend migration visible at the hinge:** an OpenAI usage-billing burst (daily API charges,
  late June, intensifying 07-04..07-08) STOPS ~07-13; Anthropic billing begins 07-14. The
  Codex-API era hands off to the Claude era across a single day. W29's "week" is really the
  hinge of 2026-07-13/14.
- **Subscription != adoption (measured):** Grok/xAI billed monthly since 2026-01-10; first
  in-repo artifact 2026-07-30 -- six months of paid access before use. ChatGPT Plus and GitHub
  (Copilot) billed continuously from the ledger's start (Jan 2026, predating it). Billing
  OVERCOUNTS adoption; the repo UNDERCOUNTS access; each clock corrects the other. Owner
  weighting (2026-08-09, verbatim intent): "my use of grok and copilot is trivial" -- so for
  attribution, F1's load-bearing agents are ChatGPT/Codex (the pre-hinge era) and Claude (the
  post-hinge era); Grok and Copilot are held at negligible weight regardless of billing tenure.
- **M2 verdict on F1-vs-F2 ordering: unanswerable, and that is the finding.** They were never
  separate events. F3 (model generation) remains entangled with F1 by construction (one
  subscribes to whatever generation is current). The supportable claim: the acceleration
  correlates with a deliberate, dateable regime change (2026-07-14) comprising tool + doctrine
  together, applied at scale the following week, automated the week after.

Remaining before M3: owner review of this extraction; then the findings report.

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
