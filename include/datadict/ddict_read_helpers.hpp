#pragma once
#include <string>
#include <unordered_map>
namespace dottalk::datadict {
using DDictRow = std::unordered_map<std::string, std::string>;
std::string lower_copy(std::string value);
std::string trim_copy(std::string value);
std::string upper_copy(std::string value);
std::string short_text(const std::string& value, std::size_t limit);
std::string value_of(const DDictRow& row, const std::string& key);
} // namespace dottalk::datadict
