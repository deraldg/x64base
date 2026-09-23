// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <algorithm>
#include <cctype>
#include <charconv>
#include <optional>
#include <string>
#include <string_view>
#include <system_error>

namespace dottalk { namespace expr {

inline std::string up(std::string s) {
  for (auto& c: s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
  return s;
}

inline bool iequals(std::string_view a, std::string_view b) {
  if (a.size()!=b.size()) return false;
  for (size_t i=0;i<a.size();++i) {
    unsigned char ca = static_cast<unsigned char>(a[i]);
    unsigned char cb = static_cast<unsigned char>(b[i]);
    if (std::toupper(ca)!=std::toupper(cb)) return false;
  }
  return true;
}

// PERF-3 (AIF-168, 2026-09-22): std::from_chars, NOT std::stod.
//
// The old body allocated a std::string and called stod, WHICH THROWS on
// non-numeric text -- so every char-leaf comparison paid a thrown-and-caught
// C++ exception per coercion attempt, measured at ~1.3 us per call in the
// sandbox harness (a bare BAND = 'CSCI' leaf pays TWO: the field probe and
// the literal probe -- 2.6 of its 3.0 us). Worse than the serial cost:
// concurrent throws serialize on the unwinder's global lock, which is the
// measured function-WHERE plateau at 6-12 workers (PERF-2 MEASURED, charter).
// from_chars is non-throwing, non-allocating, and locale-free.
//
// Semantics preserved from the stod body, deliberately:
//   - leading whitespace is skipped (stod did, via strtod);
//   - a leading '+' is accepted (stod did; from_chars alone refuses it),
//     but only ONE sign total -- "+-3" stays refused;
//   - trailing garbage refuses, as before (idx != size).
// Semantics CHANGED, deliberately: stod accepted hex floats ("0x10" -> 16)
// and locale-grouped digits; xBase numerics are decimal and canonical, so
// both now refuse. from_chars still accepts inf/nan spellings as stod did.
inline std::optional<double> to_number(std::string_view s) {
  const char* b = s.data();
  const char* e = b + s.size();
  while (b != e && std::isspace(static_cast<unsigned char>(*b))) ++b;
  if (b != e && *b == '+') {
    const char* n = b + 1;
    if (n == e || (*n != '-' && *n != '+')) b = n;
  }
  if (b == e) return std::nullopt;
  double v = 0.0;
  const auto res = std::from_chars(b, e, v);
  if (res.ec != std::errc() || res.ptr != e) return std::nullopt;
  return v;
}

}} // namespace



