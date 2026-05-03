#include "workspace/workarea_utils.hpp"
#include "workareas.hpp"

// Intentionally minimal.
//
// open_count() and occupied_desc() now live inline in src/cli/workareas.hpp
// so the workareas compatibility layer remains the single source of truth
// during the WorkArea/DbArea transition.