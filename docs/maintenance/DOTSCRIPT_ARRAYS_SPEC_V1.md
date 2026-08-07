---
title: "DotScript Arrays"
subtitle: "Complete Language, Runtime, Compatibility, and Implementation Specification"
author: "DotTalk++ / x64base Project"
date: "2026-07-20"
version: "1.0-draft"
status: "Design specification; implementation not yet runtime-proven"
language: "en-US"
document_id: "DOTSCRIPT-ARRAYS-SPEC-V1"
---

> **Repository note.** This is the **design authority** for the DOTSCRIPT-ARRAYS lane
> (`docs/maintenance/DOTSCRIPT_ARRAYS_LANE_V1.md`, intake AIF-038). It is normative
> *design intent*; the runtime does **not** implement arrays yet. Before the spec's
> Phase 1, the lane's **Phase 0** reconciles three things this spec assumes against
> the real engine -- the `$VAR` variable convention (repo evidence flags `$` as
> non-DotScript PowerShell), the canonical `Value` model (the real `xexpr::Value` is a
> tagged `ValueKind{None,Bool,Number,String,Date,Error}`, not the `std::variant` in
> sec. 30, with a second `EvalValue` on the eval path), and the missing `ASSERT` /
> `VALTYPE` / `NIL` facilities the acceptance scripts use. Source review:
> `outputs/DOTSCRIPT_ARRAYS_SPEC_REVIEW_2026-07-20.md`.

