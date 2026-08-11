---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260811-001
  recorded_at_utc: 2026-08-11T01:05:00Z
  agent:
    provider: Anthropic
    product: Claude Cowork
    model: Claude Opus 5
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: member.derald
    owner: member.derald
    committer: member.derald
  authorization:
    requested_by: maintainer
    scope: >
      AIF-101 M5: regenerate the weekly acceleration series and report the W33
      single-coworker natural experiment against its 2026-08-10 pre-registration,
      including the pre-measured Codex residue offset. Scheduled, non-interactive
      run. No mutating git performed.
  report:
    path: docs/maintenance/AIF101_M5_W33_SINGLE_COWORKER_REPORT_V1.md
    kind: measurement_report
  session:
    id: COWORK-20260811-AIF101-M5-001
    chat_reference: not_exposed
    run_id: AIPR-20260811-001
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: AIPR-20260810-008
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: cbf83522d
    head_commit: cbf83522d
---

# AIF-101 M5 -- W33 single-coworker window: report against pre-registration (V1)

**Status: PREMATURE. The window is 1 day of 7 old. All three predictions are INCONCLUSIVE
on the pre-registered test.** This is not a hedge; it is the arithmetic. The pre-registration
(`DEVELOPMENT_ACCELERATION_ANALYSIS_LANE_V1.md`, "M5 PRE-REGISTRATION", Reporting clause)
says to regenerate and compare **at or after 2026-08-17**. This run executed
2026-08-11T00:54Z. ISO week 33 spans 2026-08-10 .. 2026-08-16; the series contains exactly
one author-day of it (2026-08-10), and the extractor itself flags the row `<- partial
(current week)`.

Reporting a verdict off 1/7 of the window would be exactly the class of error the lane's
pre-registration discipline exists to prevent. The numbers below are recorded as a dated
first reading so the eventual 08-17 run has something to be checked against -- not as a result.

**Re-run this report at or after 2026-08-17.**

## 1. What was predicted

Read verbatim from the lane doc, section "M5 PRE-REGISTRATION -- the W33 single-coworker
natural experiment", written 2026-08-10 before any of the window's data existed:

1. **"Commits fall, but well short of half."** A fall near 50% would indicate the two
   coworkers were close to independent; a fall near 15% would indicate heavily overlapping
   work. A fall of 0% would falsify F1 having any measurable throughput component at all.
2. **"The doc/closeout ratio per commit holds roughly flat."** Doctrine is a per-commit
   property, not a capacity property. If that ratio moves with headcount, the process is less
   institutionalized than the lane has been claiming, which would be the more interesting
   finding.
3. **"W34 will show a spike that is NOT a rebound."** Reading it as recovery would be the
   single easiest error available here.

## 2. What happened -- the series as regenerated

Command (sandbox, read-only; the extractor shells `git --no-optional-locks log`):

```
cd /sessions/<session>/mnt/ccode      # = D:\code\ccode
python3 tools/analysis/acceleration_metrics.py
```

| week    | commits | eng_code | tool_code | data_add | doc_add | newdoc | closeout | proofs | aifclaim | regress | note |
|---------|--------:|---------:|----------:|---------:|--------:|-------:|---------:|-------:|---------:|--------:|------|
| 2026-W30 |      82 |    27615 |      4953 |     2249 |   40215 |     96 |       68 |      0 |        2 |      16 | |
| 2026-W31 |     178 |     7277 |    226256 |     8321 |   31563 |     52 |       12 |     66 |       17 |      19 | |
| 2026-W32 |     229 |     3605 |      6702 |     1612 |   59106 |    149 |       19 |      8 |       17 |       1 | |
| 2026-W33 |      18 |       21 |      1482 |       13 |    1547 |      4 |        2 |      0 |        1 |       1 | **partial: 1 of 7 days** |
| 2026-W34 |       - |        - |         - |        - |       - |      - |        - |      - |        - |       - | does not exist yet |

