#pragma once
// include/cli/text_match.hpp
// Pure text-matching helpers for fuzzy "did-you-mean" suggestions (AIF-047).
//
// Header-only and dependency-free so it is unit-testable standalone. Provides the
// canonical Soundex (the single implementation, also used by the DotScript SOUNDEX()
// function), bounded Levenshtein edit distance, and a soundex-aware ranker.

#include <algorithm>
#include <cctype>
#include <string>
#include <unordered_set>
#include <vector>

namespace dottalk::text {

inline std::string to_upper(std::string s) {
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

// Classic Soundex (4 chars). Canonical implementation — SOUNDEX() calls this too.
inline std::string soundex(const std::string& in) {
    std::string letters;
    for (char ch : in) {
        const unsigned char u = static_cast<unsigned char>(ch);
        if (std::isalpha(u)) letters.push_back(static_cast<char>(std::toupper(u)));
    }
    if (letters.empty()) return {};

    const auto code_for = [](char c) -> char {
        switch (c) {
            case 'B': case 'F': case 'P': case 'V': return '1';
            case 'C': case 'G': case 'J': case 'K': case 'Q':
            case 'S': case 'X': case 'Z': return '2';
            case 'D': case 'T': return '3';
            case 'L': return '4';
            case 'M': case 'N': return '5';
            case 'R': return '6';
            default: return '0';
        }
    };

    std::string out;
    out.reserve(4);
    out.push_back(letters[0]);
    char prev = code_for(letters[0]);
    for (std::size_t i = 1; i < letters.size() && out.size() < 4; ++i) {
        const char c = letters[i];
        const char code = code_for(c);
        if (c == 'H' || c == 'W') continue;
        if (code == '0') { prev = '0'; continue; }
        if (code != prev) out.push_back(code);
        prev = code;
    }
    while (out.size() < 4) out.push_back('0');
    return out.substr(0, 4);
}

// Case-insensitive Levenshtein edit distance.
inline std::size_t levenshtein(const std::string& aRaw, const std::string& bRaw) {
    const std::string a = to_upper(aRaw), b = to_upper(bRaw);
    const std::size_t n = a.size(), m = b.size();
    if (n == 0) return m;
    if (m == 0) return n;
    std::vector<std::size_t> prev(m + 1), cur(m + 1);
    for (std::size_t j = 0; j <= m; ++j) prev[j] = j;
    for (std::size_t i = 1; i <= n; ++i) {
        cur[0] = i;
        for (std::size_t j = 1; j <= m; ++j) {
            const std::size_t cost = (a[i - 1] == b[j - 1]) ? 0 : 1;
            cur[j] = std::min({prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost});
        }
        std::swap(prev, cur);
    }
    return prev[m];
}

// Rank candidates as near-matches of `term`. Tiers: 0 prefix, 1 substring, 2 same
// Soundex (phonetic — catches GAINT->GIANT), 3 small edit distance. Sorted by tier,
// then distance, then name. Case-insensitive; exact matches are skipped (they resolve
// upstream). Returns up to `limit` distinct original-case names.
inline std::vector<std::string>
rank_suggestions(const std::string& termRaw,
                 const std::vector<std::string>& candidates,
                 std::size_t limit) {
    const std::string term = to_upper(termRaw);
    if (term.empty()) return {};
    const std::string term_sx = soundex(term);
    const std::size_t maxd = std::max<std::size_t>(2, term.size() / 3 + 1);

    struct Scored { int tier; std::size_t dist; std::string name; };
    std::vector<Scored> hits;
    std::unordered_set<std::string> seen;

    for (const auto& raw : candidates) {
        const std::string c = to_upper(raw);
        if (c.empty() || c == term) continue;
        if (!seen.insert(c).second) continue;
        const std::size_t dist = levenshtein(term, c);
        int tier;
        if (c.rfind(term, 0) == 0)                                 tier = 0;   // prefix
        else if (c.find(term) != std::string::npos)                tier = 1;   // substring
        else if (!term_sx.empty() && soundex(c) == term_sx
                 && dist <= maxd + 1)                              tier = 2;   // phonetic
        else if (dist <= maxd)                                     tier = 3;   // near edit
        else continue;
        hits.push_back({tier, dist, raw});
    }

    std::sort(hits.begin(), hits.end(), [](const Scored& a, const Scored& b) {
        if (a.tier != b.tier) return a.tier < b.tier;
        if (a.dist != b.dist) return a.dist < b.dist;
        return a.name < b.name;
    });

    std::vector<std::string> out;
    for (const auto& h : hits) {
        if (out.size() >= limit) break;
        out.push_back(h.name);
    }
    return out;
}

} // namespace dottalk::text
