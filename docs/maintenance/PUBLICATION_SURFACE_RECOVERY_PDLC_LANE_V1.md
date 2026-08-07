---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260807-001
  recorded_at_utc: 2026-08-07T16:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer
    scope: >
      Owner directed recovery of orphaned public documents and asked whether
      MANIFEST.txt could be derived from the source-code databases, then ruled
      "gold unless the cost is platinum" and instructed a new AIF be claimed.
  git:
    branch: development
    baseline_commit: d083e6ea4
  report:
    path: docs/maintenance/PUBLICATION_SURFACE_RECOVERY_PDLC_LANE_V1.md
    kind: lane_charter
---

# Publication Surface Recovery -- PDLC Charter V1

**Status:** `active` -- five documents recovered, one derived, four items open.
**Intake:** AIF-092 - **Claim:** `coordination/aif/AIF-092.claim` - **Run:** `COWORK-20260807-003`
**Owner:** member.derald
**Steward/author:** member.ai.claude.cowork, until reassigned by the owner.
**Parent projects:** `project.x64base.public_staging` (the SUBJECT -- the surface
this lane is about), `project.x64base.runtime` (the WORKSPACE -- where every
change is authored). The envelope's `project.root` must name the **workspace**,
never the subject; see section 6b.
**Baseline:** `development` @ `d083e6ea4`
**Origin:** discovered by AIF-090 probe C; that lane is about agent onboarding
and closed NO-GO. This is about the public face of the repository, which is what
the finding actually produced.

---

## 1. Lane identity and lifecycle placement

**PDLC.** The subject is a delivery surface -- what package an outside
contributor receives and is judged against. Per
`SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`, PDLC governs "product, lab, lesson,
workshop, dashboard, manual, or **public page**". No engine behavior changes
here, so nothing in this lane may claim runtime evidence.

**REGISTRATION IS LATE AND THAT IS RECORDED.** The coordination protocol says
register a lane *before or with* the work. Here the recovery was performed
first, at the owner's direction, and AIF-092 was claimed afterward. The work is
docs-only and reversible, so the cost was low, but the sequence was wrong and is
noted rather than tidied away.

## 2. The defect this lane exists to close

