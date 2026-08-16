---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260806-002
  recorded_at_utc: 2026-08-07T03:45:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: d4ad1b2ee
  authorization:
    requested_by: maintainer
    scope: >
      Owner assigned this project to the agent as a literal Claude Project and
      made the agent responsible for initiating the AIF (ruling 9.1,
      2026-08-06). Charter authoring is that initiation. Rulings R1-R3 recorded
      below were given by the owner in the same session.
  report:
    path: docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md
    kind: lane_charter
---

# x64base Agent Skill -- PDLC Charter and Plan of Record V1

**Status:** `CONVERTED to a repair lane by owner ruling R7 (2026-08-06). D1-D4
IMPLEMENTED and runtime-proven.` The skill programme (projector, bundle, shim
collapse) is retired unbuilt: P0 falsified its premise. What P0 found instead is
fixed. See sections 9 and 10.
**Intake:** AIF-090 - **Claim:** `coordination/aif/AIF-090.claim` - **Run:** `COWORK-20260806-001`
**Owner:** member.derald
**Steward/author:** member.ai.claude.cowork, until reassigned by the owner.
**Parent projects:** `project.ai_friendly`, `project.labtalk.campus`, `project.labtalk.pdlc`
**Baseline:** `development` @ `d4ad1b2ee`

---

## 1. Lane identity and lifecycle placement

**What is being delivered:** a distributable skill that makes an AI development
partner safe and productive in this repository, consumable both by an agent
working inside the tree and by an outside agency that has never cloned it.

| Concern | Lifecycle |
| --- | --- |
| Package identity, audience, setup, support, retirement, distribution | **PDLC** -- Programming Development Life Cycle, delivery scope |
| The projector program and registry inside each phase | **PDLC** run in full: analyze -> design -> code -> test/debug -> document -> maintain |
| The doctrine and gates the package projects | **DotTalk++ SDLC** and **maintenance SDLC** -- already proven, not re-opened here |

PDLC is gated on the SDLC evidence beneath it and **cannot outrun SDLC proof**
(`DOTTALKPP_SDLC_CHARTER_v0.md:183`). This lane adds no doctrine. It packages
doctrine that already exists and already has gates.

**Why this lane exists.** The retrieval architecture is already built and already
passes: Tier 0 generated (`generate_tier0_state.py`), Tier 1 budgeted to 8 KB
(`AI_TIER1_SEED_V1.md`), Tier 2 trigger-indexed (`recall.py` over
`portal_recall_graph.yaml`). Measured in the sandbox 2026-08-06:

```
python3 labtalk/ai_portal/recall.py --validate
recall: 10 trigger(s), 31 node(s), 44 edge(s)
recall: PASS -- no dangling edges, every node reachable

python3 labtalk/ai_portal/recall.py commit
working set: 6 node(s), 27384 B (21% of the 127704 B entry path this replaces).
```

What is missing is a front door that fires **without being asked**. Every path
today depends on an agent choosing to read `AI_README.md`, then choosing to read
the seed, then choosing to run `recall.py`. AIF-082 measured unenforced
obligations holding at 33 percent against 83-94 for gated ones. A skill is a
description-triggered loader with progressive disclosure, which is the shape the
three tiers already have.

## 2. Rulings ledger (owner rulings, binding on this lane)

