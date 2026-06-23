#include "dt/meta/metacollect.hpp"

#include <exception>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    try {
        dt::meta::CollectOptions options;

        if (argc > 1 && argv[1]) {
            options.workspace_root = argv[1];
        } else {
            options.workspace_root = ".";
        }

        const auto result = dt::meta::collect_catalog_facts(options);

        for (const auto& warning : result.warnings) {
            std::cerr << "METACOLLECT warning: " << warning << '\n';
        }

        dt::meta::write_metafacts_csv(std::cout, result.facts);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "METACOLLECT error: " << ex.what() << '\n';
        return 2;
    }
}