`PROMOTE.manifest` is an allow-list: a file publishes to `main` only if a
pattern matches it. **A pattern can match nothing.** When it does, the file
exists on `main` from history, is allow-listed, has no source in `development`,
and can therefore never be updated -- while `PROMOTION_PROCESS.md` section 8
forbids the only other route ("no change is hand-edited in both `development`
and `main`").

`PROMOTION_PROCESS.md:112` already names the condition **GONE** and already
prescribes both remedies: keep it in the manifest preserve set, **or pull it
back into development so it is not orphaned.** The doctrine was correct and
unexecuted. This lane executes it.

Measured 2026-08-06, of the nine allow-listed root documents: **five were
orphaned.**

## 3. Rulings ledger

| # | Date | Ruling |
| --- | --- | --- |
| R1 | 2026-08-07 | **Pull orphans back into `development`** rather than adding them to a preserve set. A file with a source can be corrected; a preserved orphan cannot. |
| R2 | 2026-08-07 | **`MANIFEST.txt` is DERIVED, not authored.** Owner asked whether it could be derived or merely reported; answer is both, from one tool. "Gold unless the cost is platinum" -- per-file checksums verified during the C: build are platinum and deferred. |
| R3 | 2026-08-07 | **Never touch `C:\x64base` without instruction.** It is a build output, regenerated from a clean `main` clone plus the manifest overlay, and is a source of truth in exactly one window: freshly synchronized, staged for commit and push. A final build runs there before publishing. Regenerating rather than editing is what keeps it free of dirty trees. |
| R4 | 2026-08-07 | **`WORKFLOW_X64BASE.md` is RETIRED, not sourced.** Owner ruling. It is not in `PROMOTE.manifest` at all, has no `development` source, and `PROMOTION_PROCESS.md:3-5` already declares it superseded ("describes a now-retired intermediate tree ... and an outdated `C:\x64base is a mirror only` role. Reconcile or delete that file"). Sourcing it would resurrect a document the process doc calls dead. The outsider-facing need it partly served is now met by `CONTRIBUTING.md`, which IS allow-listed and current. Removal from `main` is a publication action taken inside the rebuild-review-commit window; it is not scripted here. |
| R5 | 2026-08-07 | **Both new gates flipped to HARD** (`check_seed_budget.py`, `check_aif_claimed.py`) after their advisory cycles. See section 6c. |

## 4. Done, with evidence

| Item | State |
| --- | --- |
| `CONTRIBUTING.md` | **new D: source.** Every sentence of main's copy preserved, verified string by string. Adds branch baselining (enumerate; read from `development`, PR against `main`), the roles table, AI-contributor expectations, and a tiebreaker clause making it current where `main` documents disagree. `c686f0219` |
| `SECURITY.md` | new D: source, verbatim from `main` |
| `CODE_OF_CONDUCT.md` | new D: source, verbatim from `main` |
| `RELEASE_NOTES.md` | new D: source; one em-dash to `--` per house rule, otherwise verbatim |
| `CHANGELOG.md` | new D: source, verbatim plus one Added bullet recording the `CONTRIBUTING.md` branch guidance |
| `MANIFEST.txt` | **derived**, not authored. `tools/staging/generate_public_manifest.py` emits provenance (branch, source commit, generation time), inventory (80 patterns, 828 files, 0 empty), and surface counts read live from `SYSCMD`/`SYSFUNC`/`SYSARGS`/`SYSHELP`/`SYSENTVAR`/`SYSFLDDIC`. `d083e6ea4` |

**Why the receipt matters:** nothing on `main` previously answered "what am I
looking at, and how stale is it?" A cold outside agent measured exactly that gap
on 2026-08-06 and had to guess. `README.md` describes the project and
`RELEASE_NOTES.md` lists release contents; neither states the provenance of the
snapshot in front of the reader.

**Reuse, not reinvention:** the generator reads DBFs through
`tools/fullstack_docs/dbfread.py` rather than opening them a second way.

    consumes: tools/fullstack_docs/dbfread.py       (stdlib-only DBF reader)
    consumes: PROMOTE.manifest                      (allow-list, parsed not restated)
    consumes: dottalkpp/data/metadata/SYS*.dbf      (surface counts, measured)
    searched-and-absent: any existing manifest generator or publication receipt

## 5. Three defects the generator caught in itself before shipping

Recorded because each is the defect class this project names above all others --
a thing that reports success without doing its job -- and all three were produced
while building a tool meant to prevent exactly that.

1. **A silent-fallback zero.** The first DBF probe used
   `hasattr(t, "records")` with an `else []`, so a missing attribute printed
   `rows=0` identically to an empty table. `SYSCMD.dbf` is 53 KB and has 212
   rows. The correct attribute is `rows`, with `header_rows`, `deleted`,
   `phantoms` and `live` alongside.
2. **A generated artifact that was not a fixed point of its own generator.**
   `MANIFEST.txt` is allow-listed, so writing it changed the file count it
   reports; `--check` failed immediately after `--write` and only converged on a
   second run. Fixed by excluding the receipt from its own inventory. Caught by
   a write-then-check fixture, which is why that is a fixture and not an
   assumption.
3. **A phantom defect rate, nearly published.** `Path.glob("a/**")` yields
   DIRECTORIES, not files, so every recursive manifest pattern matched nothing
   and the tool was about to report **29 of 80 allow-list patterns broken.**
   They were not: `dottalkpp/data/dbf/x64` alone holds 46 files. Caught by
   checking a suspicious number against the filesystem before publishing it.
   The corrected figure is 828 files, 0 empty patterns.

## 6. Open

| # | Item | Note |
| --- | --- | --- |
| O-1 | `WORKFLOW_X64BASE.md` | **RULED: RETIRE** (R4, 2026-08-07). Evidence and reasoning in section 6c. Removal from `main` happens in the rebuild-review-commit window; nothing is owed on D:. |
| O-2 | `MANIFEST.txt text eol=lf` in `.gitattributes` | The generator writes LF; `.txt` is deliberately `text=auto`, so git stores CRLF and the generated file shows perpetually modified. `CMakeLists.txt` already uses this remedy at `.gitattributes:44`. A tree-wide governance file, so not changed unasked. |
| O-3 | Wire `generate_public_manifest.py --check` | **DONE 2026-08-07, and the trigger I originally proposed was wrong.** Wired as pre-push check 7, HARD, but conditional: it runs ONLY when `MANIFEST.txt` is itself in the change set. The receipt reports 828 allow-listed files, a figure that moves whenever any one of them is added or removed, so an unconditional check would be red most days -- and a permanently red gate is switched off. The receipt is a promotion-time artifact; between promotions it is EXPECTED to trail the tree, and that lag is the information it publishes. The narrow question worth blocking is: if you are committing the receipt, is it derived rather than stale or hand-edited? Precedent for the conditional shape is the normalization guard directly above it, which runs only when the change set touches its surface. |
| O-4 | Regenerate the receipt at promotion time | So its provenance names the commit actually being published, not whenever it was last run by hand. This is a step in the staging rebuild sequence and is the owner's to place. |
| O-5 | Flip `check_aif_claimed.py` to hard | Wired advisory (`--warn`) as pre-push check 6. After one clean cycle, drop `--warn` and treat `rc == 2` as blocking, matching checks 1-3. Both halves proven: the synthetic unclaimed row returns 2, `--warn` returns 0 on the same input. |

## 6a. The allocator had no teeth (2026-08-07)

Owner asked whether the allocator was baked into the workflow. Measured, it was
half in:

| Half | Tool | Status |
| --- | --- | --- |
| ALLOCATOR | `session_coordinator.py claim-aif` -- atomic `O_EXCL` | correct, and entirely **optional** |
| DETECTOR | `aif_collision_gate.py` -- hard-fails a duplicate | correct, and fires only **after** two lanes collide |

Nothing forced a lane through the allocator. A number chosen by eye satisfied the
duplicate check right up until someone else chose the same one. **25 claim files
against 89 intake rows**, and `claim-aif` is absent from `AGENTS.md`,
`.github/copilot-instructions.md` and `AI_PORTAL.md` -- so a Codex or Copilot
session gets no pointer to it from its own shim.

**Closed from the front** by `tools/coordination/check_aif_claimed.py`: a row
that ENTERS the queue must name a number the allocator issued. Added rows only,
because 65 rows predate coordination and a gate that failed on those would be
switched off within a day -- the same reasoning that makes `check_house_style.py`
check added lines and the same reason it has survived.

**Deliberately NOT hardened with prose.** The obvious second move was a
`claim-aif` line in `AGENTS.md`. That is the wrong instinct: the Tier-1
maintenance contract says a rule that gains a hard-failing gate **demotes out**
of the entry path, because the gate is now the memory. Adding a shim paragraph is
what you do when you cannot gate something. This one is gated.

**Fixtures, including a false pass that was caught.** The first positive test
reported "no new intake rows in scope" and was recorded as a PASS -- but the
AIF-092 row was unstaged, so `diff --cached` had seen nothing. A pass that means
"I looked at nothing" is the same silent-zero shape this lane already recorded
twice. Re-tested against `e9d2033d3~1..e9d2033d3`, the commit that really did add
the AIF-090 row: it detected the row and named it. Also verified that a passing
prose mention of an AIF number is not mistaken for a row.

## 6b. SUBJECT is not WORKSPACE (2026-08-07, caught by the gate)

The first closeout for this lane was **BLOCKED** by the report-audit:

    ai_report_audit.project.root: does not match project registry root: C:/x64base

The envelope declared `project.x64base.public_staging` -- registered root
`C:/x64base` -- while stating `root: D:/code/ccode`. The lane is *about* the
publication surface, so naming that project felt right; but
`ai_report_audit.project` records **where the work was authored**, not what it
concerns. Every change in this lane was made in `D:/code/ccode`, which is
`project.x64base.runtime`.

Corrected in both the closeout and this charter. `enforced=91 valid=91
findings=0` after the fix.

**Worth keeping because the confusion is structural, not careless.** A lane whose
subject is one tree and whose workspace is another invites exactly this slip, and
the slip is indistinguishable from the far more dangerous claim that work was
done in staging. The registry caught it because roots are declared data rather
than prose -- the same reason the AIF ledger catches number collisions.

The rule, stated once: **subject may be any project; `project.root` is always the
tree your hands were in.**

## 6c. Gates armed, and one ruling closed (2026-08-07)

**Both new gates are now HARD** in `prepush_gate.py`.
`check_seed_budget.py` survived 12 clean commits; `check_aif_claimed.py` 2.

**The short advisory cycle earned its keep.** Before arming
`check_aif_claimed.py` its precondition was tested, and it FAILED: a MODIFIED
legacy row surfaces in `git diff` as a `+` line exactly like a new one, so with
65 pre-coordination rows lacking claim files, fixing a typo in the AIF-041 row
returned exit 2. A gate hostile to routine maintenance is a gate switched off
within a week.

Corrected by asking the right question. Not "is this line added" but "is this
NUMBER new to the file" -- answered from the pre-image (HEAD for a staged check,
the range base otherwise). Re-verified in both directions: AIF-090 and AIF-092
still detected as genuine introductions, the AIF-041 edit no longer fires, a
synthetic unclaimed number still returns 2.

