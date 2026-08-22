// @dottalk.file v1
// subsystem: dottalk
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>

// AIF-120. The version has ONE authority: `project(DotTalkpp VERSION x)` in the
// root CMakeLists.txt, which reaches every target through
// dottalk_apply_common_settings -> dottalk_apply_version_metadata as
// -DDOTTALKPP_VERSION.
//
// This fallback is deliberately NOT a plausible version number. It used to read
// "0.6-dev" -- a second hand-kept copy that had already drifted from the
// authority's "0.6", and which a target built without the define would have
// shipped as though it were real. The house already settled this shape one
// header over: recordLength() returns -1 rather than saturating to INT_MAX,
// "so a 32-bit consumer sees out of range and skips/errors, instead of acting
// on the wrong record". A version fallback that looks like a version is the
// same lie in a different field.
//
// A build that lands here is unconfigured, and now says so.
#ifndef DOTTALKPP_VERSION
#define DOTTALKPP_VERSION "0.0-unconfigured"
#endif

#ifndef DOTTALKPP_VERSION_DATE
#define DOTTALKPP_VERSION_DATE __DATE__
#endif

#ifndef DOTTALKPP_GIT_SHA
#define DOTTALKPP_GIT_SHA "nogit"
#endif

#ifndef DOTTALKPP_GIT_DIRTY
#define DOTTALKPP_GIT_DIRTY 0
#endif

namespace dottalk::version {

inline std::string version_label()
{
    return DOTTALKPP_VERSION;
}

inline std::string version_date()
{
    return DOTTALKPP_VERSION_DATE;
}

inline std::string git_sha()
{
    return DOTTALKPP_GIT_SHA;
}

inline bool git_dirty()
{
    return DOTTALKPP_GIT_DIRTY != 0;
}

inline std::string display_version()
{
    std::string text = "v" + version_label() + " (" + version_date();
    const std::string sha = git_sha();
    if (!sha.empty() && sha != "nogit") {
        text += ", " + sha;
        if (git_dirty()) {
            text += " dirty";
        }
    }
    text += ")";
    return text;
}

} // namespace dottalk::version
