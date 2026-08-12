# External Intake -- DotScript Gap Analysis + Project Assessment (2026-08-11)

Classification: **external evaluation** (gap analysis + hiring-question
assessment). Author: an Outside-AI instance working from PUBLIC materials
only (x64base.com, dottalkpp.com, GitHub `development`, agent-sync through
~2026-08-05), identity not designated by the owner beyond "Outside-AI";
received 2026-08-11 via the owner (relay). Route: AIF-109;
`DOTSCRIPT_FUNCTION_SURFACE_PRIOR_ART_V1.md` section 1 carries the
claim-by-claim tree check.

Status of this package: **summary-of-record, not verbatim.** The full
original text was relayed in-session and its substantive content was checked
against the tree the same day; this MANIFEST preserves the findings table
and verdicts exactly as evaluated, and marks the package as summary-tier.
If the owner supplies the original text later, it is appended below this
line verbatim and this paragraph is amended -- the intake-preserve rule then
applies to that body.

## Received findings (as evaluated)

Overall verdict quoted: on the publicly visible work, hire/recommend --
"high velocity with unusually good taste in architecture and process,"
with normal caveats (live-tree depth, maintenance debt, collaboration under
disagreement, active-beta surface share).

Gap table as received (status per public 2026-08 materials):

| Gap (July ranking) | Status claimed | Impact claimed |
| --- | --- | --- |
| User-defined functions/procedures | still missing | Critical |
| Error handling (ON ERROR / TRY) | still missing | High |
| Variable scoping (LOCAL) | still global-centric | High |
| Structured data (arrays/maps) | arrays LIVE (`{...}`, `$name`, one-based, shared_ptr) | reduced to Medium |
| Script composition (multi-level) | still limited (1-level nesting) | High |
| Line continuation | now present | closed |
| Control flow / engine binding | strong | Low |
| Expression / scalar surface | usable, improved by arrays | Low |

Recommended priorities as received: (1) minimal PROCEDURE/FUNCTION +
parameters + RETURN + LOCAL, xBase-faithful; (2) simple ON ERROR or
TRY/CATCH with explicit buffering policy; (3) remove the 1-level nesting
limit once call frames exist. Closing instruction as received: "Confirm
against the live tree ... before treating any item as closed or starting
implementation" -- which is the house rule, applied by the evaluator to
itself.

## House assessment (pointer)

Every presence/absence claim verified correct against the tree 2026-08-12
(`DOTSCRIPT_FUNCTION_SURFACE_PRIOR_ART_V1.md` section 1) with the material
refinement that DEFFN/DEFCMD already own the registration/resolution seams,
shrinking gap 1 to binding + execution + RETURN. All three recommended
priorities were subsequently RULED by the owner (section 6 of the findings
note) and are executing under `DOTSCRIPT_BUILD_PLAN_V1.md`. The evaluation's
own tree-check instruction is what the house did; its accuracy is banked as
AIF-108 cooperation evidence alongside the Grok peer review.
