// @dottalk.file v1
// subsystem: cli
// layer: service
// owns: non-owning shell engine binding
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "shell_api.hpp"
namespace { xbase::XBaseEngine* bound_engine = nullptr; }
extern "C" xbase::XBaseEngine* shell_engine() { return bound_engine; }
void shell_bind_engine(xbase::XBaseEngine* engine) noexcept { bound_engine = engine; }
