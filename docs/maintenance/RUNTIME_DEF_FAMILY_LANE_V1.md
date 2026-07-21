# RUNTIME_DEF_FAMILY Lane V1

**Status:** active — DEFCMD shipped; `fn_custom` eval hook + DEFFN in progress; DEFTYPE planned.
**Owner intent:** give an AI (or developer) a way to mint *throwaway, session-only* commands,
functions, and field types at runtime — no rebuild, no source edit — as a testbed for token
parsing, command/expression routing, and custom-type behavior.
**Freshness:** 2026-07-21.

---

## 0. Governing rule — x8/x16/x32/x64 ("design for the largest, drop back")

> When targeting a mixed **x8 / x16 / x32 / x64** environment, it is easier to code for the
> **largest** capability first and then constrain (drop back) than to build up from the
> smallest.

Applied to this lane: design ONE unified runtime-definition facility around the *fullest*
capability (a DotScript/data-driven body shared by all surfaces), then let each surface —
`DEFCMD`, `DEFFN`, `DEFTYPE` — be a thin adapter that constrains that fullest form to its
target. Do not build three bespoke mechanisms bottom-up.

This rule is engine doctrine; record it wherever engine doctrine lives (CURRENT_TARGET /
AI_PORTAL / doctrine index) as the **x8x16x32x64 rule**.

---

## 1. The three registration seams (investigation, preserved)

DotTalk++ has three extension surfaces. They differ sharply in runtime mutability — which is
the whole story for this lane:

| Surface | Registration seam | Runtime-mutable today? | Lookup path |
|---|---|---|---|
| **Commands** | `dli::registry().add / add_extension` (command_registry) | **Yes** — live `std::function` map; `try_run` does `map_.find` per command | shell dispatch |
| **Field types / codecs** | `register_codec` / `register_field_type` / `codec_for` (field_codec) | **Yes** — "the single extensibility seam"; every store/fetch dispatches `codec_for(field.type)` | storage layer |
| **Expression functions** | `string_fn_specs()` / `date_fn_specs()` / `numeric_fn_specs()` (fn_string/date/numeric) | **No** — three **static const** `BuiltinFnSpec[]` tables of raw function pointers | expression evaluator |

Key consequences:

- **Commands were trivial** — the registry was already a live map. `DEFCMD`/`UNDEFCMD` shipped
  (commit `77ee573a3`): session-scoped, guarded against shadowing protected built-ins, never
  persisted. Added `CommandRegistry::remove()` for non-protected names.
- **Field types are structurally ready** — `register_codec`/`codec_for` is already dynamic; the
  worked example is the `X` = **pronoun** codec (`pronoun_encode`/`pronoun_decode` in
  `field_codec.cpp`). (Note: pronoun is a custom *field type*, **not** a function. The pronoun
  *function* accessors `PSUBJ`/`POBJ`/`PPOSS` are a documented but unbuilt future layer.)
- **Functions need new infrastructure** — the evaluator resolves a call by looping three static
  tables in two evaluators; there is no dynamic seam. This lane adds one (`fn_custom`).

### 1.1 The shared hard part — the "body" problem

A command's body can be plain text/DotScript. But a function's body (`BuiltinFnEval` =
`std::string(*)(const std::vector<std::string>&)`, a raw pointer) and a codec's encode/decode
are **C++ logic** — you cannot author arbitrary C++ at runtime. So runtime functions and types
must express behavior as either:

- **(a) an interpreted DotScript body**, or
- **(b) a data-driven / parameterized template** — an enumerated value-set, a formula, or a
  self-describing binary container. Pronoun's set-code stack is exactly this shape.

The `std::function` (not raw pointer) entry type is what lets a runtime body be captured.

---

## 2. Storage fallback — the OOP "mini-memo" custom field (design)

Per the x8x16x32x64 rule, the **widest** custom field type is the fallback everything else
constrains from: a **binary / `char[n]`-backed, self-describing "mini-memo"** — a length-prefixed
structure (small header + typed payload) stored through a generic "opaque/custom" `Codec`
registered via `register_codec`/`register_field_type`. Narrower custom types (enums, pronoun's
set stack) are *data-driven specializations* dropped back from that fullest container.

`DEFTYPE` (planned) registers such a codec at runtime: the type char + a value-set / format
spec, no C++ authored. This gives an AI runtime custom field types with no interpreter work.

