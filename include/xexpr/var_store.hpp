// src/xexpr/var_store.hpp
//
// DotScript scoped memory-variable store (DOTSCRIPT-ARRAYS lane, AIF-038, M1b-2).
//
// This is the value store the arrays lane's Phase-0 §1 mandates: the `$name`
// memory variables that hold typed values — including array references. It is the
// counterpart to macro substitution (`&name`), which is a *separate* operator lane
// and is NOT this store (you never macro-substitute a composite value).
//
// Ownership model (kept teaching-grade and single-source, AIF-037):
//   * The stored value type is the array lane's `dottalk::array::Value` variant
//     (NIL / bool / int64 / double / string / ArrayRef) — reused, not reinvented,
//     so a variable can hold a scalar OR an array with shared-reference identity.
//   * Names are case-insensitive (xBase family): keys are normalized to upper-ASCII.
//   * Scope is a stack of frames. Frame 0 is the PUBLIC/global frame and always
//     exists; entering a routine pushes a frame, leaving pops it (frame 0 is never
//     popped). PUBLIC variables live in frame 0 regardless of where declared; LOCAL
//     and implicit variables live in the current (top) frame. Lookup searches from
//     the innermost frame outward, so a LOCAL shadows a PUBLIC of the same name.
//
// PRIVATE dynamic-scope hiding and STATIC persistence are deliberately deferred; the
// model above is the honest, provable first cut (PLANNED → PARTIAL only on proof).

#pragma once

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

#include "xexpr/array_value.hpp"

namespace dottalk::dotscript {

// A DotScript variable value is exactly the array-lane value (scalars + ArrayRef).
using Value = dottalk::array::Value;

enum class VarScope {
    Public,   // frame 0, visible everywhere, persists until released
    Local     // current frame, discarded when the frame is popped
};

// Normalize a variable name to its case-insensitive key (upper-ASCII).
std::string normalize_var_name(const std::string& name);

class VarStore {
public:
    VarStore();

    // Scope frames (routine entry/exit). Frame 0 is never popped.
    void push_scope();
    void pop_scope();
    std::size_t depth() const noexcept { return frames_.size(); }

    // Declare with explicit scope: PUBLIC writes frame 0, LOCAL writes the top frame.
    void declare(const std::string& name, VarScope scope, Value initial);

    // Implicit assignment (STORE / `=`): update the nearest existing binding, or
    // create the variable in the current (top) frame if it does not exist.
    void assign(const std::string& name, Value v);

    // Lookup the nearest binding. Returns false if the name is not bound.
    bool get(const std::string& name, Value& out) const;
    bool exists(const std::string& name) const;

    // Remove the nearest binding of `name`. Returns true if something was removed.
    bool release(const std::string& name);

    // Diagnostics / lifecycle.
    std::size_t count() const noexcept;   // total distinct bindings across all frames
    void clear();                          // release everything, keep only empty frame 0

private:
    using Frame = std::unordered_map<std::string, Value>;
    std::vector<Frame> frames_;

    // Index of the nearest frame holding `key`, or -1. (Signed so callers can test < 0.)
    std::ptrdiff_t find_frame(const std::string& key) const;
};

// Process-wide session store, so the VAR command and the expression evaluator reach
// the same variables without threading a pointer through every call site (mirrors the
// existing thread-local error-context accessor pattern).
VarStore& session_vars();

} // namespace dottalk::dotscript
