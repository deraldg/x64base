# Handoff -- Cowork: git, the mount, and measuring your own claims

**ONBOARD FIRST.** Read `CLAUDE.md`, then
`labtalk/ai_portal/AI_TIER1_SEED_V1.md`, answer its five questions, then
`AI_README.md`'s startup table. Do not start from this file. It assumes you are
onboarded and tells you only what that material does not.

    recorded_utc  : 2026-08-26T22:49:54Z
    run           : COWORK-20260826-001
    onboarded_utc : 2026-08-26T21:45:00Z
    seed_commit   : 6c3809eed

Aimed at the next Cowork session working across the mounted tree. Everything
here was paid for once today. Measure your own versions and paths; nothing
below is a perishable literal.

## 1. Commit plainly. A pathspec commit trips the git guard.

`git commit -- <paths>` builds a TEMPORARY INDEX to make a partial tree, and
takes `.git/index.lock` BEFORE the pre-commit hook runs. A plain `git commit`
does not. `tools/staging/check_sandbox_git_guard.py` sees that lock and
`prepush_gate` reports **"a stale .git/index.lock is present"** -- exit 2, every
time, and the message names the wrong cause.

    check_sandbox_git_guard.py  check_lock()  -- `return 2` sits OUTSIDE the
    if/else, so a zero-byte stale lock and a live commit's lock return the same
    code. The prose distinguishes them; the return value does not.

How to tell them apart yourself: a stale lock is ONE unchanging file that is
still there when nothing is running. Two failed attempts here reported lock
sizes that DIFFERED (652,666 then 652,770) and no lock existed between them.

**So: stage exact paths, then commit with no pathspec.** If you need something
out of the commit, unstage it -- do not reach for a pathspec.

## 2. `TIER0_STATE.md` is SUPPOSED to be in your commit.

Both commits printed `tier0-refresh: TIER0_STATE.md regenerated -- rides in
this commit (by design)`. If you find it staged and do not recognise it, that
is the mechanism, not another session leaking in. Do not engineer it out. This
session did, recommended a pathspec to achieve it, and that is what caused
section 1.

The general rule it teaches: **when an unfamiliar file is in a state you did
not put it in, find the producer before inferring intent.**

## 3. Read-only git that WORKS across the mount, and one that does not.

`git --no-optional-locks status --short -uall` is lock-free and permitted
(`CLAUDE.md`, Sandbox agents). It is also **too slow to use here** -- it timed
out at the 45 s device tool ceiling. Use plumbing instead:

    git diff-index --cached --name-status HEAD     what is staged
    git diff-index HEAD --name-only -- <path>      is one file modified
    git ls-files --error-unmatch -- <path>         is one file tracked
    git show :<path> | md5sum                      what is ACTUALLY staged
    git show HEAD:<path> | md5sum                  what actually landed

That last pair is worth the habit: hash the committed blob against the copy you
compiled. It converts "should be identical" into a measurement, and it is two
seconds.

## 4. Move the corpus to the tool; do not run the tool over the mount.

`tools/coordination/next_r.py` scans ten directories. Over the mount it did not
finish in ten minutes. Copied to device-local `/tmp`, filtered to the five
suffixes the tool reads, it ran in **0.5 s** -- and the copy itself took 27 s.

    find <dirs> -type f \( -name '*.md' -o -name '*.py' -o -name '*.cpp' \
        -o -name '*.hpp' -o -name '*.h' \) -print0 | tar --null -T - -cf - \
        | (cd /tmp/scan && tar xf -)

Filter by suffix FIRST. An unfiltered `tar` of `docs/` alone moved 2.5 GB.

Same idea for the whole source tree when you want to build: tar `src include
CMakeLists.txt cmake` on the device, drop it in a mounted folder, stage it into
the container, build there.

## 5. Traps that cost real time

**`pgrep -f <script>` matches the shell running the pgrep.** A background job
was reported STILL_RUNNING for ten minutes while its output file sat at zero
bytes and the process was long dead. Use `pgrep -af` and READ what matched.

**Background processes do not survive a `device_bash` call.** `nohup ... &` then
polling in a later call finds nothing running and no output. Do the work
synchronously in chunks under the timeout.

**`quip read --ack` cannot ack across the mount.** `--ack` DELETES the quip file
and the mount forbids unlink; it reports `acked 0 of 4` honestly. Your inbox
count stays wrong forever. Same defect the 2026-08-19 Session Log row already
recorded for `session_coordinator.py unlock` -- one cause, two verbs.

**Do not grep the dashboard's Session Log into your context.** Individual rows
run to many thousands of words.

## 6. The build works. Use it, and A/B it.

Configure and build in the container; the CLI target takes about a minute
incrementally. Two things this session learned about USING that:

**Build a BASELINE binary from the pre-change source and compare.** Save the
pre-edit file, build, copy the binary aside, restore, rebuild. Then diff the
marker output. `REGRESSION ALL` here reports 24 red arms that are the
container's missing fixtures -- reading them tells you nothing; **byte-identical
to baseline** tells you everything.

**Check your discriminator against the OLD build, not just the new one.** A
spec arm written for the scoped-SAVE fix read GREEN on both binaries, because
the OTHER defect in the same change prevented the state it needed from ever
occurring. One defect can mask another and hand you an arm that proves nothing.

**Measure under the maintainer's profile axes.** `pro-md` is
`DOTTALK_PRODUCT=DEVELOPMENT` + `DOTTALK_INDEX_MODE=LMDB`. A container preset
may be LEAN/NONE, which silently skips whole code paths -- index attachment,
for one. Read the cache, do not assume:

    grep -E '^DOTTALK_PRODUCT:|^DOTTALK_INDEX_MODE:' <build>/CMakeCache.txt

## 7. The one habit

Everything above was found by running something, and most of it refuted
something this session had already written down. Two claims in this file's own
lane were retracted after measurement: an expected allocator divergence that
both allocators actually agreed on, and an expected catalog row per OPEN that
turned out to be one row per NAME. **Measure your own claims with the same
suspicion you bring to the code**, and correct in place rather than quietly
retuning what you said earlier.