# Document Status and Authority
This document consolidates the current design decisions for arrays in DotTalk++ and DotScript. It replaces earlier partial notes and incorporates the later amendments concerning xBase/Fox compatibility, DotTalk++ identity, command provenance, and implementation boundaries.
The design is **normative for planned implementation**, but it is not a claim that the current runtime already implements every feature described here. Each command and function must remain marked as `PLANNED`, `PARTIAL`, or `SUPPORTED` until runtime tests prove its state.
The project authority chain remains:
> **Runtime proves. Source defines. HELP explains.**
For array language provenance:
- `include/foxref.hpp` is the historical and compatibility reference lane.
- `include/dotref.hpp` is the project-native DotTalk++ reference lane.
- Live command metadata, SelfDoc catalogs, usage contracts, tests, and the running interpreter determine actual implemented behavior.
- Overlap between `foxref.hpp` and `dotref.hpp` is permitted when a command has both historical ancestry and a preferred DotTalk++ public role.
The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.
# 1. Purpose
Arrays provide DotScript with a general-purpose in-memory ordered collection type. They are intended for:
- temporary working sets;
- lists of fields, tags, files, aliases, paths, values, or commands;
- command arguments and function results;
- batch processing and script control;
- metadata and schema inspection;
- historical xBase programming patterns;
- structured interchange with JSON and AI facilities;
- explicit materialization of bounded tuple streams;
- educational inspection of reference identity, mutation, nesting, and memory use.
Arrays are the first general-purpose composite runtime value in DotScript. Their implementation should establish machinery later reusable by tuples, maps, objects, iterators, AI request structures, and structured procedure interfaces.
# 2. Language Position
DotTalk++ is not defined by Visual FoxPro compatibility. It is a complete command language composed of:
1. broadly inherited xBase language;
2. selectively retained Fox/FoxPro-compatible language;
3. native DotTalk++ and DotScript language.
Provenance explains where a feature came from; it does not determine whether that feature is important. Native DotTalk++ commands MUST be documented, tested, grouped, and promoted as first-class language facilities rather than treated as incidental extensions.
The permanent language rule is:
> Retain established xBase and Fox language where it remains useful and compatible. Do not copy FoxPro merely for imitation. Preserve native DotTalk++ and DotScript syntax, commands, architecture, and terminology as first-class parts of the total command language.
# 3. Provenance Classification
Every public array command, function, or syntax form SHOULD carry provenance metadata.
## 3.1 XBase or Fox compatibility lane
These names have established xBase ancestry and belong primarily in `foxref.hpp` when implemented:
`DIMENSION`, `DECLARE`, `ARRAY()`, `ALEN()`, `AADD()`, `ACLONE()`, `ACOPY()`, `ADEL()`, `AEVAL()`, `AFILL()`, `AINS()`, `ASCAN()`, `ASIZE()`, `ASORT()`, `ATAIL()`, `AFIELDS()`, `DBSTRUCT()`.
The exact dialect ancestry differs by feature. Documentation SHOULD label `Origin: xBase` / `Compatibility: CA-Clipper/Harbour family`, or `Origin: Fox-compatible declaration syntax`. The reference should not claim strict Visual FoxPro compatibility unless behavior is deliberately tested against that dialect.
## 3.2 DotScript syntax lane
These forms belong to DotScript even when they combine with inherited xBase operations: `$A`, `$A[1]`, `$A[2,3]`, `$A = { 1, 2, 3 }`, `FORMULA $A[1]`, `LOOP WHILE $I <= ALEN($A) ... END LOOP`. The `$VAR` convention, DotScript parser, expression evaluator, command routing, script execution, tuple bridge, and diagnostic behavior are native project language.
## 3.3 Native DotTalk++ lane
Native or proposed-native facilities belong in `dotref.hpp` when implemented: `ARRAY INFO`, `ARRAY LIST`, `ARRAY VALIDATE`, `ARRAY STATS`, `ARRAY LIMITS`, `ARRAY TRACE`, `ASAME()`, `ISARRAY()`, `TUPTOARRAY()`, `ARRAYTOTUP()`, `TUPMATERIALIZE()`. JSON functions (`JSONENCODE()`, `JSONDECODE()`) may be shared structured-value services rather than array-only functions. These native capabilities MUST be included in ordinary help, SelfDoc, manuals, examples, tests, website documentation, and command-category listings.
# 4. Core Array Contract
1. Array indexes are one-based.
2. Array literals use braces.
3. Square brackets are used for subscripts.
4. Arrays may contain any DotScript runtime value, including other arrays.
5. Multidimensional arrays are represented by nested arrays.
6. Array assignment shares the array object.
7. `ACLONE()` creates an independent recursive clone.
8. Indexed assignment never enlarges an array implicitly.
9. `ADEL()` and `AINS()` retain traditional fixed-length behavior.
10. Arrays live in the DotScript runtime, not in `DbArea`.
11. Database transactions do not automatically roll back script arrays.
12. Tuple streams remain streams until explicitly materialized.
13. Runtime limits protect against accidental excessive allocation.
14. Array mutations are observable through native diagnostics.
15. Compatibility features and DotTalk++ extensions are documented separately but presented as one usable language.
# 5. Value Model
An array is a first-class DotScript runtime value: stored in a `$VAR`, assigned, passed/returned, nested, compared structurally, inspected, serialized, or used as a future map/object element. Arrays MUST NOT be a special side table disconnected from the ordinary expression `Value` type. A single array may hold heterogeneous elements (`NIL`, character, numeric, logical, date/date-time, memo reference, tuple, array, future map/object/stream/callable). `VALTYPE()` (or equivalent) SHOULD report `A`; `ISARRAY()` is the preferred guard predicate.
# 6. Array Construction
Four forms: empty literal `{}`; populated/nested literal with accepted trailing comma and rejected missing element; `ARRAY([dim...])` (NIL-filled, `ARRAY()` == `{}`, every dimension an exact non-negative integer within limits, overflow-checked); and `DIMENSION`/`DECLARE $A[dim...]` (DECLARE is a compatibility alias). Re-dimensioning replaces the binding only after new dimensions validate and allocate; use `ASIZE()` to preserve content.
# 7. Grammar and Literal Disambiguation
`array_literal := "{" [ expression ("," expression)* [","] ] "}"`. Reserve `{|` for future code blocks and `{^` for a possible typed date literal; otherwise `{` begins an array literal. The current parser MUST be audited before implementation to ensure braces do not already have conflicting DotScript meaning.
# 8. Indexing
One-based; index zero invalid. Subscripts MUST evaluate to an exact integer (`2`, `2.0`, `$I+1` valid; `0`, `-1`, `2.5`, `"2"`, `.T.`, `NIL` invalid -- no silent coercion). Multidimensional arrays are nested; `$GRID[2,3]` == `$GRID[2][3]`; a non-array intermediate MUST fail clearly. Postfix indexing SHOULD work on any array-producing expression (`GETNAMES()[1]`), i.e. indexing is an ordinary high-precedence postfix expression.
# 9. Indexed Assignment
Indexed expressions are valid assignment targets. The evaluator MUST resolve the target array, evaluate every index exactly once, validate all intermediate levels, evaluate the RHS, reject prohibited cycles, reject frozen mutation (if added later), mutate, and update diagnostic state. Indexed assignment MUST NOT enlarge implicitly (`$A[3]=3` on a length-2 array errors; use `AADD()`/`ASIZE()`).
# 10. NIL, Empty Arrays, and Uninitialized Elements
Dimensioned elements are `NIL`. Empty array != NIL: `{} == NIL` is `.F.`, `EMPTY({})` is `.T.`, `ISNIL({})` is `.F.`, `ISNIL(NIL)` is `.T.`. `EMPTY({NIL})` is false (one element). Structural equality MUST NOT collapse empty-like values (`""`, `0`, `.F.`, `NIL`, `{}`) merely because `EMPTY()` treats several as empty.
# 11. Reference Semantics
Assignment shares the reference (Clipper/Harbour value model): `$B=$A; $B[1]="X"` changes `$A[1]` too. `ACLONE()` makes an independent recursive copy that **preserves shared child topology** (a child referenced twice is cloned once, both clone refs point to the one clone). `ASAME()` tests object identity, distinct from `==` structural equality.
# 12. Equality
`==` compares array contents recursively; identity is `ASAME()`. Scalar comparison delegates to the ordinary DotScript comparison contract (`SET CASE` applies to string elements unless a future strict mode is added). Structural equality MUST use visited-pair tracking against infinite recursion.
# 13. Cycle Policy
The initial implementation MUST prohibit direct and indirect cycles (a refcounted runtime cannot safely reclaim them); both MUST fail before mutation. Cycle checks apply to indexed assignment, `AADD()`, `AFILL()`, `ACOPY()` into a target, and future insert operations. Cycles MAY return later with tracing GC; not part of the initial contract.
# 14. Canonical XBase Array Functions
Established names form the compatibility core; historical behavior MUST NOT be silently changed.

