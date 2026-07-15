#pragma once

#include "xbase_security_policy.hpp"
#include "xbase_security_runtime.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <exception>
#include <iostream>
#include <string>

namespace cli::security {

inline std::string upper_trimmed(std::string value)
{
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const auto last = value.find_last_not_of(" \t\r\n");
    value = value.substr(first, last - first + 1);
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return value;
}

inline bool env_truthy(const char* name)
{
    const char* raw = std::getenv(name);
    if (!raw) return false;
    const std::string value = upper_trimmed(raw);
    return value == "1" || value == "TRUE" || value == "YES" || value == "ON";
}

inline xbase::security::policy::config external_process_policy()
{
    auto cfg = xbase::security::policy::standard_profile();
    cfg.allow_host_commands = env_truthy("DOTTALK_ALLOW_HOST_COMMANDS");
    cfg.allow_network = env_truthy("DOTTALK_ALLOW_NETWORK");
    return cfg;
}

inline bool authorize_external_process(const char* operation, bool requires_network)
{
    try {
        xbase::security::runtime::context ctx(external_process_policy());
        xbase::security::runtime::on_host_command_begin(ctx);
        if (requires_network) xbase::security::runtime::on_network_begin(ctx);
        return true;
    } catch (const std::exception& ex) {
        std::cout << operation << " blocked: " << ex.what() << "\n"
                  << "Set DOTTALK_ALLOW_HOST_COMMANDS=1 to allow delegated processes.\n";
        if (requires_network) {
            std::cout << "Set DOTTALK_ALLOW_NETWORK=1 to allow network access.\n";
        }
        return false;
    }
}

} // namespace cli::security
