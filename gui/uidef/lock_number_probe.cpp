// @dottalk.file v1
// subsystem: gui
// layer: probe
// owns: standalone main(); no uidef_register
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: supported
// summary:
//   R48 -- whether AIF-116's defect shape exists for a frontend
//
// notes:
//   Contract added 2026-08-22. This directory was promoted from lane to
//   project in 898a37b62 without them, so 14 of its 15 C++ files were
//   INVISIBLE to the doc pass -- not undocumented, invisible: the pass
//   completed and reported success while covering less than it claimed.

// AIF-120 R48 -- does AIF-116's defect surface exist for a FRONTEND?
//
// AIF-116: `xbase::locks` wrote the owner pid through an un-imbued stream while a
// grouping locale was active, producing `pid=16,984`. The reader used std::stoul,
// which stops at the comma and returns 16, so the liveness check asked whether pid
// 16 was alive, said no, called the lock stale and granted it. Cross-process mutual
// exclusion did not hold, deterministically. Fixed at fe42666e.
//
// A generated frontend that renders a RECORD NUMBER into a command has the same
// surface. This is that surface, in isolation. The answer R48 takes from it is not
// "imbue carefully" -- it is that DotTalk++'s bare `LOCK` locks the current record
// and carries no number, so the runtime never renders one.
//
//   g++ -std=c++14 gui/uidef/lock_number_probe.cpp -o lock_number_probe && ./lock_number_probe
#include <cstdio>
#include <locale>
#include <sstream>
#include <string>

struct Grouping : std::numpunct<char> {
    char do_thousands_sep() const override { return ','; }
    std::string do_grouping()  const override { return "\3"; }
};

int main() {
    std::locale grouping(std::locale::classic(), new Grouping);
    std::locale::global(grouping);              // exactly AIF-116's runtime condition

    unsigned long recno = 16984;

    std::ostringstream imbued;                  // a default-constructed stream
    imbued << "LOCK " << recno;                 // picks up the GLOBAL locale

    std::ostringstream classic;
    classic.imbue(std::locale::classic());
    classic << "LOCK " << recno;

    printf("  default-constructed ostringstream : %s\n", imbued.str().c_str());
    printf("  imbued with classic()             : %s\n", classic.str().c_str());
    printf("  std::to_string                    : LOCK %s\n", std::to_string(recno).c_str());

    unsigned long back = std::stoul(imbued.str().substr(5));
    printf("  round-trip of the grouped form    : %lu   <-- AIF-116\n", back);
    return 0;
}