- **`ARRAY([dim...]) -> Array`** -- empty or dimensioned; extra dims nest.
- **`ALEN(array) -> Numeric`** -- outer length (`ALEN({})`=0). `LEN(array)` MAY alias if `LEN()` dispatch supports it; `ALEN()` preferred. A VFP-style 2nd arg is deferred (jagged nested arrays).
- **`AADD(array,value) -> value`** -- append, +1 length, returns appended value; array values inserted by shared reference unless `ACLONE()`.
- **`ASIZE(array,n) -> array`** -- resize 1-D target; grow adds `NIL`, shrink discards tail; affects only the target array.
- **`ADEL(array,pos) -> array`** -- delete+shift-left, last becomes `NIL`, **length preserved**.
- **`AINS(array,pos) -> array`** -- insert `NIL`+shift-right, last discarded, **length preserved**.
- **`AFILL(array,value[,start[,count]]) -> array`** -- fill range (validate whole range first); array value stored by shared reference.
- **`ASCAN(array,value[,start[,count]]) -> Numeric`** -- one-based position or 0; ordinary equality. Code-block predicate form deferred.
- **`ACOPY(source,target[,src_start[,count[,tgt_start]]]) -> target`** -- copy into existing target (not enlarged), nested by reference; overlap-safe; validate ranges first.
- **`ACLONE(array) -> Array`** -- recursive clone preserving shared child topology; a `MemoRef` stays a copied reference, not a duplicated payload.
- **`ASORT(array[,start[,count]]) -> array`** -- in-place stable sort of comparable scalar groups (numeric/character/date/date-time/logical); mixed incompatible types MUST fail clearly; `NIL` sorts after non-`NIL` ascending. Comparator/code-block form deferred.
- **`ATAIL(array) -> Any`** -- last element (empty -> `NIL`).
- **`AEVAL(array,code_block[,start[,count]]) -> array`** -- **deferred** until code blocks exist; MUST NOT be faked via ad-hoc string eval.

