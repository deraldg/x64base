---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-106
  recorded_at_utc: 2026-08-22T14:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 5fcf2f467
  authorization:
    requested_by: steward (member.derald), in-session 2026-08-22 -- "that needs
      fixing too" on the silent zero, then two corrections that reshaped it:
      "at the source test the field name exists or is a mangled one" and
      "long field names mangle". Priced first, then "A".
  report:
    path: docs/maintenance/AIF120_FIELD_NAME_AUTHORITY_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R116: five field-name resolvers, one of which knew about mangled long names

Status: **ruling, review-needed. FIXED (4 files). REBUILD REQUIRED.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `5fcf2f467`.

**Area:** engine (`src/cli/expr/`). Changed under the steward's explicit go.

This began as "make `COUNT` stop answering `0` for a clause that never
resolved" (R115 sec 3/3a). The steward's two corrections turned it into a
different and better change, and this document is the first half of it.

---

## 1. Measured

**How it started.** In-session, on the shipped x64 STUDENTS fixture:

    . count for lname = Clark
    8
    . count for name = White
    0

`STUDENTS` has `LNAME` and `FNAME`; it has no `NAME`. The `0` is not a count,
it is a question that was never asked -- and it looks exactly like an answer.

**What the steward corrected.** *"At the source test the field name exists or
is a mangled one."* / *"Long field names mangle."* Both matter, and the second
is what makes the naive fix wrong.

On x64, `logical_name` is authoritative and the physical descriptor carries a
**10-byte token** derived from it (`field_name_policy.hpp`
`plan_x64_unique_fallback`): the plain truncation when it is free, a
DOS-style `~n` alias on collision, and a `~` + base36-hash token if the `~n`
space is exhausted. So a long field name exists on disk under a name that is
**not** its logical name, and "is this a field?" cannot be answered by
comparing against one list.

**The engine already knows this -- in exactly one place.**
`xfg::resolve_field_index_std` (`include/xbase_field_getters.hpp:130-175`):

1. authoritative/logical names win;
2. on `versionByte() == 0x64` only, descriptor tokens are re-derived and
   accepted as aliases;
3. an alias that maps to more than one field is **refused**, not guessed;
4. `-1` means genuinely not a field.

**Four other resolvers ask the same question and get it wrong.** All four
compare the name against `fields()[i].name` and nothing else:

| site | returns | role |
|---|---|---|
| `xbase_field_getters.hpp:130` `resolve_field_index_std` | 0-based, -1 | **the house resolver -- complete** |
| `glue_xbase.cpp:37` `field_index_ci` | 1-based, 0 | the record view (both variants), scan/FOR path |
| `rhs_eval.cpp:200` `field_index_ci` | 1-based, -1 | the marker / `?` evaluator |
| `normalize_where.cpp:62` `is_known_field_ci` | bool | field-vs-literal decision, **16 command paths** |
| `predicates.cpp:108` `is_known_field_ci` | bool | predicate-chain fast path |

**The `normalize_where` site is the worst of the four, because it decides
MEANING rather than lookup.** `normalize_unquoted_rhs_literals` is what tells
an unquoted right-hand word apart from a string literal -- it is why
`FOR LNAME = Clark` works without quotes. A bare word that IS a mangled
descriptor name failed that test and fell through to "literal", so on a table
with long field names

    COUNT FOR DEPT = PAYLOAD_SH

compared `DEPT` against the ten characters `PAYLOAD_SH` instead of against
that field's value. Not an error. A different answer to a different question.

**This is the lane's recurring two-authority shape**, alongside `dotref`
vs `foxref`, `category: navigation` vs the printed index family, and
`name()` vs `logicalName()` (R112).

## 2. What changed

Four files, one line of real body each. The four weak resolvers now delegate
to `xfg::resolve_field_index_std`, converting index conventions at the seam:

- **`src/cli/expr/glue_xbase.cpp`** -- `field_index_ci` (0-based/-1 in,
  1-based/0 out). Feeds `make_record_view` and `make_record_view_raw` through
  the existing `field_index_ci_cached`.
- **`src/cli/expr/rhs_eval.cpp`** -- `field_index_ci` (1-based/-1 out).
- **`src/cli/expr/normalize_where.cpp`** -- `is_known_field_ci` -> `>= 0`.
- **`src/cli/expr/predicates.cpp`** -- `is_known_field_ci` -> `>= 0`.

**Cost is bounded and was measured, not assumed.** Step 2 of the resolver
rebuilds `plan_x64_unique_fallback` per call -- a vector allocation plus the
collision loop. All four `glue_xbase.cpp` sites already route through
`field_index_ci_cached`, and `make_record_view` / `make_record_view_raw` each
hold their own `idx_cache`, so the resolver runs **once per distinct name per
scan**, not per row. The M1/M2 selective-decode work is untouched. The
`normalize_where` and `predicates` sites are called once per expression during
normalization, not per row.

