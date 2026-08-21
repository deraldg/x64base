// @dottalk.file v1
// subsystem: gui
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// src/gui/wx/res/app_icon.hpp
// -----------------------------------------------------------------------------
// The x64base application icon, as a wxIconBundle.
//
// Two paths, because the platforms disagree about where an icon lives:
//
//   MSW    the icon is a linked RESOURCE (x64base.rc -> x64base.ico). One .ico
//          carries every size, so wxIconBundle takes the whole set by name and
//          Explorer gets the executable icon from the same resource.
//   other  the icon is COMPILED IN as XPM -- three sizes, ASCII, no file to
//          find at run time and nothing to install.
//
// Neither path reads a file at run time. That is deliberate: an icon loaded
// from disk is an icon that can be missing, and a missing icon fails silently
// -- the window simply gets the toolkit default and nobody knows the product
// shipped without its face on.
//
// Provenance and the regeneration recipe: src/gui/wx/res/README.md
// -----------------------------------------------------------------------------

// @dottalk.location v1
// id: DOTSRC-DOTTALKPP-GUI-WX-RES-APP-ICON
// home: src/gui/wx/res
// canonical-path: src/gui/wx/res/app_icon.hpp
// project: dottalkpp
// role: resource-accessor
// @dottalk.end

#ifndef DOTTALK_GUI_WX_RES_APP_ICON_HPP
#define DOTTALK_GUI_WX_RES_APP_ICON_HPP

#include <wx/bitmap.h>
#include <wx/icon.h>
#include <wx/iconbndl.h>

#ifndef __WXMSW__
#include "x64base_16.xpm"
#include "x64base_32.xpm"
#include "x64base_48.xpm"
#endif

namespace dottalk {
namespace gui {
namespace wxui {

/// Every size of the application icon, ready for wxTopLevelWindow::SetIcons().
inline wxIconBundle app_icon_bundle()
{
#ifdef __WXMSW__
    // Loads all seven sizes the .ico carries (16, 24, 32, 48, 64, 128, 256).
    return wxIconBundle("x64base_icon", nullptr);
#else
    wxIconBundle bundle;
    const char *const *const sources[] = {
        x64base_16_xpm, x64base_32_xpm, x64base_48_xpm,
    };
    for (const char *const *const xpm : sources) {
        // CopyFromBitmap rather than a wxIcon(xpm) constructor: the bitmap ctor
        // from static XPM data is the one every wx port provides, and it needs
        // no image handler registered.
        wxIcon icon;
        icon.CopyFromBitmap(wxBitmap(xpm));
        if (icon.IsOk()) {
            bundle.AddIcon(icon);
        }
    }
    return bundle;
#endif
}

} // namespace wxui
} // namespace gui
} // namespace dottalk

#endif // DOTTALK_GUI_WX_RES_APP_ICON_HPP
