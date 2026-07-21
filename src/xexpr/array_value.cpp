// src/xexpr/array_value.cpp
// DotScript array runtime core. See array_value.hpp. Single source of truth for
// array graph mechanics (DOTSCRIPT-ARRAYS lane, AIF-038, M1a). Unit-proven.

#include "xexpr/array_value.hpp"

#include <atomic>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace dottalk::array {

namespace {

std::uint64_t next_object_id() noexcept
{
    static std::atomic<std::uint64_t> counter{0};
    return ++counter;
}

ArrayRef make_array()
{
    auto a = std::make_shared<ArrayValue>();
    a->object_id = next_object_id();
    return a;
}

const ArrayRef* as_array(const Value& v) noexcept
{
    return std::get_if<ArrayRef>(&v);
}

// Depth-first reachability over the array graph: can `from` reach `target`?
bool reaches(const ArrayValue* from, const ArrayValue* target,
             std::unordered_set<const ArrayValue*>& visited) noexcept
{
    if (from == nullptr) return false;
    if (from == target) return true;
    if (!visited.insert(from).second) return false;   // already explored
    for (const Value& e : from->elements) {
        if (const ArrayRef* child = as_array(e)) {
            if (reaches(child->get(), target, visited)) return true;
        }
    }
    return false;
}

ArrayRef clone_rec(const ArrayRef& src,
                   std::unordered_map<const ArrayValue*, ArrayRef>& clones)
{
    if (!src) return nullptr;
    auto it = clones.find(src.get());
    if (it != clones.end()) return it->second;        // shared child cloned once (§37)

    ArrayRef dst = make_array();
    clones.emplace(src.get(), dst);                   // register BEFORE recursing
    dst->elements.reserve(src->elements.size());
    for (const Value& e : src->elements) {
        if (const ArrayRef* child = as_array(e)) {
            dst->elements.push_back(clone_rec(*child, clones));
        } else {
            dst->elements.push_back(e);               // scalar: plain copy
        }
    }
    return dst;
}

bool equal_rec(const Value& l, const Value& r,
               std::unordered_set<std::uint64_t>& comparing)
{
    const ArrayRef* la = as_array(l);
    const ArrayRef* ra = as_array(r);
    if ((la != nullptr) != (ra != nullptr)) return false;   // one array, one scalar

    if (la && ra) {
        const ArrayValue* lp = la->get();
        const ArrayValue* rp = ra->get();
        if (lp == rp) return true;                          // same object
        if (!lp || !rp) return false;
        if (lp->elements.size() != rp->elements.size()) return false;
        // visited-pair guard (cycle safety, §12.3): pack the two ids into a key.
        const std::uint64_t key = (lp->object_id << 32) ^ rp->object_id;
        if (!comparing.insert(key).second) return true;     // already comparing this pair
        for (std::size_t i = 0; i < lp->elements.size(); ++i) {
            if (!equal_rec(lp->elements[i], rp->elements[i], comparing)) return false;
        }
        return true;
    }
    // Both scalars: variant equality (NilValue/bool/int64/double/string).
    return l == r;
}

} // namespace

// ---- construction -----------------------------------------------------------

ArrayRef create_empty() { return make_array(); }

ArrayRef create_sized(std::size_t count)
{
    ArrayRef a = make_array();
    a->elements.assign(count, Value{NilValue{}});
    return a;
}

ArrayRef create_nested(const std::vector<std::size_t>& dims, ArrayError& err)
{
    err = ArrayError::None;
    if (dims.empty()) return create_empty();

    // Build depth-first so each child is an INDEPENDENT array (§33), never a
    // repeated reference to one shared child.
    const std::size_t count = dims.front();
    ArrayRef a = create_sized(count);
    if (dims.size() > 1) {
        std::vector<std::size_t> rest(dims.begin() + 1, dims.end());
        for (std::size_t i = 0; i < count; ++i) {
            a->elements[i] = create_nested(rest, err);
            if (err != ArrayError::None) return nullptr;
        }
    }
    return a;
}

// ---- inspection -------------------------------------------------------------

std::size_t length(const ArrayRef& a) noexcept
{
    return a ? a->elements.size() : 0;
}

bool is_array(const Value& v) noexcept { return as_array(v) != nullptr; }

// ---- indexing ---------------------------------------------------------------

bool checked_offset(const ArrayValue& a, std::int64_t one_based,
                    std::size_t& out, ArrayError& err) noexcept
{
    if (one_based < 1) { err = ArrayError::IndexRange; return false; }
    const std::size_t idx = static_cast<std::size_t>(one_based);
    if (idx > a.elements.size()) { err = ArrayError::IndexRange; return false; }
    out = idx - 1;                                        // the ONE place we subtract 1
    err = ArrayError::None;
    return true;
}

bool get(const ArrayRef& a, std::int64_t one_based, Value& out, ArrayError& err)
{
    if (!a) { err = ArrayError::IndexRange; return false; }
    std::size_t off = 0;
    if (!checked_offset(*a, one_based, off, err)) return false;
    out = a->elements[off];
    return true;
}

bool set(const ArrayRef& a, std::int64_t one_based, Value v, ArrayError& err)
{
    if (!a) { err = ArrayError::IndexRange; return false; }
    std::size_t off = 0;
    if (!checked_offset(*a, one_based, off, err)) return false;   // no implicit resize (§9)
    if (would_create_cycle(a, v)) { err = ArrayError::Cycle; return false; }
    a->elements[off] = std::move(v);
    ++a->mutation_sequence;
    err = ArrayError::None;
    return true;
}

// ---- mutation ---------------------------------------------------------------

bool add(const ArrayRef& a, Value v, Value& appended, ArrayError& err)
{
    if (!a) { err = ArrayError::IndexRange; return false; }
    if (would_create_cycle(a, v)) { err = ArrayError::Cycle; return false; }
    a->elements.push_back(std::move(v));
    appended = a->elements.back();
    ++a->mutation_sequence;
    ++a->structure_sequence;
    err = ArrayError::None;
    return true;
}

bool resize(const ArrayRef& a, std::size_t new_len, ArrayError& err)
{
    if (!a) { err = ArrayError::IndexRange; return false; }
    if (new_len > a->elements.size()) {
        a->elements.resize(new_len, Value{NilValue{}});           // grow with NIL
    } else {
        a->elements.resize(new_len);                              // shrink, discard tail
    }
    ++a->mutation_sequence;
    ++a->structure_sequence;
    err = ArrayError::None;
    return true;
}

// ---- identity / clone / equality --------------------------------------------

ArrayRef clone_deep(const ArrayRef& src)
{
    std::unordered_map<const ArrayValue*, ArrayRef> clones;
    return clone_rec(src, clones);
}

bool same_object(const ArrayRef& l, const ArrayRef& r) noexcept
{
    return l.get() == r.get() && l.get() != nullptr;
}

bool equal_structural(const Value& l, const Value& r)
{
    std::unordered_set<std::uint64_t> comparing;
    return equal_rec(l, r, comparing);
}

// ---- cycle policy -----------------------------------------------------------

bool would_create_cycle(const ArrayRef& container, const Value& candidate) noexcept
{
    const ArrayRef* ca = as_array(candidate);
    if (!ca || !*ca || !container) return false;
    // Inserting `candidate` into `container` cycles iff candidate can already
    // reach container (or is container).
    std::unordered_set<const ArrayValue*> visited;
    return reaches(ca->get(), container.get(), visited);
}

} // namespace dottalk::array
