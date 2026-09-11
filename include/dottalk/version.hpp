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
//
// AIF-122. The four values now arrive from a GENERATED HEADER emitted by
// configure_file (copy-if-different), not as -D on every command line. This
// header has exactly two includers, so a changed SHA recompiles two files
// instead of the ~400 the command-line form recompiled.
//
// Guarded by __has_include so this header still stands alone: a non-CMake
// build, or a bare `g++ -fsyntax-only`, finds no stamp and falls through to
// the deliberately-implausible defaults below, which is the behaviour the
// comment above describes.
#if defined(__has_include)
#  if __has_include(<dottalk/version_stamp.hpp>)
#    include <dottalk/version_stamp.hpp>
#  endif
#endif

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

// THE MATURITY WORD IS THE SECOND HALF OF THE PRODUCT LABEL, AND THE ONLY PART
// A HUMAN SETS ON PURPOSE (2026-09-11).
//
// The numbers say WHICH release; this word says WHAT KIND. It is deliberately a
// single coarse token -- alpha, beta, rc, release -- changed rarely and by
// decision, because a maturity that moved as often as a patch number would be
// telling nobody anything.
//
// Its fallback carries NO DIGITS by design. The unconfigured version marker
// works by being unmistakable; this one works the same way, and additionally
// cannot trip check_version_coherence.py, whose literal detector looks for
// MAJOR.MINOR and would need an exception for any maturity token holding one.
#ifndef DOTTALKPP_MATURITY
#define DOTTALKPP_MATURITY "unconfigured"
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

inline std::string maturity()
{
    return DOTTALKPP_MATURITY;
}

// THE HUMAN LABEL, DERIVED AND NEVER DECLARED (2026-09-11).
//
// The product read v0.6 for months because the numeral was the only thing
// anyone saw, and a numeral nobody can interpret is a numeral nobody bumps. The
// label a reader actually wants is "which beta is this", and that is not a
// second fact -- it is the SAME two numbers, rendered:
//
//     major -> the cycle     1
//     minor -> a letter      0 -> a, 1 -> b, 2 -> c ...
//
// so project(DotTalkpp VERSION 1.1) renders "beta 1.b" and the next bump is one
// line in CMakeLists.txt. There is nothing here to keep in step, which is the
// entire point. AIF-120 collapsed five hand-typed copies of the version and
// check_version_coherence.py now blocks a sixth; a hand-kept "beta 1.b" beside
// a numeric 0.6 would have BEEN that sixth copy, and worse than the ones the
// gate catches -- it holds no MAJOR.MINOR for the gate's literal detector to
// find, so it would have drifted silently and permanently.
//
// THE BARE NUMERAL IS WITHHELD WHILE THE BUILD IS PRE-RELEASE, and that is what
// makes 1.x honest here: nothing renders "1.1" until the maturity word says
// release, so the number cannot be read as a shipped one. At release the word
// changes and the SAME numbers render "1.1". The numbers never jump and never
// lie.
//
// EVERY PATH THAT CANNOT PRODUCE A LABEL SAYS SO INSTEAD OF GUESSING -- an
// unconfigured build, an unparseable version, a minor past 'z'. The alternative
// is 'a' + 26 silently becoming '{', which is this tree's recurring failure
// shape in a new field: an instrument that cannot report its own limit.
inline std::string release_label()
{
    const std::string numeric = version_label();
    const std::string word    = maturity();

    if (word == "unconfigured" || numeric == "0.0-unconfigured") {
        return "UNCONFIGURED BUILD (" + numeric + ")";
    }

    // A released build is its numeral and nothing else -- decided HERE, above
    // every fallback below, so the word can never leak into a degraded label as
    // "release 1.26". The maturity word exists to say a build is NOT released;
    // once it is, there is nothing left for it to say.
    if (word == "release") return numeric;

    const std::string::size_type first_dot = numeric.find('.');
    if (first_dot == std::string::npos) return word + " " + numeric;

    const std::string major = numeric.substr(0, first_dot);
    std::string       minor = numeric.substr(first_dot + 1);
    const std::string::size_type second_dot = minor.find('.');
    if (second_dot != std::string::npos) minor = minor.substr(0, second_dot);
    if (major.empty() || minor.empty()) return word + " " + numeric;

    for (const char c : major) {
        if (c < '0' || c > '9') return word + " " + numeric;
    }
    for (const char c : minor) {
        if (c < '0' || c > '9') return word + " " + numeric;
    }

    int minor_value = 0;
    for (const char c : minor) {
        minor_value = minor_value * 10 + (c - '0');
        if (minor_value > 25) return word + " " + numeric;   // out of letters
    }

    const char letter = static_cast<char>('a' + minor_value);
    return word + " " + major + "." + std::string(1, letter);
}

// The banner shows the human label and the COMMIT the code came from. WHICH
// BUILD the binary came from is a separate question with a separate answer, in
// dottalk/build_stamp.hpp: a rebuild of an unchanged commit produces a new
// executable and an identical SHA, which is how 2026-09-11 was spent asking
// which of two binaries had produced a transcript.
//
// `dirty` WAS HERE AND IS NOT ANY MORE. It is an HONEST flag -- AIF-120 R118
// fixed it on 2026-08-22, and it has since meant "a TRACKED file differed from
// HEAD when CMake configured", which is a true and useful thing. It is gone
// from the DISPLAY because in a shared development worktree it is true on every
// build ever made here, and a light that is always on is not a warning, it is
// furniture. git_dirty() is UNCHANGED and still available to any reader that
// wants it: nothing was deleted, only unpublished, and putting it back is one
// line if this tree ever builds from a clean checkout.
//
// version_date() is likewise unpublished rather than removed. It is HEAD's
// COMMIT date (git log -1 --format=%cs), never the build date -- a distinction
// that misled a reader of this very banner on 2026-09-11 -- and the SHA beside
// it identifies the same commit more precisely in less room.
inline std::string display_version()
{
    std::string text = release_label();
    const std::string sha = git_sha();
    if (!sha.empty() && sha != "nogit") {
        text += ", " + sha;
    }
    return text;
}

} // namespace dottalk::version
