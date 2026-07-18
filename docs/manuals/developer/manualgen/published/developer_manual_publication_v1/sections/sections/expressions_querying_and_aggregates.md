# Expressions, Querying, and Aggregates




Pippets used:
- PIP-001 Target Selection
- MDO-151 Target Selection
- MDO-152 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches known command/function and parser canaries.
- Do not send this directly to generic PIP-003.
- Run a slow-lane expression/function/aggregate review first.

Evidence tokens under review:
- CALC
- CALCWRITE
- WHERE
- FOR
- LOCATE
- CONTINUE
- SCAN
- COUNT
- SUM
- AVG
- MIN
- MAX
- AGGS
- FUNCTION
- FUNCTIONS
- PREDICATES
- MIN()
- MAX()
- xexpr
- DELETED
- NOT DELETED
- !DELETED

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Generated command draft pages remain draft evidence, not final command prose.
- xexpr owns expression evaluation surfaces unless current source proves a narrower owner for a specific path.
- SYSFUNC is a future semantic feeder even if current seeding is sparse.
- Scalar function forms and aggregate command forms must remain separate until runtime/source evidence closes the ambiguity.
- AGGS is treated as internal/family-owner evidence unless explicitly accepted as a user-facing command surface.

## Purpose of this section

This section explains expression evaluation, predicates, query filters, aggregate commands, and function surfaces in DotTalk++.

It follows Navigation and Indexing because those sections establish record movement, search context, active order, tags, projection, and relation boundaries. Expressions sit beneath many of those surfaces. Predicates decide which records are considered. Aggregate commands summarize values across records. Function calls support scalar calculation, command-line function applications, and calculated command behavior.

The goal is not to publish a final function reference. The goal is to establish safe developer-manual prose that preserves the boundaries between expression evaluation, command parsing, predicate filtering, aggregate traversal, scalar functions, and future metadata feeders.

## Evidence lanes

This draft uses several evidence lanes.

Current DotTalk evidence lane:
- CALC
- CALCWRITE
- WHERE
- FOR
- LOCATE
- CONTINUE
- SCAN
- COUNT
- SUM
- AVG
- MIN
- MAX
- AGGS
- FUNCTION
- FUNCTIONS
- PREDICATES
- MIN()
- MAX()
- xexpr
- DELETED
- NOT DELETED
- !DELETED

Generated command-reference lane:
- Generated command pages may identify draft command evidence.
- They are not final prose and should not be quoted as final command authority.
- AGGS and MIN/MAX require extra review because generated pages can expose implementation or family-owner concepts that may not be intended as public command surface.

Runtime evidence lane:
- Runtime examples have shown direct aggregate verbs SUM, AVG, MIN, and MAX working against an open table.
- Runtime examples have shown WHERE and FOR producing matching aggregate results in tested cases.
- Runtime examples have shown deleted-record filters affecting aggregate outputs in tested cases.
- Runtime examples have shown command-line function application behavior for functions such as UPPER and LEFT.
- Runtime examples have shown MIN/MAX parser ambiguity that must remain canary-sensitive.

Concept lane:
- An expression computes a value.
- A predicate is an expression used as a true/false condition.
- A query filter selects records.
- An aggregate command computes a result across records.
- A scalar function computes a result from arguments.
- A command parser may route command-like input differently from expression-function input.

Compatibility lane:
- xBase/FoxPro lineage can explain vocabulary, but compatibility evidence must not be promoted as current DotTalk behavior without runtime proof.
- Function names that overlap with command verbs are especially compatibility-sensitive.

Future META feeder lane:
- SYSFUNC should eventually carry canonical function identity, display name, category, argument range, handler, CALC_CALL, PUB_SURF, SELF_REG, MSG_CAT, and active status.
- SYSARGS should eventually carry function and command argument shapes, required/repeatable flags, predicate shapes, deleted filters, and expression values.
- SYSCMD should eventually carry command identity for COUNT, SUM, AVG, MIN, MAX, CALC, CALCWRITE, LOCATE, CONTINUE, SCAN, and related command surfaces.
- SYSSUBCMD should eventually carry aggregate-family or predicate-related subcommands if the command model keeps subcommand ownership.
- SYSENTVAR should eventually carry command/function variants, aliases, and app-style function entry points after seed hygiene review.
- SYSHELP should eventually carry curated/generated help text for functions, predicates, aggregate commands, and expression concepts.
- SYSMSG should eventually carry expression errors, nonnumeric aggregate values, no-active-table messages, not-found messages, deleted-filter outcomes, and parser ambiguity warnings.

