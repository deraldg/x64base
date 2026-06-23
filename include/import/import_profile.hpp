#pragma once
// @dottalk.contract
// file: include/import/import_profile.hpp
// subsystem: import
// role: Declares import-path helpers for loading external data into DotTalk++ workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include <cstddef>
#include <string>

namespace dottalkpp::import
{
    struct ColumnProfile
    {
        bool seenInteger = false;
        bool seenDecimal = false;
        bool seenDate = false;
        bool seenLogical = false;
        bool seenText = false;

        bool sawAnyNonEmpty = false;
        std::size_t maxLen = 0;

        std::size_t maxIntegerDigits = 0;
        std::size_t maxDecimalDigits = 0;
        bool sawNegative = false;
    };

    bool is_integer_text(const std::string& s);
    bool is_decimal_text(const std::string& s);
    bool is_date_text(const std::string& s);
    bool is_logical_text(const std::string& s);

    void update_profile(ColumnProfile& profile, const std::string& value);
    std::string classify_profile(const ColumnProfile& profile);

    char proposed_target_type(const ColumnProfile& profile);
    int proposed_target_width(const ColumnProfile& profile);
    int proposed_target_decimals(const ColumnProfile& profile);
}
