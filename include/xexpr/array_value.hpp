// src/xexpr/array_value.hpp
//
// DotScript array runtime core (DOTSCRIPT-ARRAYS lane, AIF-038, M1a).
//
// This is the central array API the spec mandates (§31/§32/§37): one place owns
// array construction, one-based checked indexing, shared-reference assignment,
// topology-preserving deep clone, cycle rejection, and structural equality. No
// parser, command, or function pokes the element vector directly.
//
// The element leaf is the spec's conceptual runtime Value (§30). It is kept
// self-contained here so the array *graph mechanics* — where the real bugs live —
// can be unit-proven independently of the engine. Engine integration (M1b) binds
// this to xexpr::Value by adding ValueKind::Array + an ArrayRef payload and
// mapping scalar leaves; the mechanics below do not change.

#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <variant>
#include <vector>

namespace dottalk::array {

struct ArrayValue;
using ArrayRef = std::shared_ptr<ArrayValue>;

// NIL is a distinct value, not an empty string and not an empty array (spec §10).
struct NilValue {};
inline bool operator==(NilValue, NilValue) noexcept { return true; }

// Conceptual runtime value (spec §30). Integration maps this onto xexpr::Value.
//
// Numbers are `double` only — matching the engine's canonical number model
// (`xexpr::Value` / `dottalk::expr::EvalValue` are both double-based) and the xBase
// family's char-level cross-program compatibility: values cross program boundaries as
// characters, so a distinct integer kind would not survive a string round-trip. There
// is intentionally no `std::int64_t` leaf.
using Value = std::variant<
    NilValue,
    bool,
    double,
    std::string,
    ArrayRef>;

struct ArrayValue {
    std::vector<Value> elements;
    std::uint64_t object_id = 0;
    std::uint64_t mutation_sequence = 0;
    std::uint64_t structure_sequence = 0;
    bool frozen = false; // reserved (spec §30)
};

struct ArrayLimits {
    std::size_t max_elements = 1'000'000;
    std::size_t max_depth = 64;
};

enum class ArrayError {
    None,
    IndexType,      // index not an exact integer
    IndexRange,     // index outside 1..length
    Dimension,      // bad dimension in ARRAY()/create_nested
    TooLarge,       // exceeds max_elements
    Cycle,          // would create a prohibited reference cycle
    Frozen          // reserved
};

// ---- construction -----------------------------------------------------------
ArrayRef create_empty();
ArrayRef create_sized(std::size_t count);                         // NIL-filled
ArrayRef create_nested(const std::vector<std::size_t>& dims,
                       ArrayError& err);                          // independent children (§33)

// ---- inspection -------------------------------------------------------------
std::size_t length(const ArrayRef& a) noexcept;                   // ALEN (outer)
bool        is_array(const Value& v) noexcept;                    // ISARRAY

// ---- one-based checked indexing (§8, §32) -----------------------------------
// Converts a one-based script index to a zero-based offset; the ONLY place that
// subtracts one. false + err on non-integer / out-of-range.
bool checked_offset(const ArrayValue& a, std::int64_t one_based,
                    std::size_t& out, ArrayError& err) noexcept;

bool get(const ArrayRef& a, std::int64_t one_based, Value& out, ArrayError& err);
bool set(const ArrayRef& a, std::int64_t one_based, Value v, ArrayError& err); // no implicit resize; cycle-checked

// ---- mutation ---------------------------------------------------------------
bool  add(const ArrayRef& a, Value v, Value& appended, ArrayError& err);       // AADD
bool  resize(const ArrayRef& a, std::size_t new_len, ArrayError& err);         // ASIZE

// ---- identity / clone / equality --------------------------------------------
ArrayRef clone_deep(const ArrayRef& src);                         // ACLONE (topology-preserving §37)
bool     same_object(const ArrayRef& l, const ArrayRef& r) noexcept;           // ASAME
bool     equal_structural(const Value& l, const Value& r);        // == (cycle-safe §12.3)

// ---- cycle policy (§13) -----------------------------------------------------
// True if placing `candidate` into `container` would create a direct or indirect
// reference cycle.
bool would_create_cycle(const ArrayRef& container, const Value& candidate) noexcept;

} // namespace dottalk::array
