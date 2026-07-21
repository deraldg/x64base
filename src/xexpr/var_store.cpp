// src/xexpr/var_store.cpp
// DotScript scoped memory-variable store. See var_store.hpp.

#include "xexpr/var_store.hpp"

#include <utility>

namespace dottalk::dotscript {

std::string normalize_var_name(const std::string& name) {
    std::string key;
    key.reserve(name.size());
    for (char c : name) {
        if (c >= 'a' && c <= 'z') c = static_cast<char>(c - 'a' + 'A');
        key.push_back(c);
    }
    return key;
}

VarStore::VarStore() {
    frames_.emplace_back();   // frame 0 = PUBLIC/global, always present
}

void VarStore::push_scope() {
    frames_.emplace_back();
}

void VarStore::pop_scope() {
    if (frames_.size() > 1) {   // never pop frame 0
        frames_.pop_back();
    }
}

std::ptrdiff_t VarStore::find_frame(const std::string& key) const {
    for (std::ptrdiff_t i = static_cast<std::ptrdiff_t>(frames_.size()) - 1; i >= 0; --i) {
        if (frames_[static_cast<std::size_t>(i)].count(key) != 0) return i;
    }
    return -1;
}

void VarStore::declare(const std::string& name, VarScope scope, Value initial) {
    const std::string key = normalize_var_name(name);
    Frame& target = (scope == VarScope::Public) ? frames_.front() : frames_.back();
    target[key] = std::move(initial);
}

void VarStore::assign(const std::string& name, Value v) {
    const std::string key = normalize_var_name(name);
    const std::ptrdiff_t f = find_frame(key);
    if (f >= 0) {
        frames_[static_cast<std::size_t>(f)][key] = std::move(v);   // update nearest binding
    } else {
        frames_.back()[key] = std::move(v);                          // implicit: current frame
    }
}

bool VarStore::get(const std::string& name, Value& out) const {
    const std::string key = normalize_var_name(name);
    const std::ptrdiff_t f = find_frame(key);
    if (f < 0) return false;
    out = frames_[static_cast<std::size_t>(f)].at(key);
    return true;
}

bool VarStore::exists(const std::string& name) const {
    return find_frame(normalize_var_name(name)) >= 0;
}

bool VarStore::release(const std::string& name) {
    const std::string key = normalize_var_name(name);
    const std::ptrdiff_t f = find_frame(key);
    if (f < 0) return false;
    frames_[static_cast<std::size_t>(f)].erase(key);
    return true;
}

std::size_t VarStore::count() const noexcept {
    std::size_t n = 0;
    for (const Frame& fr : frames_) n += fr.size();
    return n;
}

void VarStore::clear() {
    frames_.clear();
    frames_.emplace_back();
}

VarStore& session_vars() {
    static VarStore store;
    return store;
}

} // namespace dottalk::dotscript
