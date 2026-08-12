# RAM / MINIDB / memo workspaces -- operations manual (V1)

    owner of record : member.derald
    author          : member.ai.claude.cowork
    status          : candidate (dev-only), review-needed
    lane            : AIF-070 (coworker)
    audience        : the operator driving the CLI
    grounded in     : src/cli/cmd_workspace.cpp, src/cli/cmd_vdisk.cpp,
                      dottalkpp/data/scripts/{mem,x64}.dts, read 2026-08-12
    doctrine source : MEMO_RESIDENT_MINIDB_V1.md (mechanism, residence, lanes)

This is the how-to-drive-it companion to `MEMO_RESIDENT_MINIDB_V1.md`, which
explains what the mechanism IS. Read that one for design and rationale; read
this one when you are sitting at the prompt.

Every command grammar below was read out of the parser, not recalled. Where a
refusal is quoted it is the literal string the engine emits.

---

## 1. The one-paragraph model

A **workspace** is a set of open work areas plus their index bindings, relations
and cursor state. Saving it normally records a *posture* -- a text description
of that layout, pointing at tables that stay on disk. A **MINIDB** save is
different in kind: the container carries **the table bytes themselves**, so the
payload IS the database. That container lives in a **memo** (the WORKSPACES DTX
sidecar), registered by a row in `WORKSPACES.dbf`. Loading it **hydrates** those
bytes into the **RAM VFS**, where the tables are live and no disk file backs
them. **WRITEBACK** is the return leg: it lands the working set back onto real
disk.

    disk  --SAVE MEMO MINIDB-->  memo  --LOAD MEMO RAM-->  RAM  --WRITEBACK-->  disk

The memo is durable. The hydrated instance is ephemeral and dies at
`VDISK UNMOUNT`, by design. **The gap between those two facts is the entire
reason WRITEBACK exists.**

---

## 2. The four verbs, with their real grammar

### 2.1 VDISK -- the RAM disk itself

    VDISK MOUNT | ON          mount the in-process RAM VFS
    VDISK UNMOUNT | OFF       unmount, dropping every resident file
    VDISK CLEAR               drop resident files
    VDISK STATUS              root, mount state, byte use, resident file list
    VDISK CONFIG
    VDISK USAGE

`MOUNT` repoints the **DBF, INDEXES and LMDB path slots** under the relocatable
RAM slot and mounts that root. Default RAM root is `<DATA>/ram`; relocate it
BEFORE mounting with `SET PATH RAM <path>`.

The house shorthand is a flavor script:

    DO mem      -- one line: VDISK MOUNT
    DO x64      -- SET PATH {DBF,INDEXES,LMDB} back to the on-disk x64 roots

`DO x64` is how you leave RAM and return to disk.

### 2.1a The path model, and the idiom that follows from it

**DATA is the root.** A relative token is DATA-relative, an absolute one is
taken as given:

    SET PATH DBF D:\code\ccode\dottalkpp\data\x64      absolute
    SET PATH DBF x64                                   DATA-relative -- same place

The sanctioned way to open a schema is therefore **point the slot, then scan
it**:

    SET PATH DBF x64
    WORKSPACE OPEN DBF          opens the x64 schema from the configured slot

`WORKSPACE OPEN DBF` means "the DBF slot", not a directory named DBF. This is
the main road, and it is unaffected by anything in section 6.

**Secondary form, with a caveat.** `WORKSPACE OPEN <dir>` takes a directory
directly. Measured 2026-08-12: it resolves **CWD-relative**, not through the
slot -- so `WORKSPACE OPEN DBF/x64` (the DATA-relative spelling) opens NOTHING
and says so only by omission, while the same directory named absolutely, or
CWD-relatively, opens 15 tables. The runtime usage text already promises
"Relative targets resolve from SETPATH/INIT slots, primarily DBF", so the
promise and the behaviour disagree. This is a **pre-existing** sibling of the
defect in section 6, in a fourth surface, and it fails silently. It is NOT
fixed by the 2026-08-12 slice and is flagged for a number of its own. Bare
stems (`WORKSPACE OPEN students`) do go through the slot and are fine.

### 2.1b Probing: functions are SCALAR COMMANDS, no parens

Read this before writing a script to answer a question. Any function in the
catalog is callable directly as a command -- **bare name, comma-separated
arguments, NO parentheses** -- and it prints its value:

    DATE                              -> 20260812
    LEFT "hello", 2                   -> he
    UPPER "hello"                     -> HELLO
    LEN "hello"                       -> 5
    SUBSTR "abcdef", 2, 3             -> bcd
    DATEDIFF 20260812, 20260801       -> -11
    SOUNDEX "Anderson"                -> A536
    FILE "DBF/x64/STUDENTS.dbf"       -> .T.
    RECNO                             -> 42     (with a table open)

