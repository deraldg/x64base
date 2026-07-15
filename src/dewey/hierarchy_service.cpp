#include "hierarchy_service.hpp"

#include <algorithm>
#include <cctype>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kSegWidth = 3;
constexpr int kSegStep  = 10;

std::string trim_copy(const std::string& s)
{
    std::size_t b = 0;
    std::size_t e = s.size();

    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;

    return s.substr(b, e - b);
}

std::string upper_copy(std::string s)
{
    for (char& ch : s)
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

int find_field(const xbase::DbArea& area, const std::string& name)
{
    const auto& fields = area.fields();
    const std::string want = upper_copy(name);

    for (std::size_t i = 0; i < fields.size(); ++i)
    {
        if (upper_copy(fields[i].name) == want)
            return static_cast<int>(i + 1); // 1-based
    }

    return 0;
}

bool goto_rec64(xbase::DbArea& area, uint64_t recno)
{
    if (recno == 0) return false;
    if (recno > static_cast<uint64_t>(INT32_MAX)) return false;
    return area.gotoRec(static_cast<int32_t>(recno));
}

std::string field_get(xbase::DbArea& area, int fld)
{
    if (fld <= 0) return "";
    return trim_copy(area.get(fld));
}

bool field_set(xbase::DbArea& area, int fld, const std::string& value)
{
    if (fld <= 0) return false;
    return area.replaceFieldStored(fld, value);
}

bool field_set_bool(xbase::DbArea& area, int fld, bool value)
{
    if (fld <= 0) return false;
    return area.replaceFieldStored(fld, value ? "T" : "F");
}

std::vector<std::string> split_path(const std::string& path)
{
    std::vector<std::string> out;
    std::string cur;

    for (char ch : path)
    {
        if (ch == '.')
        {
            out.push_back(cur);
            cur.clear();
        }
        else
        {
            cur.push_back(ch);
        }
    }

    if (!cur.empty() || !path.empty())
        out.push_back(cur);

    return out;
}

std::string parent_path(const std::string& path)
{
    const std::size_t pos = path.rfind('.');
    if (pos == std::string::npos) return "";
    return path.substr(0, pos);
}

std::string last_segment(const std::string& path)
{
    const std::size_t pos = path.rfind('.');
    if (pos == std::string::npos) return path;
    return path.substr(pos + 1);
}

bool starts_with_path(const std::string& path, const std::string& root)
{
    if (path == root) return true;
    if (path.size() <= root.size()) return false;
    if (path.compare(0, root.size(), root) != 0) return false;
    return path[root.size()] == '.';
}

std::string format_segment(int n)
{
    std::ostringstream oss;
    oss.width(kSegWidth);
    oss.fill('0');
    oss << n;
    return oss.str();
}

std::string join_path(const std::string& parent, const std::string& seg)
{
    if (parent.empty()) return seg;
    return parent + "." + seg;
}

int parse_int_safe(const std::string& s, int fallback = 0)
{
    try
    {
        if (s.empty()) return fallback;
        return std::stoi(s);
    }
    catch (...)
    {
        return fallback;
    }
}

bool choose_gap(int left_seg, int right_seg, int& mid_out)
{
    if (right_seg - left_seg <= 1) return false;

    mid_out = left_seg + ((right_seg - left_seg) / 2);

    if (mid_out <= left_seg || mid_out >= right_seg)
        return false;

    return true;
}

bool node_sort_less(const HierNode& a, const HierNode& b)
{
    if (a.sort_hint != b.sort_hint) return a.sort_hint < b.sort_hint;
    if (a.name != b.name) return a.name < b.name;
    return a.node_id < b.node_id;
}

struct FieldMap
{
    int node_id   = 0;
    int parent_id = 0;
    int path_key  = 0;
    int name      = 0;
    int type      = 0;
    int sort_hint = 0;
    int active    = 0;
};

FieldMap get_fields(const xbase::DbArea& area)
{
    FieldMap f;
    f.node_id   = find_field(area, "NODE_ID");
    f.parent_id = find_field(area, "PARENT_ID");
    f.path_key  = find_field(area, "PATH_KEY");
    f.name      = find_field(area, "NAME");
    f.type      = find_field(area, "TYPE");
    f.sort_hint = find_field(area, "SORT_HINT");
    f.active    = find_field(area, "ACTIVE");
    return f;
}

void require_core_fields(const FieldMap& f)
{
    if (f.node_id <= 0 || f.parent_id <= 0 || f.path_key <= 0)
        throw std::runtime_error("HierarchyService: required fields NODE_ID / PARENT_ID / PATH_KEY not found");
}

bool load_node_by_rec(xbase::DbArea& area, const FieldMap& f, uint64_t recno, HierNode& out)
{
    if (!goto_rec64(area, recno)) return false;
    area.readCurrent();

    out.recno      = area.recno64();
    out.node_id    = field_get(area, f.node_id);
    out.parent_id  = field_get(area, f.parent_id);
    out.path_key   = field_get(area, f.path_key);
    out.name       = field_get(area, f.name);
    out.type       = field_get(area, f.type);
    out.sort_hint  = parse_int_safe(field_get(area, f.sort_hint), 0);

    const std::string active = upper_copy(field_get(area, f.active));
    out.active = !(active == "F" || active == "N" || active == "0");

    return true;
}

bool find_node_recno(xbase::DbArea& area, const FieldMap& f, const std::string& node_id, uint64_t& recno)
{
    area.top();
    while (!area.eof())
    {
        area.readCurrent();
        if (field_get(area, f.node_id) == node_id)
        {
            recno = area.recno64();
            return true;
        }
        area.skip(1);
    }
    return false;
}

bool load_node_by_id(xbase::DbArea& area, const FieldMap& f, const std::string& node_id, HierNode& out)
{
    uint64_t recno = 0;
    if (!find_node_recno(area, f, node_id, recno)) return false;
    return load_node_by_rec(area, f, recno, out);
}

std::vector<HierNode> fetch_all_nodes(xbase::DbArea& area, const FieldMap& f)
{
    std::vector<HierNode> out;

    area.top();
    while (!area.eof())
    {
        area.readCurrent();

        HierNode row;
        if (load_node_by_rec(area, f, area.recno64(), row))
            out.push_back(row);

        area.skip(1);
    }

    return out;
}

std::vector<HierNode> fetch_roots_ordered(xbase::DbArea& area, const FieldMap& f)
{
    auto rows = fetch_all_nodes(area, f);
    std::vector<HierNode> out;

    for (const auto& row : rows)
    {
        if (row.parent_id.empty())
            out.push_back(row);
    }

    std::sort(out.begin(), out.end(), node_sort_less);
    return out;
}

std::vector<HierNode> fetch_children_ordered(xbase::DbArea& area, const FieldMap& f, const std::string& parent_id)
{
    auto rows = fetch_all_nodes(area, f);
    std::vector<HierNode> out;

    for (const auto& row : rows)
    {
        if (row.parent_id == parent_id)
            out.push_back(row);
    }

    std::sort(out.begin(), out.end(), node_sort_less);
    return out;
}

std::vector<HierNode> fetch_subtree_by_path(xbase::DbArea& area, const FieldMap& f, const std::string& root_path)
{
    auto rows = fetch_all_nodes(area, f);
    std::vector<HierNode> out;

    for (const auto& row : rows)
    {
        if (starts_with_path(row.path_key, root_path))
            out.push_back(row);
    }

    std::sort(out.begin(), out.end(),
        [](const HierNode& a, const HierNode& b) {
            return a.path_key < b.path_key;
        });

    return out;
}

int next_available_segment(const std::vector<HierNode>& siblings)
{
    std::set<int> used;

    for (const auto& row : siblings)
    {
        used.insert(parse_int_safe(last_segment(row.path_key), 0));
    }

    int n = kSegStep;
    while (used.find(n) != used.end())
        n += kSegStep;

    return n;
}

bool renumber_children(xbase::DbArea& area, const FieldMap& f, const std::string& parent_id)
{
    std::string parent_pk;
    if (!parent_id.empty())
    {
        HierNode parent;
        if (!load_node_by_id(area, f, parent_id, parent)) return false;
        parent_pk = parent.path_key;
    }

    auto kids = fetch_children_ordered(area, f, parent_id);
    int seg = kSegStep;

    for (const auto& child : kids)
    {
        const std::string old_root = child.path_key;
        const std::string new_root = join_path(parent_pk, format_segment(seg));

        auto affected = fetch_subtree_by_path(area, f, old_root);
        for (const auto& row : affected)
        {
            if (!goto_rec64(area, row.recno)) return false;
            area.readCurrent();

            std::string suffix;
            if (row.path_key == old_root)
                suffix = "";
            else
                suffix = row.path_key.substr(old_root.size());

            field_set(area, f.path_key, new_root + suffix);

            if (!area.writeCurrent()) return false;
        }

        seg += kSegStep;
    }

    return true;
}

bool would_create_cycle(xbase::DbArea& area, const FieldMap& f,
                        const std::string& moving_id,
                        const std::string& new_parent_id)
{
    if (moving_id == new_parent_id) return true;

    HierNode cur;
    if (!load_node_by_id(area, f, new_parent_id, cur)) return true;

    std::set<std::string> seen;

    while (!cur.parent_id.empty())
    {
        if (cur.node_id == moving_id) return true;
        if (!seen.insert(cur.node_id).second) return true;
        if (!load_node_by_id(area, f, cur.parent_id, cur)) return false;
    }

    return cur.node_id == moving_id;
}

bool rebuild_children(xbase::DbArea& area, const FieldMap& f,
                      const std::string& parent_id,
                      const std::string& parent_path)
{
    auto kids = fetch_children_ordered(area, f, parent_id);
    int seg = kSegStep;

    for (const auto& child : kids)
    {
        if (!goto_rec64(area, child.recno)) return false;
        area.readCurrent();

        const std::string new_path = join_path(parent_path, format_segment(seg));
        field_set(area, f.path_key, new_path);
        if (!area.writeCurrent()) return false;

        if (!rebuild_children(area, f, child.node_id, new_path)) return false;

        seg += kSegStep;
    }

    return true;
}

} // namespace

