#pragma once

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <limits>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/logical_nav.hpp"
#include "cli/settings.hpp"
#include "help/helpdata_messages.hpp"

namespace cli::nav {

enum class Endpoint {
    Top,
    Bottom,
    First,
    Last
};

inline std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

inline bool try_parse_int_token(const std::string& s, int& out)
{
    if (s.empty()) return false;

    std::size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    if (i == s.size()) return false;

    for (; i < s.size(); ++i) {
        if (!std::isdigit(static_cast<unsigned char>(s[i]))) return false;
    }

    try {
        const long long v = std::stoll(s);
        if (v < static_cast<long long>(std::numeric_limits<int>::min()) ||
            v > static_cast<long long>(std::numeric_limits<int>::max())) {
            return false;
        }
        out = static_cast<int>(v);
        return true;
    } catch (...) {
        return false;
    }
}

// 64-bit record-number token parser (RECNO64). A record number is unsigned;
// rejects overflow rather than wrapping. Use for absolute GO/GOTO/RECNO targets.
inline bool try_parse_u64_token(const std::string& s, std::uint64_t& out)
{
    if (s.empty()) return false;
    std::size_t i = (s[0] == '+') ? 1 : 0;
    if (i == s.size()) return false;
    for (std::size_t j = i; j < s.size(); ++j) {
        if (!std::isdigit(static_cast<unsigned char>(s[j]))) return false;
    }
    try {
        out = std::stoull(s.substr(i));
        return true;
    } catch (...) {
        return false;
    }
}

inline bool refresh_current(xbase::DbArea& A, const char* who)
{
    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavNoFileOpenText);
        return false;
    }
    if (!A.readCurrent()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavReadCurrentFailedText);
        return false;
    }
    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno64())}});
    }
    return true;
}

// Authoritative 64-bit absolute positioning (RECNO64).
inline bool go_absolute(xbase::DbArea& A, std::uint64_t n, const char* who)
{
    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavNoFileOpenText);
        return false;
    }
    if (n == 0) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::GoExpectedPositiveRecordNumberText);
        return false;
    }
    if (!A.gotoRec64(n) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavFailedText);
        return false;
    }
    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno64())}});
    }
    return true;
}

// 32-bit compatibility overload -> 64-bit path (preserves the negative-target
// diagnostic that uint64 can't express).
inline bool go_absolute(xbase::DbArea& A, int n, const char* who)
{
    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavNoFileOpenText);
        return false;
    }
    if (n <= 0) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::GoExpectedPositiveRecordNumberText);
        return false;
    }
    return go_absolute(A, static_cast<std::uint64_t>(n), who);
}

inline bool go_endpoint(xbase::DbArea& A, Endpoint ep, const char* who)
{
    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavNoFileOpenText);
        return false;
    }

    std::uint64_t rn = 0;

    switch (ep) {
    case Endpoint::Top:
    case Endpoint::First:
        rn = cli::logical_nav::first_recno(A);
        break;

    case Endpoint::Bottom:
    case Endpoint::Last:
        rn = cli::logical_nav::last_recno(A);
        break;
    }

    if (rn == 0) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavFailedText);
        return false;
    }

    if (!A.gotoRec64(rn) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavFailedText);
        return false;
    }

    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno64())}});
    }
    return true;
}

inline bool skip_relative(xbase::DbArea& A, int n, const char* who)
{
    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavNoFileOpenText);
        return false;
    }

    const bool talk = cli::Settings::instance().talk_on.load();

    int steps = (n >= 0 ? n : -n);
    const bool forward = (n >= 0);

    if (steps == 0) {
        if (!A.readCurrent()) {
            cli::cmdout::print_prefixed_message(
                who,
                dottalk::helpdata::MessageId::NavReadCurrentFailedText);
            return false;
        }
        if (talk) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::NavRecnoLine,
                {{"recno", std::to_string(A.recno64())}});
        }
        return true;
    }

    std::uint64_t current = A.recno64();
    std::uint64_t next = 0;
    bool moved = false;

    while (steps-- > 0) {
        next = forward
            ? cli::logical_nav::next_recno(A, current)
            : cli::logical_nav::prev_recno(A, current);

        if (next == 0) {
            if (!moved) {
                cli::cmdout::print_prefixed_message(
                    who,
                    dottalk::helpdata::MessageId::NavAtEndText);
                return false;
            }
            break;
        }

        current = next;
        moved = true;
    }

    if (!moved) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavAtEndText);
        return false;
    }

    if (!A.gotoRec64(current) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message(
            who,
            dottalk::helpdata::MessageId::NavReadCurrentFailedText);
        return false;
    }

    if (talk) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno64())}});
    }
    return true;
}

} // namespace cli::nav
