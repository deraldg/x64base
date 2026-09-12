// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace dottalk::expr {

enum class FunctionCategory {
    String,
    Search,
    Construction,
    Conversion,
    Logical,
    Numeric,
    Date,

    // CURSOR-STATE FUNCTIONS ARE A DIFFERENT KIND OF THING, and until 2026-09-05
    // this taxonomy had nowhere to put them.
    //
    // Every category above transforms an ARGUMENT: UPPER(x), ROUND(n), DTOS(d).
    // DELETED(), RECNO(), RECCOUNT() and ISNULL(f) interrogate the CURSOR -- their
    // real input is the record the area is parked on, which arrives implicitly and
    // is not written in the call at all.
    //
    // THE CODE HAD ALREADY SAID SO. All four are special-cased in
    // FunctionCall::evalString() BEFORE the builtin lookup, because none of them
    // can be expressed as a function over evaluated arguments. That escape hatch
    // WAS this category, written in C++ instead of in this enum; they fell out of
    // the catalogue entirely rather than into a wrong bucket, which is why they
    // went undocumented for so long.
    //
    // ISNULL is the one that proves the point rather than merely fitting it: its
    // argument must NOT be evaluated. A null cell and a blank cell both evaluate
    // to the empty string, so a value-category function handed an evaluated
    // argument could not answer the only question it exists to answer. min_args /
    // max_args below therefore count TOKENS for this category, not values.
    //
    // NOT the same as a SYSTEM function. SYS()-style calls (paths, session,
    // version) are about the process and would want their own category; these are
    // specifically about the record under the cursor. RECCOUNT() is the boundary
    // case -- it is about the TABLE rather than the row -- and is placed here
    // because it still needs an open area and still takes no argument.
    Cursor,

    Misc
};

struct FunctionDoc {
    std::string name;                  // canonical uppercase
    std::vector<std::string> aliases;  // alternate names
    FunctionCategory category{FunctionCategory::Misc};

    std::size_t min_args{0};
    std::size_t max_args{0};

    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

const FunctionDoc* get_function_doc(const std::string& name);
std::vector<const FunctionDoc*> all_function_docs();

const char* to_string(FunctionCategory cat);

} // namespace dottalk::expr