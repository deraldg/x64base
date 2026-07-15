#include "workareas.hpp"
#include "xbase.hpp"

// This must match however your shell currently exposes the engine

// If you already have a global shell engine function, reuse it.
// Most of your codebase already uses something like this:

extern "C" xbase::XBaseEngine* shell_engine();  // existing global

namespace workareas {

xbase::XBaseEngine* shell_engine() {
    return ::shell_engine();   // forward to existing implementation
}

}