---

## 3. Eval hook — `fn_custom` (this milestone)

New dynamic function seam, sibling to `fn_string` / `fn_date` / `fn_numeric`, with a matching
header in `include/cli/expr/` (`fn_custom.hpp`) as the codebase convention requires.

Entry type carries a real body (`std::function`, not a raw pointer):

```cpp
struct CustomFnEntry {
    std::string name;                 // UPPER
    int minArgs, maxArgs;
    std::function<std::string(const std::vector<std::string>&)> eval;
};
const CustomFnEntry* find_custom_fn(const std::string& nameUpper);   // nullptr if absent
bool register_custom_fn(...);  bool unregister_custom_fn(...);        // live registry singleton
bool is_builtin_fn(const std::string& nameUpper);                    // guard: don't shadow builtins
```

**Four insertion points** (additive; the three static tables are untouched):

1. `value_eval.cpp` — 4th block in the `Ident (` dispatch, after the numeric block, before the
   final `return false`.
2. `value_eval.cpp` — `is_known_value_fn_upper`: add a `find_custom_fn` membership check.
3. `rhs_eval.cpp` — new `call_custom_builtin` helper (mirrors `call_string_builtin`).
4. `rhs_eval.cpp` — invoke `call_custom_builtin` after `call_numeric_builtin` (~L756).

Both evaluators matter: `value_eval` is the scan/known-fn path; `rhs_eval` is the display (`?`)
/ CALC path. Custom fns must resolve in both.

`fn_custom.cpp` lives in `src/cli/expr/` and rides the `src/CMakeLists.txt` recursive glob (like
`value_eval.cpp`) — no explicit CMake entry.

---

## 4. DEFFN / UNDEFFN (this milestone — MVP)

Built-in commands (like `DEFCMD`), thin adapters onto the `fn_custom` registry:

- `DEFFN <NAME> = <text>` — register a session custom fn returning the text (MVP body ignores
  args). Guards: refuse to shadow a builtin fn (`is_builtin_fn`) or an existing custom fn not our
  own (redefining your own is OK).
- `UNDEFFN <NAME>` — remove a session custom fn.
- `DEFFN LIST` — list session custom fns.

Proof: `DEFFN GREET = hi` then `? GREET()` → `hi` inside the expression evaluator; `UNDEFFN GREET`
→ `? GREET()` no longer resolves. Session-only, never persisted.

Follow-up (not MVP): **formula body** `DEFFN NAME(a,b) = <expression>` evaluated through the
expression evaluator with args bound, then **DotScript body**.

---

## 5. Roadmap

| Unit | Surface | State |
|---|---|---|
| DEFCMD / UNDEFCMD | commands | **shipped** (`77ee573a3`) |
| `fn_custom` eval hook | functions (infra) | **shipped** (proven) |
| DEFFN / UNDEFFN (text body) | functions | **shipped** (proven) |
| DEFFN formula / DotScript body | functions | planned |
| Mini-memo generic custom codec | field types (storage) | **PARKED** (see 5.1) |
| DEFTYPE (data-driven codec) | field types | **PARKED** (see 5.1) |

All three surfaces converge on one philosophy: a live registry + a runtime body, built widest-
first per the x8x16x32x64 rule.

### 5.1 Parked — DEFTYPE / mini-memo custom codec (retrievable pin)

**Deferred by decision (2026-07-21).** Runtime custom *field types* stay parked until DotTalk++
genuinely ties custom types into the **type system** — real typing (validation, display,
coercion, catalog identity) rather than an opaque binary / mini-memo blob dressed up as a field.
A runtime `DEFTYPE` that only registers a container codec adds little until there is type
machinery behind it that makes the type actually *mean* something.

**Retrieval trigger:** revisit when field-type typing is tied in — i.e., when the
FIELD_TYPE_CODEC lane advances past the pronoun-style single-codec demo toward first-class typed
fields. The design above (mini-memo container + `register_codec` / `register_field_type` seam) is
preserved and ready; only the go/no-go decision is deferred. Nothing to build here now.

---

## 6. Safety model

- Never shadow protected built-ins (commands: `is_protected`; functions: `is_builtin_fn`).
- Never persist — session-only; everything vanishes on EXIT.
- Never clobber a pre-existing non-scratch entry; redefining your own scratch entry is allowed.
- Registry-backed removal only touches entries this facility created.
