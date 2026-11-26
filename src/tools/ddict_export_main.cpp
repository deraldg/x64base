// @dottalk.file v1
// subsystem: datadict
// layer: tool
// owner: member.derald
// status: supported
#include "datadict/ddict_catalog_view.hpp"
#include <iostream>
#include <stdexcept>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: ddict_export <catalog-directory> (JSON to stdout; 0 clean, 2 review, 1 failure)\n";
        return 1;
    }
    try {
        if (!std::filesystem::is_directory(argv[1])) throw std::runtime_error("catalog directory missing");
        const auto view = dottalk::datadict::read_catalog_view(argv[1]);
        dottalk::datadict::write_catalog_json(view, std::cout);
        if (!std::cout) return 1;
        return view.diagnostics.empty() ? 0 : 2;
    } catch (const std::exception& e) {
        std::cerr << "DDICT export failed: " << e.what() << '\n';
        return 1;
    }
}