HierarchyService::HierarchyService(xbase::DbArea& area)
    : _area(area)
{
    require_core_fields(get_fields(_area));
}

bool HierarchyService::create_root(const HierNodeInput& in)
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    uint64_t recno = 0;
    if (find_node_recno(_area, f, in.node_id, recno)) return false;

    int max_root = 0;
    const auto roots = fetch_roots_ordered(_area, f);

    for (const auto& row : roots)
        max_root = std::max(max_root, parse_int_safe(row.path_key, 0));

    const int new_root = (max_root == 0) ? 100 : max_root + 100;

    _area.appendBlank();
    field_set(_area, f.node_id, in.node_id);
    field_set(_area, f.parent_id, "");
    field_set(_area, f.path_key, std::to_string(new_root));
    if (f.name > 0)      field_set(_area, f.name, in.name);
    if (f.type > 0)      field_set(_area, f.type, in.type);
    if (f.sort_hint > 0) field_set(_area, f.sort_hint, std::to_string(in.sort_hint));
    if (f.active > 0)    field_set_bool(_area, f.active, in.active);

    return _area.writeCurrent();
}

bool HierarchyService::add_child(const std::string& parent_id, const HierNodeInput& in)
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    uint64_t recno = 0;
    if (find_node_recno(_area, f, in.node_id, recno)) return false;

    HierNode parent;
    if (!load_node_by_id(_area, f, parent_id, parent)) return false;

    const auto siblings = fetch_children_ordered(_area, f, parent_id);
    const int next_seg = next_available_segment(siblings);
    const std::string new_path = join_path(parent.path_key, format_segment(next_seg));

    _area.appendBlank();
    field_set(_area, f.node_id, in.node_id);
    field_set(_area, f.parent_id, parent_id);
    field_set(_area, f.path_key, new_path);
    if (f.name > 0)      field_set(_area, f.name, in.name);
    if (f.type > 0)      field_set(_area, f.type, in.type);
    if (f.sort_hint > 0) field_set(_area, f.sort_hint, std::to_string(in.sort_hint));
    if (f.active > 0)    field_set_bool(_area, f.active, in.active);

    return _area.writeCurrent();
}

