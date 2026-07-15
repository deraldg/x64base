#pragma once
#include <string>
#include <vector>
#include "xbase.hpp"

struct HierNodeInput {
    std::string node_id;
    std::string name;
    std::string type;
    int sort_hint = 0;
    bool active = true;
};

struct HierNode {
    std::string node_id;
    std::string parent_id;
    std::string path_key;
    std::string name;
    std::string type;
    int sort_hint = 0;
    bool active = true;
    uint64_t recno = 0;
};

class HierarchyService {
public:
    explicit HierarchyService(xbase::DbArea& area);

    bool create_root(const HierNodeInput& in);
    bool add_child(const std::string& parent_id, const HierNodeInput& in);
    bool insert_between(const std::string& left_id,
                        const std::string& right_id,
                        const HierNodeInput& in);

    bool move_subtree(const std::string& moving_id,
                      const std::string& new_parent_id);

    bool delete_node(const std::string& node_id);
    bool delete_subtree(const std::string& node_id);

    bool rebuild_paths();
    std::vector<std::string> validate_hierarchy() const;

    std::vector<HierNode> list_children(const std::string& parent_id) const;
    std::vector<HierNode> list_subtree(const std::string& node_id) const;

private:
    xbase::DbArea& _area;
};
