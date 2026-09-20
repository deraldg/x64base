---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260809-001
  recorded_at_utc: 2026-08-09T16:17:29Z
  agent:
    provider: Anthropic
    product: Cowork / Claude
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: ce81379098a6fdd23117e1671ff15585711e188d
  authorization:
    requested_by: maintainer
    scope: >
      Run an adversarial falsification probe against the pre-commit gate set and
      report findings as E1 input. Pre-commit set only; whole/partial gate
      deferred. Report-only against D:/code/ccode: no source mutation, no
      staging, no commit, no push, no hook installation.
  report:
    path: docs/maintenance/BETA1_E1_GATE_FALSIFICATION_FINDINGS_2026-08-09.md
    kind: gate_falsification_findings
---

# BETA-1 E1 -- Gate Falsification Findings (AIF-041)

    status      : runtime-observed. Every verdict below was produced by running
                  the named script and reading its exit code, not by reading it.
    lane        : AIF-041 M6 (peer review) -> BETA-1 exit gate E1
    baseline    : development @ ce81379098a6fdd23117e1671ff15585711e188d
    scope       : the pre-commit gate set only, by maintainer direction
    discharges  : E1 PARTIAL. See section 9 for what remains.

---

## 1. What this is, and why it is not a review

BETA-1 exit gate E1 asks for a peer-review pass, human and/or cross-AI, with
findings triaged into the gate. AIF-041 M6 is the milestone that fills it.

This pass was deliberately **not** conducted as a review. AIF-082 records four
instruments built in one session, all four wrong on first build, and states the
finding plainly: all four were caught by running them, none by inspection. A
reading pass over the same code would have reproduced the modality that already
failed.

So the method here is adversarial execution. For each gate: construct an input
the gate must reject, run it, and record whether it rejected. AIF-082's rule is
the acceptance criterion.

> A checker is unproven until you have seen it FAIL. A passing run and a run
> that parsed nothing are indistinguishable from outside.

A gate never observed failing is reported below as **untrusted**, not as
passing.

## 2. Independence

Authored by Cowork / Claude, which did not write any gate in the set. On this
surface the author is a cold outside runner, which is the condition AIF-082 asks
for when it says the author of an instrument is its worst tester.

The same agent is **not** independent of, and did not probe, the withdrawn
AIF-044 peer-review package it produced earlier in the same session against the
lagging `main` snapshot. That package is superseded and is named here only to
record the exclusion.

Provider-level independence only. Run-level and session-level independence is
not claimable until AIF-050 lands the run identity model; see section 9.

## 3. The unit of measurement, declared before measuring

**12 delegated sub-scripts**, enumerated from the invocation sites in
`tools/staging/prepush_gate.py` at the baseline commit. All 12 are present.

This is **not** the twelve in `PREPUSH_GATE_REFERENCE_V1.md` section 2. That
table counts twelve *checks* in execution order, which includes in-process
checks (classification, mass change, BOM) and omits three delegated scripts
(`check_seed_budget.py`, `check_aif_claimed.py`, `generate_public_manifest.py`).
Two different twelves. Stating which one is meant is not pedantry: three of the
four defects AIF-082 records were denominator or encoding errors rather than
logic errors.

The reference document is itself now behind the thing it describes. Its section
12 records it as read at `99b32f5e6` (2026-08-01); the baseline here is
`ce813790` (2026-08-09), and scripts were added in between. Its known-defect 3
already says the portal names two guards where twelve run.

The 12:

    labtalk/ai_portal/audit_trail.py
    labtalk/ai_portal/check_mandatory_tracked.py
    tools/coordination/aif_collision_gate.py
    tools/coordination/check_aif_claimed.py
    tools/coordination/check_session_log_row.py
    tools/fullstack_docs/normcheck_v1.py
    tools/fullstack_docs/refcheck_v1.py
    tools/staging/check_house_style.py
    tools/staging/check_sandbox_git_guard.py
    tools/staging/check_seed_budget.py
    tools/staging/generate_public_manifest.py
    tools/staging/repository_role_guard.py

## 4. Results