bool HierarchyService::insert_between(const std::string& left_id,
                                      const std::string& right_id,
                                      const HierNodeInput& in)
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    uint64_t recno = 0;
    if (find_node_recno(_area, f, in.node_id, recno)) return false;

    HierNode left;
    HierNode right;

    if (!load_node_by_id(_area, f, left_id, left)) return false;
    if (!load_node_by_id(_area, f, right_id, right)) return false;
    if (left.parent_id != right.parent_id) return false;

    const std::string base_parent_path = parent_path(left.path_key);

    int left_seg  = parse_int_safe(last_segment(left.path_key), 0);
    int right_seg = parse_int_safe(last_segment(right.path_key), 0);

    if (left_seg >= right_seg) return false;

    int mid = 0;
    if (!choose_gap(left_seg, right_seg, mid))
    {
        if (!renumber_children(_area, f, left.parent_id)) return false;
        if (!load_node_by_id(_area, f, left_id, left)) return false;
        if (!load_node_by_id(_area, f, right_id, right)) return false;

        left_seg  = parse_int_safe(last_segment(left.path_key), 0);
        right_seg = parse_int_safe(last_segment(right.path_key), 0);

        if (!choose_gap(left_seg, right_seg, mid)) return false;
    }

    const std::string new_path = join_path(base_parent_path, format_segment(mid));

    _area.appendBlank();
    field_set(_area, f.node_id, in.node_id);
    field_set(_area, f.parent_id, left.parent_id);
    field_set(_area, f.path_key, new_path);
    if (f.name > 0)      field_set(_area, f.name, in.name);
    if (f.type > 0)      field_set(_area, f.type, in.type);
    if (f.sort_hint > 0) field_set(_area, f.sort_hint, std::to_string(in.sort_hint));
    if (f.active > 0)    field_set_bool(_area, f.active, in.active);

    return _area.writeCurrent();
}

