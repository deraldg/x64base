#pragma once

namespace xbase {

void request_shell_exit();
void clear_shell_exit_request();
bool shell_exit_requested();

} // namespace xbase