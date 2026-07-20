#pragma once

#include <cstdint>
#include <memory>

namespace xbase {

class DbArea;

namespace index_hooks {

// Opaque index state captured around a physical record update.  xbase owns the
// lifecycle call sites, but it deliberately knows nothing about index manager
// types, key formats, or backends.
struct Snapshot {
    std::shared_ptr<const void> payload;

    explicit operator bool() const noexcept { return static_cast<bool>(payload); }
};

struct Hooks {
    Snapshot (*capture)(DbArea&) = nullptr;
    bool (*apply_replace)(DbArea&,
                          const Snapshot&,
                          const Snapshot&,
                          std::uint64_t) = nullptr;
    void (*detach)(DbArea&) noexcept = nullptr;
};

void install(Hooks hooks) noexcept;
Snapshot capture(DbArea& area);
bool apply_replace(DbArea& area,
                   const Snapshot& before,
                   const Snapshot& after,
                   std::uint64_t recno);
void detach(DbArea& area) noexcept;

} // namespace index_hooks
} // namespace xbase