This is the fastest way to check a resolution, a value, or whether a function
exists. Authoring a whole `.dts` to answer "does this path resolve" is the
long way round.

**What is NOT here.** `RECCOUNT`, `ALIAS` and `DELETED` return
`Unknown command` -- they are neither commands nor catalog functions. Area and
record reflection is reported by the COMMANDS `AREA`, `DBAREA`, `DBAREAS`
[`ALL`], `WORKSPACE`, `DISPLAY` and `RECNO`, not by functions you can embed in
an expression. That boundary is why every regression marker in this subsystem
asserts a FIELD VALUE rather than interrogating session state.

**Listing: use SMARTLIST, not LIST.** `LIST` is a developer command with a
MANUAL cursor -- its own contract says `mutates_cursor: temporary during scan`
/ `cursor_restore: best effort`, and its footer reports the SCAN position, not
where the session is. `SMARTLIST` is the cursor-controlled one: order-aware,
projections, `FOR <pred>`, `FIRST n` / `NEXT n`, `ALL`, `DELETED`, `TUPLES`,
and a `RECNO` column per row.

    SMARTLIST LNAME,FNAME FIRST 3
    SMARTLIST SID,LNAME,GPA FOR GPA >= 3.9

Measured gap worth knowing: `RECNO` resolves as a PROJECTION but not as a
PREDICATE identifier, and the mismatch is silent -- `SMARTLIST ... FOR GPA >=
3.98` returns 2 records while `SMARTLIST ... FOR RECNO > 195` returns 0 with
no error.

Operator vocabulary, which differs by evaluator: the `?` / FORMULA path takes
BARE `AND` / `OR` / `NOT` and REJECTS the dotted xBase forms `.AND.` / `.OR.` /
`.NOT.` with `FORMULA error: scalar evaluation failed`.

### 2.2 WORKSPACE SAVE -- posture, or the database itself

    WORKSPACE SAVE <file>                     posture to a file (default)
    WORKSPACE SAVE <name> MEMO                posture into the memo catalog
    WORKSPACE SAVE <name> MEMO V3             ... as a self-locating v3 posture
    WORKSPACE SAVE <name> MEMO MINIDB         THE CONTAINER: posture + table bytes

Trailing keywords, **any order**. `MINIDB` implies `V3`, because the embedded
posture must be self-locating to survive being re-pointed at RAM on load.

What `MINIDB` gathers: every **OPEN** area's table file, plus its index file
when an order is attached. Reads are residence-aware -- a source living in the
RAM VFS is read through `xbase::ramfs`, not the OS -- so **a RAM-resident
working set can be saved whole.**

`MINIDB` without `MEMO` is refused: `WORKSPACE SAVE: MINIDB is a memo carrier
(WORKSPACE SAVE <name> MEMO MINIDB).`

### 2.3 WORKSPACE LOAD -- and why RAM is not optional for a container

    WORKSPACE LOAD <file>                     posture from a file
    WORKSPACE LOAD <name> MEMO                posture from the catalog
    WORKSPACE LOAD <name> MEMO RAM            hydrate a MINIDB container into RAM

Keywords in either order. `RAM` without `MEMO` is refused (`RAM hydration is
memo-carrier only today`).

**Load a MINIDB payload without `RAM` and the engine refuses on purpose.** Its
tables have no disk home to open; standing up empty areas over missing files is
precisely the silent-success failure this codebase exists to hunt. The refusal
tells you the hydration instruction instead.

`VDISK` must already be mounted: `WORKSPACE LOAD RAM: VDISK is not mounted --
run VDISK MOUNT`.

### 2.4 WORKSPACE WRITEBACK -- the return leg

    WORKSPACE WRITEBACK [<name>] [TO <root>] [WITH INDEXES] [CONFIRM]

- **`<name>` is required.** The source comment above the dispatcher spells the
  grammar `[<name>] [TO <root>]`, which reads as though the name were optional.
  It is not: the `TO` parse looks for a `" to "` with a token before it, so a
  leading `TO <root>` is swallowed whole as the NAME and the verb fails looking
  for a catalog row called `TO DBF/...`. Measured by running it, 2026-08-12 --
  the first draft of this document repeated the comment's claim and was wrong.
- `TO <root>` defaults to the catalog row's `DBF_ROOT` -- where the workspace
  came from.
