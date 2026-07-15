#include "fox_standard_render.hpp"

#include "fox_standard_catalog.hpp"

#include <sstream>
#include <string>
#include <vector>

namespace dottalk::foxstd {
namespace {

void emit_list(std::ostringstream& oss,
               const char* heading,
               const std::vector<std::string>& items)
{
    if (items.empty()) {
        return;
    }

    oss << heading << "\n";
    for (const auto& item : items) {
        oss << "  " << item << "\n";
    }
    oss << "\n";
}

} // namespace

std::string render_doc(const std::string& command)
{
    const FoxStandardDoc* doc = get(command);
    if (!doc) {
        return "FOXSTANDARD: no historical reference entry for " + command + ".";
    }

    std::ostringstream oss;
    oss << doc->command << "\n";
    oss << "\n";
    oss << doc->summary << "\n\n";

    emit_list(oss, "Historical Syntax:", doc->syntax);
    emit_list(oss, "Examples:", doc->examples);
    emit_list(oss, "Notes:", doc->notes);
    emit_list(oss, "Aliases:", doc->aliases);
    emit_list(oss, "Versions:", doc->versions);

    return oss.str();
}

std::string render_topic_list()
{
    const auto topics = list_topics();

    std::ostringstream oss;
    oss << "FOXSTANDARD topics (" << topics.size() << "):\n";

    constexpr int per_line = 4;
    int col = 0;

    for (const auto& topic : topics) {
        oss << "  " << topic;
        ++col;

        if (col >= per_line) {
            oss << "\n";
            col = 0;
        } else {
            const std::size_t pad_to = 24;
            if (topic.size() < pad_to) {
                oss << std::string(pad_to - topic.size(), ' ');
            } else {
                oss << "  ";
            }
        }
    }

    if (col != 0) {
        oss << "\n";
    }

    oss << "\nUse: FOXSTANDARD <topic>\n";
    oss << "Example: FOXSTANDARD USE\n";

    return oss.str();
}

} // namespace dottalk::foxstd
