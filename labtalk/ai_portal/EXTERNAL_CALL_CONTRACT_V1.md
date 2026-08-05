# External Call Contract -- @dottalk.external v1

**Concept id:** `EXTERNAL_CALL_CONTRACT_V1` - **owner:** member.derald - **status:** candidate
(dev-only; introduced in full-stack doc flush v4, 2026-08-05) - **lane:** AIF-088

## What it is

`@dottalk.external` is a source-comment contract block, a sibling of `@dottalk.file`
and `@dottalk.usage`, that marks a command as crossing the engine boundary into the
host OS -- launching an external process, shelling out, toggling host state, or
otherwise doing something the engine cannot bound or undo from inside its own runtime.

A command that carries it is **OS-sensitive**. The block records exactly what the
command reaches outside the engine, what gates it, and whether it is audited, so the
harvest, the reviewer, and the HELP surface can see the OS boundary as a first-class
fact rather than inferring it from prose.

## Why it exists

The `risk:` sub-block of `@dottalk.usage` can note `launches_external_process`, but it
is free-form and easy to miss. External calls are the highest-consequence surface in
the engine (they can spawn processes, change host network policy, or hand a file to an
arbitrary program), so they earn their own named, harvestable contract. Making the OS
boundary explicit means a future gate can require an `@dottalk.external` block on any
command whose handler shells out, and refuse to publish HELP that understates it.

## When it is required

Any command whose implementation:

- spawns or executes an external process (editor, shell, tool);
- changes host state outside the DBF store (network policy, environment, services);
- requires elevation (UAC / sudo) or a host-command allowlist;
- performs egress or any network I/O to a non-loopback endpoint.

Pure in-engine commands (read/mutate the DBF store, indexes, workspace) do **not** need
one. When in doubt: if the engine cannot describe the full effect in terms of its own
tables and state, it is external.

## Fields

```
// @dottalk.external v1
// owner: <FAMILY>|<COMMAND>
// command: <COMMAND>
// external-kind: os-process | host-config | network | shell
// os-sensitive: yes
// target: what external thing is invoked (program, service, endpoint)
// invocation: how it is invoked (spawn, shell, API, elevated process)
// touches: host resources reached (process table, filesystem, network, registry)
// requires: preconditions/permissions (settings, RBAC permission, allowlist flag)
// guard: what gates or short-circuits it (USAGE returns first, mode Off disables, RBAC)
// egress: none | loopback-only | outbound (describe)
// audit: none | transcript path (whether the call is recorded)
// reversible: yes | no (can the engine undo the effect)
// notes:
//   free text; call out anything the engine cannot bound.
// @dottalk.end
```

`@dottalk.external` does not replace `@dottalk.usage`; it complements it. The command
still declares its surface in `@dottalk.usage` (which should also carry
`// os-sensitive: yes`), and `@dottalk.external` is the OS-boundary record that the
usage `risk:` block summarizes.

## First carriers

- **EDIT** (`src/edu/edu_edit.cpp`) -- launches the configured external editor as a
  child process; the reference implementation of this contract.
- **NET** (`src/cli/cmd_net.cpp`) -- host network egress toggle, RBAC-gated, UAC-
  elevated, transcript-audited: a strong candidate to backfill with an explicit
  `@dottalk.external` block (its usage already documents the host-command sensitivity).

## Follow-ups

- Backfill `@dottalk.external` onto the other OS-sensitive commands (NET first).
- Teach the comment harvest (`tools/comments/reharvest_source_comment_catalog.py`) to
  collect `@dottalk.external` blocks as their own kind, so OS-sensitive surfaces are
  enumerable.
- Once coverage is real, add a gate: a command whose handler shells out must carry an
  `@dottalk.external` block, or the contract audit fails.