- **`CONFIRM` is required to replace existing files.** Without it you get a
  listing of what WOULD be replaced and nothing is written.
- `WITH INDEXES` additionally copies index container bytes (see 5.3 for exactly
  what that does and does not promise).
- Replaced files are preserved as `<name>.__wbak` beside the new ones.

**Path resolution (corrected 2026-08-12).** `TO <root>` resolves through the
engine's standard rule: absolute stays absolute, a token containing separators
is **DATA-root-relative**, a bare name sits in the DBF slot. This is the same
rule `SET PATH`, `ERASE DIR` and `FILE()` use. Before the fix these disagreed --
WRITEBACK followed the process CWD while SET PATH followed DATA -- and the
regression guarding the verb wrote to one directory while asserting against
another. See section 6.

---

## 3. The workflows

### 3.1 Capture a disk database into a portable container

    DO x64                                  point the slots at disk
    WORKSPACE OPEN DBF                      open the tables you want carried
    WORKSPACE SAVE mydb MEMO MINIDB         container into the memo

The catalog row now registers it: `FMT = MINIDB 1`, `SIZE_B`, dims, lineage.
**The row IS the registration** -- nothing about the payload is knowable only
by parsing it.

### 3.2 Hydrate and work entirely in RAM

    DO mem                                  VDISK MOUNT
    WORKSPACE LOAD mydb MEMO RAM            zero disk reads; tables live in RAM
    ... USE / SET ORDER / REPLACE / query freely ...

Orders attach in RAM through the native CDX fallback. Everything here is
ephemeral.

### 3.3 Land the working set back on disk

    WORKSPACE WRITEBACK mydb TO DBF/target CONFIRM
    WORKSPACE CLOSE
    VDISK UNMOUNT

Drop `CONFIRM` first if you want to see what would be replaced. Drop `TO` to
write back where it came from.

### 3.4 Save the RAM state back into the memo instead of to disk

    WORKSPACE SAVE mydb MEMO MINIDB          from RAM, residence-aware reads

This is the owner's "save the state in the memo when we close", made literal.
The gather reads through the VFS, so a RAM-only working set round-trips into a
new container without ever touching disk. Supersedes the prior live row of that
name; `PREV_ID` keeps the lineage.

### 3.5 Move a database between machines

The container carries **relative paths only** (`basename`, `indexes/basename`)
and a self-locating posture. It is portable by construction: hydrate it
anywhere, write it back anywhere. Nothing machine-specific rides along.

### 3.6 Mirror the indexes too

    WORKSPACE WRITEBACK mydb TO DBF/target WITH INDEXES CONFIRM
    SET PATH DBF     DBF/target
    SET PATH INDEXES DBF/target/indexes
    SET PATH LMDB    DBF/target/lmdb
    USE STUDENTS
    BUILDLMDB                                REQUIRED -- see 5.3
    SET ORDER TO TAG <tag>

---

## 4. Refusals, and what each one is telling you

A refusal here is a feature. This subsystem's design position is that a partial
result which looks finished is worse than a loud stop.

| Refusal | Meaning | What to do |
|---|---|---|
| `ABORTED -- the posture declares N table(s); M are not open` | Enumeration authority: the **posture** is the manifest, not your session's attach state. You have fewer areas open than the workspace declares. | Open the full set, or write back a workspace whose posture matches what you have. |
| `N existing file(s) would be REPLACED at <root>` + `Nothing written. Re-run with CONFIRM` | Collision guard. Nothing was written. | Re-run with `CONFIRM` once you have read the list. |
| `ABORTED -- cannot read <file>` | Gather-all-before-writing. A source failed to read, so **nothing** was written. | Fix the source. The disk side never holds a partial workspace. |
| `refusing -- target resolves <inside the mounted RAM root>` | Writing RAM to RAM is a mistake, not a no-op. | Point `TO` at a real disk root. |
| `no open areas -- nothing to write` | Nothing is loaded. | Load or hydrate first. |
| `'<name>' is a MINIDB payload` (on plain `LOAD ... MEMO`) | The container has no disk home to open. | Use `WORKSPACE LOAD <name> MEMO RAM`. |
| `RAM hydration is memo-carrier only today` | You passed `RAM` without `MEMO`. | Add `MEMO`. |
| `VDISK is not mounted -- run VDISK MOUNT` | No RAM VFS to hydrate into. | `DO mem`. |
| `MINIDB is a memo carrier` | You passed `MINIDB` without `MEMO`. | Add `MEMO`. |
| `no live memo workspace named '<name>'` | No unsuperseded row by that name. | Check the catalog. |
| `MINIDB: unrecognized container header` / `truncated posture` / `bad FILE section` / `container carried no posture` | The payload is not a well-formed `MINIDB 1` container. | Integrity problem; do not retry blindly. |

