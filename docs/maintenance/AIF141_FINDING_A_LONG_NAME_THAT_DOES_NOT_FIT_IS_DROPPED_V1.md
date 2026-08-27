# AIF-141 -- A LONG NAME THAT DOES NOT FIT IS DROPPED, AND NOTHING SAYS SO

    Number  : AIF-141, claimed 2026-08-27 with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001). Claim file verified
              present at `coordination/aif/AIF-141.claim` before this
              number was cited anywhere.
    Found   : 2026-08-27, while measuring whether CDX tags resolve against
              descriptor tokens or logical names (they resolve against
              logical names -- see the AIF-078 name-tiers design note).
    Lane    : AIF-078 adjacent; the defect is in the x64 name-vector layer
              and predates the multi-workspace work entirely.
    Status  : review-needed. The author does not self-approve.
    Basis   : SOURCE-EVIDENCED, lines cited. NOT RUN. No fixture exists that
              reaches the ceiling, which is exactly why this is latent.
    Shape   : AIF-118 -- a guard whose "did not apply" is indistinguishable
              from "applied and was already correct".

## 1. THREE SITES, ONE SHAPE, AND THE WRITER'S IS DESTRUCTIVE

An x64 table carries its authoritative long names in an `X64M` metadata block
beside the classic 10-byte descriptors. Three places decide whether a given
name makes it into or out of that block, and all three decide by silently
skipping.

**THE WRITER -- `include/xbase_64.hpp:302-309`.** Building the block:

    for (std::size_t i = 0; i < field_names.size(); ++i) {
        const std::string& name = field_names[i];
        if (name.empty()) continue;
        if (!x64_field_name_fits(name.size())) continue;
        ...
        pending.push_back(...);
    }

**A name that does not fit is never written.** Not truncated-and-flagged --
OMITTED. What lands in the file is the 10-byte descriptor token and nothing
else, so the long name is not "unavailable at runtime", it is **gone from the
artifact**. Re-saving the table cannot recover it because it was never stored.

**THE WRITER, TABLE NAME -- `:297`.** `const bool use_table_name =
!table_name.empty() && x64_table_name_fits(table_name.size());` Same decision,
same silence, for the table's own name.

**THE READER -- `:469-470`.**

    if (!name.empty() && x64_field_name_fits(name.size())) {
        area.setFieldName(static_cast<int>(field_index), std::move(name));
    }

`setFieldName` (`xbase.hpp:383`) OVERWRITES `_fields[i].name` in place, and
`FieldDef` has exactly one name slot (`xbase.hpp:166`). So when the guard
passes, the field answers to its long name; when it does not, the field keeps
the descriptor-derived name it was read with. **Both outcomes are a populated,
plausible-looking string.** Nothing distinguishes them.

**THE READER, TABLE NAME -- `:435`.** Same again.

## 2. WHY THIS IS WORSE THAN A TRUNCATION

**A table can carry a MIX.** The guard is per field, so a table with one
over-ceiling name and nine under it comes back with nine long names and one
descriptor token, in one `fields()` vector, with no marker on the odd one.

**And every name-based consumer resolves against that one vector.** Measured
the same day: a CDX tag has no key expression at all -- `CDX ADDTAG <name>`
(`cmd_cdx.cpp:341`) stores the uppercased tag NAME, and
`field_index_for_tag_()` (`cdx_native_backend.cpp:72`) string-matches it
against `A.fields()[i].name`. The relation engine resolves the same way. So a
field that lost its long name is a field that **silently answers to a different
string than its siblings**, and a tag or relation naming it resolves, or does
not, depending on which side of the ceiling it fell.

**`field_name_policy` already carries the flag that would make this loud and
nobody reads it.** `FieldNamePlan` (`include/xbase/field_name_policy.hpp:25`)
has `truncated`, `mangled` and `sanitized` booleans, and the policy's own
comment states the contract this defect breaks:

    // - logical_name remains authoritative and is not modified.
    // - descriptor_name is a unique 10-byte DBF/VFP fallback token.

**"Remains authoritative and is not modified" is exactly what the writer's
`continue` violates.** The plan says the long name is the authority; the writer
drops it when it is inconvenient; the reader then reports the fallback as
though it were the authority.

## 3. HOW REACHABLE IS IT, HONESTLY

