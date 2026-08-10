// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

namespace xbase {

void request_shell_exit();
void clear_shell_exit_request();
bool shell_exit_requested();

} // namespace xbase