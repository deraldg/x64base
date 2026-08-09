# Summary for the maintainer -- Specialty LMS intake

    package    : AIPR-20260809-COPILOT-001  (Microsoft Copilot, hosted_proposal)
    assessment : AIPR-20260809-003          (Cowork/Claude, local_write)
    proposed   : AIF-103
    baseline   : development @ 648967b74

## In one paragraph

Copilot produced a 13-slide specialty-LMS proposal without access to the
repository. It reads well and it is wrong about what this project is: it treats
the AI development coordination vocabulary (lane, proof, member, board, AI
Portal) as learning-management concepts, and invents an "xBridge Protocol" that
exists nowhere in the tree. It is preserved unchanged as prior art. Correcting
it produced the first actual measurement of the LabTalk campus registries, and a
reviewed website deck at `/lms-architecture/` that states the corrected reading.

## The number worth carrying forward

    labs        4   (1 first_runnable, 2 draft, 1 design_only)
    lessons    16   (9 career, 7 student; 1 proof_linked)
    concepts   36   (20 lab-reachable, 8 orphaned)
    proofs     56   (31 runtime_observed, 3 validated)
    student-ready  0

**56 proof records against 4 labs.** The evidence machinery is an order of
magnitude ahead of the curriculum. The campus is real and pre-student.

## What changed in the tree

| Path | Change | Class |
| --- | --- | --- |
| `docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/` | new; received package + assessment | intake |
| `labtalk/registries/ai_report_index.yaml` | two proposed entries | registry |
| `D:/dev/x64base-site config/nav.ts` | `Architecture` nav entry | publication |
| `D:/dev/x64base-site content/docs/dev/website-documentation-matrix.mdx` | `static` row for `/lms-architecture/` | publication |
| `D:/dev/x64base-site app/lms-architecture/`, `public/lms-architecture/` | deck route + 14 slide documents | publication |

Website `Last audited` was **not** advanced; that is a push-time action.

## Decisions owed

1. **Confirm or reassign AIF-103.** Verified free in both the claim ledger
   (`coordination/aif/`, highest AIF-101) and the intake queue. Not claimed --
   `claim-aif` shells out to `git grep` and is host-side only.
2. **Q1-Q5** in the assessment, section 6. Q3 (do learner records live in
   x64base tables) and Q5 (does a lab proof carry engineering-proof weight) are
   the two that change what a campus build looks like.
3. **Is the career-lessons set the actual curriculum?** Nine post-mortems with
   measured evidence, about engineering judgment rather than database syntax.
   Currently filed as lessons; arguably the strongest teaching content here.
4. **Keep or drop the website deck.** It is live and classified. If it is not
   worth maintaining, the nav entry and matrix row should come out rather than
   sit stale.

## Not in this package

The gateway client-abort patch (`tools/reports/serve_dynamic_reports.py`) was
carried in the same session but is unrelated work. It is runtime-proven and
belongs under AIF-100 gate governance, reported in this session's closeout, not
here.
