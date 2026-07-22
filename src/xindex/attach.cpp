#include "xindex/attach.hpp"
#include "xindex/index_manager.hpp" // ensure IndexManager is visible
#include "xbase.hpp"                // ensure xbase::DbArea is visible
#include "xbase/index_hooks.hpp"

#include <unordered_map>
#include <memory>
#include <mutex>

namespace xindex {
namespace {

using ManagerMap = std::unordered_map<const xbase::DbArea*, std::unique_ptr<IndexManager>>;

ManagerMap& managers()
{
    static ManagerMap map;
    return map;
}

std::mutex& managers_mutex()
{
    static std::mutex mutex;
    return mutex;
}

xbase::index_hooks::Snapshot capture_hook(xbase::DbArea& area)
{
    auto* manager = manager_if_attached(area);
    if (!manager) return {};

    auto snapshot = std::make_shared<IndexManager::DeleteSnapshot>(
        manager->capture_delete_snapshot_for_current_record());
    return {std::move(snapshot)};
}

bool apply_replace_hook(xbase::DbArea& area,
                        const xbase::index_hooks::Snapshot& before,
                        const xbase::index_hooks::Snapshot& after,
                        std::uint64_t recno)
{
    auto* manager = manager_if_attached(area);
    if (!manager || (!before && !after)) return true;

    static const IndexManager::DeleteSnapshot empty;
    const auto before_snapshot = before
        ? std::static_pointer_cast<const IndexManager::DeleteSnapshot>(before.payload)
        : std::shared_ptr<const IndexManager::DeleteSnapshot>{};
    const auto after_snapshot = after
        ? std::static_pointer_cast<const IndexManager::DeleteSnapshot>(after.payload)
        : std::shared_ptr<const IndexManager::DeleteSnapshot>{};

    return manager->apply_replace_snapshot(
        before_snapshot ? *before_snapshot : empty,
        after_snapshot ? *after_snapshot : empty,
        static_cast<RecNo>(recno));
}

void detach_hook(xbase::DbArea& area) noexcept
{
    detach_manager(area);
}

} // namespace

IndexManager& ensure_manager(xbase::DbArea& area) {
    install_xbase_index_hooks();
    std::lock_guard<std::mutex> lock(managers_mutex());
    auto& map = managers();

    auto it = map.find(&area);
    if (it == map.end()) {
        auto mgr = std::make_unique<IndexManager>(area);
        auto [ins, ok] = map.emplace(&area, std::move(mgr));
        return *ins->second;
    }
    return *it->second;
}

IndexManager* manager_if_attached(xbase::DbArea& area) noexcept
{
    std::lock_guard<std::mutex> lock(managers_mutex());
    const auto it = managers().find(&area);
    return it == managers().end() ? nullptr : it->second.get();
}

const IndexManager* manager_if_attached(const xbase::DbArea& area) noexcept
{
    std::lock_guard<std::mutex> lock(managers_mutex());
    const auto it = managers().find(&area);
    return it == managers().end() ? nullptr : it->second.get();
}

void detach_manager(xbase::DbArea& area) noexcept
{
    std::unique_ptr<IndexManager> manager;
    {
        std::lock_guard<std::mutex> lock(managers_mutex());
        const auto it = managers().find(&area);
        if (it == managers().end()) return;
        manager = std::move(it->second);
        managers().erase(it);
    }
    manager->close();
}

void install_xbase_index_hooks() noexcept
{
    static std::once_flag once;
    std::call_once(once, [] {
        xbase::index_hooks::install({capture_hook, apply_replace_hook, detach_hook});
    });
}

} // namespace xindex