## Expression evaluation surfaces

Expression evaluation is shared infrastructure. The manual should treat xexpr as the expression engine unless current source evidence proves otherwise for a specific path.

Expression surfaces include:
- CALC
- CALCWRITE
- command arguments that accept value expressions
- predicates in WHERE or FOR style clauses
- function calls
- calculated values used by aggregate commands

The developer manual should make a distinction between expression syntax and command syntax. A command may accept an expression, but that does not make the command itself the expression engine.

## CALC and CALCWRITE

CALC and CALCWRITE are expression-oriented command surfaces. They are useful places to explain evaluated expressions without requiring table traversal.

Safe wording:
- CALC evaluates an expression and displays or returns the result according to its command contract.
- CALCWRITE evaluates and writes or displays according to its command contract.
- Exact output behavior should be verified with HELP and runtime evidence before final wording.

These commands are natural cross-references for function help and the xexpr engine.

## Predicates, WHERE, and FOR

A predicate is an expression used as a condition. WHERE and FOR are predicate-bearing clauses or surfaces.

Safe wording:
- WHERE and FOR can restrict which records participate in a command where supported.
- Runtime evidence has shown matching aggregate results for equivalent WHERE and FOR predicates in tested aggregate cases.
- This equivalence should not be generalized across all commands without evidence.

The manual should not imply that WHERE and FOR are always identical. It should say that they can serve related predicate-filter roles and that each command surface must be checked.

## LOCATE, CONTINUE, and SCAN

LOCATE, CONTINUE, and SCAN connect predicates with traversal.

Safe distinctions:
- LOCATE searches for records matching a condition.
- CONTINUE resumes a prior locate-style search where supported.
- SCAN iterates over records and may use predicate or scope rules depending on command syntax.

These commands connect this section with Navigation and Indexing:
- Navigation owns movement and current record context.
- Indexing owns active order and tag-sensitive traversal context.
- Expressions own predicate evaluation.
- Commands own their own syntax and side effects.

## COUNT and aggregate commands

COUNT, SUM, AVG, MIN, and MAX belong to aggregate command discussion when they operate across records.

Safe aggregate wording:
- COUNT counts records or matched records according to command syntax and scope.
- SUM computes a total for a numeric expression across records.
- AVG computes an average for a numeric expression across records.
- MIN and MAX compute minimum and maximum aggregate results where command syntax and runtime support them.

The final manual should attach runtime proof for each command surface before claiming exact syntax, deleted-record behavior, or null/empty-set behavior.

## Direct aggregate verbs and AGGS

Direct aggregate verbs should be treated as the user-facing command surface where runtime and HELP evidence support them:
- SUM
- AVG
- MIN
- MAX

AGGS should be treated carefully. Current doctrine is:
- AGGS is intended as an owner/internal grouping for aggregate verbs.
- AGGS being executable or printing usage may be debug/scaffold leakage unless explicitly accepted.
- Generated command pages for AGGS are draft evidence, not final public-surface proof.

The manual should explain aggregate family ownership without accidentally publishing an internal owner as a user command.

## Scalar functions versus aggregate commands

MIN and MAX are the important canary.

There are two concepts:
- scalar function form: MIN() or MAX() as a function over supplied arguments;
- aggregate command form: MIN <value_expr> or MAX <value_expr> over records.

These must not be collapsed.

Known runtime canary:
- command-style input has shown MIN/MAX aggregate behavior.
- function-app and command-line function bridging exists for functions such as UPPER and LEFT.
- MIN(2,1) versus MIN 2,1 parser behavior must remain canary-sensitive until current runtime/source evidence closes it.

The manual should preserve the ambiguity:
- MIN/MAX aggregate commands are command surfaces.
- MIN()/MAX() scalar functions are function surfaces if current function registry/runtime evidence confirms them.
- Parser dispatch and command/function shadowing must be documented carefully.

## Function command-line bridge

DotTalk++ allows some function/app forms to be used directly from the command line.

Examples in prior runtime notes include:
- UPPER with a string-like value
- LEFT with a value and length argument

This is important because function names may appear command-like when typed at the prompt. The manual should explain that some command-line input can bridge into scalar/function-app evaluation.