| Script | Known-bad input | Result | Verdict |
| --- | --- | --- | --- |
| `check_house_style.py` | added line with em-dash + curly quotes | rc=2, named all three codepoints with line number and offered the fixer | SEEN TO FAIL |
| `check_seed_budget.py` | padded Tier-1 seed 200 B past ceiling | rc=2, `8348 B against its own declared 8192 B ceiling, OVER BY 156` | SEEN TO FAIL |
| `aif_collision_gate.py` | duplicate AIF number in intake queue | rc=1, `two lanes claimed the same number` | SEEN TO FAIL |
| `audit_trail.py` | closeout with no front matter | rc=1, named the file and the missing envelope | SEEN TO FAIL |
| `check_aif_claimed.py` | intake row naming unclaimed AIF-777 | rc=2, named the absent claim file | SEEN TO FAIL |
| `check_sandbox_git_guard.py` | injected zero-byte `.git/index.lock` | rc=0 clean, rc=2 with lock, diagnostic named the stale signature | SEEN TO FAIL |
| `check_mandatory_tracked.py` | deleted a mandatory document | rc=0, **PASS** | **DEFECT 1** |
| `check_session_log_row.py` | closeout with no Session Log row | rc=0, **OK** | **DEFECT 2** |
| `normcheck_v1.py` | none needed; fails at baseline | crashes on any clone | **DEFECT 3 (recurrence)** |
| `refcheck_v1.py` | not falsified | rc=0 with substantive output (295 commands, 76 functions, 0 phantoms) | UNTRUSTED |
| `generate_public_manifest.py` | not falsified | rc=0, 46 lines of manifest | UNTRUSTED |
| `repository_role_guard.py` | not falsified | rc=2 sandbox block, exactly as the portal predicts | NOT ASSESSED |

Six seen to fail. Three defects. Two untrusted for want of a known-bad case.
One not assessable off-host.

## 5. Defect 1 -- `check_mandatory_tracked.py` cannot detect the removal of a
mandatory file

**Severity: material.** The gate exists to ensure declared files stay tracked,
and deleting a declared file is the exact event it should catch.

    baseline                     : 48 document(s) and 11 script(s) checked
                                   PASS -- every declared file is tracked
    remove AI_TIER1_SEED_V1.md
    from index AND disk          : 47 document(s) and 11 script(s) checked
                                   PASS -- every declared file is tracked
    exit code                    : 0

`declared()` builds its list by discovery rather than from a fixed manifest, so
removing a protected file removes it from the checklist that protects it. The
denominator moved and the verdict did not.

This is the AIF-082 pattern exactly: the code was right about the wrong
question. It answers "is every file I can see tracked" when the obligation is
"is every file that must exist present and tracked."

**PRIOR ART -- correction added 2026-08-12.** This is not a new finding. AIF-082
section 12, "C8b -- my own mandatory-tracked gate has the wrong denominator",
recorded the same root cause on 2026-07-31, self-reported by the gate's own
author: `check_mandatory_tracked.py:36` derives its universe from
`ENTRY_DOCS = ("AI_README.md", "AI_PORTAL.md")`, so "a file the portal never
names cannot fail the gate."

What section 5 above adds is a **second symptom of the same defect**, reached
from the other direction: C8b showed a file that was never in the universe
cannot fail; this shows a file that WAS in the universe leaves it silently when
deleted, taking the denominator with it (48 -> 47, still PASS). One root cause,
two failure modes, and the removal case had not been recorded.

Recorded as a correction rather than quietly rewritten, because the miss is
itself the finding: this probe did not do prior-art discovery before reporting,
which the AI Systems Integration SDLC charter section 3.1 requires of an agent
authorized to analyze a scope. The rule existed; I did not run it.

Suggested smallest correction: pin the declared set in a committed manifest and
fail when a declared path is absent, so the denominator cannot shrink silently.

## 6. Defect 2 -- `check_session_log_row.py` excludes what it cannot parse and
reports OK

**Severity: material.** This is the second incarnation of the instrument
AIF-082 already recorded as defective.

Its own docstring records the first version matching any AIF number anywhere in
the body, which passed 79 of 83 while the stricter probe found 12 of 18 missing.
The rewrite narrowed the match to the H1 title with a fallback to the header
region. It now fails from the other direction.

Probe input: a staged closeout with no Session Log row. Output:

    session-log-check: inspected 1 closeout(s)
    session-log-check: 1 closeout(s) name no lane in their title --
                       not checkable, and arguably its own defect
    session-log-check: OK -- every closeout in scope has a Session Log row
    rc=0

The caveat was written into the output and left out of the exit code. Measured
across all 102 closeouts in `docs/maintenance/` at the baseline:

| Resolution path | Count | Share |
| --- | --- | --- |
| lane named in the H1 title | 21 | 20.6% |
| lane resolved via header fallback | 19 | 18.6% |
| neither -- excluded and reported OK | **62** | **60.8%** |

