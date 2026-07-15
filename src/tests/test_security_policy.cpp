#include "xbase_security_policy.hpp"

#include <exception>

int main()
{
    using namespace xbase::security::policy;

    const auto standard = standard_profile();
    if (standard.allow_host_commands || standard.allow_network) return 1;

    bool host_blocked = false;
    bool network_blocked = false;
    try { enforce_host_commands_allowed(standard); }
    catch (const std::exception&) { host_blocked = true; }
    try { enforce_network_allowed(standard); }
    catch (const std::exception&) { network_blocked = true; }

    if (!host_blocked || !network_blocked) return 2;

    const auto permissive = permissive_profile();
    try {
        enforce_host_commands_allowed(permissive);
        enforce_network_allowed(permissive);
    } catch (...) {
        return 3;
    }

    return 0;
}
