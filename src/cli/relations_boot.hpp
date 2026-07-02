
// src/cli/relations_boot.hpp
#pragma once
namespace relations_boot {
// Explicit hooks (optional; you can ignore and rely on static init).
void autoload();
bool retry_pending_autoload();
void autosave();
bool autosave_enabled() noexcept;
} // namespace relations_boot