| # | Date | Ruling |
| --- | --- | --- |
| R1 | 2026-08-06 | ~~**Lifecycle is PLDC.** The earlier "PDLC" was an owner typo; canonical usage governs.~~ **Superseded by R8 (2026-08-07).** Engine-adjacent work inside a phase runs as a full PDLC, gated on SDLC evidence beneath it. |
| R2 | 2026-08-06 | **Skills are a first-class LabTalk asset class.** `labtalk/skills/<name>/`, registered in `labtalk/registries/skills.yaml` beside `labs.yaml` / `proofs.yaml` / `apps.yaml`. NOT `src/` -- that tree is compiled runtime truth under `file(GLOB_RECURSE ...)` (`src/CMakeLists.txt:82,368`), and governance places portal/teaching material under LabTalk identity. |
| R3 | 2026-08-06 | **Bundle and tree are orthogonal, on the `dottalkpp` / `dottalk_bbsd` model.** Independently runnable; no runtime coupling in either direction; coordination only through the shared registry substrate. "Separate, but not far." |
| R4 | 2026-08-06 | **Drift gate runs advisory for one cycle**, then promotes to hard-fail. |
| R5 | 2026-08-06 | **`.claude/skills/` is an accepted vendor target in `development`.** |
| R6 | 2026-08-06 | **Audience is repo-partner onboarding.** Engine/DotScript-operator and website-maintenance skills are deferred, not cancelled (section 8). |
| R7 | 2026-08-06 | **G0 ruled: CONVERT.** "develop and document, it is our thesis". The skill programme is retired unbuilt; the lane becomes the D1-D4 repair lane, developed and documented as one act. P1-P9 below are superseded by section 11. |
| R8 | 2026-08-07 | **PLDC is merged into PDLC and retired.** "PLDC -- Product/Lab Delivery Cycle" and PDLC are one lifecycle. PDLC's SCOPE widens to span both the change and the deliverable; its NAME does not change -- it remains the **Programming** Development Life Cycle (`PDLC_STUDENT_WORKING_MODEL_LANE_V1.md`, `projects.yaml` `project.labtalk.pdlc`). This reverses R1, which had ruled the opposite. Doctrine of record: `SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`, "Lifecycle vocabulary". Lane file renamed `X64BASE_AGENT_SKILL_PLDC_LANE_V1.md` -> `X64BASE_AGENT_SKILL_PDLC_LANE_V1.md`. |