**An abort leaves the filesystem untouched, including empty directories.** The
first cut created target dirs before the manifest check while printing "Nothing
was written"; that was fixed, and the regression's WB_T6 arm exists to keep it
fixed.

---

## 5. Limits -- stated, not implied

### 5.1 No LMDB carriage
Out of scope by the ramfs contract (LMDB must mmap a real OS file) and by owner
rule: **lmdb only for disks**. CDX orders attach in RAM through the native
fallback; the LMDB route fails there correctly and loudly.

### 5.2 No multi-file atomicity on hydration
The container is written in one memo put and verified as one unit -- atomic at
the carrier level -- but hydration writes N RAM files sequentially. A
mid-hydration failure leaves a partial RAM set. Acceptable because the RAM set
is disposable by definition. **WRITEBACK answers its own half**: gather-all
-before-writing means a read failure aborts having written nothing.

### 5.3 WITH INDEXES ships bytes, not a ready index
The landed `.cdx` is a **byte-mirror**. LMDB environments are not carried, so
the destination needs `BUILDLMDB` before `SET ORDER TO TAG` will work. That is
the entire promise the flag makes. (Regression arms WB_T10/WB_T11 assert exactly
this and nothing more.)

Note also: `WITH INDEXES` was **inert** until 2026-08-12. The posture parse
counted `index=` selections and discarded the names, so the gather had nothing
to enumerate and fell back on session attach state, landing zero containers. It
is now posture-driven.

### 5.4 A hydrated memo sidecar is disk-resident
Unavoidable until ramfs memo-store coverage lands. It survives unmount as
residue, truncate-overwritten by the next hydration of the same name.

### 5.5 No size governance, and supersede does not reclaim
`SIZE_B` records what a container weighs; nothing refuses a save that would
dwarf the sidecar or the RAM budget. **Supersede does not erase the old token's
bytes** -- ten saves of a 94 KB container retain roughly 1 MB in the sidecar.
`MemoStore::erase` exists and is zoo-proven; a compaction policy is a chartered
decision, not an oversight. History-keeping versus space is the owner's call.

### 5.6 PAYLOAD_SHA is chartered, not live
The oracle verifies at save time. Nothing re-verifies a container years later.
`VERIFIED_AT` waits on `WORKSPACE VERIFY`.

---

## 6. The lesson this subsystem paid for twice

**Enumeration authority.** The first writeback cut asked the *session* what to
write and silently wrote 15 of 27 files while reporting cheerful success. The
manifest is the **posture's AREA lines** -- the record of what the workspace IS
-- never the session's attach order. The same order-dependent enumeration is why
a posture once omitted `students.cdx`. A count is a fact about a loop until
something declares what the count SHOULD be.

**A guard that shares its subject's bug agrees instead of failing.** The
writeback regression carried an `ERASE DIR` pre-clean specifically to stop stale
false greens. It ran. It reported success. It cleaned the CWD-relative directory
while the assertions read the DATA-relative one, because `ERASE DIR`, `FILE()`
and `WRITEBACK TO` all resolved paths the same wrong way -- and `SET PATH` did
not. Six markers reported green off a directory populated by an unrelated
earlier run. Two components agreeing is not evidence that either is right.

Both failures have the same shape, and it is the shape worth carrying out of
this document: **something reported success without doing its job, and the thing
watching it was looking somewhere else.**

---

## 7. Quick reference

    DO mem                                        mount RAM (VDISK MOUNT)
    DO x64                                        slots back to disk
    VDISK STATUS                                  what is resident
    WORKSPACE                                     report open areas
    WORKSPACE OPEN DBF                            open the DBF slot's tables
    WORKSPACE SAVE <n> MEMO MINIDB                capture database into memo
    WORKSPACE LOAD <n> MEMO RAM                   hydrate into RAM
    WORKSPACE WRITEBACK <n> TO <root> CONFIRM     land it on disk
    WORKSPACE WRITEBACK <n> TO <root> WITH INDEXES CONFIRM
    WORKSPACE CLOSE                               close areas, clear relations
    VDISK UNMOUNT                                 drop the RAM set

Regression: `REGRESSION RUN WORKSPACE_WRITEBACK`
Spec: `dottalkpp/data/scripts/workspace_writeback.dts`
