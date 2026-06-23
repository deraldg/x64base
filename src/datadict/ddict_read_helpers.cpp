#include "datadict/ddict_read_helpers.hpp"

#include <algorithm>
#include <cctype>

// DD-089C extraction preview only.
// This generated candidate is not installed or wired by DD-089C.

namespace dottalk::datadict {

std::string lower_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return s;
}

std::string trim_copy(std::string s) {
    auto not_space = [](unsigned char ch) {
        return !std::isspace(ch) && ch != '\0';
    };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return s;
}

std::string short_text(const std::string& s, std::size_t n) {
    return s.size() <= n ? s : s.substr(0, n);
}

std::string value_of(const DDictRow& row, const std::string& key) {
    auto it = row.find(key);
    return it == row.end() ? std::string{} : it->second;
}

} // namespace dottalk::datadict
