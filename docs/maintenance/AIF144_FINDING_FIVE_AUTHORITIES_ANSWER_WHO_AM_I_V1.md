# AIF-144 -- FIVE AUTHORITIES ANSWER "WHO AM I", AND THE LOCK SYSTEM ASKS NONE OF THEM

    Number  : AIF-144, claimed 2026-08-27 with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001, lane
              'identity-authority-fragmentation'). Claim file verified present
              at `coordination/aif/AIF-144.claim` before the number was cited.
    Found   : 2026-08-27. The path-resolver half surfaced while looking for a
              way to keep regression rows out of the production workspace
              catalog; the LOCK half was surfaced by the owner --
              "record locking is user controlled too - it should be globally
              consistent" -- and is the half that matters most.
    Lane    : identity / RBAC / concurrency. Predates multi-workspace, and
              multi-workspace is what makes it reachable.
    Status  : review-needed. The author does not self-approve.
    Basis   : SOURCE-EVIDENCED, lines cited. **NOTHING HERE WAS RUN.** No
              two-member session was driven, no lock contention was staged, no
              threaded GUI exists to race. Every claim below is a reading of
              the tree, and the two claims that would most repay a runtime
              check are named in sec 8.
    Shape   : R5 -- one question, five answers. With the aggravation that the
              five do not disagree about a VALUE, they disagree about what the
              question means, so no comparison between them can ever be wrong.
    Severity: SPLIT, and the split is the useful part.
              ATTRIBUTION is wrong TODAY and reachable in two commands.
              EXCLUSION is correct today and becomes wrong the day two
              sessions share one process -- which the GUI is now close to.

## 1. THE FIVE

| authority | what it answers with | who consumes it |
|---|---|---|
| `identity::acting_member_key()` | `member.derald` | RBAC, BBS authorship, NET, SFTP, SMTP, BANG, APPGUI, ai_devtools_policy -- **12 sites, 7 subsystems** |
| `TeamMember::profile_home_key` | `dottalkpp/user/<key>/` | **nothing** |
| `user_scope_paths::current_user_name()` | the literal `"default"` | workspace/script roots |
| `cmd_security` legacy selector | `DEVELOPER / TEACHER / STUDENT` + six roots | `SECURITY SHOW/WHOAMI`, self-declared legacy |
| `locks::current_owner()` | `host:pid:ms` | every table and record lock |

**Authority 1 is live and load-bearing.** `src/identity/identity_admin.cpp:366`.
Twelve call sites gate host commands, egress toggling, external processes, the
GUI, and BBS post attribution (AIF-075).

**Authority 2 is persisted and unread.**
`include/identity/identity_entities.hpp:47`:

    std::string  profile_home_key;  // binds to dottalkpp/user/<key>/  (Contract 5)

Written to DBF as `PROFHOME` (`identity_dbf_store.cpp:157`), read back
(`:301`), set at bootstrap (`identity_bootstrap.cpp:107`). Nothing consumes it.

**Authority 3 is hardcoded past authority 1.**
`include/user_scope_paths.hpp:34`:

    inline std::string current_user_name()
    {
        // Replace later with real authenticated user/profile selection.
        return "default";
    }

Its `user_profile_root(name)` builds `app_root()/"user"/name` -- **the exact
path authority 2's contract comment names.** The two halves already agree on
the directory layout; the only thing between them is that one never asks the
other. And `workspace_search_roots()` in the same header is included by exactly
ONE file in the tree, `src/cli/extension_manifest.cpp` -- not by
`cmd_workspace.cpp`, whose `catalog_dir()` (`:2738`) resolves through
`paths::Slot::WORKSPACES` alone.

**Authority 4 declares its own conflict, which is the good version.**
`cmd_security.cpp`'s usage block says plainly that its LOGIN "establishes only
the legacy diagnostic role selector ... it is not USER authentication and
grants no RBAC access", and points the reader at `USER`. It nevertheless
carries `detect_profile_name()` (`:106`) and a six-root context
(`app_user_root`, `app_public_root`, `app_default_root`, and the three `os_`
counterparts) printed by `SECURITY SHOW` (`:207-213`) -- a second, independent
implementation of the profile-root idea. The fence is prose in a usage block
and nothing enforces it.

**Authority 5 does not know people exist.** See sec 2.

## 2. THE LOCK HALF -- FIRST, BECAUSE IT CAN LOSE WORK

