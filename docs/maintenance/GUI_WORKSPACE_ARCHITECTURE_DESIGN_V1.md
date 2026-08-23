---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-115
  recorded_at_utc: 2026-08-22T23:55:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: GUI API
    run_id: COWORK-20260822-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: a1045256b
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- "a redesign
      is in scope because our capabilities have increased ... harden the handles
      and where we are going with them, what is going to buy us the most
      flexibility"; plus two governing directives, "modify the new product to the
      existing dottalkpp product, so truth can flow from the bottom up" and "the
      last gui was the model to use with threading etc. it was getting good".
      Authorises this design note. Authorises NO build.
  report:
    path: docs/maintenance/GUI_WORKSPACE_ARCHITECTURE_DESIGN_V1.md
    kind: design_note
---

# GUI workspace architecture -- convergence, not rewrite

Status: **design note, review-needed. NO build authorised.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260822-001`.
Date: 2026-08-22. Baseline `a1045256b`.

**A number must be claimed with `claim-aif` before anything here is built.**
`TICKET_MULTI_WORKSPACE_GUI_V1.md` says it and it is right: grep is not an
allocator. This note takes no claim.

---

## 0. The one-paragraph version

The steward asked to harden the handles and asked what buys the most
flexibility. The answer is not a better handle. **The GUI currently reaches the
engine three different ways, and a handle means something different down each
one**, so no addressing model can be sound until that collapses to one path.
The good news, measured: the right path is **already built and already the
Windows default**, the threading layer around it is contract-bound and correct,
and the tree's own contract document names the two wrong paths as
anti-patterns. This is a convergence onto work already done, plus a five-tier
identity model that gives each existing number a defined lifetime.

## 1. Three paths to the engine, measured

| # | path | evidence | status |
|---|---|---|---|
| 1 | **Persistent child process** | `PersistentProcessShellRuntime`, `src/gui/core/gui_shell_runtime.cpp:132`; `make_script_shell_runtime()` returns it on Windows (`:497-504`) | **the destination** |
| 2 | One-shot `_popen` per command | `src/gui/core/gui_cli_bridge.cpp:242`; `ScriptShellRuntime` (`:34`) is what every non-Windows build gets | anti-pattern |
| 3 | **A second engine, in process** | `dottalk_gui_core PUBLIC xbase`; `Session::open_table` does `area->area.open(...)` with its own `impl_->next_area_id++` | anti-pattern |

**The tree already ruled paths 2 and 3 out, in its own words.**
`docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`, Anti-Patterns:

> - **GUI-specific database cursor state separate from x64base/DotTalk++ state**
> - **detached command bridge processes for ordinary persistent-session commands**
> - parsing console text as the only contract for new native GUI features

and, immediately after:

> Console parsing is acceptable as a **compatibility bridge** while the shared
> runtime API is being extracted. It should be replaced by typed runtime APIs
> where the core already exposes stable state.

Path 3 is the first bullet, verbatim. Path 2 is the second, verbatim. Nothing
here is a new opinion; it is the contract being applied.

**Correction to a prior document, and it changes that ticket's estimate.**
`TICKET_MULTI_WORKSPACE_GUI_V1.md` sec 1 states *"One engine, one area array,
one command executor."* That is **false**. It was checked against
`LoadWorkspaceFile`, which does submit a command string -- but `open_table`
bypasses the CLI entirely and opens the DBF in the GUI's own process. The
ticket's "genuinely small" slice is small only after paths 2 and 3 collapse.

## 2. What is already good and is KEPT

The steward: *"the last gui was the model to use with threading etc. it was
getting good."* Measured, and agreed:

- **`AsyncSession`** (`include/gui/core/async_session.hpp`,
  `src/gui/core/async_session.cpp`) -- RAII-owned worker thread, mutex +
  condition_variable + deque, `cancel_pending`, join on destruction. It carries
  a `@dottalk.contract v1` block whose clauses are exactly this design's
  constraints, including *"queued GUI work ... must not invent a frontend-only
  DBF/index/relation behavior layer."* **Unchanged by this design.**
- **`GuiShellRuntime` + `PersistentProcessShellRuntime`** -- the persistent
  session behind an interface, with a `ScriptShellRuntime fallback_`. Already
  the Windows default. **This is the direction that was getting good.**
- **`gui_runtime_adapter`** -- contract: *"adapters may project DbArea state
  into GUI models, but they must not redefine database semantics or take
  ownership of engine truth ... adapters are translation seams only."*
  `gui_workspace_of_area()` is documented as **the** seam that becomes a
  registry lookup: *"the single place that becomes a registry lookup, so no
  caller learns to assume the constant."* Somebody built the door. **Nothing
  needs designing here; it needs walking through.**

## 3. What is retired

1. **`Session`'s in-process area array.** `impl_->areas`, `impl_->next_area_id`,
   `area->area.open()`. The GUI stops owning `DbArea`s.
2. **The one-shot `_popen` path** for ordinary session commands, in favour of
   the persistent runtime. `ScriptShellRuntime` survives as the non-Windows
   fallback until a persistent POSIX implementation lands -- and that gap
   should be stated in the open items rather than discovered.
3. **`Session::save`'s posture emitter** (`session.cpp:2044-2115`, the
   `file << "AREA " << visible_area_id(...)` loop). It enumerates from
   `impl_->areas` -- **the session's own list** -- which is precisely the defect
   `WORKSPACE_WRITEBACK` exists to prevent: *"the manifest comes from the
   POSTURE's AREA lines ... not from the session's attached order, because the
   first cut asked the session and silently wrote 15 of 27 files while reporting
   cheerful success."* The engine's `WORKSPACE SAVE` carries seven registered
   regressions; the GUI's copy carries none. Consuming the engine's makes those
   seven specs cover the GUI by construction.

## 4. Harden the handles -- five tiers, each with a defined lifetime

This is the steward's central question. The defect today is not that any number
is wrong; it is that **five numbers are in play and none of them declares how
long it is valid.** Naming the lifetime is the hardening.

| tier | what | lifetime | may be persisted? | may cross a process? |
|---|---|---|---|---|
| **T1 durable identity** | catalog `WS_ID` (+ `PREV_ID` lineage) | forever | **yes -- it is the persisted identity** | yes |
| **T2 session handle** | `_ws_handle`, `uint64`, monotonic, never reused after destroy, 0 = none | ONE engine lifetime | **no** | **no** |
| **T3 engine slot** | `_engine_slot`, array position, stamped once | ONE engine lifetime | no | no |
| **T4 workspace-local slot** | `_ws_local_slot`, 0-based, reused after leave | ONE membership | no | no |
| **T5 posture ordinal** | `AREA <n>` in a `.dtschema` | the posture | yes (it IS the posture) | yes |

**T1 is the identity, and the catalog already proves why.** `WS_ID` is a
surrogate with no business meaning, allocated max+1 under `FLOCK`, declared
PRIMARY, with `PREV_ID` chaining lineage across 106 rows. `WS_NAME` is
**deliberately not unique** -- 89 of 106 rows are `SUPERSEDED` and the names
repeat on purpose. *Had identity been keyed on the name, the supersede chain
could not exist.* Any GUI model that keys workspaces by name inherits that
defect.

**T2's lifetime is the whole argument for section 1.** `workspace::create`
allocates from a function-local `static` counter that starts fresh in every
process. Under path 2 a handle is born and dies inside one `_popen` call, so
`WORKSPACE REGISTRY` output reports handles that are meaningless the moment the
pipe closes. **Under path 1 the engine lifetime IS the GUI session**, so T2
becomes stable and usable -- and stays private, never persisted, never shown as
identity.

**T5 is not T3 and the GUI must never print it as one.** Invariant I3: LOAD
walks `AREA` lines in order, allocates a fresh slot per line, and resolves
`CURSOR k` / `CURRENT k` **by position**. The two agree only in the classic
single-workspace case.

**Reserved, and nothing may depend on it yet.**
`dottalk::reference::WorkspaceIdentity` / `WorkspacePath` are the intended
public spelling. Measured occurrences: `src/xbase` **0**, `src/cli` **0**,
`src/gui` **0** -- only their own definition plus one smoke test constructing
literals. **Zero runtime writers.** They become the public identity when
something produces one; until then a design that keys on them is naming a type
the engine does not speak. `DbAreaIdentity::generation` is the same shape --
the field exists to distinguish "same slot, different life" and has no writer.

## 5. What the GUI consumes, and it is all already printed

No engine change is required to render the tree. The verbs exist and ship:

    WORKSPACE REGISTRY   handle, name, PARENT, depth, members, local slot,
                         engine slot, current handle, recursion, ambiguity count
                         -> the workspace tree AND area membership, complete
    WORKSPACE CATALOG    name, FMT, SIZE_B, areas, timestamp, author, superseded
                         -> the persisted list; FMT distinguishes MINIDB 1 from
                            DTSHEMA 2/3, which is where "nested database" lives
    REL LIST ALL         the relation tree with match counts
    BUILDVECTORS         the capacity authority
    VDISK STATUS         RAM root, mount state, bytes, resident files

**A memo-resident mini-database is not a third kind of node.** Design invariant
I6 makes carrier and residence WORKSPACE PROPERTIES:

    carrier   : FILE | MEMO     residence : DISK | RAM

So the tree is workspaces and areas; MINIDB-ness is an attribute. That is also
the GUI's column set, already specified: `WORKSPACE LIST` is *"registry
projection: name, carrier, residence, areas, groups, locks held."*

## 6. Rules the GUI must not break, each measured by someone else

- **Never render per slot.** `MAX_AREA` has no upper bound; the CLI's own
  listing prints 512 `--- closed ---` lines. List OPEN AREAS only.
- **Carry the slot as 64-bit and format it as text.** `MAX_AREA` is an `int`
  while the build vector asserts only `<= uint32_t::max()` -- a two-fold
  narrowing window with no guard (ticket F8, AIF-078 D3, open).
- **No linear name resolution in the GUI.** Ask the registry. `WS` is the
  ambiguity signal, not decoration: when two workspaces hold `STUDENTS`, the
  column is the difference between two rows and one quietly-wrong row.
- **Do not ship a fifth cascade number.** Depth is a call-site literal at four
  sites -- 24, 24, 24, and **64** at `cmd_dbareas.cpp:157` -- and its
  enforcement is SILENT while the scan limit announces truncation. The answer
  to "what is the cascade limit" is *24, unless you came through DBAREAS*.
- **Draw `ON key TO childkey`.** 190 of 1,102 posture RELATION lines (17.2%)
  bind differently-named endpoints. A renderer labelling edges with one key is
  wrong one time in six.

## 7. Sequence

- **S1.** Collapse to the persistent runtime. Retire path 2 for session
  commands; state the POSIX gap.
- **S2.** Retire `Session`'s own `DbArea` array; `open_table` becomes `USE`
  through the runtime, projected by the adapter. **This is the load-bearing
  step** -- T2 is not trustworthy until it lands.
- **S3.** Retire the GUI posture emitter; consume `WORKSPACE SAVE`.
- **S4.** `gui_workspace_of_area()` becomes the registry lookup it was written
  to become. Parse `WORKSPACE REGISTRY`; the model gains handle, parent, depth,
  carrier, residence.
- **S5.** The `WS` column and the workspace selector (ticket sec 2).
- **S6.** The tree view. No `wxTreeCtrl` exists anywhere in `src/gui/wx` today,
  so this is genuinely new UI and is the only step that is.

S1-S4 are deletions and re-pointings. **Only S6 is new construction**, which is
why "start over" is not the cheapest route to what the steward asked for.

## 8. Open for the steward

- **O1.** Claim a number, or run as a GUI slice under AIF-078? (Ticket T1,
  still open.)
- **O2.** The non-Windows persistent runtime gap: accept `ScriptShellRuntime`
  as the POSIX fallback, or is a POSIX persistent implementation in scope?
- **O3.** Ticket T2: projection-not-source for `WS_AREAS`/`WS_RELATION`/
  `WS_CURSOR`. Still unanswered and it decides whether the GUI joins tables or
  parses blobs.
- **O4.** Ticket T4 / F2: AIF-108's recursion blocker is **stale** -- memo
  sidecar carriage landed 2026-08-12 and 30 of 37 MINIDB containers now carry a
  nested `.dtx`. Ten test ideas are unblocked and the row still says blocked.
  Whose correction?
- **O5.** Ticket F5: `resolve_current_index()` -- the same MAX_AREA pointer scan
  this session deleted ONE copy of -- exists in **ten more files** under
  `src/cli`, two of them byte-identical, on the ordinary DELETE/RECALL mutation
  path. `cli::slot_of_area` is now const-correct and already visible to all ten.
  Ten one-line deletions.

## 9. Evidence tier

**Measured at `a1045256b`:** sec 1 (all three paths, at file:line), sec 2 (the
contract blocks quoted from the headers), sec 3 item 3 (the emitter's loop),
sec 4's `WorkspaceIdentity` census, sec 5's verb output (observed in this
session's own regression transcripts).
**Source-evidenced:** sec 4's tier table (each member read from `xbase.hpp` /
`workspace_membership.hpp` / the catalog ticket), sec 6 (each rule carries the
prior document that measured it).
**Chat/AI output:** sec 7's sequencing, sec 0's framing.
**NOT measured:** that retiring `Session`'s area array is behaviour-preserving
for the browse grid. It is the largest claim in S2 and it is unverified.

## 10. Good Neighbor note

- **What changed.** This document. No code, no build, no test.
- **Whose area.** The GUI lane's presentation layer; it corrects one factual
  claim in `TICKET_MULTI_WORKSPACE_GUI_V1.md` sec 1 and depends on
  `WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` invariants I1, I3, I4 and I6.
- **What authorization.** The steward, in-session 2026-08-22, quoted in the
  audit block above. **No build is authorised and no AIF number is claimed.**
- **How to verify.** `sed -n '132p;497,505p' src/gui/core/gui_shell_runtime.cpp`;
  `grep -n 'area->area.open' src/gui/core/session.cpp`;
  `grep -n 'target_link_libraries' src/gui/core/CMakeLists.txt`;
  `sed -n '114,128p' docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`;
  `grep -rn WorkspaceIdentity src/xbase src/cli src/gui | wc -l`.
- **How to undo.** Delete this file. Nothing depends on it.
