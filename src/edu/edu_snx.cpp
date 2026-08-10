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
// This translation unit contains NO CODE. It is a reserved placeholder for
// future SNX educational / index material, exports no shell command, registers
// nothing, and defines nothing.
//
// It previously carried a usage-contract block declaring `command: none`, which
// CONTRACT_QA reported as a non-identity name. The report was right, and the
// remedy is not a better name: a usage contract asserts "I am this command",
// and a file with no code is not a command. `layer:` was `command` for the same
// mistaken reason and is now `helper`.
//
// Rule settled with member.derald, 2026-07-27: a file that owns no command gets
// the file contract only. Prose belongs in prose.
//
// THE EMPTY FILE IS DELIBERATE, NOT RESIDUE (member.derald, 2026-07-27):
// "0 byte commands, plugs, and prototypes help define the top level layer of
// our systems design". This translation unit reserves SNX's place in the
// education subsystem, stated in the vocabulary the build reads: a file that
// exists. Stronger than a TODO -- it survives refactors, appears in the census,
// and must be deliberately deleted to disappear.
//
// The correction is narrow: the ZERO-BYTE FILE is right, the USAGE CONTRACT on
// it was wrong. A file may declare a reserved slot in the design; a usage
// contract may not declare a command that does not exist, because SYSCMD, HELP,
// dotref and the census all treat it as a real surface and count it.
//
// ONE OF THREE IDENTICAL PLACEHOLDERS (see edu_boyce_codd.cpp and
// edu_dewey_decimal.cpp). All three shared the name `none`, and CONTRACT_QA
// groups by NAME, so three occurrences presented as one finding until the first
// was removed.
//
// IF AN SNX COMMAND EVER BECOMES USER-FACING: add the runtime handler and the
// full usage contract IN THE SAME COMMIT. A contract written ahead of its
// implementation is a claim with nothing behind it.