# 15. Native DotTalk++ Array Functions
- **`ISARRAY(value) -> Logical`** -- native convenience predicate.
- **`ASAME(left,right) -> Logical`** -- object identity, not structural equality.
# 16. Names Not Adopted as Core
`APUSH`, `APOP`, `ASHIFT`, `AUNSHIFT`, `ASLICE`, `ACONTAINS`, `AFREEZE`, `AINSERT`, `AREMOVE` are not part of the canonical initial language; MAY return later for material capability, MUST NOT be presented as historical xBase functions. Prefer `AADD`, `ADEL`, `AINS`, `ASIZE`, `ASCAN`, `ASORT`.
# 17. DotTalk++ Diagnostic Command Family
The `ARRAY` command is distinct from the `ARRAY()` constructor. Grammar: `ARRAY INFO <expr>`, `ARRAY LIST <expr> [RECURSIVE] [FROM <n>] [COUNT <n>]`, `ARRAY VALIDATE <expr>`, `ARRAY STATS`, `ARRAY LIMITS`, `ARRAY TRACE ON|OFF|STATUS`. Native (dotref lane). `ARRAY INFO` reports id/length/frozen/mutation seq/structure seq/nested/max depth/estimated bytes (shared_ptr use_count approximate -- not an exact variable count). `ARRAY LIST` prints index/type/value with a `RECURSIVE` form and MUST obey paging/`FROM`/`COUNT`. `ARRAY VALIDATE` checks integrity/values/limits/depth/cycles/id/sequence/handles. `ARRAY STATS` and `ARRAY LIMITS` report live totals and configured caps. `ARRAY TRACE` is off by default and MUST NOT alter semantics.
# 18. Control Flow and Iteration
First release needs no new loop syntax (`$I=1; LOOP WHILE $I<=ALEN($NAMES) ... END LOOP`). Examples use `FORMULA`; `?` remains governed by the existing DotScript command contract. Future `FOR EACH $NAME [, $INDEX] IN $ARR ... END FOR` MAY be added (syntax not yet normative). If added, element replacement MAY be allowed but structural change during iteration MUST be detected (track a general mutation sequence and a structure sequence).
# 19. Procedure and Function Parameters
Arrays pass as reference values; element mutation affects the caller's shared array. Rebinding a local parameter (`$VALUES = {}`) changes only the local binding unless explicit by-reference binding is later added (out of scope; design consistently for all DotScript types).
# 20. Arrays Versus Tuples
An array is positional, mutable, one-based, script-owned, heterogeneous, integer-indexed -- for lists/arguments/intermediates/algorithms. A tuple is field-aware/named, tied to work areas/records/relations/streams, with its own live/snapshot lifecycle. Arrays MAY contain tuple values but MUST NOT replace tuple streams or semantics.
# 21. Tuple Bridges
`TUPTOARRAY(tuple) -> Array` (positional under explicit field order); `ARRAYTOTUP(array, schema) -> Tuple` (only after validating field count/names/types/constraints); `TUPMATERIALIZE(stream, limit [, mode]) -> Array` (bounded; default preserves tuple meaning; a limit SHOULD be mandatory unless the stream is known finite -- prevents loading millions of records into script memory).
# 22. DBF and Work-Area Integration
Arrays are memory-only and not DBF field types. `AFIELDS($FIELDS)` may populate field metadata (positional legacy form; richer metadata SHOULD prefer tuples/maps). `DBSTRUCT()` returns a structured array of the current table definition. `SCATTER TO`/`GATHER FROM` compatibility MAY be added; `GATHER` MUST route through the normal mutation layer (validation, buffering, memo, index maintenance) -- never bypass it. Named tuple forms SHOULD be preferred for ordinary record work.
# 23. Memo Integration
An array may carry a `MemoRef` value only; it does not interpret/stream/clone/repair/persist payloads. Separation stays: `DbArea` stores MemoRef, `MemoManager` owns payload, Array may carry MemoRef. `ACLONE()` copies the reference, not the payload.
# 24. Persistence and Serialization
Session-memory by default; persistence explicit. JSON: `JSONENCODE`/`JSONDECODE` with natural mappings (NIL<->null, logical<->boolean, numeric<->number, character<->string, array<->array, tuple/map<->object). Dates/date-times/memo refs/handles need explicit policy; `PORTABLE` vs `TYPED` modes (`{"$type":"date","value":"..."}`); streams/live handles rejected unless materialized. Encoded arrays may be stored via the memo subsystem (`MEMOPUT(JSONENCODE($A,"TYPED"),"application/json")`); the DBF stores the memo reference, not the array.
# 25. AI Integration
Arrays are a basic structured interchange type for AI workflows. Future `AIASKARRAY`/`AIEMBED` may return arrays. AI boundaries MUST serialize/clone rather than share mutable interpreter objects, validate count/depth, enforce type/byte limits, treat returned content as untrusted, and avoid implicit materialization of unbounded DB streams. Maps/named objects will eventually be better for named payloads.
# 26. Transaction Boundaries
DB transactions do not auto-snapshot or roll back ordinary script arrays; after `ROLLBACK`, `$A[1]` stays changed unless a future script-state transaction system is introduced. DB transactions govern persistent work (table buffers, record/memo/index mutations, commit/rollback), not scalar variables or arrays. Live tuple handles invalidated by a rollback are a tuple-lifecycle matter, not array rollback.
# 27. Runtime Limits
The runtime MUST protect against accidental/hostile allocation. Recommended configurable caps: max elements/array 1,000,000; max nested depth 64; max runtime array bytes 256 MB; cycles OFF. Possible `SET ARRAY MAXELEMENTS|MAXDEPTH|MAXBYTES TO ...` via ordinary SET routing + help metadata. Allocation checks MUST occur before substantial allocation. Track per-array count, total live elements, max depth, estimated bytes, object count (memory values are estimates).
# 28. Display Rules
A raw array through `FORMULA` SHOULD be concise (`<ARRAY id=17 length=210>`), not a full dump; detail belongs to `ARRAY LIST`. A future literal-like conversion MUST enforce max depth/element count/output length, cycle detection, and escaping; human-readable output SHOULD use braces when every element is safely representable.
# 29. Error Contract
Array errors MUST be explicit, cataloged, localizable, SelfDoc-usable. Message identifiers: `ARRAY_EXPECTED`, `ARRAY_INDEX_TYPE`, `ARRAY_INDEX_RANGE`, `ARRAY_DIMENSION_TYPE`, `ARRAY_DIMENSION_RANGE`, `ARRAY_TOO_LARGE`, `ARRAY_DEPTH`, `ARRAY_CYCLE`, `ARRAY_FROZEN`, `ARRAY_ITERATION_MUTATION`, `ARRAY_SORT_TYPES`, `ARRAY_COPY_RANGE`, `ARRAY_LITERAL_MISSING`, `ARRAY_INTERMEDIATE_TYPE`. Each carries a templated message (e.g. `Array index {index} is outside the valid range 1..{length}.`). Source-aware script errors SHOULD show filename, line, text, and caret when available.
# 30. Runtime Representation
Conceptual model (must follow the current expression architecture):
```cpp
struct ArrayValue;
using ArrayRef = std::shared_ptr<ArrayValue>;
using Value = std::variant<
    NilValue, bool, std::int64_t, double, std::string,
    DateValue, DateTimeValue, MemoRef, TupleValue, ArrayRef>;

struct ArrayValue {
    std::vector<Value> elements;
    std::uint64_t object_id = 0;
    std::uint64_t mutation_sequence = 0;
    std::uint64_t structure_sequence = 0;
    bool frozen = false; // reserved for future use
};
```
(See the Repository note: the real engine `Value` is a tagged `ValueKind`, not a `std::variant`; Phase 0 reconciles this.) Reserving `frozen` internally is acceptable if it does not complicate the initial patch.
# 31. Central Runtime API
All operations MUST pass through one shared array API; no parser/command/function pokes `std::vector<Value>` directly:
```cpp
namespace dottalk::array {
ArrayRef create_empty();
ArrayRef create_sized(std::size_t count);
ArrayRef create_nested(const std::vector<std::size_t>& dimensions);
std::size_t length(const ArrayRef&);
Value get(const ArrayRef&, std::size_t one_based_index);
void set(const ArrayRef&, std::size_t one_based_index, Value);
Value add(const ArrayRef&, Value);
ArrayRef resize(const ArrayRef&, std::size_t new_size);
ArrayRef clone_deep(const ArrayRef&);
bool equal_structural(const ArrayRef&, const ArrayRef&);
bool same_object(const ArrayRef&, const ArrayRef&);
}
```
# 32. Central Index Conversion
One shared helper MUST validate/convert script indexes: `std::size_t checked_array_offset(const ArrayValue&, const Value& script_index)` -- numeric + exact-integer + lower/upper-bound validation + one-based->zero-based conversion. No other code subtracts one from an array index.
# 33. Nested Array Allocation
`ARRAY(2,3)` creates two independent child arrays of length three; the implementation MUST NOT fill the outer array with repeated references to one child. (Recursive `create_nested(dims, depth)` per the spec.)
# 34. Parser and AST Requirements
Additions: array literals, postfix subscript expressions, multiple subscripts, indexed assignment targets, `DIMENSION` statements. AST nodes: `ArrayLiteralExpr{elements}`, `SubscriptExpr{base, indexes}`, `DimensionStmt{variable_name, dimensions}`. Subscript binds with function-call precedence (`$A[1] + 2` means `($A[1]) + 2`).
# 35. Generalized Assignment Targets
Array support SHOULD introduce/use a generalized `LValue` abstraction (`read()`/`write()`), with variable / array-element / future tuple-field / future map-entry implementations -- preparing compound assignment and named structured values without duplicating assignment logic.
# 36. Mutation Tracking
Every public mutation increments `mutation_sequence` once; structural mutations (length/order change: `AADD`, `ASIZE`, `ADEL`, `AINS`, `ASORT`) also increment `structure_sequence`. `ADEL`/`AINS` preserve length but change position and count as structural for iterator safety. Internal shifts count as one public mutation, not one per moved value.
# 37. Deep Clone Algorithm
`ACLONE()` MUST use a source-object->clone-object map, preserving shared child topology, preventing repeated cloning, and staying safe if cycles are ever allowed. Scalars copied normally; nested arrays cloned recursively; external handles retain ordinary value/reference semantics.
# 38. Thread Ownership
Arrays are owned by one interpreter session; no internal locking for a single-threaded interpreter. Crossing into GUI/AI/background threads requires serialize/clone/freeze or an explicit ownership transfer; mutable `ArrayRef` MUST NOT be shared across unrelated threads without synchronization.
# 39. Suggested Source Modules
Follow the current repo organization; logical boundaries resemble `src/xexpr/{value.hpp, array_value.*, array_compare.cpp, array_clone.cpp, array_functions.cpp}`, `src/cli|src/dotscript/{parser_array.cpp, evaluator_array.cpp, statement_dimension.cpp, cmd_array.cpp}`, `include/{foxref.hpp, dotref.hpp}`, `tests/{test_array_value.cpp, test_array_parser.cpp, test_array_functions.cpp}`. Reuse existing expression/parser/command-registration/error/function-registry patterns rather than a parallel subsystem.
# 40. Help and SelfDoc Integration
Every exposed command/function requires a usage contract (`HELP ARRAY`, `HELP FUNCTION ALEN`, ...). Recommended metadata fields: NAME, CANONICAL_NAME, CATEGORY, KIND, ORIGIN, REFERENCE_LANE, SYNTAX, ARGUMENTS, RETURNS, MUTATES, REFERENCE_BEHAVIOR, COMPATIBILITY, IMPLEMENTATION_STATUS, EXAMPLES, ERRORS, TEST_IDS. (Lane note: map these onto the existing SYSCMD/SYSFUNC + HELP metadata the catalogs harvest, not a parallel store.)
# 41. Implementation Phases
- **Phase 1 -- Runtime foundation:** `ArrayRef`/`ArrayValue`, array alternative in `Value`, object ids, literals, `ARRAY()`, `$A[n]` read/write, `ALEN`, `AADD`, `ASIZE`, `ACLONE`, `ASAME`, `ISARRAY`, cycle rejection, basic errors.
- **Phase 2 -- Compatibility functions:** `DIMENSION`, `DECLARE`, `ADEL`, `AINS`, `AFILL`, `ASCAN` (value form), `ACOPY`, `ASORT` (default), `ATAIL`.
- **Phase 3 -- Native diagnostics:** `ARRAY INFO/LIST/VALIDATE/STATS/LIMITS/TRACE` (before deeper integration, for observability).
- **Phase 4 -- Control flow:** possible `FOR EACH` + iterator structure-change detection; optional code-block runtime -> `AEVAL`, predicate `ASCAN`, comparator `ASORT`.
- **Phase 5 -- Data bridges:** `AFIELDS`, `DBSTRUCT`, tuple bridges, bounded materialization, JSON encode/decode, optional `SCATTER`/`GATHER`.
# 42. Unit-Test Matrix
Construction (empty/populated/trailing-comma/nested/missing-rejection/`ARRAY()`/`ARRAY(0|10|2,3)`/row-independence/negative+fractional+excessive rejection); Indexing (first/final/computed/zero/negative/out-of-range/character/fractional rejection, nested comma+bracket, non-array intermediate, function-result); Assignment (scalar/nested/array-ref, direct+indirect cycle rejection, mutation+structure sequence); References & cloning (identity share, `ACLONE` separation, nested independence, shared-topology preservation, `ASAME`, structural equality, case-sensitive/insensitive comparison); Functions (`ALEN`, `AADD`+return, `ASIZE` grow/shrink/zero, `ADEL`/`AINS` fixed length, `AFILL` whole/range/ref, `ASCAN` found/not/range, `ACOPY` defaults/ranges/overlap/shared, `ACLONE`, `ASORT` numeric/string/NIL/mixed-rejection, `ATAIL` populated/empty); Diagnostics (id reporting, nested listing, paging, validation, limits, trace, stats without double-count).
# 43. Script Test Set
Permanent scripts: `ARRAY_BASIC`, `ARRAY_REFERENCE`, `ARRAY_NESTED`, `ARRAY_FUNCTIONS`, `ARRAY_ERRORS`, `ARRAY_LOOP`, `ARRAY_DIAGNOSTICS`, `ARRAY_JSON`, `ARRAY_TUPLE_BRIDGE` (repo convention: lowercase `.dts`).
# 44. Phase 1 Acceptance Script
`ARRAY_PHASE1.DTS` -- target contract, executable only after the syntax/functions exist (and after Phase 0 settles `ASSERT`/`$VAR`/`NIL`): empty array + `ISARRAY`/`ALEN`, three `AADD`, index reads, `$B=$A` identity share, `ACLONE` separation + structural equality, `ASIZE` to 5 with NIL tail, `ARRAY(2,3)` grid writes/reads, and `ARRAY INFO/LIST/VALIDATE`.
# 45. Compatibility Acceptance Script
`ARRAY_COMPAT.DTS` -- `ADEL` fixed-length (last->NIL), `AINS` fixed-length (NIL inserted, last dropped), `AFILL` whole+range, `ASCAN` found/not-found, `ATAIL`.
# 46. Definition of Done
Complete only when: arrays live in the ordinary `Value`; literals/`ARRAY()` parse+evaluate; one-based read/write; nested + comma subscripts; cataloged out-of-range/type errors; assignment shares identity; `ACLONE` recursive + topology-preserving; Phase-1 compat functions correct; direct+indirect cycles rejected; limits enforced pre-allocation; native diagnostics report identity/contents/limits/integrity; arrays work in `$VAR`/expr/functions/assertions/loops; no array responsibility in `DbArea`; tuple/memo boundaries orthogonal; existing scalar/db/index/tuple/memo tests green; every public command/function has HELP+SelfDoc metadata; foxref/dotref provenance correct; implementation status truthful and runtime-proven.
# 47. Machine-Readable Canonical Summary
`DotScript_Arrays_Catalog_v1.json` is the machine-readable catalog (identity, normative core rules, syntax forms, command/function entries, provenance lane, mutation/return contracts, phase, status, exclusions, tests). It is an implementation seed and interchange artifact, not a substitute for runtime metadata; once the subsystem exists, generated metadata from source/runtime supersedes manually maintained status fields.
# 48. Final Architectural Statement
DotScript arrays are one-based, heterogeneous, mutable runtime objects with xBase-compatible reference semantics, created via brace literals / `ARRAY()` / `DIMENSION` / `DECLARE`; multidimensional arrays are nested; assignment shares identity; independent copies require `ACLONE()`. Established xBase names retain their meanings; Fox-compatible syntax is preserved where it serves the language; native DotTalk++ diagnostics, validation, tuple bridges, runtime limits, and structured integration remain visibly native. Arrays remain orthogonal to DBF storage, work areas, indexes, memo payloads, and tuple traversal -- a composite-value foundation for the next generation of DotScript without surrendering the historical language that already makes sense.

