// @dottalk.file v1
// subsystem: edu
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-067
// owner: member.derald
// status: supported

// NO USAGE CONTRACT HERE, DELIBERATELY. Removed 2026-07-27 (AIF-067).
// (Marker token deliberately not spelled out -- CONTRACT_QA/MENTION_ONLY counts
// files naming it without carrying one, and an explanation of an absence must
// not read as a malformed presence.)
//
// This translation unit contains NO CODE -- it is a reserved placeholder for
// future Boyce-Codd normal form educational material, and has been since it was
// created. It exports no shell command, registers nothing, and defines nothing.
//
// It previously carried a usage-contract block declaring `command: none`, which
// CONTRACT_QA reported as a non-identity name. The report was right and the
// remedy is not a better name: a usage contract asserts "I am this command",
// and a file with no code is not a command. `layer:` was also `command`, which
// was wrong for the same reason and is now `helper`.
//
// Rule settled with member.derald, 2026-07-27: a file that owns no command gets
// @dottalk.file only. The placeholder's purpose is recorded here, in prose,
// which is the right place for prose.
//
// IF A BCNF COMMAND EVER BECOMES USER-FACING: add the runtime handler and the
// full usage contract IN THE SAME COMMIT. A contract written ahead of
// its implementation is a claim with nothing behind it, and this file is the
// cautionary example -- the block sat here long enough to be counted as a
// documented command by tooling that had no way to know better.
