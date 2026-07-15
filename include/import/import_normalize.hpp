#pragma once
// @dottalk.contract
// file: include/import/import_normalize.hpp
// subsystem: import
// role: Declares import-path helpers for loading external data into DotTalk++ workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include <string>
#include <cctype>

namespace dottalkpp::import
{
    inline std::string normalize_field_name(const std::string& input)
    {
        std::string result;
        result.reserve(input.size() + 2);

        for (unsigned char uc : input)
        {
            if (std::isalnum(uc))
            {
                result += static_cast<char>(std::toupper(uc));
            }
            else
            {
                result += '_';
            }
        }

        while (result.find("__") != std::string::npos)
        {
            result.replace(result.find("__"), 2, "_");
        }

        if (!result.empty() && std::isdigit(static_cast<unsigned char>(result[0])))
        {
            result = "F_" + result;
        }

        return result;
    }
}
