# Canonical DotTalk Value (DTV) — DECISION ACCEPTED (maintainer sign-off)

**Signed off:** 2026-07-20 by the maintainer. Shared Phase-0 across tuples (PDLC packet),
arrays (AIF-038), and the expression runtime. **No engine code changed by this record.**

## Decision

Adopt `dottalk::value::Value` as the single canonical **DotTalk Value (DTV)** — exact,
stateful, char-canonical — under a **two-tier model**: DTV is the domain / storage /
tuple / reference / interchange source-of-truth; the engine's `double`-based value
(`xexpr::Value`, `dottalk::expr::EvalValue`, `rhs_eval`'s `ScalarValue`) is DTV's
*evaluation projection*, fast and deliberately lossy, not a rival. New tuple / reference
/ field / persistence / array-interchange work is authored in DTV; existing evaluation
types converge through named adapters. No fourth value type; no big-bang replacement;
conversions only at named seams; DTV authoritative after a lossy projection; domain state
never reconstructed from evaluation output.

## Accepted amendments (ChatGPT design, reconciled)

- **A — Unsigned RECNO64.** DTV distinguishes `Integer(int64)` and
  `UnsignedInteger(uint64)` (plus `Decimal`/`Floating`). **Verified load-bearing:** the
  engine defines `using RecNo = std::uint64_t` (`include/xindex/key_common.hpp`) and all
  nav/lock APIs take `std::uint64_t`, so the signed-only framing in Claude's original
  recommendation was insufficient. Proof values `9007199254740993` and
  `18446744073709551615` (UINT64_MAX) must never pass through `double`; `> INT64_MAX`
  must never be cast to signed.
- **B — Tagged, versioned canonical wire.** The interchange form is
  `DTV1|<state>|<kind>|<payload…>`, locale-free and fully reversible
  (`parse(canonical_text(v)) == v`). Human display is a separate formatter. (Sharpens
  Claude's under-specified "canonical_text".)
- **C — Comparison is semantic, not lexical.** Canonical text is the interchange form
  and proof oracle, **not** the ordering algorithm (lexical would order `10 < 2`).
  Comparison is kind/state-aware (numeric compares numerically, dates chronologically,
  memo by identity, etc.); canonical text is only the fallback for custom/unknown.
  (Corrects Claude's recommendation, which conflated serialization with ordering.)
- **D — Field-code mapping stays outside `Value`.** `C/N/F/I/D/T/M/Y/B/X → ValueKind`
  lives in `EffectiveFieldType` / the field-semantic registry (single-source, AIF-030),
  never as a DBF switch inside `Value`. Orthogonality: Value knows semantic kind; the
  registry knows storage code; the source adapter knows physical source.
- **E — Array Nil → DTV `Null`.** DBF storage blanks remain DTV `Blank`. An explicit
  array blank may be added later if the array language needs it.
- **F — Projection reports loss.** Adapters return `ProjectionResult<T>{ok, value, loss,
  diagnostic}` with a `ProjectionLoss` enum (None/StateCollapsed/PrecisionLost/RangeLost/
  TypeCollapsed/ReferenceSerialized). No exact→double conversion occurs invisibly.

## Array identity (retained bridge)

Live `shared_ptr<ArrayValue>` ↔ canonical `ArrayReference{object_id, generation,
index_path}`, via a registry `object_id → weak_ptr<ArrayValue> + generation`. Resolution
failure yields `ValueState::Unavailable` + `ValueKind::ArrayReference` (not Nil/Blank/
Error). **Downstream on the runtime side: the live `ArrayValue` must gain a `generation`
field** (currently it has only an atomic `object_id`).

## Evidence

- ChatGPT amended the first-build packet to add `ValueKind::UnsignedInteger`, a `uint64`
  payload, and `Value::unsigned_integer()`; standalone build clean (GNU 14.2.0, C++17),
  ctest 1/1, smoke now prints `recno64_max=18446744073709551615`. See
  `FIRST_BUILD_TRANSCRIPT_v2_unsigned.md` and `CLAUDE_VALUE_RECONCILIATION_DELTA.md`.
- Claude verified the unsigned-recno premise against the live tree but has **not** yet
  rebuilt the *amended* packet (amended source not yet delivered) or run the MSVC
  authoritative build.

## Phase-0 exit criteria

```
[x] maintainer signs off two-tier model
[x] UnsignedInteger accepted
[x] canonical wire grammar accepted (tagged/versioned; final escaping TBD by proof)
[x] semantic comparison policy accepted
[x] registry-owned type-code mapping accepted
[x] array Nil -> Null accepted
[x] projection-loss result accepted
[x] compile-only authoritative D:\code\ccode build passes   <- MSVC-green 2026-07-20
```

**Phase-0 COMPLETE (8/8).** The DTV foundation is integrated into the authoritative tree
as an isolated `dottalk_value` static lib (value + reference sources, real
`dottalk::memo::MemoRef`, excluded from the `dottalkpp` glob, linked into `dottalkpp`,
foundation smoke test target added) and the **MSVC Release build is green**. Claude
pre-verified the real-`MemoRef` integration under g++ before the MSVC build; the smoke
proves signed/unsigned exact integers (incl. UINT64_MAX), ExactDecimal, reference
parse/reject, and exact address text. No `DbArea`/tuple/expression/array/field-codec
integration yet — that is the next construction sequence.

## Next steps

1. ChatGPT: deliver the amended source packet; build the next standalone contract step
   (tagged canonical wire round-trip + semantic comparison service + adapters).
2. Claude: rebuild the amended packet under g++; then perform the authoritative
   compile-only integration when authorized; add a `generation` field to the runtime
   `ArrayValue` when the array↔DTV bridge is wired.
3. Tuple lane intake remains a separate open item; this decision is its prerequisite,
   now satisfied.

## Provenance

- Decision (ChatGPT): `PDLC_SHARED_P0_CANONICAL_DOT_TALK_VALUE_DECISION_v1.md`.
- Delta: `CLAUDE_VALUE_RECONCILIATION_DELTA.md`. Transcript:
  `FIRST_BUILD_TRANSCRIPT_v2_unsigned.md`.
- Claude recommendation + packet evaluation: session outputs
  `CANONICAL_VALUE_RECOMMENDATION_2026-07-20.md`,
  `PDLC_FIRST_BUILD_PACKET_EVALUATION_2026-07-20.md`.