**LATENT, NOT LIVE, AND THE CEILING IS A BUILD VECTOR.**
`X64_FIELD_NAME_LENGTH_MAX` and `X64_TABLE_NAME_LENGTH_MAX`
(`xbase_64.hpp:204-205`) resolve to `dottalk::build::x64::field_name_max` and
`table_name_max`. This build prints `x64 names default=128/128 max=256/256` in
its configure summary. **No fixture in the tree carries a name near that**, so
nothing has ever crossed it and no arm would catch it if something did.

**The ceiling is not a constant a reader can trust from the header, either.**
`include/xbase_64_phase1_contract.txt:150-151` still states
`X64_TABLE_NAME_LENGTH_MAX = 128` and `X64_FIELD_NAME_LENGTH_MAX = 64`. Those
are the pre-build-vector numbers. The contract document and the live constants
disagree, and the code comment beside the constants (`// was 256`) is the only
hint. Not fixed here -- named so the next person reading the contract file
knows to check the build vectors instead.

**AND THE CONTRACT DOCUMENT CANNOT BE CORRECTED THROUGH THE NORMAL PATH.**
Measured 2026-08-27 by the `cited-paths` gate on the commit that landed this
finding: `include/xbase_64_phase1_contract.txt` reports as **IGNORED**, not
merely untracked -- *"`git add` on it is a no-op (R42.1)"*, and the gate's own
summary line says *"An IGNORED path can never be staged at all."* So a document
that states this subsystem's name ceilings, and states them wrongly, is
gitignored: it cannot be staged, reviewed in a diff, or gated. **The author
first reported it as a plain WIDOW** after checking `ls-files --error-unmatch`
and not `check-ignore` -- true and incomplete, corrected here rather than
edited above. Whether that file should be tracked or retired is not this
finding's call, but it is now part of why the stale ceiling persists.

**So the honest severity is: cannot happen today, will happen silently the
first day someone raises a ceiling or imports a schema from a system with
longer names** -- which is precisely the CONVERT thesis this project is built
around (R7, AIF-090).

## 4. WHAT THE FIX IS NOT

**Not "truncate instead of skip".** A truncated long name collides with its
neighbours exactly the way descriptor tokens do, and `plan_x64_unique_fallback`
already exists to solve that problem at the descriptor tier. Doing it twice, in
two tiers, with two mangling schemes, is how you get two answers to one
question.

**Not "raise the ceiling".** The ceiling can always be crossed; the defect is
the silence, not the number.

**The shape of a fix is: the writer REFUSES or RECORDS, and the reader can tell
which name tier it is holding.** Whether that is a per-field flag on
`FieldDef`, a refusal at save time, or a count reported by the loader is not
proposed here -- see sec 5.

## 5. WHAT IS NOT RULED

- **Refuse at write, or record-and-report?** A refusal cannot silently lose
  data but can block a save the user wants; a report cannot block but relies on
  someone reading it. This project has ruled both ways in different places
  (WRITEBACK aborts on shortfall; LOAD reports an unmappable CURSOR).
- **Should `FieldDef` know which tier its name came from?** It has one name
  slot today. Adding a provenance flag is the smallest change that makes the
  mix in sec 2 detectable, and it is a header change to a very hot struct.
- **Does the same hazard exist on the CLASSIC path?** `plan_classic_strict`
  truncates without mangling and its comment says collisions "are destructive,
  so callers should fail by default." **Whether callers actually do fail is
  NOT MEASURED HERE** and should not be assumed from the comment.

## 6. NO ARM COVERS THIS AND ONE IS BUILDABLE

An arm is straightforward and does not need the ceiling raised: create an x64
table with one field named at the ceiling and one field one byte over, save,
reopen, and read a value **through each field name**. The over-ceiling field
will not answer to its long name. That is a FIELD-VALUE assertion, which is the
only kind this language can make (the FIELDMGR_APPEND doctrine), and it goes
red today.

Not written here, because the fix is not ruled and an arm written against
unruled behaviour asserts a guess.

**GOOD NEIGHBOR**

- **What changed:** nothing. This is a finding document.
- **Whose area:** the x64 name-vector layer, `include/xbase_64.hpp`. Not
  modified. It is engine and would want an explicit go.
- **What authorization:** found while answering an owner design question about
  long names in relational algebra; the owner asked for the number to be
  claimed and the finding written.
- **How to verify:** read the three cited guards. Each is two lines.
- **How to undo:** delete this file.
