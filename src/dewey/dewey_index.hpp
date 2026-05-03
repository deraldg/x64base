#pragma once
#include "xbase.hpp"
#include <string>
#include <vector>
#include <optional>

namespace xbase {

class DeweyIndex {
public:
    explicit DeweyIndex(DbArea& area);

    std::string insertChild(const std::string& parent_id,
                            const std::string& label = "",
                            const std::string& payload = "");

    std::string insertBetween(const std::string& left_id,
                              const std::string& right_id,
                              const std::string& label = "",
                              const std::string& payload = "");

    std::vector<uint64_t> getSubtreeRecnos(const std::string& root_id) const;
    std::vector<uint64_t> getDirectChildrenRecnos(const std::string& parent_id) const;
    std::vector<uint64_t> getPathToRootRecnos(const std::string& node_id) const;

    std::string getDeweyId(uint64_t recno64) const;
    bool setDeweyId(uint64_t recno64, const std::string& new_id);

    std::string nextSiblingId(const std::string& sibling_id) const;

private:
    DbArea& _area;
    int _deweyFieldIdx;

    int findDeweyField() const;
    std::string parentOf(const std::string& id) const;
    bool isDescendant(const std::string& id, const std::string& ancestor) const;
    bool replaceDewey(uint64_t recno64, const std::string& value);
};

} // namespace xbase