bool HierarchyService::move_subtree(const std::string& moving_id,
                                    const std::string& new_parent_id)
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    if (would_create_cycle(_area, f, moving_id, new_parent_id)) return false;

    HierNode moving;
    HierNode new_parent;

    if (!load_node_by_id(_area, f, moving_id, moving)) return false;
    if (!load_node_by_id(_area, f, new_parent_id, new_parent)) return false;

    const auto siblings = fetch_children_ordered(_area, f, new_parent_id);
    const int next_seg = next_available_segment(siblings);

    const std::string old_root = moving.path_key;
    const std::string new_root = join_path(new_parent.path_key, format_segment(next_seg));

    auto affected = fetch_subtree_by_path(_area, f, old_root);

    for (const auto& row : affected)
    {
        if (!goto_rec64(_area, row.recno)) return false;
        _area.readCurrent();

        std::string suffix;
        if (row.path_key == old_root)
            suffix = "";
        else
            suffix = row.path_key.substr(old_root.size());

        field_set(_area, f.path_key, new_root + suffix);

        if (row.node_id == moving_id)
            field_set(_area, f.parent_id, new_parent_id);

        if (!_area.writeCurrent()) return false;
    }

    return true;
}

bool HierarchyService::delete_node(const std::string& node_id)
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    if (!fetch_children_ordered(_area, f, node_id).empty()) return false;

    HierNode row;
    if (!load_node_by_id(_area, f, node_id, row)) return false;
    if (!goto_rec64(_area, row.recno)) return false;

    _area.readCurrent();
    _area.deleteCurrent();
    return true;
}

bool HierarchyService::delete_subtree(const std::string& node_id)
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    HierNode root;
    if (!load_node_by_id(_area, f, node_id, root)) return false;

    auto rows = fetch_subtree_by_path(_area, f, root.path_key);

    std::sort(rows.begin(), rows.end(),
        [](const HierNode& a, const HierNode& b) {
            return split_path(a.path_key).size() > split_path(b.path_key).size();
        });

    for (const auto& row : rows)
    {
        if (!goto_rec64(_area, row.recno)) return false;
        _area.readCurrent();
        _area.deleteCurrent();
    }

    return true;
}