**A `+` in a diff means "this line is in the new version", not "this is new."**
That is the sixth instance this lane has recorded of a signal that looked
correct and was not.

### R4 -- `WORKFLOW_X64BASE.md` retired

Ruled by the owner, 2026-08-07. The evidence was unusually clean:

- **Not in `PROMOTE.manifest`** -- not allow-listed, not even in the commentary.
  A pure history orphan on `main`.
- **No `development` source.** Nothing exists to update it from.
- **`PROMOTION_PROCESS.md:3-5` already declares it superseded**, and section 9.1
  already lists retiring it as an open item.

The deciding fact: its superseding document, `PROMOTION_PROCESS.md`, is
`development`-only. So `main` carries the stale document and not its
replacement -- the same asymmetry AIF-090 probe C found for the branch rule, in
a different file. Sourcing it would resurrect a document the process doc calls
dead; retiring it costs nothing in the promotion path because it was never
allow-listed, and `CONTRIBUTING.md` now carries the roles table it partly
served.

**Not scripted here.** Removing a file from `main` is a publication action taken
inside the rebuild-review-commit window (R3).

## 7. Not claimed

No engine build, no runtime execution, no DotScript. Truth state for this lane
is **source-evidenced** throughout. The receipt's counts are measured
registration figures, not proof of behavior: a registered command is
source-evidenced until a runtime proof exists for it.

`CONTRIBUTING.md` and the four recovered documents are **authored on D: and not
yet promoted**. Nothing an outside contributor reads has changed. They reach
`main` when a staging rebuild carries them, which is maintainer-operated.

## 8. Maintenance rule for this file

Phase state, rulings, and pointers. Do not restate what a pointed-to document
says. A row changes when its evidence tier changes; "authored" is not
"promoted", and "promoted" is not "published".