**Non-x64 tables are unaffected.** Step 2 is gated on `versionByte() == 0x64`,
so for v32/VFP this is byte-for-byte the previous behaviour.

**This change adds no refusals.** It only makes MORE names resolve -- names
that are already on disk. Nothing that worked can stop working through a name
failing to resolve.

Verified: all four TUs pass `g++ -std=c++20 -Wall -fsyntax-only` (gcc 11.4).
**Not built, not run.**

## 3. What this does NOT do

**The silent zero is still silent.** `COUNT FOR NOSUCHFIELD = "x"` still
returns `0`. This ruling makes that reportable -- after it, `-1` from the one
resolver means *genuinely not a field*, unambiguously -- but it does not
report it. That is part B, and it is the half with blast radius:

- `scan_selector.cpp:167` and `:236` each declare `std::string err` and
  **never read it**, collapsing three outcomes into one with
  `ok = eval_bool(...) && result`: failed-to-evaluate, evaluated-false, and
  threw all become "row does not match". A whole-scan failure reads as "no
  rows matched". Another writer with no reader, the same shape as `_db_name`
  (R111) and `bbs_store.cpp:333`.
- Deciding what `COUNT` should DO on an unresolvable clause -- refuse, or
  report and continue -- is a behaviour ruling and is the steward's.

## 4. Risk -- the one thing that can change meaning

Because `normalize_where` decides field-vs-literal, a bare unquoted word that
**is** a mangled descriptor token on the current table now resolves as a FIELD
where it previously became a STRING LITERAL. That is the defect being fixed,
and it is also the only way this change can alter an existing script's answer.

It requires all of: an x64 table, a field whose logical name is long enough to
be truncated or `~n`-mangled, and a script using that exact token as an
unquoted right-hand literal. No such usage was found in the tracked `.dts`
corpus, but that is a weak negative and is stated as one.

## 5. Scope -- what I did NOT measure

- Whether any of the ~21 direct `compile_where` consumers hold a **sixth**
  private resolver. I found five by grepping for the two known idioms; a
  differently-named one would not have matched.
- Whether the `~hash` branch of `plan_x64_unique_fallback` is reachable in any
  live fixture. The `~n` branch needs a collision in the first 10 bytes; the
  hash branch needs 999999 of them.
- Behaviour on VFP flavours that also truncate. Step 2 is x64-gated by the
  resolver's own policy; whether VFP wants the same treatment is unasked.
- The marker path's OTHER name defect (`rhs_eval.cpp:849`, an unknown bare
  identifier becoming its own name as a string) is untouched -- see R115 sec 3
  and the steward's bare-word-scalar warning about `DATE`/`TIME`/`NOW`.

## 6. Evidence tier

**Runtime-measured:** the `count for name = White` -> `0` and
`count for lname = Clark` -> `8` pair, run by the steward in-session
2026-08-22 on the x64 STUDENTS fixture at build `49b2690d`.

**Source-evidenced:** the five resolvers and their return conventions
(`xbase_field_getters.hpp:130-175`, `glue_xbase.cpp:37`, `rhs_eval.cpp:200`,
`normalize_where.cpp:62`, `predicates.cpp:108`); the mangling policy
(`field_name_policy.hpp:106-155`); the 16 callers of
`normalize_unquoted_rhs_literals`; the per-view `idx_cache` at
`glue_xbase.cpp:177/197/263/281`; the swallowed `err` at
`scan_selector.cpp:167,236`.

**Compile-verified only:** the change -- `-Wall -fsyntax-only`, gcc 11.4.
**Not built, not run.**

**Explicitly unmeasured:** sec 5.

## 7. Good Neighbor note

- **What changed.** Four source files -- `src/cli/expr/glue_xbase.cpp`,
  `src/cli/expr/rhs_eval.cpp`, `src/cli/expr/normalize_where.cpp`,
  `src/cli/expr/predicates.cpp` -- plus this document. No header, no build
  file, no script. Pre-edit copies are kept untracked at `tmp/*.pre-r116`.
- **Whose area.** Engine. Changed under the steward's in-session go
  ("that needs fixing too", then "A" against a written price).
- **What authorization.** The steward chose option A of a two-part price:
  unify the resolver now, decide the reporting behaviour separately.
- **How to verify.** Rebuild, then `REGRESSION ALL` plus the explicit-run
  specs. Nothing should change on the shipped fixtures -- STUDENTS has no long
  field names, so every name resolves through step 1 exactly as before. The
  capability this adds needs a table that has one: create an x64 table with a
  field name longer than 10 characters, then confirm a `FOR` clause resolves
  it by BOTH its logical name and its descriptor token. That spec does not
  exist yet and is owed.
- **How to undo.** Restore the four files from `tmp/*.pre-r116`, or
  `git checkout -- src/cli/expr/glue_xbase.cpp src/cli/expr/rhs_eval.cpp src/cli/expr/normalize_where.cpp src/cli/expr/predicates.cpp`,
  and delete this document.