Bound: the checkable share must exceed the excluded share for the reported
figure to mean anything. It does not. 40 checkable against 62 excluded.

Suggested smallest correction: make unparseable a non-zero condition. A closeout
whose owning lane cannot be resolved is a finding about that closeout, which the
script's own message already says out loud.

## 7. Defect 3 -- crash rendered as a substantive finding, second instance

`PREPUSH_GATE_REFERENCE_V1.md` known-defect 1 records `audit_trail.py` exiting
non-zero with `ModuleNotFoundError: No module named 'yaml'` and the gate
reporting "a closeout is missing its ai_report_audit envelope, or a report id is
duplicated". Neither named cause was true.

The same rendering now occurs on a second script, from a different cause:

    FileNotFoundError: [Errno 2] No such file or directory:
      '<root>/dottalkpp/data/metadata/SYSCMD.dbf'

`normcheck_v1.py` reads a data fixture that is deliberately not published, so it
crashes on **any clone**, and `prepush_gate.py` renders the crash as
"ADVISORY -- catalog drift present (see above)".

The consequence is bounded and worth stating: for every agent working from a
clone, which is every outside partner the portal invites, the normalization
guard can never pass and always reports a false cause. It is advisory, so it
blocks nothing; it misinforms every time.

Suggested smallest correction: distinguish "guard could not run" from "guard
ran and found drift" at the call site, which is the generalisation of
known-defect 1 rather than a second point fix.

## 8. Incidental findings, outside this probe's remit

1. **A block is armed at the baseline commit, and already fixed in the working
   tree. Corrected 2026-08-09 after checking both.**
   `docs/maintenance/SESSION_CLOSEOUT_COORDINATION_ONTOLOGY_AND_REGRESSION_2026-08-08.md`
   carries no envelope in the commit (`git show HEAD:` finds zero occurrences of
   `ai_report_audit`), so `audit_trail.py` exits non-zero against a clean clone.
   The `D:\code\ccode` working tree has it repaired: +30 unstaged lines carrying
   a full envelope, and `audit_trail.py` run against the live tree reports
   `enforced=95 valid=95 findings=0`, rc=0.

   **The methodological point outranks the finding.** A probe run against the
   committed branch reports defects the dirty working tree has already fixed.
   The portal's own Evaluation Rule says development-tree dirtiness is not a
   release-risk signal; here the dirtiness *is* the remediation. Every gate
   finding must therefore name the tree it was measured against. This report is
   measured against `ce813790` throughout, and only this item was checked both
   ways. The other findings in sections 5 through 7 are code defects rather than
   content defects and are not tree-sensitive, but they have not been re-run
   against the live tree either.

2. **The Tier-1 seed has 44 bytes of headroom**: 8148 B of its declared 8192 B
   ceiling, 99%. The gate is behaving correctly and is the best-built instrument
   in the set; the number is reported because it is close to its bound.

3. **`repository_role_guard.py` behaved exactly as the portal predicts** in a
   sandbox mount, blocking at rc=2 and short-circuiting the rest. Recorded as
   evidence the portal's sandbox section is accurate, not as a defect.

4. **The envelope on this report is not machine-validated, and that is a gap.**
   Found by running the gates against this file before handing it over.
   `audit_trail.py` enforces on `closeout_glob` (`SESSION_CLOSEOUT_*.md`) plus
   the external intake landing zone. Staging this report moved `enforced` not at
   all: 93 before, 93 after. The contract in `AI_REPORT_AUDIT_CONTRACT_V1.md`
   requires the envelope on any "report that changes AI Portal lane state,
   contracts, registries, proofs, promotion state, or publication state", which
   this report does. So a lane-state-changing report filed under any name other
   than `SESSION_CLOSEOUT_*` carries an envelope nobody checks. The obligation is
   broader than its enforcement glob. Severity: minor, but it is the same shape
   as defects 1 and 2 -- a scope that silently excludes, reported as clean.

## 9. What this does not discharge

E1 is marked **PARTIAL** by this report, not MET.

- **Pre-commit set only**, by maintainer direction. The whole/partial gate
  inventory is deferred to a later moment.
- **No engine surface.** E1's wording covers the engine surface, the usage
  contracts, and the regression suite. None were touched. This probe covers the
  gate surface alone.
- **Two gates remain untrusted** for want of a known-bad case: `refcheck_v1.py`
  and `generate_public_manifest.py`.
