# Python Binding Trust Contract v1

Status: active contract; declares posture, authorizes nothing new.

Kind: bindings | trust boundary | data safety

Evidence class: Source-defined + runtime-proven (locking measured in the engine
write path; authorization measured absent in the binding)

Owner area: bindings, xbase engine, identity, contract lane

Related:

- `bindings/pydottalk/src/module.cpp`
- `bindings/pydottalk/CMakeLists.txt`
- `src/xbase/dbarea.cpp` (record locking, line 253)
- `src/xbase/xbase_locks.cpp`
- `tools/dbf/maint_server.py` (the console's write-token boundary, for contrast)
- `coordination/OPEN_ITEMS.md` (OI-004, OI-005)

## Why this contract exists

`docs/contracts/CONTRACT_REGISTRY_V1.md` lists **"Python/C++ binding contracts"**
in its Gaps section -- a contract kind the project recognised as existing
informally with no registry entry. This is that gap filled for `pydottalk`.

It was written because a measurement, not a worry: `pydottalk` exposes
`append_blank`, `delete_current`, `set`, `set_field` and `write_current`, and
consults no member, permission or token. Every other write surface in this
project carries one -- the maintenance console gained a write-token boundary in
`6a931ab3d`, the CLI has `cmd_security` and the AIF-075 permission gate, the BBS
refuses unauthenticated sessions. The binding was the only one without, and
nobody had decided that; it simply shipped that way.

**Undeclared trust is indistinguishable from an oversight.** That is this
project's signature defect shape -- absent and fine reading the same -- so the
posture is stated here rather than left as an absence in the source.

## The declaration

**`pydottalk` is TRUSTED. The Python process is the trust boundary.**

Anyone who can `import pydottalk` can read and write the tables the process can
reach. This is intended. It is a first-party binding, over a first-party engine,
in the maintainer's own tree, called by scripts the maintainer wrote. Adding an
identity check inside the module would guard nothing: the caller already holds
the interpreter, the filesystem, and the same credentials any check would
consult.

Owner ruling, 2026-08-17: *"with security we would have to say its trusted,
after all it is our tool, our app."*

## What the binding does NOT need to add

- **No identity or member check.** The caller is trusted by construction.
- **No permission gate.** There is no untrusted principal on the other side.
- **No token.** There is no network listener and no cross-origin surface. The
  console needed one because a browser can be induced to POST; a Python import
  cannot.
- **No additional locking.** See below -- adding it would be a defect, not a
  hardening.

## Locking is INHERITED, and must not be re-added

Measured 2026-08-17: `pydottalk` writes go through `xbase::DbArea`, and
`src/xbase/dbarea.cpp:253` calls `xbase::locks::try_lock_record` before writing,
releasing at line 275. The `.lock` sidecars are pid-stamped with stale-owner
recovery (`xbase::locks`).

So the binding is a well-behaved third participant in the same cooperative
scheme `dottalkpp` and `dottalk_bbsd` already use -- three processes sharing an
on-disk store with no IPC between them, coordinating through locks.

**This is recorded because the obvious "hardening" is wrong.** A future reader
who notices the binding never mentions a lock may add one. That would double-lock
the engine's own acquisition. The correct statement is that locking is inherited,
not missing.

Caveat carried honestly: AIF-116 found the lock subsystem writing a pid through
an un-imbued stream, undetected for a year because no test of it existed. The
regression added there (`lock_mutual_exclusion_regression.ps1`) covers the
engine. It has NOT been exercised with `pydottalk` as one of the contending
processes.

## Where trusted STOPS

The boundary is this build, in this tree, called by this maintainer. Three edges
where the assumption fails, and each requires a new decision rather than an
extension of this one:

1. **Shipping the `.pyd` outside the tree.** To a student, a customer, or a
   package index. The caller is then not the maintainer, and "our tool, our app"
   no longer holds. This contract does not authorize distribution.
2. **Exposing the binding over a network.** Wrapping it in a web service, an
   RPC endpoint, or a notebook server reachable off-host reintroduces exactly
   the untrusted principal this contract assumes away. The console's write-token
   boundary is the precedent for what that then requires.
3. **Command-shell execution.** OI-005. Trusted-for-data-writes does not extend
   to trusted-for-arbitrary-command-execution, because the blast radius is
   different in kind: data writes are bounded by the engine's own validation and
   locking, while a command surface inherits everything the CLI can do,
   including destructive verbs behind their own confirmation gates. If `run` is
   built, it needs its own posture -- and the superseded `src/bindings/
   pydottalk.cpp` already implements one version of it (OI-002).

## Required declaration in source

`bindings/pydottalk/src/module.cpp` carries a `@dottalk.file v1` header. It must
name this contract, so the posture travels with the code rather than living only
here:

    // @dottalk.contract PYTHON_BINDING_TRUST_CONTRACT_V1
    // trust: caller-is-boundary (first-party, in-tree)
    // mutates: dbf-records
    // locking: inherited-from-dbarea

`owns:` and `lane:` in that header were EMPTY and are now filled; an empty field
in a declared-capability header is the same absent-vs-fine ambiguity this
contract was written to remove.

### The harvest path, and the gap found while asserting it

This contract originally claimed the annotation "is harvested". **That was false
when written, and is recorded rather than quietly corrected.**

Measured 2026-08-17, two tools and neither saw it:

- `src/meta/metacollect.cpp:152` DOES walk `bindings/`, but it harvests
  `@dottalk.usage` -- COMMAND contracts. `pydottalk` is not a command, so it
  matches nothing.
- `tools/contracts/contract_scan.py` DOES parse `@dottalk.contract` (line 171),
  but its `source_roots` were `include/`, `src/`, `tools/` only. It never looked
  in `bindings/`.

So the annotation existed, the contract said it travelled, and no inventory knew
about it. **Silent in the worst direction:** compliant from the source side,
missing from the registry side, and neither side complains -- which is the exact
defect shape AIF-118 exists for, committed by the author of this contract while
writing it.

Fixed by adding `root / "bindings"` to `contract_scan.py` source roots. Verified:
the scanner compiles, `bindings/` is in the list, it `rglob`s each root, and
`module.cpp:10` carries the annotation.

**Standing caution for the next binding.** A `@dottalk.contract` line is not
self-executing. Before claiming any annotation ripples, name the tool that reads
it and check that tool's roots.

## Promotion rule

This contract authorizes NOTHING new. It records a posture that already exists
and fixes its edges. Any of the three "where trusted stops" cases requires a new
contract revision and an owner ruling before code is written -- not after.
