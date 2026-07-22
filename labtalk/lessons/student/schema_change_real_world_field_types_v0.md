# When the World Changes Your Schema v0

Status: draft
Audience: student, developer, educator
Registry ID: lesson.student.schema_change_real_world_field_types

## Lesson Thesis

Real systems do not only change because programmers think of new features.
They change because the world changes around the stored data.

Dates, currencies, identity fields, language, location, privacy rules, and
accessibility expectations can all change after a system is already in
production. The engineering question is not only "can we add a new field?" The
deeper question is:

> How adaptable is the system when the meaning of a field changes?

## Why This Is a Real Lesson

This lesson uses the proposed PRONOUNS semantic field hook as a modern case
study. It belongs in the same family of problems as:

- Y2K: date storage and interpretation became a systemic risk.
- The Euro: currency fields became conversion, rounding, locale, reporting, and
  audit problems.
- ERP modernization: organizations had to decide whether maintaining legacy
  systems was cheaper or safer than moving to commercial ERP.
- Modern semantic fields: a value may still be stored as character data, but
  validation, display, documentation, import/export, UI behavior, and policy may
  all change.

The point is not to debate one field. The point is to study how data systems
respond when requirements change outside the codebase.

## Current x64base Framing

x64base already has several concepts that make this teachable:

- DBF compatibility keeps older data readable.
- x64 metadata can add meaning without immediately breaking classic storage.
- validation and normalization are becoming explicit write-time gates.
- `REPLACE`, `MULTIREP`, and `CALCWRITE` expose how mutation paths must agree.
- `FIELDS`, `STRUCT`, `FIELDMGR`, HELP, SelfDoc, MDO, and manualgen expose how
  a change becomes visible and documented.
- public websites and manuals must stay proof-labeled and avoid claiming more
  than the implementation proves.

## Student Questions

Use these questions before designing a solution:

1. What changed in the real world?
2. Is this a storage problem, a validation problem, a reporting problem, a UI
   problem, a policy problem, or all of them?
3. Who owns the requirement?
4. What breaks if the system does nothing?
5. What breaks if the system changes too quickly?
6. Can metadata describe the new meaning without changing the stored bytes?
7. Which command paths can write this value?
8. Which readback tools must show the new meaning?
9. How should import/export behave when the target system does not understand
   the new semantic type?
10. How do we prove the change is safe?
11. How do we document the difference between implemented behavior, planned
   behavior, and policy discussion?
12. At what point is maintaining the old system more expensive than replacing
   it?

## Exercise A: Classify the Change

Given a new PRONOUNS semantic field, classify the work:

| Surface | Student Decision |
| --- | --- |
| storage | Is this a new DBF type or a character field with semantic metadata? |
| validation | Free text, normalized common values, strict list, or policy-driven? |
| relation | Should it relate to `SEX`, and if so, advisory or strict? |
| mutation | Which commands can change it? |
| buffering | What happens when table buffering is on and the row is dirty/stale? |
| import/export | How does it round-trip to CSV, classic DBF, VFP, and x64 DBF_64? |
| documentation | Which HELP, SelfDoc, MDO, and manual sections need updates? |
| proof | Which canaries or transcripts prove the behavior? |

## Exercise B: Compare Historical Changes

Compare PRONOUNS with Y2K and Euro-era changes:

| Change | Similarity | Difference |
| --- | --- | --- |
| Y2K | Existing fields became semantically unsafe. | Date storage/interpretation could affect nearly every transaction. |
| Euro | Currency required policy, conversion, rounding, and audit behavior. | The field may need paired currency code and amount rules. |
| PRONOUNS | Character storage may be enough, but semantics and UI behavior change. | The best default may be no automatic coupling unless metadata opts in. |

## Exercise C: Maintain or Replace

Ask the ERP-style question:

```text
Is it cheaper and safer to evolve this system,
or to replace it with a commercial platform?
```

Students should consider:

- data migration cost,
- loss of local knowledge,
- licensing and vendor lock-in,
- audit and proof requirements,
- customization cost,
- training cost,
- long-term maintainability,
- whether the current system is already solving part of the problem through
  metadata and documentation.

## Expected Observations

Students should be able to explain:

- a field type is not just a byte code;
- storage compatibility and semantic meaning can be separated;
- mutation commands must share validation and normalization behavior;
- documentation is part of the system, not an afterthought;
- public claims must be tied to evidence;
- planned design lanes should stay labeled until proven.

## Proof Links

- `docs/manuals/developer/dev/dev-20-semantic-field-hooks-and-pronouns.md`
- `docs/manuals/developer/dev/DotTalk++x64base Field Types & Validation System.txt`
- `include/xbase.hpp`
- `include/datatype_index.hpp`
- `src/cli/cmd_replace.cpp`
- `src/cli/cmd_replace_multi.cpp`
- `src/cli/cmd_calcwrite.cpp`

## Next Gate

Promote this lesson from draft to proof-linked after:

- a reviewed command transcript or canary shows current field validation
  behavior;
- a metadata example shows how a semantic role can be attached without changing
  classic storage;
- a teacher-facing worksheet is written with expected answers.