Author dates, not committer dates (extractor default; the pre-registration's defense (a)).
W33's 18 commits all carry author date 2026-08-10; there are zero on 08-11 or later.

```
git --no-optional-locks log --since=2026-08-08 --date=format:'%Y-%m-%d' --pretty=format:'%ad' | sort | uniq -c
  13 2026-08-08
  22 2026-08-09
  18 2026-08-10
```

## 3. Per-prediction verdict

### P1 -- commits fall, but well short of half: **INCONCLUSIVE**

Deciding number: **the window is 14% elapsed (1 author-day of 7).** No percentage change
computed now can be compared to the pre-registered 15%/50% decision boundaries, because those
boundaries were written against a full week.

Recorded for the 08-17 re-run, both clearly labelled as NOT the pre-registered test:

- Raw, uncorrected for elapsed time: 18 vs a W30-W32 mean of 163.00 commits = **-88.96%**.
  This figure is meaningless as stated; it is dominated by the six days that have not happened.
- Day-normalized: baseline 163.00/7 = 23.29 commits/day; W33 day 1 ran 18 commits/day =
  **-22.70%**. This lands inside the pre-registered "well short of half" band, which is
  suggestive of overlapping rather than independent coworker output -- but a single Monday
  against a seven-day mean that includes two weekend days is not a like-for-like comparison,
  and day-of-week composition is one of the confounds the pre-registration named. One day is
  not evidence about a week.

Do not quote either number as the P1 result.

### P2 -- doc/closeout ratio per commit holds roughly flat: **INCONCLUSIVE**

Ratios as they stand (pooled baseline = sum over W30-W32, not mean of ratios):

| ratio             | W30   | W31   | W32   | W30-W32 pooled | W33 (partial) |
|-------------------|------:|------:|------:|---------------:|--------------:|
| newdoc / commit   | 1.171 | 0.292 | 0.651 |          0.607 |         0.222 |
| closeout / commit | 0.829 | 0.067 | 0.083 |          0.202 |         0.111 |

The point-estimate movement (0.607 -> 0.222, 0.202 -> 0.111) would read as a fall, and per the
pre-registration a fall is the *more interesting* finding -- it would mean documentation
discipline is carried by coworker count rather than by institutionalized process. **That claim
cannot be made from this table**, and the reason is worth recording independently of the timing
problem:

**P2's test has close to no resolving power as specified.** The baseline weeks disagree with
each other by more than the effect being looked for: newdoc/commit spans 0.292 to 1.171
(**4.0x**) and closeout/commit spans 0.067 to 0.829 (**12.3x**) across three consecutive
two-coworker weeks with no headcount change at all. W33's partial 0.222 and 0.111 both sit
inside those baseline ranges. "Roughly flat" was never operationalized as a threshold, and any
threshold wide enough to accommodate a 12.3x baseline spread cannot be moved by a
single-week headcount change. This is a defect in the prediction, not in the data, and it
should be fixed before 08-17: either define the flatness band up front, or pool more baseline
weeks, or accept that P2 is unfalsifiable as written and say so.

### P3 -- W34's spike is parked residue, not recovery: **INCONCLUSIVE (trivially)**

Deciding number: **W34 has zero commits, because W34 begins 2026-08-17.** There is no spike to
characterize. The prediction cannot be evaluated for another week and a half.

## 4. The residue correction

Applied as a standing correction to every number above, per the pre-registration's defence (b):

- Codex's W33 work exists but is **uncommitted**: **62 modified tracked files + 1 deletion**,
  measured 2026-08-10 and triaged into five groups in
  `docs/maintenance/SESSION_CLOSEOUT_SITE_PUBLISH_AND_CODEX_RESIDUE_TRIAGE_2026-08-10.md`.
- Therefore **W33 undercounts** work produced in the window, and **W34 will overcount** when
  the residue lands in a lump.
- Author-date attribution (defence (a)) does **not** fix this. Author date is stamped when the
  change is committed, so parked residue committed after 2026-08-16 will carry a W34 author
  date regardless. The residue offset must be subtracted by hand at the 08-17 reading; the
  extractor cannot do it.
- **Consequence for P3, stated in advance so it is not rationalized later:** if the 08-17/08-24
  series shows a V-shape, the null explanation is that a pre-measured 62-file lump landed in
  W34. That explanation must be excluded before the word "recovery" is used, and excluding it
  means checking the W34 diff against the five triage groups by name, not by size.

## 5. Confounds not ruled out

Correlational only. n=1 week, no control group, no randomization. Nothing here identifies a
causal effect of coworker count on anything.

- **Substitution.** The owner's attention is a shared resource. Any W33 output level is
  consistent with the remaining coworker absorbing redirected owner attention, which is
  substitution, not a capacity measurement.
- **Weekend / day-of-week composition.** Baseline weeks are seven-day means including weekends;
  the W33 partial is one weekday. The day-normalized -22.70% above is contaminated by this and
  by nothing else that can currently be separated from it.
- **The residue offset**, per section 4 -- unresolved by construction until the residue lands.
- **No per-coworker attribution exists in the record.** Every commit since 2026-07-27 (396 of
  them) is authored `Derald Grimwood <derald@grimwood.ws>`
  (`git --no-optional-locks log --since=2026-07-27 --pretty=format:'%an <%ae>' | sort | uniq -c`).
  Commits are a joint owner-plus-coworkers output measure; the series cannot decompose a fall
  into "which coworker stopped". This is a structural limit on F1 identification that the
  pre-registration did not list, and it applies to the 08-17 reading too.
- **Doctrine-unchanged is asserted, not measured.** The pre-registration pins doctrine, model,
  disk access and owner across the window by claim. Only the exogeneity of the billing cycle is
  independently verifiable.

## 6. What this does and does not license

**Licensed now:**

- Stating that the W33 window is open and its first author-day is on record, with the figures
  in section 2 as a dated first reading.
- Stating that P2 as written is under-specified relative to its own baseline variance, and
  fixing that before the real reading. This finding does not depend on the window being
  complete.
- Stating that per-coworker decomposition is not available from git at all.

**Not licensed:**

- Any verdict of MET or MISSED on P1, P2 or P3.
- Any statement of the form "removing a coworker reduced/did not reduce throughput by X%".
- Any use of -88.96% or -22.70% as the W33 result.
- Any causal language whatsoever, at 08-17 or later. The pre-registration's own words: the
  result is "suggestive, never identifying".

**Next action:** re-run this report at or after 2026-08-17, against a complete W33 and a W34
that can be checked for residue. Before that run, decide P2's flatness band in advance.

## Appendix -- ready-to-paste BBS POST body

The AI-BBS daemon binds 127.0.0.1:8765 on the Windows host and is not reachable from this
sandbox; the clean attributed-post path (AIF-098 Lane 1 write adapter, KIND=5
`consolidated_from_chat`) is ON HOLD and not yet built. No BBS write was attempted. If Derald
wants this on the board now, post by hand. When AIF-098 lands, this hand-step is replaced by
`tools/memory/promote.py`.

```
SUBJECT: AIF-101 M5 -- W33 window read PREMATURE, all three predictions INCONCLUSIVE

The scheduled M5 report fired 2026-08-11, six days before the pre-registration's own
reporting date (at or after 2026-08-17). ISO W33 runs 2026-08-10..08-16 and the series
holds exactly one author-day of it, so P1/P2/P3 are all INCONCLUSIVE on the
pre-registered test. No verdict is claimed.

First reading, dated, NOT a result: W33 partial = 18 commits, 4 newdoc, 2 closeout vs a
W30-W32 mean of 163 commits. Day-normalized that is -22.7%, inside the "well short of
half" band, but one Monday against a seven-day mean including weekends is not a
like-for-like comparison.

One finding that does NOT depend on the window being complete: P2 is under-specified.
Across three unchanged two-coworker weeks the baseline newdoc/commit ratio spans 4.0x
(0.292..1.171) and closeout/commit spans 12.3x (0.067..0.829). "Roughly flat" was never
given a threshold, and no threshold wide enough for that spread can be moved by a
one-week headcount change. Fix the band before 08-17 or concede P2 is unfalsifiable.

Residue correction stands: 62 modified tracked files + 1 deletion parked 2026-08-10.
W33 undercounts, W34 will overcount. Author-date attribution does NOT fix this -- parked
work committed after 08-16 carries a W34 author date. If W34 shows a V, exclude the
residue lump by matching the five triage groups by name before saying "recovery".

Correlational only, n=1 week, no control, no randomization. Confounds open: substitution
of owner attention, day-of-week composition, the residue offset, and the fact that all
396 commits since 07-27 carry one author, so the series cannot decompose a fall by
coworker.

Report: docs/maintenance/AIF101_M5_W33_SINGLE_COWORKER_REPORT_V1.md
Regenerate: python3 tools/analysis/acceleration_metrics.py
```

## Regeneration

Every number in this report comes from one of:

```
python3 tools/analysis/acceleration_metrics.py
git --no-optional-locks log --since=2026-08-08 --date=format:'%Y-%m-%d' --pretty=format:'%ad' | sort | uniq -c
git --no-optional-locks log --since=2026-07-27 --pretty=format:'%an <%ae>' | sort | uniq -c
```

Ratios and percentages are arithmetic on the extractor table and are shown with their inputs
in sections 3 and 4. No mutating git command was run by this session.
