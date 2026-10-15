#include "cli/help_router.hpp"

#include <iostream>
#include <string>

namespace {

int failures = 0;

void check(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

void check_explicit_namespace(const std::string& raw, const char* label) {
    const dottalk::help::HelpOpts opts = dottalk::help::parse_opts(raw);
    check(!opts.predOnly, label);
    check(opts.term == "PREDICATES", "explicit namespace must retain PREDICATES term");
}

} // namespace

int main() {
    {
        const dottalk::help::HelpOpts opts = dottalk::help::parse_opts("PREDICATES");
        check(opts.predOnly, "bare PREDICATES must retain predicate-help shortcut");
        check(opts.term.empty(), "bare PREDICATES shortcut must consume the term");
    }
    {
        const dottalk::help::HelpOpts opts = dottalk::help::parse_opts("/PRED");
        check(opts.predOnly, "explicit /PRED must select predicate help");
    }
    {
        const dottalk::help::HelpOpts opts = dottalk::help::parse_opts("/DOT PREDICATES");
        check(opts.onlyDot, "/DOT must select the DOT namespace");
        check_explicit_namespace("/DOT PREDICATES",
                                 "/DOT PREDICATES must not become generic predicate help");
    }
    {
        const dottalk::help::HelpOpts opts = dottalk::help::parse_opts("/FOX PREDICATES");
        check(opts.onlyFox, "/FOX must select the FOX namespace");
        check_explicit_namespace("/FOX PREDICATES",
                                 "/FOX PREDICATES must not become generic predicate help");
    }
    {
        const dottalk::help::HelpOpts opts = dottalk::help::parse_opts("/ED PREDICATES");
        check(opts.onlyEd, "/ED must select the education namespace");
        check_explicit_namespace("/ED PREDICATES",
                                 "/ED PREDICATES must not become generic predicate help");
    }

    if (failures != 0) {
        std::cerr << failures << " help-router assertion(s) failed\n";
        return 1;
    }
    std::cout << "help-router namespace precedence: PASS\n";
    return 0;
}
