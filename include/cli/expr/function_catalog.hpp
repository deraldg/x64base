#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace dottalk::expr {

enum class FunctionCategory {
    String,
    Search,
    Construction,
    Conversion,
    Logical,
    Numeric,
    Date,
    Misc
};

struct FunctionDoc {
    std::string name;                  // canonical uppercase
    std::vector<std::string> aliases;  // alternate names
    FunctionCategory category{FunctionCategory::Misc};

    std::size_t min_args{0};
    std::size_t max_args{0};

    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

const FunctionDoc* get_function_doc(const std::string& name);
std::vector<const FunctionDoc*> all_function_docs();

const char* to_string(FunctionCategory cat);

} // namespace dottalk::expr