## Appendix A. Quick Reference

| Surface | Syntax | Origin | Phase |
|---|---|---|---:|
| Empty literal | `$A = {}` | xBase-family / DotScript | 1 |
| Populated literal | `$A = {1,2,3}` | xBase-family / DotScript | 1 |
| Constructor | `$A = ARRAY(10)` | xBase | 1 |
| Declaration | `DIMENSION $A[10]` | Fox/xBase | 2 |
| Declaration alias | `DECLARE $A[10]` | Fox/xBase | 2 |
| Read / Write | `$A[1]` / `$A[1] = value` | DotScript + xBase | 1 |
| Length / Append / Resize | `ALEN` / `AADD` / `ASIZE` | xBase | 1 |
| Clone / Identity / Type | `ACLONE` / `ASAME` / `ISARRAY` | xBase / DotTalk++ / DotTalk++ | 1 |
| Del / Ins / Fill / Scan / Copy / Sort / Tail | `ADEL`/`AINS`/`AFILL`/`ASCAN`/`ACOPY`/`ASORT`/`ATAIL` | xBase | 2 |
| Diagnostics | `ARRAY INFO/LIST/VALIDATE/STATS/LIMITS/TRACE` | DotTalk++ | 3 |
| Materialize tuples | `TUPMATERIALIZE(...)` | DotTalk++ | 5 |

## Appendix B. Source Alignment
Aligned with `include/dotref.hpp` (native surface / preferred identity), `include/foxref.hpp` (historical/compat surface that must describe implemented behavior truthfully), and the rule *runtime proves, source defines, HELP explains*. The core `A*` family was checked against the CA-Clipper/Harbour tradition; DotScript-specific syntax and native diagnostics remain project-defined.