| R9 | 2026-08-16 | **Licence is DUAL: GPL-3.0-only, plus commercial terms from the author.** Settled by the owner; retires the "to be defined" placeholder that section 5 listed as blocking P9. Authority: `README.md` "License" section and `LICENSING.md` (<https://x64base.com/licensing/>); `LICENSE` is 34,510 B in `development` and on `main`. GPL-3.0-only covers free, open, educational and non-commercial use; a **commercial licence** is required to embed x64base in a closed-source or proprietary product. **Consequence for the lane, and it is not a formality:** a distributed `.skill` bundle is a derivative distribution, so it inherits GPL-3.0 by default -- and an AI agency embedding it in a proprietary product is *precisely* the case the commercial track exists for. The agency-facing package must therefore state BOTH tracks and point at `LICENSING.md`, never just "GPL-3.0". **Two residuals, tracked here, neither blocking:** (a) the tree carries both `LICENSE` (34,510 B) and `COPYING` (35,149 B) with different content, ambiguous to a licence scanner, and the bundle must name which governs; (b) `README.md` on `main` still reads "License: To be determined" while `development` carries the dual-licence text -- a promotion gap, and `README.md` IS allow-listed (`PROMOTE.manifest:54`), so an ordinary promotion refresh closes it. |
| | | **CORRECTION, same day.** The first version of R9, committed in `ef8ea7899`, read "Licence is GPL-3.0" and was dated 2026-08-07. Both were wrong: the licence is dual, and the date was carried over from an earlier session day without checking the clock. Recorded rather than overwritten, because a ruling that silently changes its own terms is worse than one that shows the correction. |

## 3. Standing disciplines (adopted, enforced per phase)

1. **The skill carries no doctrine of its own.** It is a loader, a trigger
   router, and an environment prober. Every normative sentence lives in the seed
   or behind `recall.py`. A skill is a fourth vendor shim after `CLAUDE.md`,
   `AGENTS.md` and `.github/copilot-instructions.md`, and it is the most
   dangerous one because it loads with full authority and zero retrieval
   friction. `AI_TIER1_SEED_V1.md:155` is binding: *vendor shims point here,
   never restate. Two shims that restate will diverge, and have.*
2. **Generated, not authored.** `SKILL.md` is emitted by a projector and
   verified by a `check` subcommand. A hand-edit fails the gate.
3. **No perishable literal.** The seed's own maintenance contract applies
   unchanged to the projected artifact: invariants and pointers only; no
   versions, counts, lane states, or measurements. If an agent can measure it,
   say "measure it".
4. **No runtime coupling (R3).** The bundle never calls into the tree; the tree
   never imports the bundle. The BBS earns its independence precisely by having
   no pipes. The moment a call appears, this stops being the BBS pattern and
   becomes a dependency.
5. **Truth flows one way.** Registry -> bundle, never bundle -> registry. Same
   rule that forbids website prose becoming manual truth.
6. **Staleness must be measurable, not silent.** `dottalkpp` and `dottalk_bbsd`
   load identity from DBF at startup, so changes need a restart to be seen. A
   bundle is a build-time snapshot and goes stale the same way. The provenance
   manifest naming the source commit is what makes that a known snapshot rather
   than a lie. Pattern precedent: `out/artifacts/site-release.json`.
7. **`consumes:` / `searched-and-absent:` on every component.** No third value.
   No wheel reinvention; a named, verified gap is the only license for new
   machinery.
8. **ASCII only, no em-dashes**, verified by `grep -P '[^\x00-\x7F]'` before
   delivery. Cross-platform Python 3 + stdlib for all tooling; a `.ps1` or `.sh`
   only ever as a thin wrapper.
9. **Test the tool; do not merely write it.** Purpose-built throwaway fixtures,
   including the cases that must FAIL. Precedent from this session: the
   `ascii_normalize.py` prototype crashed on fixture one
   (`Path.read_text(newline=...)` is 3.13+, host targets 3.12) and on fixture
   two fused an element-of expression into `xinS`, because an alphabetic
   replacement needs spacing that a symbol replacement does not. Both would
   have shipped silently.
10. **Assume the defect shape is present.** The most common defect here is a
    thing that reports success without doing its job. Assert on the content of
    the projection, never on exit code 0.

## 4. Phase register (P-phases with G-gates)

| Phase | Content | Gate |
| --- | --- | --- |
| **P0** | **DONE 2026-08-06.** Two outside-runner cold probes, control vs skill stub, plus static reachability measurement. Evidence: `X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md`. | **G0 NO-GO RECOMMENDED.** Both arms reached Tier 1 and answered 5/5; both read ~48 KB; no material saving. Premise falsified. Owner ruling required -- no self-approval by the author. |
| **P1** | Registry substrate. Author `labtalk/registries/skills.yaml` on the `labs.yaml` / `proofs.yaml` shape. Define the skill asset class and its fields. | **G1** registry validates; `recall.py --validate` still PASSes. |
| **P2** | Projector. `tools/ai_portal/emit_skill.py` with `emit` / `install` / `check`. Derives trigger table, pointer table and stopping rule verbatim from the registry and seed. | **G2** fixture suite passes, including the must-fail cases: dangling edge, seed over budget, hand-edited `SKILL.md`, non-ASCII byte. |
| **P3** | Canonical skill. `labtalk/skills/x64base/` authored; `SKILL.md` + references emitted. | **G3** ASCII clean; no perishable literal; body within budget; a cold agent can answer the seed's five questions from it alone. |
| **P4** | Orthogonal bundle (R3). Standalone `.skill` package: vendored Tier-1 snapshot, trigger index, branch-enumeration rule, `EXTERNAL_AI_CHANGE_PACKAGE_V1` protocol, provenance manifest naming the source commit. | **G4** bundle usable with NO tree present; provenance manifest verifies against the commit it claims. |
| **P5** | Tree-side inspection. The `BBS BOARDS` analogue: `recall.py --skills` or equivalent reports which skills exist, what commit they were cut from, how far the bundle trails the seed. No coupling. | **G5** inspection reads only the registry substrate; falsification test confirms the bundle still works with the tree absent, and vice versa. |
| **P6** | Gate wiring (R4). `emit_skill.py check` into `prepush_gate.py`, advisory for one cycle. `SKILL.md` added to `check_mandatory_tracked.py`. `recall.py --validate` asserts every trigger appears in the projection. | **G6** advisory cycle observed, then promoted to hard-fail. |
| **P7** | Trigger-description evals. 15-25 prompts spanning true positives and true negatives; measure trigger rate; iterate the description only. Use the `skill-creator` eval path. | **G7** trigger rate RECORDED AS A NUMBER, not an impression. A skill that fires 60 percent of the time is a 60 percent skill. |
| **P8** | Shim collapse. `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md` become generated projections of one canonical body. | **G8** all three regenerate identically from `emit_skill.py install`; hand-edit fails. |
| **P9** | PDLC ascent. Audience documentation, setup, support path, retirement policy, LabTalk registration, website promotion. | **G9** package delivery checklist; SDLC evidence beneath every claim. |

## 5. Open rulings, placed where they block

| Blocks | Question |
| --- | --- |
| P4 | Does the distributable bundle ship from `deraldg/x64base` or `deraldg/labtalk`? Governance assigns campus/portal/teaching overlays to `labtalk`, which argues for the latter; the skill's subject is the x64base repo, which argues for the former. |
| P6 | Are vendor projections under `.claude/skills/` committed (R5 accepts the target) or regenerated per clone the way pre-commit hooks already are? R5 settles admissibility, not tracking. |
| ~~P9~~ | ~~Licensing for a distributed package. Repo licence is currently "to be defined"; a package handed to an outside agency needs an answer.~~ **SETTLED by R9 (2026-08-16): dual, GPL-3.0-only plus commercial.** Struck rather than deleted, so the ledger shows the question was asked and answered. Two residuals tracked under R9, neither blocking: the `LICENSE`/`COPYING` ambiguity, and `main`'s `README.md` still saying "To be determined". |

## 6. Registration state

| Artifact | State |
| --- | --- |
| `coordination/aif/AIF-090.claim` | written, atomic, `COWORK-20260806-001` |
| Intake row AIF-090 | **owed** -- must be added to `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` with or before this charter |
| `labtalk/registries/skills.yaml` | absent; P1 creates it |
| `labtalk/registries/ai_portal.yaml` | update owed at first material increment |
| This charter | authored, uncommitted at time of writing |

## 7. Provenance

Authored by `member.ai.claude.cowork` in a mounted Linux sandbox, read-only git
only. The agent cannot build, cannot run the engine, and hands every mutating git
to the maintainer. Owner rulings R1-R6 were given conversationally on 2026-08-06
and are recorded here because the chat is never the record.

Prior art consumed, not reinvented:

```
consumes: labtalk/ai_portal/AI_TIER1_SEED_V1.md          (the body being projected)
consumes: labtalk/ai_portal/recall.py                    (trigger routing, stdlib-only)
consumes: labtalk/registries/portal_recall_graph.yaml    (10 triggers, 31 nodes, 44 edges)
consumes: labtalk/ai_portal/generate_tier0_state.py      (generated state)
consumes: tools/staging/prepush_gate.py                  (gate host)
consumes: tools/staging/check_house_style.py             (ASCII enforcement)
consumes: labtalk/ai_portal/check_mandatory_tracked.py   (tracked-set enforcement)
consumes: scripts/publish-github-pages.mjs               (provenance-manifest pattern)
searched-and-absent: a skill projector or vendor-shim generator of any kind
searched-and-absent: labtalk/registries/skills.yaml
searched-and-absent: any `.claude/skills/` directory in this tree
```

## 8. Deferred, not cancelled

- **Engine / DotScript operator skill.** Command families, DotScript control
  flow, `SET ALTERNATE` capture (never `DOTSCRIPT ... OUT`; measured 89 lines
  vs 42), DBF/CDX/CNX/LMDB and x64-memo distinctions. Built after this lane so
  it reuses the projector rather than inventing a second one.
- **Website-maintenance skill.** Page classification matrix, direction gates,
  the four `command_catalog_sync.py` drift checks, the `publish:github-pages`
  cycle. Smallest and most mechanical of the three.
- **Plugin bundle.** Packaging step once two or three skills share a projector,
  not a design step.

## 9. P0 result -- the premise did not survive (2026-08-06)

Evidence tier: **runtime-observed** (two cold probes run; every figure re-derived
independently from the tree). Full report:
`docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md`.

The charter argued that cold agents do not reach Tier 1 without a skill. Two
cold outside runners both reached it and both answered the seed's five
questions; the control was never told the seed existed and found it anyway,
because `CLAUDE.md` is auto-injected and points there. Neither arm read less
than the other (~48 KB each).

Four defects were exposed and they outlive the lane:

| # | Defect | Evidence |
| --- | --- | --- |
| D1 | `recall.py` is cited by **zero** entry-path documents. The control probe searched for orientation tooling, found six other tools, and missed this one. | `grep -c` = 0 across all nine entry-path files |
| D2 | `ENTRY_PATH_BASELINE = 127704` (`recall.py:40`) is a stale hardcoded denominator. The path actually in force is Tier 0 + Tier 1 = 10,909 B, so a 27,384 B working set is **2.51x LARGER** than what it claims to replace, printed as "21%". The bound at `:289` that exists so the metric can fail therefore **cannot fire**. | measured; second occurrence of the same defect shape in the same file |
| D3 | The graph returns `## Pre-Push Gate`, whose prose points at `PREPUSH_GATE_REFERENCE_V1.md` -- which is not in the graph. Nor is `AI_SESSION_COORDINATION_PROTOCOL_V1.md`. Pointer without target. | `grep -c` = 0 for both |
| D4 | `AI_TIER1_SEED_V1.md` is **8,990 B against its own declared 8,192 B hard ceiling**, and no gate enforces it. `AI_PORTAL.md` cites this ceiling as its exemplar of a bounded metric. | measured; only `8192` hits in `tools/` are read buffers |

**Recommended conversion:** retire the projector/bundle/shim-collapse programme
as premature and open a small repair lane for D1-D4, cheapest first (D2, D4, D1,
D3). What genuinely survives and must be re-argued rather than assumed: the
distributable no-tree bundle (R3's design is sound but untested by this
measurement) and the vendor-shim asymmetry (`copilot-instructions.md` does not
point at the seed).

**Not tested at the time, and the one place the original argument may still
hold:** a hosted agent with no tree and no auto-injected shim. Both probes
received `CLAUDE.md` automatically, which is precisely why the control
succeeded. **This was tested later the same day -- see section 9a, and the answer
changes the ruling for that audience.**

## 9a. Probe C, the no-tree case -- G0 is audience-specific (2026-08-06)

Evidence: `docs/maintenance/external_ai_intake/aif090_cold_probes_2026-08-06/PROBE_C_NO_TREE.md`.

**Method limit, recorded first because it bounds everything else.** The harness
auto-injects `CLAUDE.md` into every subagent. The probe detected this itself and
disclosed it unprompted, refusing to claim a clean-room result. So a clean
no-tree probe **cannot be run in this harness**, and the bundle-carrying arm was
designed and deliberately NOT run rather than publish a comparison that could not
mean anything.

**The finding that survives, because it is structural rather than behavioural.**
Verified directly against `raw.githubusercontent.com`, no probe required:

| Question an outside contributor must answer | From `main` | From `development` |
| --- | --- | --- |
| Which branch do I baseline on? | **nothing on `main` answers this.** `CONTRIBUTING.md` is silent on baselining; it says `main` is "the canonical collaboration and release branch", which is a statement about where a claim becomes current. The reader falls back on `AI_README.md` @ `main`, below. | `development`; baselining on `main` is "a hard onboarding failure (observed 2026-08)" |
| Is `development` published? | "must be discovered locally" | yes, on GitHub, and richer |
| What is `C:\x64base`? | "clean staging mirror" | NOT a mirror; that wording is declared stale drift |
| Repository roles table | absent | first thing in the file |

`AI_PORTAL.md` is 24,693 B on `main` against 53,350 B on `development`;
`AGENTS.md`, `CLAUDE.md`, `PROMOTION_PROCESS.md`, `rules/` and `coordination/`
are absent from `main` entirely.

**An outside agent that follows the only instructions it can see commits the
failure this project records as hard, and the correction lives exclusively on the
branch it was told it cannot reach.** The probe navigated it anyway, but two of
its five branch-enumeration calls returned empty bodies and it said plainly that
had they kept failing it "would have been left with `main` by default and no
signal that it was a choice at all".

**CORRECTION, 2026-08-06, same day: this section originally overstated its
evidence.** It quoted `CONTRIBUTING.md`'s "canonical collaboration and release
branch" in a table row headed "which branch do I baseline on", attributing to
that file an answer it does not give. `CONTRIBUTING.md` is **silent** on
baselining; its sentence is about where a public claim becomes current, and its
"Before opening a change" list says "build from a clean checkout" without naming
a branch. The probe itself flagged this in its own guess list -- "No document I
read says in one place 'outside contributors, base on `main`'" -- and the
overstatement was written anyway.

The corrected finding is narrower and sharper. The defect is **silence plus one
wrong sentence**, and the wrong sentence is in `AI_README.md` @ `main`: "public
branch: main" and "The development branch is current workspace state and must be
discovered locally", when `development` is in fact published on GitHub. That one
file is the load-bearing defect, not `CONTRIBUTING.md`.

A second tension is real and separate: `AI_README.md` @ `development` says
baseline on `development`, while `AGENTS.md` says never merge `development` to
`main`. `PROMOTION_PROCESS.md` resolves it ("open PRs against `main`") and is
also `development`-only, so an outside contributor sees neither the instruction
nor its resolution.

**Ruling consequence.** G0 stands as NO-GO for the repo-partner audience: an
agent inside the tree with an injected shim reaches Tier 1 unaided, measured
twice. G0 does NOT stand for the audience the project brief actually named --
external AI agencies -- whose problem is not retrieval friction but that the
governance they will be judged against is unpublished where they can read it.

**And the cheapest fix is not a skill.** It is publishing the branch-enumeration
rule and the repository-roles table on `main`, where `CONTRIBUTING.md` already
sends people. A distributable bundle is the second step, not the first. Recorded
here so the next session does not reach for the bigger tool because this lane was
once about one.

### The fix, authored 2026-08-06 -- and why it went to `CONTRIBUTING.md`

**Stage: dev changed. NOT promoted. NOT published.** Outside contributors still
see the old file on `main` until a promotion runs from `C:\x64base`. This entry
does not claim otherwise.

The obvious target was `AI_README.md`, and it is the wrong one.
`PROMOTE.manifest:190` lists `AI_PORTAL.md` and `AI_README.md` under **NOT
PUBLISHED -- stays in development**, with the instruction: *"If any are
currently tracked in main, purge them (`git rm --cached`) -- they came from
history, not from this list."* Their copies on `main` are orphans of history
that the promotion path deliberately excludes, so they can never be updated
from `development`. **Correcting the false sentence in the `development` copy
would have changed nothing an outsider can see.** That is why the defect
persisted: the file carrying it is unreachable by the mechanism that would fix
it.

`CONTRIBUTING.md` is at `PROMOTE.manifest:59` -- allow-listed, already
promoting, and the file GitHub surfaces to every contributor. It also **had no
source in `development` at all**: it existed only on `main`, authored nowhere,
maintainable by no one. Same failure class as `WORKFLOW_X64BASE.md` (present in
staging, no dev counterpart, classified GONE by `PROMOTION_PROCESS.md`).

So the fix was to give it a source of truth. Every sentence of main's copy was
preserved verbatim and verified string by string; what was added is what an
outsider previously could not learn: enumerate branches with
`git ls-remote --heads`; `main` is the lagging snapshot; **read from
`development`, open the PR against `main`**, and never propose merging one into
the other; the repository-roles table; and the AI-contributor expectations
(report-only default, exact-path staging, evidence tiers, ASCII, the `&&`
marker).

It also carries a tiebreaker clause, which is a deliberate authority claim and
should be reviewed as one:

> Where any document on `main` disagrees with this file about branches, roles,
> or process, **this file is current**.

That resolves the stale `AI_README.md` and `WORKFLOW_X64BASE.md` on `main`
without either file being touched -- which matters, because neither can be.

**How this reaches `main`, and what NOT to do.** `CONTRIBUTING.md` is
manifest-matched, so it needs no special handling: the next staging rebuild
carries it. `tools/staging/rebuild-staging.ps1` regenerates `C:\x64base` from a
clean clone of `github/main` at a verified baseline, overlays every
`PROMOTE.manifest` match with `.gitignore` as a hard deny guard, and then the
maintainer reviews the diff, commits, and pushes.

**Staging is a build output and is never hand-edited.** It is a source of truth
in exactly one window: freshly synchronized from `development` and staged for
commit and push. Regenerating rather than editing is what keeps it free of dirty
trees. An earlier revision of this section advised running
`git rm --cached AI_PORTAL.md AI_README.md` there by hand; that was wrong --
it is authoring in staging, it manufactures the dirty state the rebuild design
exists to prevent, and the maintainer corrected it (2026-08-06).

**Open, and the owner's alone:** `AI_PORTAL.md` and `AI_README.md` are present
on `main` from history and are NOT manifest-matched, so a rebuild neither
updates nor removes them -- they survive from the baseline clone. Whether to
reconcile that history is a publication decision, taken inside the
rebuild-review-commit window, not by a hand-run command and not by an agent.
Until it is taken, `CONTRIBUTING.md`'s tiebreaker clause is what keeps them from
misleading an outside contributor.

**Second, smaller finding:** `WORKFLOW_X64BASE.md` on `main` calls `C:\x64base`
"a mirror only" while `AI_PORTAL.md`, same branch same commit, declares that
wording stale. The public branch ships two contradictory statements of
repository roles. Known on `development` (`PROMOTION_PROCESS.md` lists retiring
it as an open item); invisible from `main`.

## 10. Repair phase -- D1-D4 implemented (2026-08-06, owner ruling R7)

Evidence tier: **runtime-proven.** Every claim below was produced by running the
thing, and every gate was seen to FAIL on a known-bad input before its green was
trusted (`AI_PORTAL.md`, "a checker is unproven until you have seen it FAIL").

| # | Fix | Evidence |
| --- | --- | --- |
| **D2** | `ENTRY_PATH_BASELINE = 127704` **deleted**. The denominator is now DERIVED at run time from the graph itself -- the corpus a reader would otherwise face is exactly the node set the graph indexes -- so it tracks the graph and there is nothing left to update by hand. The entry path in force is declared as DATA in `portal_recall_graph.yaml` (`entry_path:`) and measured, reported as a second scale figure, never the headline. | Bound proven able to fire: a fixture graph whose single trigger reaches every node produced `100% of corpus`, the WARNING, and **exit 2**. On the real graph `commit_or_push` now prints "29% of the 150907 B corpus this graph indexes" plus "the entry path in force is 10060 B; this working set is 4.4x LARGER" -- the fact the old wording hid. |
| **D4** | New gate `tools/staging/check_seed_budget.py`. It **hardcodes no number**: it parses the `budget` line from the document's own header, so the rule travels with the document and any future budgeted file is covered without a code change. Measures **bytes, not characters**, because a byte budget measured in characters silently grants extra room -- a denominator error, the failure class recorded three times in AIF-082. | 5/5 fixtures: FAILs the real seed at 8,990 B (exit 2); `--warn` never blocks; PASSes an under-budget file; SKIPs a file declaring no budget; refuses to let multi-byte content buy headroom. |
| **D1** | `recall.py` is now reachable from the seed -- the one document every entry path leads to. Paying for it required demoting the **maintenance contract** out of the seed into `labtalk/ai_portal/TIER1_MAINTENANCE_CONTRACT_V1.md`, MOVED verbatim, not restated, which is the contract's own prescribed procedure applied to itself. | Seed **8,990 -> 8,148 B**, 44 B headroom, `check_seed_budget.py` PASS. Five questions, repository-role table, git rules and comment marker all verified intact. |
| **D3** | `PREPUSH_GATE_REFERENCE_V1.md` and `AI_SESSION_COORDINATION_PROTOCOL_V1.md` added as nodes with edges. Both were named in prose *inside nodes the graph already returned*, so a routed reader got a pointer the resolver could not assemble and fell back to linear reading -- the exact behaviour the resolver exists to remove. | Graph 31 -> 33 nodes, 44 -> 46 edges, `--validate` PASS, no dangling edges, every node reachable. `commit_or_push` now returns the mechanism doc. |

**An honest consequence worth recording.** Fixing D3 made the reported working
set *larger* (27,384 -> 44,260 B). The old number was smaller because the graph
was incomplete, and the old percentage was flattering because its denominator
was frozen. Both numbers moved toward the truth and the truth is less impressive
than the claim it replaced. `onboard` now reports 3.7x the entry path and
`commit_or_push` 4.4x -- so the graph really is over-linking, which is what the
repaired bound is for. That is the next measurement, not a regression.

**What was retired unbuilt:** the projector (`emit_skill.py`), the distributable
bundle, `labtalk/skills/`, `skills.yaml`, and the shim collapse. R2 and R3 remain
sound design and are recorded for whoever revisits the distributable case, which
P0 never tested.

### Gate wiring (2026-08-06) -- and a correction to my own plan

`check_seed_budget.py` is wired into `prepush_gate.py` as check 5, invoked with
`--warn` so the adoption cycle cannot block anyone (R4).

**FLIP CONDITION, so the advisory cycle is not forgotten:** after one clean cycle
in which no commit trips the advisory, drop the `--warn` argument and treat
`rc == 2` as `exit_code = 2`, matching checks 1-3. Both halves are proven:
advisory returns 0 on a deliberately over-budget seed (8,350 B), and the same
run in hard mode returns 2. Until the flip, D4's own lesson applies to D4 -- an
unenforced obligation is a wish.

**`ascii_normalize.py` was NOT wired, and should not be.** I had planned to, and
that plan was wrong: it is a FIXER, not a checker. In dry-run it returns 0
whether or not a file carries non-ASCII, failing only on an *unmapped* codepoint,
so wiring it as a gate would add a check that passes on exactly the condition the
gate exists to catch -- a thing that reports success without doing its job, which
is the defect class this whole lane is about. The gate for non-ASCII already
exists and already blocks: `check_house_style.py`.

What was actually missing is that the gate said a file FAILS without saying a
fixer exists. `check_house_style.py`'s failure message now names it, shows the
three invocations, and warns about the trap that made this matter -- staging a
previously untracked file makes every line an added line, so the whole file must
be clean, not just the edit. Proven by forcing the FAIL branch: exit 2, message
names the fixer, `--apply`, and the untracked trap.

## 11. Maintenance rule for this file

This file carries **phase state, rulings, and pointers**. It must not restate
what a pointed-to document says. A milestone entry changes only when its
evidence tier changes; `planned`, `source-evidenced` and `runtime-proven` are
the tiers, and "landed" is not one of them.
