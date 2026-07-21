# PDLC-SHARED-P0 — Canonical DotTalk Value Decision v1

**Authoring basis:** Claude stewardship recommendation, reconciled by ChatGPT design  
**Date:** 2026-07-20  
**Status:** Accepted with amendments; maintainer sign-off pending  
**Canonical name:** DotTalk Value (DTV)  
**C++ type:** `dottalk::value::Value`  
**Engine code changed by this record:** None  
**Construction packet adjustment:** Added unsigned 64-bit Value support before authoritative build

## Decision

Adopt `dottalk::value::Value` as the single canonical DotTalk domain Value.

Retain a two-tier model:

```text
Domain tier
  DTV / dottalk::value::Value
  exact, stateful, source-of-truth

Evaluation tier
  xexpr::Value
  dottalk::expr::EvalValue
  rhs_eval ScalarValue
  deliberately fast and potentially lossy
```

The evaluation tier is a projection of DTV, not a competing domain model.

New tuple, reference, field, persistence, and array-interchange work is authored in DTV. Existing evaluation types converge through named adapters.

## Accepted stewardship principles

The following are accepted:

- no fourth value system;
- no big-bang replacement;
- conversions occur only at named seams;
- DTV is authoritative after a lossy evaluation projection;
- domain state must never be reconstructed from evaluation output;
- arrays use a live-reference/canonical-reference registry bridge;
- exact currency and record identity do not enter the double arithmetic path;
- native storage codecs remain the owners of field bytes;
- character form is the normative cross-program and cross-layer interchange.

## Amendment A — Unsigned RECNO64 is required

Signed `int64_t` is insufficient for the full `uint64_t` RECNO64 domain.

DTV therefore distinguishes:

```text
Integer          -> int64_t
UnsignedInteger  -> uint64_t
Decimal          -> ExactDecimal
Floating         -> double
```

This is required by the existing RECNO64 contract.

The proof set includes:

```text
9007199254740993
18446744073709551615
```

Neither value may pass through `double`.

Legacy evaluation projection rules:

```text
safe uint64 <= 2^53
  may project to double under explicit policy

uint64 > 2^53
  must project as canonical character text or fail exact projection

uint64 > INT64_MAX
  must never be cast to signed int64
```

## Amendment B — Canonical text needs a tagged, versioned grammar

Plain text such as `123`, `20260720`, or `NULL` is ambiguous without kind and state metadata.

The canonical wire must be:

```text
versioned
kind-tagged
state-tagged
locale-free
fully reversible
```

Conceptual examples:

```text
DTV1|P|I|-42
DTV1|P|U|9007199254740993
DTV1|P|N|1234500|4
DTV1|P|D|2026-07-20
DTV1|P|S|<encoded UTF-8>
DTV1|P|M|<memo-backend>|<memo-token>
DTV1|P|X|X|Pronoun|<encoded payload>
DTV1|P|A|42|3|1,7
DTV1|NULL|N
DTV1|BLANK|S
DTV1|UNAVAILABLE|A|<diagnostic>
DTV1|ERROR|<diagnostic>
```

The final escaping or length-prefix format is decided by proof.

Required invariant:

```text
parse(canonical_text(value)) == value
```

Human display remains a separate formatter.

## Amendment C — Comparison is semantic

Canonical text is the deterministic interchange representation. It is not the general ordering algorithm.

Lexical ordering would incorrectly place `10` before `2`.

Comparison is kind- and state-aware:

```text
Integer / UnsignedInteger / Decimal
  exact numeric comparison

Floating
  documented IEEE comparison policy

Date / DateTime
  chronological comparison

Character
  locale-free canonical byte/code-point policy

MemoReference
  identity comparison, not payload comparison

ArrayReference
  handle/path identity comparison unless deep comparison is requested

Custom
  registered comparator, otherwise canonical-text fallback

states
  equality and ordering policies are explicit and separate
```

Canonical text is a fallback for unknown/custom values and a proof oracle, not a substitute for numeric semantics.

## Amendment D — Field-code mapping stays outside Value

The stable mapping:

```text
C/N/F/I/D/T/M/Y/B/X -> ValueKind
```

must be single-source and registry-driven.

It belongs in:

```text
EffectiveFieldType
FieldSemanticRegistry
field-codec/type metadata adapters
```

It does not belong as a DBF switch inside `Value`.

This preserves orthogonality:

```text
Value knows semantic kind
field registry knows storage/type code
source adapter knows physical source
```

## Amendment E — Array Nil has one canonical state

The array adapter must not map Nil ambiguously to “Blank/Null.”

Recommended mapping:

```text
array::Nil -> DTV Null
```

DBF storage blanks remain `DTV Blank`.

An explicit array blank value may be added later if the array language requires it.

## Amendment F — Projection reports loss

Named adapters return structured results:

```cpp
enum class ProjectionLoss {
    None,
    StateCollapsed,
    PrecisionLost,
    RangeLost,
    TypeCollapsed,
    ReferenceSerialized
};

template<class T>
struct ProjectionResult {
    bool ok;
    T value;
    ProjectionLoss loss;
    std::string diagnostic;
};
```

No exact-to-double conversion occurs invisibly.

## Canonical contract additions

DTV must provide, directly or through companion services:

```text
total canonical wire round-trip
semantic comparison
explicit evaluation projection
field text conversion through registry metadata
state-preserving construction
signed and unsigned exact integers
exact decimals
date/datetime
memo/custom/array references
loss diagnostics
```

The core `Value` remains an immutable semantic object. Formatting, field codes, storage bytes, addresses, and validation issues remain outside it.

## Array identity decision

Retain the stewardship bridge:

```text
live:
  shared_ptr<ArrayValue>

canonical:
  ArrayReference { object_id, generation, index_path }

registry:
  object_id -> weak_ptr<ArrayValue> + generation
```

Resolution failure produces:

```text
ValueState::Unavailable
ValueKind::ArrayReference
```

not Nil, Blank, or Error.

The live array object requires a generation.

## Convergence sequence

```text
1. Land the compile-only DTV foundation.
2. Complete canonical wire round-trip.
3. Complete semantic comparison.
4. Add DTV <-> evaluation adapters.
5. Add DTV <-> array adapters and registry bridge.
6. Add DTV <-> field-codec/type adapters.
7. Prove Y currency, X custom, and RECNO64 tuple cells.
8. Freeze TupleCell/TupleRow contracts from evidence.
9. Route new features through DTV.
10. Retain the double evaluation hot path.
```

## Phase-0 exit criteria

```text
[ ] maintainer signs off two-tier model
[ ] UnsignedInteger accepted
[ ] canonical wire grammar accepted
[ ] semantic comparison policy accepted
[ ] registry-owned type-code mapping accepted
[ ] array Nil -> Null accepted
[ ] projection-loss result accepted
[ ] compile-only authoritative build passes
```
