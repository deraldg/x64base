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

**M3 DRAFTED (2026-08-09):** `DEVELOPMENT_ACCELERATION_FINDINGS_V1.md` -- five findings (F-A
phase transition; F-B the 2026-07-14 regime change; F-C Frontal_Mem mechanism match; F-D the
disk-access capability event; F-E the scarcity-era origin), the not-claimed section, and the
publication note. White paper drafted (`WHITE_PAPER_JULY14_REGIME_CHANGE_V1.md`). Awaiting
owner review; publication decision rides the matrix/flush pipeline.

## STANDING RULE -- this lane is ONGOING (owner directive, 2026-08-09)

Owner (verbatim intent): "continue observations in this lane, it is ongoing, it will help us
model predictive milestones, factoring accelerated learning and technology."

Consequences, binding on the lane:

1. **The lane does not close at M3.** It is a standing observatory, not a one-shot analysis.
   The weekly series is re-run and APPENDED at natural checkpoints (session closeouts, week
   boundaries, factor events); the extractor stays maintained; new factor events (model
   generations, capability grants, coworker adoptions, process changes) are logged on the M1
   timeline WHEN THEY HAPPEN, dated, with evidence -- not reconstructed later.
2. **The mandate extends from descriptive to PREDICTIVE.** The measured series + factor
   timeline become inputs to milestone forecasting: given the observed compounding shape,
   when should the next lifecycle phases (beta gates, publication passes, coworker
   integrations) land? Two forward-looking variables are promoted from the confound ledger to
   MODELED factors: **accelerated learning** (owner + system fluency, previously C1 -- now
   tracked via its own observables: time-to-close per lane, reworks per lane, gate-failure
   rate over time) and **technology** (model/tooling generation changes, previously F3 -- now
   logged prospectively as dated events so their deltas are measurable instead of entangled).
3. **Honesty rules carry forward unchanged:** predictions are stated with bounds and revisited
   against actuals (a prediction row is a falsifiable gate, not a hope); the golden rule
   applies to forecasts exactly as to claims of work done.

| M | Delivers | Gate |
|---|---|---|
| M4 (standing) | Ongoing observation: appended weekly series + prospectively dated factor events | series never more than one closeout stale; every factor event cites evidence |

### M4 factor-event log (prospective, dated, append-only)

- **2026-08-09..10 -- Codex 24-hour continuous run** (F1 intensity event): produced AIF-103..106
  (LMS intake, clean-core CI repair, Cascade ERP gold-standard lane, AI-history evidence
  publication) + two site commits. Evidence: ccode `b06e91412..ff5f50058`; site `8ee1b4ba9`,
  `f12001464`.
- **2026-08-10 -- Codex credit exhaustion until 2026-08-16** (capacity-constraint event, the
  inverse of an upgrade): one coworker offline ~6 days; load shifts to Claude/owner. First
  natural experiment for M5 -- does throughput dip, hold, or reshape while one agent is out?
- **2025-08-02 -- earliest DOCUMENTED AI-assisted DotTalk work** (AIF-106 evidence record;
  probable start 2025-07-21, labeled inference). Third independent clock for the adoption
  timeline: owner billing recollection ("back to 08/25"), repo footprint (2025-08-29), and now
  archive/mailbox evidence (2025-08-02) mutually agree within one month.
| M5 | Predictive-milestone model v1: forecast next-phase landings from the measured compounding shape, with stated bounds | each prediction logged BEFORE the fact; scored against actuals when due |

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

## M5 PRE-REGISTRATION -- the W33 single-coworker natural experiment

**Written 2026-08-10, the first day of the window, BEFORE any of its data exists.** That is the
whole point: a prediction recorded after the fact is a story. Anything below that turns out
wrong stays on the page, struck through, not edited.

**The event.** Codex's paid capacity was exhausted 2026-08-09/10 and does not return until
2026-08-16. The cause is a billing cycle -- **exogenous** to the state of the work. This is what
makes the window worth measuring: when a coworker goes quiet because the problem got hard, the
absence and the slowdown share a cause and nothing is learned. Here they do not.

**What it can identify: F1 alone.** Every other factor is pinned across the window -- doctrine
unchanged (no new convention landed), Claude's model unchanged, disk access unchanged, owner
unchanged. The only moving variable is the count of active AI coworkers, 2 -> 1. F1 (multi-AI
combination) is exactly the factor the July 14 transition could never isolate, because tool and
doctrine arrived on one day (F-B). This window separates it by accident.

**Window.** ISO week 33 = 2026-08-10 .. 2026-08-16, which aligns to within a day of the outage.
No re-slicing of the M0 series is required; compare W33 against W30-W32 on the same eight
denominators, regenerated by `tools/analysis/acceleration_metrics.py`.

**Predictions (falsifiable, recorded in advance):**

1. **Commits fall, but well short of half.** Substitution masks part of the capacity loss -- the
   remaining coworker absorbs load. A fall near 50% would indicate the two coworkers were close
   to independent; a fall near 15% would indicate heavily overlapping work. Either reading is a
   result; a fall of 0% would falsify F1 having any measurable throughput component at all.
2. **The doc/closeout ratio per commit holds roughly flat.** Doctrine is a per-commit property,
   not a capacity property. If that ratio moves with headcount, the process is less
   institutionalized than the lane has been claiming, which would be the more interesting finding.
3. **W34 will show a spike that is NOT a rebound.** See the offset below. Reading it as recovery
   would be the single easiest error available here.

**The measurement trap, and its correction (recorded NOW so it is not estimated later).**
Codex's work exists but is uncommitted, deliberately parked for its return. **Measured
2026-08-10: 62 modified tracked files + 1 deletion**, triaged into five groups in
`SESSION_CLOSEOUT_SITE_PUBLISH_AND_CODEX_RESIDUE_TRIAGE_2026-08-10.md`. So W33 UNDERCOUNTS work
produced and W34 OVERCOUNTS when the residue lands in a lump. Unhandled, that manufactures a
clean V-shape meaning nothing. Two defenses, both required: (a) attribute by AUTHOR date, not
commit date -- the extractor already does this; (b) treat the figures above as a known,
pre-measured offset rather than a later guess.

**What this cannot do.** n=1 week, no control group, no randomization. The owner's attention is
a shared resource and may simply redirect to the remaining coworker, which is substitution, not
capacity. Weekend composition differs across weeks. The result is suggestive, never identifying,
and must be reported as such -- the lane's correlational-only rule applies here with force,
because a natural experiment invites causal language more than a plain time series does.

**Reporting.** At or after 2026-08-17, regenerate the series, compare W33, and record the
outcome against each numbered prediction above -- including the ones that miss.

## Rules inherited

Prove-the-bottleneck / measure-first (M0 before any narrative); bounded metrics only (an
unbounded number cannot fail); no perishable literals in this charter (the data lives in M0's
regenerable series, not here -- the first-reading table above is dated evidence, not maintained
state); asides follow the aside rule.

## Registration (on pickup, host-side)

`claim-aif` fresh number; intake row citing it; stamp here.