bool HierarchyService::rebuild_paths()
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    auto roots = fetch_roots_ordered(_area, f);
    int root_num = 100;

    for (const auto& root : roots)
    {
        if (!goto_rec64(_area, root.recno)) return false;
        _area.readCurrent();

        const std::string root_path = std::to_string(root_num);
        field_set(_area, f.path_key, root_path);

        if (!_area.writeCurrent()) return false;
        if (!rebuild_children(_area, f, root.node_id, root_path)) return false;

        root_num += 100;
    }

    return true;
}

std::vector<std::string> HierarchyService::validate_hierarchy() const
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    std::vector<std::string> errors;
    const auto rows = fetch_all_nodes(const_cast<xbase::DbArea&>(_area), f);

    std::set<std::string> node_ids;
    std::set<std::string> path_keys;
    std::map<std::string, HierNode> by_id;

    for (const auto& row : rows)
    {
        if (row.node_id.empty())
        {
            errors.push_back("Blank NODE_ID at recno " + std::to_string(row.recno));
            continue;
        }

        if (!node_ids.insert(row.node_id).second)
            errors.push_back("Duplicate NODE_ID: " + row.node_id);

        if (row.path_key.empty())
            errors.push_back("Blank PATH_KEY: " + row.node_id);
        else if (!path_keys.insert(row.path_key).second)
            errors.push_back("Duplicate PATH_KEY: " + row.path_key);

        by_id[row.node_id] = row;

        const auto parts = split_path(row.path_key);
        for (const auto& part : parts)
        {
            if (part.empty())
            {
                errors.push_back("Malformed PATH_KEY (empty segment): " + row.path_key);
                continue;
            }

            for (char ch : part)
            {
                if (!std::isdigit(static_cast<unsigned char>(ch)))
                {
                    errors.push_back("Non-numeric PATH_KEY segment: " + row.path_key);
                    break;
                }
            }
        }
    }

    for (const auto& row : rows)
    {
        if (!row.parent_id.empty())
        {
            auto it = by_id.find(row.parent_id);
            if (it == by_id.end())
            {
                errors.push_back("Orphan PARENT_ID: " + row.node_id + " -> " + row.parent_id);
                continue;
            }

            if (row.parent_id == row.node_id)
                errors.push_back("Self-parent: " + row.node_id);

            const std::string expected_parent_path = it->second.path_key;
            const std::string actual_parent_path = parent_path(row.path_key);

            if (actual_parent_path != expected_parent_path)
            {
                errors.push_back("Child path mismatch: " + row.node_id +
                                 " parent path=" + expected_parent_path +
                                 " child path=" + row.path_key);
            }
        }
        else
        {
            if (row.path_key.find('.') != std::string::npos)
                errors.push_back("Root with dotted PATH_KEY: " + row.node_id + " -> " + row.path_key);
        }

        std::set<std::string> seen;
        std::string cur = row.node_id;

        auto it = by_id.find(cur);
        while (it != by_id.end() && !it->second.parent_id.empty())
        {
            const std::string pid = it->second.parent_id;

            if (!seen.insert(pid).second)
            {
                errors.push_back("Cycle detected involving: " + row.node_id);
                break;
            }

            auto jt = by_id.find(pid);
            if (jt == by_id.end()) break;
            it = jt;
        }
    }

    return errors;
}

std::vector<HierNode> HierarchyService::list_children(const std::string& parent_id) const
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);
    return fetch_children_ordered(const_cast<xbase::DbArea&>(_area), f, parent_id);
}

std::vector<HierNode> HierarchyService::list_subtree(const std::string& node_id) const
{
    const FieldMap f = get_fields(_area);
    require_core_fields(f);

    HierNode row;
    if (!load_node_by_id(const_cast<xbase::DbArea&>(_area), f, node_id, row))
        return {};

    return fetch_subtree_by_path(const_cast<xbase::DbArea&>(_area), f, row.path_key);
}