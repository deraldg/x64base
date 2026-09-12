// @dottalk.file v1
// subsystem: xbase
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported
//
// R6 (ruling D10 sec 2a, 2026-08-23): an absent value must not be
// representable in the space of present ones.
//
// workspace::join() takes a signed engine slot, and -1 arrived carrying TWO
// unrelated meanings: "this area has no engine slot at all" (every DbArea not
// in XBaseEngine's array -- roughly 47 of them in this tree) and "this member
// entry is FREE" (the marker join's own claim loop looks for). The two absences
// were the same value, so a slotless area matched a free entry, was handed its
// index, and claimed nothing.
//
// Every arm below compares a VALUE the membership table reports. Nothing here
// touches the filesystem.

#include "xbase/workspace_membership.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

bool require(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        return false;
    }
    return true;
}

bool holds(const std::vector<std::int32_t>& members, std::int32_t slot) {
    return std::find(members.begin(), members.end(), slot) != members.end();
}

} // namespace

int main() {
    namespace ws = xbase::workspace;

    // ---- G0: the fixture, asserted before anything is claimed about it ----
    const std::uint64_t h = ws::create("R6TEST");
    if (!require(h != 0, "could not create the test workspace")) {
        return EXIT_FAILURE;
    }
    if (!require(ws::join(h, 3) == 0 && ws::join(h, 7) == 1,
                 "two joins did not take workspace-local slots 0 and 1")) {
        return EXIT_FAILURE;
    }
    if (!require(ws::member_count(h) == 2, "fixture workspace does not hold two members")) {
        return EXIT_FAILURE;
    }

    // ---- T1/T2: THE DISCRIMINATOR, on a FULL member list ------------------
    // Before the guard: no entry equals -1 and none is free, so join FELL
    // THROUGH to push_back(-1) and returned 2 -- it grew the member list by an
    // entry that is simultaneously a member and the free marker. Both arms
    // flip.
    if (!require(ws::join(h, -1) < 0, "join ACCEPTED a negative engine slot")) {
        return EXIT_FAILURE;
    }
    if (!require(ws::member_count(h) == 2,
                 "a refused join still changed the member list")) {
        return EXIT_FAILURE;
    }

    // ---- T3: the subtler case -- a HOLE in the member list ----------------
    // This is the arrangement the ~47 scratch handles actually met. With slot 3
    // gone, members are [-1, 7]; before the guard, join(h, -1) matched that hole
    // in the IDEMPOTENCE scan and returned 0 WITHOUT claiming it, so two
    // slotless areas could both be told they held local slot 0 while slot 0 sat
    // free.
    ws::leave(h, 3);
    {
        const auto m = ws::members(h);
        if (!require(m.size() == 2 && m[0] < 0 && holds(m, 7),
                     "leaving slot 3 did not leave a hole with slot 7 intact")) {
            return EXIT_FAILURE;
        }
    }
    if (!require(ws::join(h, -1) < 0, "join accepted a negative slot against a hole")) {
        return EXIT_FAILURE;
    }
    {
        const auto m = ws::members(h);
        if (!require(m.size() == 2 && m[0] < 0,
                     "the refused join consumed the free entry")) {
            return EXIT_FAILURE;
        }
    }
    // And the hole is still there for a REAL slot to take -- the vacancy was
    // preserved, not spent. (Not a discriminator; it held either way. It is
    // here so a future tightening that drops holes fails HERE.)
    if (!require(ws::join(h, 5) == 0, "a real join did not reuse the free local slot")) {
        return EXIT_FAILURE;
    }

    // ---- T4: leave(), the symmetric half ----------------------------------
    // STATED PLAINLY: this is NOT a discriminator. A negative leave matched a
    // hole and re-cleared it, which was harmless in every arrangement measured.
    // The guard exists so the two halves of one rule read the same, and this
    // arm exists so the guard cannot be deleted unnoticed.
    ws::leave(h, -1);
    {
        const auto m = ws::members(h);
        if (!require(holds(m, 5) && holds(m, 7),
                     "a negative leave disturbed the real members")) {
            return EXIT_FAILURE;
        }
    }

    // ---- T5: the pre-existing refusal still travels in the return value ----
    if (!require(ws::join(0, 3) < 0, "join accepted the reserved handle 0")) {
        return EXIT_FAILURE;
    }
    if (!require(ws::join(999999, 3) < 0, "join accepted an unknown handle")) {
        return EXIT_FAILURE;
    }

    // ---- teardown: a spec that leaves residue poisons what runs after it ---
    ws::leave(h, 5);
    ws::leave(h, 7);
    if (!require(ws::member_count(h) == 0, "members remained after leaving every slot")) {
        return EXIT_FAILURE;
    }
    if (!require(ws::destroy(h), "could not destroy the emptied test workspace")) {
        return EXIT_FAILURE;
    }

    std::cout << "R6: absent is not a value -- join/leave refuse a negative engine slot\n";
    std::cout << "PASS: dottalkpp workspace membership\n";
    return EXIT_SUCCESS;
}