`include/xbase_locks.hpp:20`:

    // A comparable token for "who owns the lock". Use a stable
    // per-process/session id.
    struct Owner {
        std::string id;            // e.g., "host:pid:nonce"
        bool operator==(const Owner& o) const noexcept { return id == o.id; }
    };

`src/xbase/xbase_locks.cpp` builds it as `host << ":" << pid << ":" << ms` and
memoises it:

    const Owner& current_owner() {
        static Owner g_owner{ make_owner_string() };
        return g_owner;
    }

Computed once per process and immutable thereafter. Every shim -- `:332`,
`:337`, `:418`, `:423`, `:454` -- takes locks and releases them as this token.

**`USER AS <member.key>` changes authority 1 and does not touch authority 5.**
(`identity_admin.cpp:430,:435`.) So within one process:

- Two members share ONE lock identity. The second inherits the first's locks
  and can release them.
- Conversely, one member in two processes has TWO identities and can block
  themselves.
- `LOCK WHO <n>` -- whose own usage line reads *"reports the owner of record n
  when a lock is recorded"* (`cmd_lock.cpp:39`) -- prints `host:pid:ms`.
  **A command named WHO that cannot say who.**

### The part where this finding argues against itself

Process-scoped lock identity is NOT simply wrong, and saying so would be the
easy, false version of this finding.

Classic xBase holds locks per workstation. `host:pid` is the correct token for
the MECHANISM: it answers "is the holder still alive", which is exactly what
stale-lock reclamation needs, and that parse path has already been hardened
once -- AIF-116/AIF-031, where locale digit grouping produced `16,984` and made
every live lock look stale. The comment recording that fix is still in the file
and it is right.

The defect is narrower: **the member is nowhere in the lock record at all.**
The system knows who is acting, persists that identity to a DBF, and gates host
commands on it -- then records a concurrency claim attributable to no one.
Accountability drops out at precisely the layer where two people contend.

So the fix shape is BOTH, not INSTEAD: keep the process token for liveness, add
the member for attribution.

## 3. THE PATH-RESOLVER HALF, AND WHY THE OBVIOUS FIX IS WRONG

The tempting move is to wire authority 3 to authority 1 -- `current_user_name()`
resolves through `acting_member_key()` to `profile_home_key`. It is a short
wire and the layouts already match.

**It should not be done that way, and this is the finding's main negative
recommendation.**

`current_user_name()` feeds `user_profile_root()` feeds
`resolve_workspace_file_path()` feeds BOTH `catalog_dir()` and
`WORKSPACE SAVE`. Wire it to the live actor and the workspace root changes
identity with the session: during an agent session `acting_member_key()` is
`member.ai.claude.cowork`, so every existing posture and the entire catalog
resolve under a different root and **appear to vanish** -- with no error,
because a search that finds nothing is indistinguishable from a directory that
is empty. An empty result is not a measurement, applied to a whole data root.

There is a second trap in the same header. `workspace_search_roots()` is a
SEARCH list, correct for FINDING an existing posture and ambiguous for deciding
where a NEW row is WRITTEN. Reading down a list and choosing a write root are
different operations and the header does not distinguish them; an
implementation that conflates them writes to the global root while appearing
scoped.

## 4. A LATENT THREADING DEFECT, NAMED WHILE IT IS STILL LATENT

`identity_admin.hpp:74` and `:94` declare:

    const std::string& principal_key();
    const std::string& acting_member_key();

Both return a REFERENCE into a plain mutable global (`identity_admin.cpp:311`,
`g_acting`), written by SIX sites: `set_acting_member` (`:367`), login
(`:395`, `:400`), logout (`:405`), and `USER AS` (`:430`, `:435`).

A reader holding that reference while another thread logs in or switches actor
is not racing on a value -- `std::string` assignment can reallocate the buffer
the reader is holding. That is undefined behaviour, at twelve call sites.

**It is not a bug today.** Measured: `src/gui/core/session.cpp` contains no
`std::thread`, no `QThread`, no `std::mutex`, no `invokeMethod`. Recorded now
because the moment threading arrives it is live, and because normalization is
the natural occasion to change the shape -- return by value, or move the value
into a session object where it belongs.

## 5. WHY THIS BLOCKS GUI THREADING, AND IT IS NOT THE RACE

The race in sec 4 is the small reason. The large one:

All five authorities are implicitly PROCESS-scoped. The GUI has just become a
first-class engine consumer -- `Session::Impl::Area` holds
`XBaseEngine* + int slot` (AIF-078 step 2b), so a GUI session is a real
participant rather than a mirror.

The day two sessions live in one process -- two GUI sessions, or a GUI session
beside the CLI -- `host:pid:ms` gives them ONE lock owner. **They cannot
contend.** Every lock between them succeeds and excludes nothing, because the
mutual-exclusion token is identical by construction. That is not a race a mutex
would catch; it is a mutex that was never there.

**Normalizing identity is therefore not a threading fix. It is the
prerequisite.** "Who am I" has to become per-SESSION before it can meaningfully
become per-thread, and every one of the five authorities answers per-process
today.

## 6. WHAT THIS FINDING DOES NOT CLAIM

- It does NOT claim any of the five is individually wrong. Each is defensible
  in the scope it was written for. The defect is that there are five.
- It does NOT claim data has been lost or a lock has failed. Nothing was run;
  sec 8 says what a run would settle.
- It does NOT claim `USER` can drive `current_user_name()` today. Measured:
  they do not speak. Feasibility of the wire is argued, not demonstrated.
- It does NOT claim the `SECURITY` selector is a defect. It declares its own
  limits in its usage block, which is more than most divergences do.
- It does NOT size the work. No call-site census was taken for `catalog_dir()`
  or for the `Owner` equality change.

## 7. THREE RULINGS, STATED AND NOT TAKEN

**R-a. Does `Owner::operator==` fold in the member?** It compares the whole
`id` string. Append the member and lock identity changes MEANING: either each
member's locks become their own -- right for accountability, and it means a
process can no longer release locks it took before a `USER AS` -- or equality
compares only the process half and carries the member as payload. Those are
different systems and the difference is invisible until two people share a
process.

**R-b. May the path resolver follow the live actor?** Sec 3 argues NO, or not
without separating search roots from the write root first. Regression isolation
wants a narrow, explicit, temporary redirect of the catalog root; profile-scoped
data homes are a much larger decision and should not arrive as a side effect of
tidying test residue.

**R-c. What becomes of the `SECURITY` legacy selector?** Retire it, keep it
with the fence enforced rather than merely written, or fold its six roots into
whatever authority survives.

`include/**`, `src/cli/**` and `src/xbase/**` are all engine. Any fix wants an
explicit go.

## 8. HOW TO VERIFY, AND WHAT A RUN WOULD SETTLE

Read-only verification of every claim above:

    grep -n "g_acting" src/identity/identity_admin.cpp
    grep -n "acting_member_key\|principal_key" include/identity/identity_admin.hpp
    grep -n "profile_home_key" include/identity/identity_entities.hpp
    grep -n "current_user_name" -A 4 include/user_scope_paths.hpp
    git grep -l "user_scope_paths"                 # expect: 2 (header + extension_manifest.cpp)
    grep -n "current_owner" -A 4 src/xbase/xbase_locks.cpp
    grep -n "catalog_dir" -A 4 src/cli/cmd_workspace.cpp

**Two things a run would settle, and neither was run:**

1. **`USER AS` across a lock.** `USER LOGIN` as one member, lock a record,
   `USER AS` a second member, `LOCK WHO` that record, then unlock. If the second
   member can release it, sec 2's attribution claim is runtime-proven rather
   than read. This is two commands away and should be done before any ruling.
2. **`LOCK WHO` output shape.** Confirm it prints the raw `host:pid:ms` to a
   user. Cited from `cmd_lock.cpp:39` and `:121-130`; seeing it is cheaper than
   arguing it.

## 9. GOOD NEIGHBOUR

- **What changed:** nothing executable. This document only.
- **Whose area:** `include/identity/**`, `src/identity/**`, `include/xbase_locks.hpp`,
  `src/xbase/xbase_locks.cpp`, `include/user_scope_paths.hpp`,
  `src/cli/cmd_lock.cpp`, `src/cli/cmd_security.cpp`, `src/cli/cmd_workspace.cpp`.
  None were modified.
- **Authorization:** AIF-144 claimed and verified in the ledger before the
  number appeared anywhere. The owner directed the write-up and named the lock
  half.
- **How to verify:** sec 8, seven read-only commands.
- **How to undo:** delete this file and release AIF-144 with
  `session_coordinator.py release-aif --number 144 --run COWORK-20260827-001`.
