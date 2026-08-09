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
// THE EMPTY FILE IS DELIBERATE, NOT RESIDUE (member.derald, 2026-07-27):
//
//   "0 byte commands, plugs, and prototypes help define the top level layer of
//    our systems design"
//
// So this file is a DESIGN ARTIFACT. It states that Boyce-Codd normal form has
// a reserved place in the education subsystem, and it states it in the only
// vocabulary the build actually reads: a translation unit that exists. That is
// a stronger claim than a TODO in a document, because it survives refactors,
// appears in the census, and has to be deliberately deleted to go away.
//
// The correction is therefore narrow and worth stating precisely: the ZERO-BYTE
// FILE is right; the USAGE CONTRACT on it was wrong. A file may legitimately
// declare a reserved slot in the design. A usage contract may not declare a
// command that does not exist, because everything downstream -- SYSCMD, HELP,
// dotref, the census -- treats it as a real command surface and counts it.
//
// Design intent belongs in @dottalk.file and prose. Command identity belongs in
// a usage contract, and only once there is a command.
//
// IF A BCNF COMMAND EVER BECOMES USER-FACING: add the runtime handler and the
// full usage contract IN THE SAME COMMIT. A contract written ahead of
// its implementation is a claim with nothing behind it, and this file is the
// cautionary example -- the block sat here long enough to be counted as a
// documented command by tooling that had no way to know better.
