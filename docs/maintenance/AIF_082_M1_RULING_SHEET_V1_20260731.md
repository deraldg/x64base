# AIF-082 M1 Ruling Sheet V1

    lane        : AIF-082
    gate        : M1 (owner rulings on section 6)
    charter     : docs/maintenance/ONBOARDING_COST_AND_ACCEPTANCE_LANE_V1.md
    owner       : member.derald
    steward     : member.ai.claude.cowork
    created_utc : 2026-07-31T12:35:00Z
    updated_utc : 2026-07-31T19:40:00Z
    baseline    : 1b52869e1 (development, pushed)
    status      : 24 rows, 14 closed, 10 open

---

## How to use this

The charter is 50 KB. Reviewing M1 by reading it would repeat the defect the
lane exists to fix, so this sheet is the Tier-1 form of the decision: everything
needed to rule, without re-reading the charter.

Rule each item **independently**. Mark `A` accept, `R` reject, `D` defer. Reject
and defer are ordinary outcomes, not failures -- a KILL ruling that the current
cost is correct closes the lane with a complete result.

You can mark this file directly, or just say the letters in chat and the steward
records them here.

**Most of the sheet is proposal.** Four items were built during the session and
were ratified 2026-07-31T18:22Z rather than authorised: **6.2** (Tier 1 seed),
**6.11** (maintenance contract), **6.5g** (leave a handoff), **6.5e** (UTC
headers). They are scattered across the tables below because they were added at
different points; the Ruling record at the end is authoritative.

