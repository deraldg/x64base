# AIF-082 M1 Ruling Sheet V1

    lane        : AIF-082
    gate        : M1 (owner rulings on section 6)
    charter     : docs/maintenance/ONBOARDING_COST_AND_ACCEPTANCE_LANE_V1.md
    owner       : member.derald
    steward     : member.ai.claude.cowork
    created_utc : 2026-07-31T12:35:00Z
    updated_utc : 2026-07-31T18:04:08Z
    baseline    : cf5ac99b8 (development, pushed)
    status      : awaiting rulings -- 18 rows, X1 and X2 closed, 16 open

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

**Nothing below has been built.** Every item is a proposal.

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
| 6.8a | | | |
| 6.8b | | | |
| 6.7 | | | |
| 6.5a | | | |
| 6.5b | | | |
| 6.5c | | | |
| 6.5d | | | |
| 6.5e | | | |
| 6.5f | | | |
| 6.5g | | | |
| 6.5h | | | |
| 6.1 | | | |
| 6.2 | | | |
| 6.3 | | | |
| 6.4 | | | |
| 6.9 | | | |
| 6.6 | | | |
| 6.10 | | | |
| 6.11 | | | |
| 6.12 | | | |
| X1 | **A** (retire) | 2026-07-31T12:45Z | AIF-072 retired as controlling target; stays claimed and pick-up-ready. `CURRENT_TARGET.md` top section rewritten to name the five in-flight lanes. Applied. |
| X2 | **A** (done, published) | 2026-07-31T14:30Z | Four themed commits host-side: `1024a53d5` lane artifacts, `8a3dea347` tier 1 seed + portal surfaces, `71f9b850e` agents handoff + front-door files, `cf5ac99b8` record corrections. `prepush_gate.py` PASS on all. **Pushed** `0803f0f13..cf5ac99b8` to `origin/development`. Staging and `main` not reached, out of scope. |

M1 closes when every row above carries a ruling. Partial rulings are fine and
unblock their own items; nothing waits on the sheet being complete.
