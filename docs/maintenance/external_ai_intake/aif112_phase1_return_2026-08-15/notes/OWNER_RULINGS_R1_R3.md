# Owner Rulings R1-R3 -- AIF-112 Phase-1

**Status: SIGNED 2026-08-15.** All three ruled by the owner in-session, as
recommended. The scribe's recommendations below are preserved as written so the
reasoning that was signed is visible, not just the outcome.

**Owner:** `member.derald`. **Drafted by:** `member.ai.claude.cowork`.
**Evidence baseline:** runtime `fe42666e`, tree `b8dc1e6fe`.

---

## R1. Attribution -- string stamp or `N(20)` FK

**Asked by:** the steward, who recommended a string stamp for Phase 1.
**Answered by default in the exercise:** string stamp was used.

### What the exercise measured

All **106** `WORKSPACES` rows carry `member#4/kind0` -- a string stamp produced
by `author_stamp()` in `cmd_workspace.cpp`, not a foreign key. Not one row uses
an FK. The steward's recommendation matches house practice against live data,
which was not confirmable when he made it.

### The trade-off, stated as what an audit trail is for

This is not integrity versus convenience.

**An FK follows a rename.** If `member.derald` were ever renamed, every
historical check-out row joined through an FK would retroactively report that
the *new* name checked those documents out. The ledger would be internally
consistent and historically false.

**A stamp records what was true when it was written.** For document control
specifically -- a system whose entire output is "who held what, when" --
immutability is the property being sold.

**The cost is real:** no join to `SYSMEMBER`, so "every check-out by anyone
currently holding role X" is not a query the ledger can answer alone.

### Options

1. **String stamp only.** Immutable history. No live join.
2. **`N(20)` FK only.** Joinable, referentially checked, and rewrites history on
   rename. Also requires the member row to survive forever or the FK dangles.
3. **Both.** FK for the live relation, denormalized stamp for history. The
   standard audit pattern in any system that has had this argument before.

### Recommendation

**Option 1 for Phase 1, with option 3 available in Phase 2 at no cost.** Adding
an FK column later is additive; removing a stamp later is not. Committing to the
stamp now forecloses nothing.

> **OWNER RULING R1 -- ACCEPTED AS RECOMMENDED.**
> Attribution is a **string stamp** for Phase 1, matching `WORKSPACES`. An
> `N(20)` FK may be added alongside it in Phase 2 if the live join is wanted;
> the stamp is not replaced by it. History stays immutable.
>
> Signed: **member.derald**  Date: **2026-08-15**

---

## R2. Is the ledger excluded from Git? (the steward's Q8)

**Asked by:** the steward, as Q8. **Never ruled.**

### What today demonstrated, without anyone intending to test it

`dottalkpp/data/help/*.dbf` and `*.dbt` **are** tracked. Nine of them appeared as
modified in **every single** `git status --short` run during this session --
roughly a dozen invocations, every one of them carrying the same nine files of
permanent noise inside a fifty-file dirty tree.

That is not an aesthetic complaint. This repository's commit safety depends on
the maintainer reading the first column of `git status --short` correctly before
every commit, because concurrent sessions share one working tree and the house
rule is scoped per-path slices, never `git add -A`. **Tracked runtime DBFs
actively degrade the one check that makes that rule work.** We watched it happen
all day.

### The mechanical case

- **Binary.** No meaningful diff. A reviewer cannot see what changed.
- **Constantly rewritten.** Every check-out mutates the file.
- **Unmergeable.** Two sessions checking out different documents produce a
  conflict Git cannot resolve and a human cannot resolve by hand either.
- **Growth.** A ledger that supersedes rather than overwrites only ever grows,
  and every version of it would be stored forever.

### The counter-argument, stated fairly

Untracked state can be lost, and a document-control ledger that vanishes with a
disk is a poor document-control ledger. Durability is a real requirement.

**But Git is the wrong instrument for it.** The answer to durability is a
periodic export to a text form that diffs and merges -- which is *also* what
makes the ledger auditable outside the engine, reviewable in a pull request, and
readable by a steward who cannot run the runtime. One mechanism, two problems.

### Recommendation