**Label warning.** The section headings below ("Group A -- cheap, independent,
reversible", etc.) are the sheet's own grouping and do **not** match the A/B/C/D
grouping used in chat on 2026-07-31, which sorted by *already-built / cheap /
build / blocked*. The chat "Group A" was the four ratified items above, not the
eleven under "Group A" here. Quote item numbers, not group letters.

---

## Fast path -- three decisions if you only want three

These three are cheap, independently justified, and unblock the rest.

| # | Decision in one line | Why first |
| --- | --- | --- |
| **6.8a** | One canonical Tier-1 body; `CLAUDE.md` and `AGENTS.md` become shims that include it | Delivery mechanism already exists and already fires for free. Highest value, lowest cost item on the sheet. |
| **6.1** | Build the generated Tier-0 state file | Everything else that measures or refreshes depends on it. |
| **6.7** | Run the governance-cost probe | Pure measurement, changes nothing, and tells you whether the process tax is real before you spend on it. |

If you rule only these three and defer the rest, the lane still advances.

---

## The full sheet

### Group A -- cheap, independent, reversible

| # | Proposal | Cost | Reversible | Recommend | Ruling |
| --- | --- | --- | --- | --- | :---: |
| **6.8a** | One canonical Tier-1 body; vendor files become shims. Today `CLAUDE.md` is 4,314 B and `AGENTS.md` 1,496 B, so partners onboard to different depths by accident of vendor. | small | yes | **accept** | ` ` |
| **6.8b** | Repair the staleness signal: expire heartbeats past a threshold; make `checkout` work on a delete-refusing mount. Today `status` shows 3 active sessions, 2 stale by 12+ hours, 1 that could not deregister. | small | yes | **accept** | ` ` |
| **6.7** | Probe governance cost per lane over the last 20 lanes, bucketed by change class. Measurement only, no process change. | small | n/a | **accept** | ` ` |
| **6.5a** | Split `CURRENT_TARGET.md`: keep lines 1-18 as the pointer, move 18 historical sections to `CURRENT_TARGET_HISTORY.md`. Nothing deleted. | small | yes | **accept** | ` ` |
| **6.5b** | Retire the legacy "Start Here" 11-item list at `AI_README.md:56-73`. It is marked superseded but is still a numbered list under a "Start Here" heading. Git holds it. | tiny | yes | **accept** | ` ` |
| **6.5c** | State precedence between the two overlapping mandatory field blocks (`SDLC_FAST_START_SEED_V1.md:32-57`, 20 fields vs `SCOPE_CALIBRATION_SEED_V1.md:11-24`, 10 fields, 7 shared). Or nest one in the other. | tiny | yes | **accept** | ` ` |
| **6.13** | **Gate the dashboard Session Log row.** Measured 2026-07-31 (6.7 / M6): present in 6 of 18 lanes, 33%, against 83-94% for the four obligations that have gates. It is the only AIF-006 obligation with no mechanism behind it. Proposed: `prepush_gate.py` warns when a commit adds or edits a `SESSION_CLOSEOUT_*.md` without a matching Session Log row. Warn, not hard-block, so it never wedges a commit. | small | yes | **accept** | ` ` |
| **6.14** | **Verify portal-mandatory files are tracked.** Two were found untracked on 2026-07-31 by accident, from `create mode` lines in unrelated commits: `AGENTS.md` (the always-read shim for Codex-family agents) and `SCOPE_CALIBRATION_SEED_V1.md` (step 5 of the Mandatory Start). Both were invisible to a clone. `labtalk/ai_portal/check_mandatory_tracked.py` is written and derives its list from the entry documents rather than hand-maintaining one -- 45 declared files. Needs a host run and a decision on whether it joins the pre-commit gate. | small | yes | **accept** | ` ` |
| **6.5d** | Cap intake-queue row length; depth lives in the lane doc the row already points to. AIF-078 is 1,147 words in one table cell; the file is 142 KB over 126 lines. | small | yes | **accept** | ` ` |
| **6.5h** | Enforce the house style rule that the portal itself breaks. `CLAUDE.md:54` says no em-dashes; measured 2026-07-31: **`AI_PORTAL.md` 88 em-dashes + 7 unicode arrows, `CURRENT_TARGET.md` 50 + 11, `AI_README.md` 7**. A declared rule with no gate is the AIF-079 class applied to prose. Proposed: `grep -P '[^\x00-\x7F]'` in the pre-commit gate for changed doc lines only, so the backlog does not block work while new violations become impossible. | small | yes | **accept** | ` ` |
| **6.5g** | Land the AIF-081 session handoff in the tree as the **seed of Tier 1**, and make "leave a handoff" a closeout obligation alongside the session closeout. It is already the tier design executed by hand, and its section 8 contained the fix for this session's wedge (C8, 5b) while being unreachable from the corpus. A closeout records what happened; a handoff records how to work here. AIF-006 requires the first, not the second. | small | yes | **accept** | ` ` |
| **6.5f** | Guard against git-over-an-unreliable-mount. `LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42` warns of it in specific terms; this steward read it and wedged your index anyway (5b). No mechanism exists behind the rule. Proposed: trigger-fired Tier-1 warning, or a wrapper refusing git writes from a non-host root, keyed on the same signal `repository_role_guard.py` already uses. | small | yes | **accept** | ` ` |
| **6.5e** | Header blocks take `created_utc` / `updated_utc` (ISO-8601 UTC), matching the convention the closeout envelope already enforces. A bare date cannot order four sittings in one day, nor this lane against AIF-080/081. 66 files under `docs/maintenance/` affected; this lane's three already converted. | small | yes | **accept** | ` ` |

### Group B -- the structural build

| # | Proposal | Cost | Reversible | Recommend | Ruling |
| --- | --- | --- | --- | --- | :---: |
| **6.1** | Tier 0: generated state file under 4 KB. Branch, HEAD, open lanes, owed items, **plus a staleness warning** (declared target vs HEAD distance). Generated, never authored, so it cannot drift. | medium | yes | **accept** | ` ` |
| **6.12** | **Website tree has no coordination protocol.** Two agents edited `D:\dev\x64base-site` concurrently on 2026-07-31; a collision on `config/nav.ts` was avoided only because one read the file before writing. `ccode` has claim-aif, the collision gate and the pre-push gate; the site repo has none of it, and Seed 4 governs authority but not concurrency. | small | yes | **accept** | ` ` |
| **6.11** | **Maintenance contract for auto-injected and pointed-at surfaces.** Owner correction 2026-07-31: auto-injection guarantees delivery, not accuracy, so an unmaintained always-read file is worse than a rarely-read one. Rule: only *invariants* and *pointers to gated or generated artifacts*; **no perishable literals**; hard byte ceiling; a rule that gains a hard-failing gate demotes out. Already applied to `CLAUDE.md` (its hardcoded glibc/GLIBCXX figures were removed and replaced with "measure it") and written into the Tier 1 seed as its own gate. | small | yes | **accept** | ` ` |
| **6.2** | Tier 1 under 8 KB: role table, mutation guard, local-access rules, house conventions, stopping rule. Mostly selection of existing text, not new authoring. | medium | yes | **accept** | ` ` |
| **6.3** | Tier 2: index the rest of `AI_PORTAL.md` by trigger (about to push, about to change source, about to publish, about to open a lane, about to close out). **No text deleted.** | medium | yes | **accept** | ` ` |
| **6.4** | Five-question self-test as the stopping rule, answerable from Tier 0 + Tier 1 alone. This is the acceptance gate the portal currently lacks. | small | yes | **accept** | ` ` |
| **6.9** | Read manifest emitted as a side effect of the Tier-0 pull, validated by the closeout gate. Makes the existing unverifiable `Files read:` field (`AI_README.md:365`) true. Refresh then re-reads only hash-changed docs. | medium | yes | **accept** | ` ` |

### Group C -- blocked or hand-off

| # | Proposal | Cost | Reversible | Recommend | Ruling |
| --- | --- | --- | --- | --- | :---: |
| **6.6** | Decrement operator: when a rule becomes mechanically enforced, its prose demotes one tier. Five conversions already exist in the tree; zero demotions ever collected. **BLOCKED on AIF-079 M1** -- the validator is what proves a gate hard-fails rather than merely existing. | medium | yes | **accept in principle, execute after AIF-079 M1** | ` ` |
| **6.10** | Hand the manifest storage design to the owning memo lane (DBF store on the 64-bit memo object). AIF-082 keeps only the interface and the projection requirement. **Ruling needed is the handoff, not the build.** | n/a here | yes | **accept as handoff** | ` ` |

---

## Two rulings that are not on the list but are owed

Neither belongs to AIF-082. Both surfaced during it and both are blocking
something.

| # | Question | Why it needs you |
| --- | --- | --- |
| **X1** | Does **AIF-072** remain the controlling target, or is a fresher lane promoted into `CURRENT_TARGET.md`? Recorded as open on 2026-07-29 and again 2026-07-31; three lanes have landed past it. | Only the owner sets the target. 6.1's staleness warning is what stops it recurring, but the current value still has to be set by hand once. |
| **X2** | **Commit slicing.** The intake queue and dashboard carry other sessions' uncommitted rows alongside AIF-082's. `git add` on either fuses them. AIF-082's additions are contiguous, so hunk-scoped commits separate cleanly. | Commit authority is yours; the steward does not commit. |

---

## What a KILL looks like

Rejecting the sheet is a legitimate and complete outcome. If the ruling is that
127,704 bytes is the correct price for this corpus, the lane closes having
produced:

- the measurement, which did not previously exist;
- the cold-start entry finding (C6), which no re-onboarding test could detect;
- the governance finding that a reviewed recommendation did not convert to
  action because it was never given a number (C7);
- a falsifiable acceptance target for any future attempt.

That is a Phase-0 KILL in the sense of `AI_PORTAL.md:325-337`: it costs a
measurement rather than a build, and the number stays useful either way.

---

## Ruling record

| Item | Ruling | Date | Note |
| --- | --- | --- | --- |
| 6.8a | **A** done | 2026-07-31T18:29Z | `AGENTS.md` rewritten as a shim over `AI_TIER1_SEED_V1.md`, matching `CLAUDE.md`. Verified first that the seed already asserts everything `AGENTS.md` did. Kept the role table verbatim -- the one fact the portal deliberately duplicates, per `AI_PORTAL.md:321-323`. Push-authorisation detail moved to the seed's "commit or push" trigger row, where it fires. Vendor onboarding depth is now equal by construction rather than by accident. |
| 6.8b | | | |
| 6.7 | **A** done | 2026-07-31T18:40Z | Probe run over AIF-063..082. Governance cost is FLAT (3-5 artifacts per lane) and mildly INVERTED: doc-only lanes mean 4.09, source-changing 3.71. Second finding: the dashboard Session Log row is the only obligation with no gate and is present in 6 of 18 lanes (33%), against 83-94% for the four that have gates. Result in charter 6.7, 'M6 RESULT'.
| 6.5a | **A** done | 2026-07-31T18:50Z | `CURRENT_TARGET.md` split: 26,282 B / 470 lines -> **1,9xx B pointer** + `CURRENT_TARGET_HISTORY.md` (23,919 B). Nothing deleted. Went further than proposed: the 'in flight' table was removed too, because it restated what `TIER0_STATE.md` now generates, which is the drift channel 6.11 forbids. The pointer now carries only the owner's declared priority plus decisions only he can settle. |
| 6.5b | **A** done | 2026-07-31T18:52Z | Legacy 11-item 'Start Here' list removed from `AI_README.md`. A numbered list under that heading is an instruction regardless of the 'superseded' disclaimer above it, and a cold agent follows instructions. Replaced with a one-paragraph note recording the retirement and the `git log` recovery path. |
| 6.5c | **A** done | 2026-07-31T18:54Z | Precedence stated in **both** documents. `SDLC_FAST_START_SEED_V1.md` 20-field block is the SUPERSET carried by packets and closeouts; `SCOPE_CALIBRATION_SEED_V1.md` 10-field block is the planning SUBSET, filled first, feeding the other. Seven fields shared; neither overrides the other, and a conflict is a finding to report rather than a choice to make. |
| 6.5d | | | |
| 6.5e | **A** accepted | 2026-07-31T18:22Z | `created_utc` / `updated_utc` ISO-8601 UTC in header blocks, matching the envelope convention. Applied to the 5 files authored this session. **Owed:** ~66 remaining files under `docs/maintenance/`, and a decision on whether the sweep is one slice or incremental-on-touch. Recommend incremental-on-touch, so the backlog never blocks work. |
| 6.5f | | | |
| 6.5g | **A** ratified | 2026-07-31T18:22Z | "Leave a handoff, not only a closeout" becomes a closeout obligation alongside AIF-006. Both handoffs landed: `HANDOFF_CLAUDE_WSL_DOTTALKPP_2026-07-31.md` (`71f9b850e`) and `HANDOFF_CLAUDE_COWORK_ONBOARDING_2026-07-31.md` (`554891db5`). **Owed:** add the obligation to `AI_PORTAL.md` "Closeout Updates Startup" and to `SESSION_CLOSEOUT_TEMPLATE.md` so it is a gate rather than a precedent. |
| 6.5h | | | |
| 6.1 | **A** done | 2026-07-31T18:33Z | `labtalk/ai_portal/generate_tier0_state.py` + committed `TIER0_STATE.md`, 2,133 B against a 4,096 target. Commit `a1e5e228f`. Warnings cross-validate against `aif_collision_gate.py` independently. **Owed:** nothing regenerates it, so it goes stale on the next commit -- wiring it to the pre-commit hook is an open decision.
| 6.2 | **A** ratified | 2026-07-31T18:22Z | Tier 1 seed accepted as the standard. `labtalk/ai_portal/AI_TIER1_SEED_V1.md`, 8,191 B against its 8,192 ceiling, committed `8a3dea347`. The 8 KB ceiling and its enforcement are ratified with it. |
| 6.3 | | | |
| 6.4 | | | |
| 6.9 | | | |
| 6.6 | | | |
| 6.10 | | | |
| 6.11 | **A** ratified | 2026-07-31T18:22Z | Maintenance contract binding on always-read surfaces: invariants and pointers only, no perishable literals, hard byte ceiling, demote once a hard-failing gate covers a rule. Already applied to the Tier 1 seed and to `CLAUDE.md`, whose hardcoded toolchain versions were removed as perishable. |
| 6.12 | | | |
| 6.13 | **A** partial | 2026-07-31T19:15Z | `tools/coordination/check_session_log_row.py` written and committed (`9b3977856`), standalone rather than wired into the gate. Running it surfaced a deeper defect: **76 of 83 closeouts name no lane in their title**, so the set is largely unattributable by machine. The three it can attribute and flags -- AIF-060, AIF-071, AIF-078 -- are genuinely missing rows. **Open:** a one-line convention in `SESSION_CLOSEOUT_TEMPLATE.md` (H1 carries `(AIF-NNN)`) is smaller than the checker and worth more; and whether the checker joins the gate. |
| 6.14 | **A** done | 2026-07-31T19:40Z | `check_mandatory_tracked.py` written, widened to scripts after it missed the role guard, run host-side: **16 untracked** (10 documents, 6 scripts) including `REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md` and `repository_role_guard.py`. Owner ruled commit-and-publish; all 16 landed in `1b52869e1`, 1,956 insertions, all creates. Re-run reports **PASS**. Closes C8 by mechanism. **Open:** whether the check joins `prepush_gate.py`. |
| X1 | **A** (retire) | 2026-07-31T12:45Z | AIF-072 retired as controlling target; stays claimed and pick-up-ready. `CURRENT_TARGET.md` top section rewritten to name the five in-flight lanes. Applied. |
| X2 | **A** (done, published) | 2026-07-31T14:30Z | Four themed commits host-side: `1024a53d5` lane artifacts, `8a3dea347` tier 1 seed + portal surfaces, `71f9b850e` agents handoff + front-door files, `cf5ac99b8` record corrections. `prepush_gate.py` PASS on all. **Pushed** `0803f0f13..cf5ac99b8` to `origin/development`. Staging and `main` not reached, out of scope. |

M1 closes when every row above carries a ruling. Partial rulings are fine and
unblock their own items; nothing waits on the sheet being complete.

## Group A ratified -- 2026-07-31T18:22Z

Owner ruled Group A accepted: **6.2, 6.11, 6.5g, 6.5e**. These were already built
during the session; the ruling makes them the standard rather than one session's
precedent.

What that establishes:

- **The Tier 1 seed is the canonical entry body**, under an enforced 8 KB
  ceiling. Adding to it requires removing or demoting.
- **Always-read surfaces carry invariants and pointers only.** No perishable
  literals anywhere an agent reads without asking. This binds `CLAUDE.md`,
  `AGENTS.md`, and the seed itself.
- **A handoff is owed at closeout**, not only a session record.
- **Header blocks carry UTC timestamps**, not bare dates.

Three follow-ups are owed by the ruling and are not yet done. They are what turns
these from precedent into gates:

1. ~~Add the handoff obligation to `AI_PORTAL.md` and
   `SESSION_CLOSEOUT_TEMPLATE.md`.~~ **DONE 2026-07-31T18:30Z.** `AI_PORTAL.md`
   gains "Leave a Handoff as well" after "Leave a Session Closeout", with the
   naming convention, two worked examples, four earned rules (commit it; aim at
   the next agent; assert no perishable facts; keep it Tier-1 sized) and an
   explicit escape -- a session with nothing durable to hand off says so rather
   than manufacturing a file. `SESSION_CLOSEOUT_TEMPLATE.md` gains a matching
   "Handoff left" section, so it is now a template field rather than a
   remembered good intention.
2. **`created_utc` sweep policy: incremental-on-touch, adopted 2026-07-31T18:30Z.**
   A file gets its UTC header the next time a session edits it for any other
   reason. No bulk pass. Rationale: a 66-file character sweep is its own scoped
   slice, it would fuse with every session in flight, and the backlog harms
   nobody -- only *new* drift matters, and touching a file is exactly when the
   correct timestamp is known. Revisit only if a tool ever needs to sort the
   whole corpus by time.
3. Consider whether 6.11 deserves mechanical enforcement rather than prose. It is
   currently a rule with no gate, which is the AIF-079 class this lane keeps
   naming. A checker for perishable literals in the always-read set would be
   small, and under 6.6 it would then earn its own demotion.

Groups B, C and D remain open: 16 rows.

---

## Group E -- opened by the M4 run 1 result, 2026-07-31T21:52Z

Two rows. Both are yours; neither is a judgement call I should make alone,
because both change what this lane is measured against.

**R25 -- What is M4's acceptance artifact?** Two cold agents ran; neither
produced the Minimal New-AI Checklist; both were conventionally correct on a real
owed task (ten conventions applied unprompted, three of them authored the same
day). The evidence says the checklist is not what a correctly-onboarded agent
naturally emits. Options:

- **(a)** Keep the checklist as the pass condition and add an explicit ask for it
  to the Tier 1 seed. Cost: seed bytes, against an 8,192 B ceiling currently at
  8,191. Something must be demoted to make room.
- **(b)** Replace the pass condition with conventional correctness on a real
  task, scored against the charter 11.2 rubric. Cost: a softer, judged signal --
  but it is what both runs actually produced, and it is what onboarding is FOR.
- **(c)** Both, with the checklist demoted to a diagnostic rather than the gate.

My recommendation is **(b)**, and I flag my own bias: I designed the rubric, so
of course I like the measure I can pass. That is precisely why it is your ruling.

**R26 -- M9 blocks M4 (recommend: accept as stated).** Without an emitted
`Files read:` manifest, an M4 run cannot distinguish "the 10 KB entry path was
sufficient" from "the agent read widely and expensively and got there anyway."
Run 1 spent 117,051 tokens against a 10,324 B entry path and I cannot say which
happened. Every future run is equally uninterpretable until M9 lands. This was
already filed as an argument at charter line 1128; run 1 makes it a measurement.

## Owed to the maintainer, host-side (I must not run git)

`labtalk/ai_portal/TIER0_STATE.md` is stale -- generated at `3550705dd`, HEAD is
`1b60b728f`, so it does not know AIF-083 exists. The generator shells out to git,
so it is host-side by the sandbox rule:

```powershell
cd D:\code\ccode
python labtalk\ai_portal\generate_tier0_state.py
```

Groups B, C and D remain open: 16 rows. Group E adds 2. Total open: 18.

**R27 -- invert `check_mandatory_tracked.py` to a governed-path gate (charter 12).**
The gate PASSED in commit `be8d1a12e` while ten files in `tools/staging/` sat
untracked, including `test_repository_role_guard.py` -- the test for the binding
guard that hard-blocked and then passed twice in that same transcript. It passed
because its universe is "files the portal already names," so an unmentioned file
cannot fail it. Third gate this session with a self-drawn denominator, all mine.

Proposed: govern by path (`tools/staging/`, `tools/coordination/`,
`labtalk/ai_portal/`, `docs/maintenance/`), with explicit in-repo waivers.

Your call because the cost lands on you: this turns an always-passing gate into
one that fails loudly on first run against an untriaged backlog. **6.6's demotion
rule is blocked until this is settled** -- 6.6 demotes a Tier 1 rule once a
hard-failing gate covers it, and a gate with a self-drawn denominator would
license demoting a rule that nothing actually enforces.

Total open: 19.

**R27 SPLIT after maintainer correction "valid curation tools for the full-stack
documentation process of our system" (charter 12.5).** I had filed the untracked
set as a triage backlog. It is the documentation production pipeline: ~1,142
source files, ~8.2 MB of Python and PowerShell, `tools/` not in `.gitignore`.
`stage_assembled_manual_to_site.py:73` writes into the x64base-site checkout, so
the repo-to-site publication bridge is untracked at both the script level and the
history level.

- **R27a -- track the pipeline. Act now; does not wait on R27b.** Directory-at-a-time
  commits, NEVER one `git add tools/` (that is AIF-050's fused slice at 1,142
  files). Suggested order: `tools/manualgen/`, then `tools/fullstack_docs/` --
  smallest, unambiguously source, and the two the site path runs through.
- **R27b -- invert the gate to governed paths.** Unchanged from the original R27.
  This is how we failed to notice, not the exposure itself.

Sequencing note: 6.6's demotion rule stays blocked on **R27b**, not R27a.

Total open: 20.
