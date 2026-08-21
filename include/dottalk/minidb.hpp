// @dottalk.file v1
// subsystem: dottalk
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#pragma once

#include <cctype>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <string>
#include <string_view>
#include <vector>

// AIF-120. The MINIDB 1 container reader, separated from what a reader DOES
// with it.
//
// The format is written by build_minidb_container (src/cli/cmd_workspace.cpp)
// and was, until now, read only by hydrate_minidb in the same file:
//
//   MINIDB 1\n
//   POSTURE <len>\n<posture text bytes>
//   FILE <len> <relative-path>\n<file bytes>
//   ...
//   END\n
//
// Length-prefixed, so binary sections need no escaping -- DBF and CDX images
// contain every byte value and the memo store is payload-agnostic.
//
// WHY THIS IS ITS OWN UNIT. hydrate_minidb wrote each file to the RAM VFS as
// it parsed, so the file count and byte total existed only AFTER every byte
// had landed. That made hydration admission structurally impossible: there was
// no instant at which the cost was known and not yet paid, which is why
// nothing on that path ever consulted recommended_budget_bytes(). Scanning
// first turns one pass into scan -> decide -> materialize, and the decision
// point is the thing that did not exist before.
//
// It also gives EST_HYD_B its first writer. cmd_workspace.cpp:2184 charters
// the column as "estimated hydrated bytes (budget input)" and :2418 leaves it
// deliberately empty; total_file_bytes below is that number, derivable both
// when the container is built and when it is read, so the two can be checked
// against each other.
//
// And it is what a read-only browser needs: the posture and the member list
// with sizes, having written nothing anywhere.
//
// This parser follows hydrate_minidb's original loop, including its tolerance
// of unknown sections, with ONE deliberate difference: a container with no END
// is an error here. The original simply ran off the end of the payload and, if
// a posture had already been seen, reported success -- so a truncated container
// hydrated partially and said it worked. Refusing is the point of scanning
// before writing; recording the difference here so it is not mistaken for
// fidelity. It performs NO I/O.

namespace dottalk::minidb {

struct Member {
    std::string relpath;        // as stored: "STUDENTS.dbf" or "indexes/STUDENTS.cdx"
    std::size_t offset = 0;     // byte offset of the payload within the container
    std::size_t length = 0;
};

struct Scan {
    bool ok = false;
    std::string error;                          // set when !ok
    std::string posture;                        // the DTSHEMA text the container carries
    std::vector<Member> files;
    std::uint64_t total_file_bytes = 0;         // EST_HYD_B: what hydration will cost
    std::vector<std::string> ignored_sections;  // unknown section lines, verbatim
};

// Cheap header sniff, matching cmd_workspace.cpp's own test at :2634.
inline bool is_container(std::string_view payload) noexcept {
    return payload.rfind("MINIDB 1\n", 0) == 0;
}

namespace detail {

inline std::string trim_ascii(std::string s) {
    auto sp = [](char c) noexcept {
        return std::isspace(static_cast<unsigned char>(c)) != 0;
    };
    std::size_t b = 0, e = s.size();
    while (b < e && sp(s[b])) ++b;
    while (e > b && sp(s[e - 1])) --e;
    return s.substr(b, e - b);
}

inline std::string lower_ascii(std::string s) {
    for (char& c : s) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

} // namespace detail

inline Scan scan(const std::string& payload) {
    Scan r;
    std::size_t pos = 0;

    auto read_line = [&](std::string& out) -> bool {
        const auto nl = payload.find('\n', pos);
        if (nl == std::string::npos) return false;
        out = payload.substr(pos, nl - pos);
        pos = nl + 1;
        return true;
    };

    std::string line;
    if (!read_line(line) || detail::trim_ascii(line) != "MINIDB 1") {
        r.error = "unrecognized container header";
        return r;
    }

    bool saw_end = false;
    while (read_line(line)) {
        const std::string t = detail::trim_ascii(line);
        if (t == "END") { saw_end = true; break; }
        const std::string low = detail::lower_ascii(t);

        if (low.rfind("posture ", 0) == 0) {
            const std::size_t len =
                static_cast<std::size_t>(std::strtoull(t.substr(8).c_str(), nullptr, 10));
            if (pos + len > payload.size()) { r.error = "truncated posture"; return r; }
            r.posture = payload.substr(pos, len);
            pos += len;
        } else if (low.rfind("file ", 0) == 0) {
            // trim first: the original used istringstream >>, which skips
            // leading whitespace, so "FILE  123 x" must still parse.
            const std::string rest = detail::trim_ascii(t.substr(5));
            const std::size_t sp = rest.find(' ');
            if (sp == std::string::npos) { r.error = "bad FILE section"; return r; }
            const std::size_t len =
                static_cast<std::size_t>(std::strtoull(rest.substr(0, sp).c_str(), nullptr, 10));
            const std::string rel = detail::trim_ascii(rest.substr(sp + 1));
            if (rel.empty() || pos + len > payload.size()) {
                r.error = "bad FILE section";
                return r;
            }
            r.files.push_back(Member{rel, pos, len});
            r.total_file_bytes += len;
            pos += len;
        } else {
            // Faithful to the original loop: an unknown section is reported and
            // skipped. Note it carries no length, so a future section that does
            // would desync the stream here -- it is recorded, not swallowed.
            r.ignored_sections.push_back(t);
        }
    }

    if (!saw_end) { r.error = "container has no END"; return r; }
    if (r.posture.empty()) { r.error = "container carried no posture"; return r; }

    r.ok = true;
    return r;
}

} // namespace dottalk::minidb