However, the bridge must not override command ownership:
- A direct command verb may own a word such as MIN or MAX.
- A scalar function may also exist with the same name.
- The parser/dispatcher decides which surface receives the input.

## Deleted-record filters

Aggregate commands may support deleted-record filters.

Evidence-sensitive filter vocabulary:
- DELETED
- NOT DELETED
- !DELETED

Safe wording:
- Deleted-record filters may affect which records participate in aggregate results where supported.
- Runtime evidence has shown DELETED returning empty/null-like aggregate behavior in tested cases and NOT DELETED matching full nondeleted results in tested cases.
- Exact behavior must be verified per command, expression type, and data state.

The manual should not generalize deleted-record behavior beyond tested aggregate surfaces without proof.

Proof boundary:
- deleted-record aggregate filters are proof-aware.
- DELETED, NOT DELETED, and !DELETED should not be generalized beyond tested aggregate surfaces.
- Final wording must remain tied to command, expression type, and data-state evidence.

## Error and null behavior

Aggregate and expression commands can produce errors or null-like results.

Examples needing proof-aware wording:
- nonnumeric expression supplied to a numeric aggregate;
- character expression supplied to AVG;
- unknown field or expression;
- empty or deleted-only record sets;
- no active table;
- invalid function argument count.

SYSMSG is the intended future feeder for error symbols, severity, short text, suggested actions, and implementation status.

## HELP FUNCTIONS and FUNCTION help

HELP FUNCTIONS and HELP FUNCTION <name> should be included as user-facing discovery surfaces for expression functions.

The manual should distinguish:
- command help for command verbs;
- function help for expression functions;
- generated command draft pages;
- future SYSFUNC metadata.

SYSFUNC is important even when sparsely seeded because it is the future semantic feeder for canonical function identity, argument ranges, handlers, public surface status, and message-catalog alignment.

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- MIN/MAX scalar function versus aggregate command ambiguity
- AGGS internal family owner exposure
- direct aggregate verbs versus scalar function forms
- command parser function bridge
- WHERE FOR predicate equivalence
- DELETED NOT DELETED !DELETED aggregate filters
- xexpr owns expression evaluation surfaces
- HELP FUNCTIONS FUNCTION name SYSFUNC future feeder
- generated command pages draft evidence
- MIN(2,1) versus MIN 2,1 parser behavior

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Future META alignment

This section should eventually align with the metadata system.

Expected future feeders:
- SYSFUNC for canonical function identity, display name, category, argument range, implementation status, visibility tier, owner, source authority, source file, handler, CALC_CALL, PUB_SURF, SELF_REG, MSG_CAT, active status, and notes.
- SYSARGS for function and command argument shapes, predicates, deleted filters, repeatable arguments, and required values.
- SYSCMD for command identity and handler alignment for CALC, CALCWRITE, COUNT, SUM, AVG, MIN, MAX, LOCATE, CONTINUE, and SCAN.
- SYSSUBCMD for aggregate-family or predicate-related subcommands if those are modeled as subcommands.
- SYSENTVAR for variants, aliases, and command-line function-app entry points after seed hygiene review.
- SYSHELP for generated and curated help text connected to command and function owners.
- SYSMSG for expression, aggregate, predicate, and parser diagnostics.

Temporary evidence is acceptable only when marked as temporary and crosswalked to future META feeders.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- generated command pages are treated as draft evidence;
- AGGS is not promoted as a public user command without explicit acceptance;
- MIN/MAX scalar function and aggregate command forms are separated;
- function-command bridge behavior is described conservatively;
- WHERE and FOR equivalence is evidence-gated;
- deleted-record filters are proof-aware;
- xexpr ownership is preserved;
- HELP FUNCTIONS, HELP FUNCTION <name>, and SYSFUNC future feeder notes are present;
- compatibility evidence is not presented as runtime proof;
- parser ambiguity remains visible.

Recommended required tokens for later PIP-003:
- CALC
- CALCWRITE
- WHERE
- FOR
- LOCATE
- CONTINUE
- SCAN
- COUNT
- SUM
- AVG
- MIN
- MAX
- AGGS
- FUNCTION
- FUNCTIONS
- PREDICATES
- MIN()
- MAX()
- xexpr
- DELETED
- NOT DELETED
- !DELETED

## Boundary

- prose draft fill only
- slow-lane review still required
- no reviewed candidate generated
- no final prose promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion


