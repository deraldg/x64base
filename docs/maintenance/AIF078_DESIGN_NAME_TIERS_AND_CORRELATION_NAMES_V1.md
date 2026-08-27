# AIF-078 DESIGN -- NAME TIERS, AND THE ALIAS AS A CORRELATION NAME

    Date    : 2026-08-27
    Lane    : AIF-078 (multi-workspace). Rides the lane number; no new AIF.
    Asked   : by member.derald -- "we need to account for long table and long
              field names when working with relational algebra, those mangling
              algorithms need to be refactored for workspace and x64base engine
              usage -- so using the alias has a double use of allowing us to use
              a unique temporary name with no meaning, kind of like a unique
              key. am i right, advise"
    Status  : review-needed, and DESIGN ONLY. Nothing here is ruled and no code
              is proposed for writing.
    Basis   : SOURCE-EVIDENCED, lines cited, measured 2026-08-27. The runtime
              claims in sec 2 were read from code today; the prose they
              contradict is named in sec 6.

## 1. THE ANSWER IN ONE PARAGRAPH

**Yes on correlation names -- that is what relational algebra requires, and
`USE ... ALIAS <name>` is already the right surface for it.** No on the alias
becoming the identity: that makes one string do two jobs whose requirements
point in opposite directions. **The unique meaningless identity the question is
reaching for ALREADY EXISTS** -- `DbArea::_area_handle` -- and nothing resolves
on it. And **the long-name problem the question assumes is mostly not there at
runtime on x64**, for a reason that contradicts what the tree says about
itself.

## 2. THE MEASUREMENT THAT CHANGES THE QUESTION

**A CDX TAG HAS NO KEY EXPRESSION. THE TAG NAME IS THE KEY.**
`CDX ADDTAG <name>` (`src/cli/cmd_cdx.cpp:341`) stores `up_copy(name)` and
nothing else. `field_index_for_tag_()` (`src/xindex/cdx_native_backend.cpp:72`)
resolves it at use time by walking `A.fields()` and string-matching.

**AND `FieldDef` HAS EXACTLY ONE NAME SLOT** (`include/xbase.hpp:166`). On an
x64 table the descriptors are read first, and then
`x64_apply_name_metadata` (`include/xbase_64.hpp:469-470`) calls
`setFieldName()`, which **OVERWRITES `_fields[i].name` in place**
(`include/xbase.hpp:383`) with the long name from the `X64M` string pool. The
descriptor token is not retained anywhere in memory.

**THEREFORE, ON AN x64 TABLE AT RUNTIME, CDX AND THE RELATION ENGINE RESOLVE
AGAINST THE SAME STRING: THE LOGICAL LONG NAME. ONE NAMESPACE, NOT TWO.**

So `field_name_policy` is a **write-side** concern only. Its own comment
already says so -- *"logical_name remains authoritative and is not modified;
descriptor_name is a unique 10-byte DBF/VFP fallback token"* -- and the reader
supersedes the fallback on load. **It does not need refactoring for relational
use on x64. There is no boundary to translate across.**

## 3. THE THREE TIERS, AND WHICH ONES EXIST

| tier | what it is | built? | stable? |
|---|---|---|---|
| IDENTITY | `_area_handle` -- minted by `open()`, cleared by `close()`, never reused, 64-bit monotonic, `xbase.hpp:555` | **YES** | yes, within a session |
| NAME | `_logical_name` -- what a person types | yes | **NO -- collides** |
| STORAGE TOKEN | descriptor / `~n` mangle | yes, `field_name_policy` | **NO -- order-dependent** |

**THE IDENTITY TIER IS BUILT AND UNUSED FOR RESOLUTION.** Its own comment
states the property the question is asking for: *"a monotonic counter over the
life of a session, not an index into anything."* `WORKSPACE REGISTRY` prints it
(`area handle 128`). Nothing resolves a name through it.

## 4. WHY THE ALIAS MUST NOT BECOME THE IDENTITY

A handle must be unique and stable and is ALLOWED to be meaningless.
A name must be meaningful and memorable and is ALLOWED to be ambiguous.
**`students2` fails both tests at once.** It is not meaningful -- it means
"whichever one was not first" -- and it is not stable, because
`derive_distinct_alias()` (`cmd_use.cpp:491`) scans `stem+2..999` for the first
free candidate, so which instance receives it depends on OPEN ORDER.

That is the same objection R129 sec 6.1a used to reject parking `_current` at a
closed slot: **a value that is a function of unrelated state.** The field
mangler has the identical flaw one tier down -- `make_mangled_token` allocates
`~1`, `~2` by first-free scan over `used`, so a field's descriptor token depends
on the order the fields were planned in.

**THE PRECEDENT IS ALREADY RULED, ONE LEVEL UP.** A workspace has exactly this
split: `WS_ID` is durable, minted, and never reused; `WS_NAME` is human,
unique-among-live, and reclaimable (AIF-078 D10.1/D10.2/D10.3, and `WSL_T4`
asserts the reclamation directly). **The answer for AREAS is the answer already
ruled for WORKSPACES, one level down.**

## 5. WHAT A CORRELATION NAME ACTUALLY NEEDS, AND WHERE THE SURFACE FALLS SHORT

Relational algebra needs per-expression correlation names because one table can
appear twice in one expression -- `FROM orders o JOIN orders p`. **That is a
LABEL BOUND IN A SCOPE, not an identity**, and it is exactly the reading of the
question that is right.

**`USE ... ALIAS <name>` IS THE RIGHT SURFACE AND MAY BE THE WRONG LIFETIME.**
It binds for the life of the OPEN. SQL's `AS` binds for the life of the
STATEMENT. Those are different scopes:

- a session-scoped alias cannot express two correlations of one table inside a
  single `REL ENUM` or `SQLSEL` without opening the table twice;
- an expression-scoped alias can, and disappears afterward, which is what makes
  it safe to be meaningless.

**R130 IS WHAT MADE THIS LOAD-BEARING RATHER THAN OPTIONAL.** Before it, LOAD
emptied the session, so one name meant one table by construction. Now two areas
in ONE workspace can answer to one name -- measured 2026-08-27,
`ws 3 area 10, ws 3 area 22`. That collision is **AIF-140**.

## 6. THE REAL TWO-NAMESPACE PROBLEM IS MIXED FLAVOURS, AND R128 PUT IT THERE

A classic or VFP table has no `X64M` block, so `setFieldName` never fires and
its `FieldDef.name` stays the truncated descriptor. **R128 explicitly permits
mixed flavours in one workspace** -- *"mixed flavors AND mixed index types are
allowed to coexist"*, and the LOAD path repeats it at `cmd_workspace.cpp:2500`
as the property that makes per-table index choice possible.

So one relational expression can span an x64 table answering to
`CUSTOMER_ACCOUNT_ID` and a classic table answering to `CUSTOMER_A`. **That is
the genuine two-namespace case. It is a flavour problem, not an x64 problem,
and it is the one worth designing for.**

**A RECORDED EXPLANATION THAT CANNOT BE RIGHT AS WRITTEN.** The CASCADE_ERP
relation header and the CASCADE_ENV registration both say *"REL resolves x64
LONG names, CDX resolves descriptors"* and report *"22 truncated names rejected,
36 short names landed"* on 2026-08-10. Sec 2 measured the resolution path and
it is single-namespace. Those two texts are **one prose source cited twice**,
not two measurements. **The 22/58 figure is NOT re-measured here and should not
be built on until it is** -- the likely reading is an AUTHORING problem, a
generator that emitted descriptor tokens into the relation file, rather than a
runtime namespace split. Stated as a doubt, not replaced with a new claim.

## 7. WHAT R130 ALREADY ANSWERED THAT GENERALISES

R130 ruled that a posture's `AREA <n>` is a KEY, resolved to a slot at load
time through a map, because an address recorded in a file cannot survive into a
session that allocates.

**A RELATION HAS THE IDENTICAL QUESTION ABOUT NAMES.** Today the store holds a
name and resolves it LATE, on every refresh -- which is how AIF-137 happened,
and how `ws 3 area 10, ws 3 area 22` happened. Bind at declaration to a handle
and it never drifts; but handles are session-scoped, so a saved relation cannot
carry one.

**Which is the same problem R130 just solved, one layer over: store a KEY,
resolve to a HANDLE at load, keep the MAP.** Whether the relation store should
adopt that shape is the sharpest open question this note produces.

## 8. HOW TRANSPARENT CAN THIS BE

- **Live resolution: fully transparent.** Resolve name to handle once where the
  user typed it, bind to the handle after. No grammar change. **But not free:**
  R129 measured 36 call sites on `find_open_area_by_name_ci`, **21 of them
  depending on first-match-wins**, so this changes what 21 sites silently get.
- **Save and load: transparent to the user, real work in the loader.** A map,
  per sec 7.
- **Classic and VFP: NOT transparent, ever.** The long name was never stored.
- **Ambiguous intent: not a transparency problem at all.** If LOAD auto-renamed
  like USE does, `WORKSPACE_LOADSHORT`'s `L_T3` would still read the wrong
  table -- it would merely have a clearer name available for the right one.
  **Two tables legitimately answer to TEACHERS; no naming scheme supplies
  intent.** Name-addressed specs need editing one at a time.

## 9. OPEN QUESTIONS THIS NOTE POSES AND DOES NOT ANSWER

1. **Does an alias share the logical-name namespace, or get its own?** SQL
   correlation names SHADOW within a scope. Sharing is simpler; shadowing is
   what the algebra actually wants.
2. **Alias lifetime: per-open (today) or per-expression (SQL)?** Sec 5.
3. **Does a relation store a name, or a key plus a load-time map?** Sec 7.
4. **Mixed-flavour expressions: refuse, translate, or require qualification?**
   Sec 6. P6's `SALES:STUDENTS.FNAME` qualified form is the obvious hook.
5. **Should `FieldDef` record which tier its name came from?** Raised by
   **AIF-141**, claimed alongside this note.

## 10. CORRECTIONS TO THE TREE, RECORDED NOT MADE

- **`_db_name`'s retirement note is now false.** `xbase.hpp:564` justifies the
  removal on the grounds that *"the table-name-vs-alias split they were shaped
  for ... is done by `_ws_handle`/`_engine_slot` plus the one real name,
  `_logical_name`."* Today's transcript disproves it: `_ws_handle` was EQUAL on
  both colliding areas. The reasoning was sound when written on 2026-08-22 and
  R130 invalidated it on 2026-08-27. **Not edited** -- correcting a comment
  inside a change set that does not otherwise touch its file is how a change
  set stops being reviewable (the AIF-139 precedent).
- **`include/xbase_64_phase1_contract.txt:150-151`** states the name ceilings
  as 128/64; the live constants come from build vectors and this build reports
  `256/256`. Named in **AIF-141**.

**GOOD NEIGHBOR**

- **What changed:** nothing in the tree. This is a design note.
- **Whose area:** AIF-078, and it touches `src/cli/cmd_use.cpp`,
  `src/cli/cmd_workspace.cpp`, `src/cli/set_relations.cpp` and
  `include/xbase.hpp` IF AND WHEN any of sec 9 is ruled. None is modified.
- **What authorization:** the owner asked the design question and asked for the
  answer written up.
- **How to verify:** sec 2 is four line citations and each is a two-line read.
- **How to undo:** delete this file.
