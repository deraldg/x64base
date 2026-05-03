#include "xbase.hpp"
#include "textio.hpp"
#include "hierarchy_service.hpp"

#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static void usage()
{
    std::cout <<
        "Usage:\n"
        "  HIER CREATE ROOT <node_id> [NAME <text>] [TYPE <text>] [SORT <n>]\n"
        "  HIER ADD CHILD <parent_id> <node_id> [NAME <text>] [TYPE <text>] [SORT <n>]\n"
        "  HIER INSERT BETWEEN <left_id> <right_id> <node_id>\n"
        "  HIER MOVE <node_id> TO <new_parent_id>\n"
        "  HIER DELETE <node_id>\n"
        "  HIER DELETE SUBTREE <node_id>\n"
        "  HIER REBUILD\n"
        "  HIER VALIDATE\n"
        "  HIER CHILDREN <node_id>\n"
        "  HIER SUBTREE <node_id>\n";
}

static HierNodeInput parse_input(const std::vector<std::string>& toks, size_t start)
{
    HierNodeInput in;

    for (size_t i = start; i < toks.size(); )
    {
        std::string key = textio::upper(toks[i]);

        if (key == "NAME" && i + 1 < toks.size())
        {
            in.name = toks[i+1];
            i += 2;
            continue;
        }
        if (key == "TYPE" && i + 1 < toks.size())
        {
            in.type = toks[i+1];
            i += 2;
            continue;
        }
        if (key == "SORT" && i + 1 < toks.size())
        {
            in.sort_hint = std::stoi(toks[i+1]);
            i += 2;
            continue;
        }

        ++i; // ignore unknowns for now
    }

    return in;
}

void cmd_HIER(xbase::DbArea& area, std::istringstream& iss)
{
    auto toks = textio::tokenize(iss);

    if (toks.empty())
    {
        usage();
        return;
    }

    const std::string a1 = textio::upper(toks[0]);

    HierarchyService hs(area);

    // -------------------------------------------------
    // CREATE ROOT
    // -------------------------------------------------
    if (a1 == "CREATE" && toks.size() >= 3)
    {
        if (textio::upper(toks[1]) == "ROOT")
        {
            std::string node_id = toks[2];
            auto in = parse_input(toks, 3);
            in.node_id = node_id;

            if (!hs.create_root(in))
            {
                std::cout << "CREATE ROOT failed\n";
                return;
            }

            std::cout << "Root created: " << node_id << "\n";
            return;
        }
    }

    // -------------------------------------------------
    // ADD CHILD
    // -------------------------------------------------
    if (a1 == "ADD" && toks.size() >= 4)
    {
        if (textio::upper(toks[1]) == "CHILD")
        {
            std::string parent_id = toks[2];
            std::string node_id   = toks[3];

            auto in = parse_input(toks, 4);
            in.node_id = node_id;

            if (!hs.add_child(parent_id, in))
            {
                std::cout << "ADD CHILD failed\n";
                return;
            }

            std::cout << "Child added: " << node_id << "\n";
            return;
        }
    }

    // -------------------------------------------------
    // INSERT BETWEEN
    // -------------------------------------------------
    if (a1 == "INSERT" && toks.size() >= 5)
    {
        if (textio::upper(toks[1]) == "BETWEEN")
        {
            std::string left  = toks[2];
            std::string right = toks[3];
            std::string node  = toks[4];

            HierNodeInput in;
            in.node_id = node;

            if (!hs.insert_between(left, right, in))
            {
                std::cout << "INSERT BETWEEN failed\n";
                return;
            }

            std::cout << "Inserted: " << node << "\n";
            return;
        }
    }

    // -------------------------------------------------
    // MOVE
    // -------------------------------------------------
    if (a1 == "MOVE" && toks.size() >= 4)
    {
        if (textio::upper(toks[2]) == "TO")
        {
            std::string node = toks[1];
            std::string dest = toks[3];

            if (!hs.move_subtree(node, dest))
            {
                std::cout << "MOVE failed\n";
                return;
            }

            std::cout << "Moved: " << node << "\n";
            return;
        }
    }

    // -------------------------------------------------
    // DELETE
    // -------------------------------------------------
    if (a1 == "DELETE" && toks.size() >= 2)
    {
        if (textio::upper(toks[1]) == "SUBTREE" && toks.size() >= 3)
        {
            if (!hs.delete_subtree(toks[2]))
            {
                std::cout << "DELETE SUBTREE failed\n";
                return;
            }

            std::cout << "Subtree deleted\n";
            return;
        }

        if (!hs.delete_node(toks[1]))
        {
            std::cout << "DELETE failed\n";
            return;
        }

        std::cout << "Node deleted\n";
        return;
    }

    // -------------------------------------------------
    // REBUILD
    // -------------------------------------------------
    if (a1 == "REBUILD")
    {
        if (!hs.rebuild_paths())
        {
            std::cout << "REBUILD failed\n";
            return;
        }

        std::cout << "Rebuilt\n";
        return;
    }

    // -------------------------------------------------
    // VALIDATE
    // -------------------------------------------------
    if (a1 == "VALIDATE")
    {
        auto errs = hs.validate_hierarchy();

        if (errs.empty())
        {
            std::cout << "OK\n";
            return;
        }

        for (auto& e : errs)
            std::cout << e << "\n";

        return;
    }

    // -------------------------------------------------
    // CHILDREN
    // -------------------------------------------------
    if (a1 == "CHILDREN" && toks.size() >= 2)
    {
        auto rows = hs.list_children(toks[1]);

        for (auto& r : rows)
            std::cout << r.node_id << " " << r.path_key << "\n";

        return;
    }

    // -------------------------------------------------
    // SUBTREE
    // -------------------------------------------------
    if (a1 == "SUBTREE" && toks.size() >= 2)
    {
        auto rows = hs.list_subtree(toks[1]);

        for (auto& r : rows)
            std::cout << r.path_key << " " << r.node_id << "\n";

        return;
    }

    usage();
}