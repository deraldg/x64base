# Handoff -- a Cowork sandbox CAN build and run the engine (2026-08-12)

    status        : measured, single session
    agent         : member.ai.claude.cowork
    lane          : AIF-070 contribution; the FINDING wants its own AIF (unclaimed)
    aimed at      : the next Cowork/sandbox agent, before it accepts a build handoff
    onboarded_utc : 2026-08-12T17:40:00Z
    seed_commit   : d08a09c5680f242abf909be0200784af1255a413

**Start at `AI_README.md`, then `AI_PORTAL.md`. If you have not onboarded this
session, do that BEFORE the work below.** This file is a trap-and-recipe note,
not an entry point. Compare `seed_commit` above against
`git log -1 --format=%H -- labtalk/ai_portal/AI_TIER1_SEED_V1.md`; if it moved,
your onboarding is stale even if it feels fresh. (Rule: `AI_PORTAL.md`, "The
onboarding instruction is the FIRST line, and onboarding expires".)

## The correction

`AI_README.md`, "A sandbox is not the WSL host", concludes:

> The practical ceiling in such a sandbox is per-translation-unit
> `g++ -fsyntax-only`. Builds and runs are therefore maintainer-operated
> handoffs.

**Measured false, 2026-08-12.** A full `dottalkpp` was built inside the Cowork
sandbox and used to run `REGRESSION RUN WORKSPACE_WRITEBACK` against the live
`dottalkpp/` data root, WB_T1..WB_T6 green, twice.

Be precise about what is and is not corrected:

- **Still true:** the *staged* `dottalkpp/bin-wsl-lean/` ELF is built against
  the WSL host's newer glibc/GLIBCXX and is not expected to execute here. That
  row of the table stands. It was not re-tested this session.
- **False:** "cannot build", and the `-fsyntax-only` ceiling drawn from it. The
  sandbox lacks a toolchain *by default*; it is not prevented from having one.
- **Consequence:** a sandbox agent can close its own proof loop instead of
  handing every build to the maintainer. That changes the cost model for every
  Cowork session, which is why this is in the tree and not in a chat.

`CLAUDE.md` already says *"Assume you cannot build or run the engine, and
verify rather than trust this line."* This is that verification coming back.
Both files should be corrected under the AIF this finding is given.

## Measure, do not trust this file either

Everything below is perishable. Check it:

```bash
command -v cmake ninja g++     # toolchain present?
ldd --version | head -1        # glibc of THIS sandbox
```

## Recipe

Five steps, four of them non-obvious. Roughly 12 minutes of wall clock, most of
it the 510-target compile.

**1. Get cmake + ninja.** No root, no apt. pip carries both:

```bash
pip install cmake ninja --break-system-packages
export PATH=$PATH:$HOME/.local/bin
```

**2. Build OFF the mount.** Copy the sources to local disk
(`src include config tools CMakeLists.txt CMakePresets.json vcpkg.json` and the
`AddPydotTalkIfPresent.cmake` shim). The mount is slow enough to dominate the
build, and two configure-time checks below need a tree you can freely `git init`.
Copy `dottalkpp/bin` + `dottalkpp/data/scripts` too -- the product manifest
insists they exist. Do NOT copy `dottalkpp/` wholesale; it is tens of GB.

**3. Reuse the repo's own dependency tree.** Do not fetch vcpkg. The tree
already carries a populated one:

```
build-wsl-lean/vcpkg_installed/x64-linux
```

It must sit at `<somewhere>/vcpkg_installed/x64-linux`, and you must pass BOTH
`-D_VCPKG_INSTALLED_DIR=<somewhere>/vcpkg_installed` and
`-DVCPKG_TARGET_TRIPLET=x64-linux`. **Trap:** the vcpkg-generated
`unofficial-sodiumConfig.cmake` interpolates exactly those two variables into
its include path. Point `CMAKE_PREFIX_PATH` at the tree without setting them and
CMake fails with `includes non-existent path "//include"` -- a doubled slash
where the two empty variables were. The message names sodium; the cause is the
variables, not sodium.

**4. `git init` the copy.** `tools/packaging/build_product_inventory.py` shells
out to `git -C <root> ls-files` at CONFIGURE time. Outside a repo it raises
`CalledProcessError` and the configure dies with a message about the packaging
script, not about git. `git init && git add -A && git commit` in the throwaway
copy. (This is a copy on local disk, NOT the mounted tree -- do not run these
against `/sessions/.../ccode`.)

**5. Swap three static libs.** This is the real blocker. The vcpkg `.a` files
were built against a newer glibc and reference `__isoc23_strtol`, which this
sandbox's glibc does not export, so the link fails on `mdb.c` with dozens of
undefined references. Take the distro's own:

```bash
cd /tmp && apt-get download liblmdb-dev libsodium-dev libsqlite3-dev
for d in *.deb; do dpkg -x "$d" sysdebs; done
cp sysdebs/usr/lib/x86_64-linux-gnu/{liblmdb,libsodium,libsqlite3}.a \
   <somewhere>/vcpkg_installed/x64-linux/lib/
```

`apt-get download` needs no root. `apt-get install` does; do not try.

Then configure with the wsl-lean cache values (`DOTTALK_INDEX_MODE=LMDB`,
`PRODUCT=DEVELOPMENT`, `PROFILE=DEV`, TV/GUI/WX/pydottalk/metacollect OFF,
`BUILD_TESTING=OFF`) and `ninja dottalkpp`.

**Budget the compile.** ~510 targets. If your shell caps tool calls at ~3
minutes, a foreground `ninja` will be killed mid-build; re-invoking it simply
resumes, so call it repeatedly rather than trying to background it.

## Running it

The binary finds its data root by walking up from **its own location first**,
then the cwd (`src/cli/cmd_init.cpp:140`). A binary sitting in `/tmp` will not
find the mounted data, so `cd` to the data root and let the cwd search win:

```bash
cd <mount>/ccode/dottalkpp
printf 'REGRESSION RUN <NAME>\nQUIT\n' | /tmp/.../build/src/dottalkpp
```

**Trap:** `cd dottalkpp/data` resolves DATA to `dottalkpp/data/data` and the
script is not found. Run from `dottalkpp/`, not `dottalkpp/data/`.

Capture with `SET ALTERNATE`, never `DOTSCRIPT ... OUT` -- see `AI_README.md`.

## What this does not license

- **Still no git mutation from the sandbox.** Unchanged, and it is the rule this
  session broke. Read-only (`git --no-optional-locks status`, `log`, `ls-files`)
  only; every add/commit/push goes to the maintainer.
- **Still not the WSL host.** A green here is a green on Ubuntu 22.04 with
  distro lmdb/sodium/sqlite, not on the maintainer's toolchain. Say which one
  you measured on. This session's proof reads "Linux build, g++ 11" for that
  reason.
- **Carry the platform precondition INTO the handoff, not just the record.**
  This bit immediately. The session proved six markers on its Linux build,
  said so honestly in the closeout, and handed over a re-run -- and the
  maintainer's Windows exe predated the new builtin by 44 minutes, so two
  markers emitted `FORMULA error: scalar evaluation failed` instead of `.T.`
  and the lane looked red. If your change adds a command or an expression
  builtin, the OTHER platform's binary is stale by definition and the handoff
  must say "rebuild first" in the same breath as "re-run this".
  Cheap decisive check, no rebuild needed -- grep the binary for a string only
  your change introduces (a `FunctionDoc` summary works; a comment does not):

  ```bash
  grep -c "Return whether a file or directory exists" dottalkpp/bin/dottalkpp.exe
  ```

  Zero means the binary predates you, whatever its build stamp claims. This is
  `AI_README.md`'s "`no work to do` is not proof your change is in the binary",
  and it applies across platforms, not just across incremental builds.
- **`git status` here HIDES untracked files.** This tree sets
  `status.showUntrackedFiles = no`, so `git status --short` shows only tracked
  modifications -- new files you just authored are simply absent, and so is any
  evidence of whether they are ignored. Verify new work with
  `git --no-optional-locks status --porcelain -uall -- <paths>`: `??` means
  untracked-and-committable, absent means `.gitignore` swallowed it. The house
  rule "status between add and commit" still works for STAGED paths (they show
  `A`/`M` in column 1); it just cannot tell you anything about untracked ones.
  Costs one flag, and its absence produced two wrong readings in one session.
- **Write handoff commands in the operator's shell, not yours.** The same
  session handed a PowerShell prompt a bash `\` line continuation; git answered
  `fatal: \: '\' is outside repository` and staged nothing, which is only
  visible if you read the ` M` column. Single line, and `git -C <tree>` /
  `Push-Location <tree>; ...; Pop-Location` so the command does not assume a
  location (owner rule, 2026-08-11).
- **Deletion may be blocked.** `rm` can return `Operation not permitted` on the
  mount until the host grants it; a regression that erases its own fixtures will
  fail teardown and, worse, may read the previous run's files on the next run.
  Verify teardown actually deleted rather than trusting the exit code.
