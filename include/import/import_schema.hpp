#pragma once
// @dottalk.contract
// file: include/import/import_schema.hpp
// subsystem: import
// role: Declares import-path helpers for loading external data into DotTalk++ workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include <string>

namespace dottalkpp::import
{

    struct ColumnProfile
    {
        std::string sourceName;
        std::string normalizedName;

        int maxWidth = 0;

        bool seenInteger = false;
        bool seenDecimal = false;
        bool seenDate = false;
        bool seenLogical = false;
        bool seenText = false;

        int decimalPlaces = 0;
        bool hasNull = false;
    };


    struct FieldDefinition
    {
        std::string name;

        char type = 'C';
        int width = 0;
        int decimals = 0;
    };

}