- **One gate is not assessable off-host**: `repository_role_guard.py`.
- **Independence is provider-level only.** The stronger claim about who reviewed
  whose work needs AIF-050's run and session identity model. The activity does
  not wait on it; the claim does.
- **No fix is proposed as a patch.** Suggested corrections above are the
  smallest ones visible from outside, offered for the owner to accept, alter, or
  reject.

## 10. The correlation worth keeping

Every gate in this set that was falsification-tested when it was built passed
this adversarial run. Both gates that were not, failed, in the same vacuous-green
manner AIF-082 already described.

That is a cheaper predictor of gate quality than any review checklist, and it
argues for making **seen-to-fail a recorded property of each gate** -- a
committed known-bad case per gate, run in CI, so a gate that has never been
observed rejecting anything is visibly untrusted rather than quietly green.

That would also close the loop AIF-082 opened by hand: it wrote the rule, this
probe applied it once, and a recorded case per gate applies it continuously
without anyone remembering to.

## 11. Reproduction

Everything below ran against a disposable clone, reset between cases. Nothing in
`D:\code\ccode` was staged, committed, or modified other than the creation of
this report.

    git clone --depth 1 --branch development \
      https://github.com/deraldg/x64base.git probe
    cd probe
    pip install pyyaml

    # DEFECT 1
    python3 labtalk/ai_portal/check_mandatory_tracked.py       # 48, PASS
    git rm --cached labtalk/ai_portal/AI_TIER1_SEED_V1.md
    rm -f labtalk/ai_portal/AI_TIER1_SEED_V1.md
    python3 labtalk/ai_portal/check_mandatory_tracked.py       # 47, PASS  <- defect
    git checkout -- . && git reset

    # DEFECT 2
    printf '# Probe closeout with no lane and no row\n' \
      > docs/maintenance/SESSION_CLOSEOUT_PROBE_2026-08-09.md
    git add docs/maintenance/SESSION_CLOSEOUT_PROBE_2026-08-09.md
    python3 tools/coordination/check_session_log_row.py        # OK, rc=0  <- defect
    git reset && rm docs/maintenance/SESSION_CLOSEOUT_PROBE_2026-08-09.md

    # DEFECT 3
    python3 tools/fullstack_docs/normcheck_v1.py .             # FileNotFoundError

## 12. Regression cases, for re-run after fixes

Offered as the standing known-bad set for these three. Each must be observed
FAILING before the corresponding fix is called proven.

| ID | Gate | Known-bad input | Must produce |
| --- | --- | --- | --- |
| R-MT-1 | `check_mandatory_tracked.py` | any single declared document removed from index and disk | non-zero, naming the absent path |
| R-MT-2 | `check_mandatory_tracked.py` | declared document present but untracked | non-zero, naming the untracked path |
| R-SL-1 | `check_session_log_row.py` | staged closeout with no resolvable lane | non-zero, naming it unresolvable |
| R-SL-2 | `check_session_log_row.py` | staged closeout with a resolvable lane and no Session Log row | non-zero, naming the missing row |
| R-SL-3 | `check_session_log_row.py` | staged closeout with a resolvable lane and a correct row | zero |
| R-NC-1 | `normcheck_v1.py` via `prepush_gate.py` | clone with no `dottalkpp/data/metadata/SYSCMD.dbf` | a message distinguishing "could not run" from "found drift" |

R-SL-3 is the control. Without it, a fix that fails everything is
indistinguishable from a fix that works, which is the same class of error this
report is about.

## 13. Evidence tier

**Runtime-observed** for every row in section 4 and every figure in sections 5
through 8. Each was produced by executing the named script at the baseline
commit and reading its exit code and output.

**Not verified**: the internals of the two untrusted gates, anything on the
engine surface, and any behaviour of `repository_role_guard.py` beyond its
documented sandbox short-circuit.

**Not claimed**: that the three defects are the only ones present. Six gates
were falsified with one known-bad case each. One case per gate is a floor, not
a sweep.

**Self-check performed.** This report was staged in the disposable clone and run
through the gates it reports on before delivery: 0 non-ASCII bytes in 15,460;
`check_house_style.py` PASS with every line counted as added (the untracked-file
trap in `PREPUSH_GATE_REFERENCE_V1.md` section 6 applies to it in full);
`check_session_log_row.py` correctly finds no closeout in scope. Its envelope was
**not** validated, for the reason recorded as incidental finding 4.
