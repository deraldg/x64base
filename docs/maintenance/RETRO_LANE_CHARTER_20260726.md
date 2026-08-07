# Retro Lane Charter 2026-07-26

Status: planned lane, parked for review.
Ticket: AIF-064.
Owner: member.derald.
Source: Google Doc `RETRO_LANE_CHARTER_20260726.md` and attached
`RETRO_LANE_PROPOSAL_V1_20260726`.
Delivery rule: Outside-AI review package first; no runtime tree edit without
explicit approval.

## Purpose

Retro is x64base's private front door to old machines: a catalog and launcher
for VMware guests and emulator configs, presented as a curated gallery with a
short heritage note for each registered machine.

The lane is intentionally optional and private. It should be invisible to
normal/public builds unless the owner enables a CMake flag. When enabled, it
can be built into the normal `dottalkpp` binary.

## Locked Decisions

- Lane identity: emulator/VM launchpad and historical gallery.
- Build flag: `X64BASE_ENABLE_RETRO`, default `OFF`.
- Repo privacy: flag-gated in the public repo, not a separate hidden repo.
- First-class backends: VMware `vmrun`, WinUAE, FS-UAE, DOSBox.
- Escape hatch backend: generic `exec`.
- Catalog source: seed file bootstraps `retro_machines.dbf` once; DBF is
  authoritative after bootstrap.
- Storage: `retro_machines.dbf` read through DotTalk++/x64base `DbArea`, with
  CDX identity on machine id when the physical implementation lands.
- Runnable ceiling: native launch through x64/cloud; mainframe/super/farm
  entries are representational or simulator-backed and must be badged honestly.

## Live Tree Facts

These replace the V1 proposal placeholders:

- Main CLI target: `dottalkpp`, defined in `src/CMakeLists.txt`.
- Core storage libraries available to `dottalkpp`: `xbase`, `xindex`, `memo`,
  `xexpr`, and `dottalk_value`, linked from `src/CMakeLists.txt`.
- Command registration: `register_shell_commands` in
  `src/cli/shell_commands.cpp` uses `registry().add(...)`.
- Existing `RETRO` command registration:
  `src/cli/shell_commands.cpp` registers `RETRO` to `cmd_RETRO`.
- Existing retro command source: `src/cli/cmd_retro.cpp`.
- Existing screen/render assets: `src/cli/retro_screen.hpp`,
  `src/cli/retro_screen.cpp`, `src/cli/retro_render.hpp`,
  `src/cli/retro_render.cpp`.
- Current screen model: compiled `dottalk::retro::Screen` records with
  `native_art`, `ascii_art`, `legacy_art`, and `profile_note`.

## Resume Prompt

Resume the Retro lane from `docs/maintenance/RETRO_LANE_CHARTER_20260726.md`
and `docs/maintenance/RETRO_LANE_PROPOSAL_V2_20260726.md`. Decisions are
locked. The real tree facts are: target `dottalkpp`; registration through
`src/cli/shell_commands.cpp` `registry().add(...)`; current retro sources in
`src/cli/cmd_retro.cpp`, `retro_screen.*`, and `retro_render.*`. Review the V2
package, then decide whether to implement the flag-gated lane and whether the
generation field lands in the first cut.