**Exclude the ledger DBFs from Git. Add a text export as the durable, reviewable
artifact.** Note that `data/dbf/sandbox/**` already sits outside the promotion
manifest, so the spike tables are correctly placed today -- by accident, not by
decision. Make it a decision.

> **OWNER RULING R2 -- ACCEPTED AS RECOMMENDED.**
> The inventory ledger DBFs are **private runtime state and excluded from
> version control**. Durability and reviewability are served by a **periodic
> text export**, which is the artifact that diffs, merges, survives review, and
> can be read by an agent that cannot run the runtime. This closes Q8 on the
> Agent Sync page.
>
> Signed: **member.derald**  Date: **2026-08-15**

---

## R3. `inv.break` -- maintainer-only?

**Asked by:** nobody. **The steward's PDLC map omits this item entirely**, which
is why it is here. It was raised during the owner's review of that map and never
carried forward.

### What the exercise measured

**No `inv.*` permission exists.** The 19 permissions are **compiled** into
`src/identity/identity_bootstrap.cpp` with literal ids 1-19 plus `grant_role`
lists -- they are not seeded data. Adding any `inv.*` permission is a code
change, which is a Phase-2 cost the schema sketch did not price.

**Phase 1 needed none.** `database.mutate` (id 5, `RiskClass::Medium`, approval
**not** required) already covers register, check-out and release, and is granted
to MAINTAINER and DEVELOPER.

So the only inventory operation that warrants its own permission is the
break-glass override.

### The house already has this exact shape, and enforces it

`host.shell` is `RiskClass::Critical` with approval required -- and it is not
merely declared. `src/cli/cmd_bang.cpp:104` checks it:

> `host.shell. The owner is exempt; a non-owner agent needs a live grant.`

with a separate environment gate (`DOTTALK_ALLOW_HOST_COMMANDS`) for the
interactive form. `cmd_sftp.cpp:514` uses the same check. This was verified
during the exercise specifically because the scribe suspected it might be an
AIF-114-style declared-but-unenforced permission. **It is not.** The codebase
enforces what it publishes here.

The two Critical peers are `role.assign` (12) and `authorization.grant` (13) --
both Critical, both approval-required. That is the company `inv.break` belongs
in.

### Recommendation

**`inv.break` = `RiskClass::Critical`, approval required, owner exempt, checked
at the call site on the `cmd_bang.cpp:104` model.**

And decide it once for two consumers: **AIF-113's FORCE verb is the same shape**
-- a break-glass override on a subsystem where the normal path has failed. If
`inv.break` and `FORCE UNLOCK` are ruled together, they can share one pattern
instead of diverging into two.

> **OWNER RULING R3 -- ACCEPTED AS RECOMMENDED.**
> `inv.break` is **`RiskClass::Critical`, approval required, owner exempt**,
> checked at the call site on the `cmd_bang.cpp` model. Ordinary ledger writes
> stay on `database.mutate` and need no new permission. **AIF-113's FORCE verb
> is ruled the same way by the same reasoning** -- one break-glass pattern, two
> consumers, decided once.
>
> Signed: **member.derald**  Date: **2026-08-15**

---

## Carried out on signature, 2026-08-15

1. **Done** -- rulings recorded above.
2. **Done** -- `AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md` section 4
   updated; R1 no longer reads as a scribe default.
3. **Done** -- Agent Sync Q8 closed by R2.
4. **Done** -- R3 is now a stated input to AIF-113's design options rather than
   a decision made later under time pressure. AIF-113's charter lists a
   permission-gated FORCE verb as option 2; that option now has its permission
   shape fixed before the work starts.

## Consequences worth stating

**R1** forecloses nothing. The FK remains addable and the stamp remains
authoritative for history.

**R2 creates one piece of owed work that did not exist before signature:** the
text export. Excluding the ledger from Git without building the export trades a
noisy repository for an undurable ledger, which is a worse position than either.
The export is the ruling, not an optional companion to it.

**R3 is the first decision this lane has made BEFORE the code that needs it.**
Every other permission question in the exercise was answered by measuring what
already existed. This one sets a shape for two consumers in advance -- which is
the PDLC working as intended rather than as archaeology.
