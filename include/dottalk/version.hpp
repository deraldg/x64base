#pragma once

#include <string>

#ifndef DOTTALKPP_VERSION
#define DOTTALKPP_VERSION "0.6-dev"
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
