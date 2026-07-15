#include "xbase/index_hooks.hpp"

namespace xbase::index_hooks {
namespace {

Hooks& active_hooks() noexcept
{
    static Hooks hooks;
    return hooks;
}

} // namespace

void install(Hooks hooks) noexcept
{
    active_hooks() = hooks;
}

Snapshot capture(DbArea& area)
{
    const auto hook = active_hooks().capture;
    return hook ? hook(area) : Snapshot{};
}

bool apply_replace(DbArea& area,
                   const Snapshot& before,
                   const Snapshot& after,
                   std::uint32_t recno)
{
    const auto hook = active_hooks().apply_replace;
    return hook ? hook(area, before, after, recno) : true;
}

void detach(DbArea& area) noexcept
{
    const auto hook = active_hooks().detach;
    if (hook) hook(area);
}

} // namespace xbase::index_hooks
