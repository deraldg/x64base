# Delivery -- Selfdoc <-> Portal schema study + R1 (2026-08-17)

Prepared by member.ai.claude.cowork (AI memory-retention lane, steward) for member.derald.
Nothing here is committed. Read-only-safe: no git was mutated, the engine was not built, and the
only executed code is pure file-parsing tests that run in the sandbox.

## What is in this bundle

1. `docs/maintenance/SELFDOC_PORTAL_SCHEMA_SHARING_STUDY_V1.md` -- the study. Learns both schema
   worlds + the CRUD/reporting surface, finds the one genuine shared concern (provenance/identity),
   the one pair of axes that must not be conflated (visibility vs sensitivity), a ranked set of
   share/normalize opportunities R1-R5, a reverse-flow list (things selfdoc does better), and the
   orthogonality boundary. Credits SYSCHATLNK's design to you.
2. `tools/dbf/schema_registry.py` (edit) -- the R1 change: a SELFDOC catalog block, SYSCMD registered
   read-only, merged into TABLES so `crud.py` and `build_reports.py` see it with no further wiring.
3. `tools/dbf/tests/test_schema_registry_selfdoc.py` (new) -- the drift guard that keeps the selfdoc
   registry DERIVED from the `.dtschema` contract, mirroring the existing header drift guard.
4. `tools/dbf/tests/test_schema_registry.py` (edit) -- taught to skip header-less selfdoc catalogs
   (they are guarded by the new sibling test instead).
5. `docs/maintenance/SELFDOC_R1_DELIVERY_2026-08-17.md` -- this handoff.
6. `docs/glossary/glossary_master_v0.csv` (edit) -- adds two canonical terms the work leaned on but
   the global glossary lacked: **Contract** (a reviewed schema/interface/behavior spec plus its proof
   state) and **Identity system** (the single security/user system: SYSUSER + SYSMEMBER + RBAC). Both
   `GREEN_TENTATIVE`, review-needed. The study's Section 8 conformance checklist maps every system to
   the Identity system.

## Why SYSCMD first (and what it proves)

R1 is a mechanism, not a table count: register a selfdoc catalog as data, keep it honest against its
contract, and it inherits read + soft-close CRUD + reporting for free. SYSCMD proves the whole
mechanism end to end AND passes every pre-existing house invariant unchanged, so R1 lands green with
the smallest possible blast radius.

SYSCMD is registered `writable=False`. That is the orthogonality boundary made literal: selfdoc is a
pipeline-owned projection, so the CRUD reads and reports it but refuses writes -- the same posture the
CRUD already takes toward the daemon-owned BBS store. Compatible (one registry, one identity space, one
lifecycle grammar); still orthogonal (no second writer).

## The honest catch this surfaced (evidence, not assertion)

The second catalog, SYSMSG, cannot register cleanly yet: it carries `VER_AT C(24)`, and the house
invariant `test_id_and_epoch_widths` requires any `*AT` field to be `N(20)`. That is study finding R5
(selfdoc's `VER_AT` display string vs the portal's `N(20)` epoch stamps) turning up as a failing test
rather than a claim. It is a decision for you: either adopt the `N(20)` epoch on selfdoc, or exempt
selfdoc's display stamp from the invariant. The remaining catalogs (HELP_*_LOCALE, the messaging pair,
and the seed-only SYSFUNC/SYSSUBCMD/SYSARGS/SYSHELP, which need a `.dtschema` authored first) are
queued behind that call. This is deliberately left as a decision, not pre-empted.

## Verification evidence (run in the sandbox, no engine)

    $ python3 tools/dbf/tests/test_schema_registry.py
    test_schema_registry: 133 passed, 0 failed          # was 130/0 before R1

    $ python3 tools/dbf/tests/test_schema_registry_selfdoc.py
    test_schema_registry_selfdoc: 5 passed, 0 failed

    # SYSCMD is now visible to the registry, read-only:
    SYSCMD subdir='' writable=False close=status pk=CMD_ID key=CAN_NAME
    readonly set: ['SYSBOARD', 'SYSCMD', 'SYSPOST', 'SYSTHREAD']

    # the new guard actually bites (matches the real .dtschema, rejects drift):
    matches real registry tuple : True
    matches DRIFTED tuple (want False): False

## Scoped commit (yours to run on the Windows host)

Per AIF-050: scoped per-path adds, never `git add -A`; `git status --short` between add and commit;
the pre-push gate runs on commit. Suggested as two logical commits (study, then code), but they can be
one if you prefer.

    git add docs/maintenance/SELFDOC_PORTAL_SCHEMA_SHARING_STUDY_V1.md ^
            docs/maintenance/SELFDOC_R1_DELIVERY_2026-08-17.md ^
            docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md
    git status --short
    git commit -m "docs(AIF-086): selfdoc<->portal schema sharing study + R1 delivery note + intake row"

    git add tools/dbf/schema_registry.py ^
            tools/dbf/tests/test_schema_registry.py ^
            tools/dbf/tests/test_schema_registry_selfdoc.py
    git status --short
    git commit -m "dbf(AIF-086): R1 -- register SYSCMD selfdoc catalog read-only + .dtschema drift guard"

    git add docs/glossary/glossary_master_v0.csv
    git status --short
    git commit -m "glossary: add canonical terms Contract and Identity system (review-needed)"

Before committing, re-run both tests on the host (`.venv312` or system python; pure file parse, no
engine) to reconfirm green in your tree.

## AIF placement

Filed under **AIF-086** (per the maintainer). No new lane number: this R1 extends the existing
AIF-086 CRUD `schema_registry` lane. The AIF-086 intake-queue row
(`docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`) is updated to list these artifacts and record
the R1 extension; the immutable `coordination/aif/AIF-086.claim` allocation stamp is left untouched.

## Next, on your word

- Make the `VER_AT` / `N(20)` normalization call, then I register SYSMSG + the HELP/messaging catalogs
  the same way (each derived from its `.dtschema`, each read-only).
- Or take R2/R3 from the study: resolve selfdoc OWNER/SRC_AUTH to `SYSMEMBER.MKEY`, and unify the
  provenance vocabulary so `RUNID`/`RUNKEY` join selfdoc rows to `SYSRUN`.
- The uniqueness regression for SYSCHATLNK (AIF-086 Finding 1) is still an ideal bounded Copilot job.
