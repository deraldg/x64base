# SYSSUBCMD seed harvest v1

Sibling of the SYSCMD seed-gap. Models the subcommand surface (SET/BUILD/ERROR) so
`SET <option>` forms seed into SYSSUBCMD, not SYSCMD. dotref.hpp is the first
collection point; source (cmd_set.cpp ladder + registry) is the authority.

## Sizes

- SET ladder options (cmd_set.cpp): 31
- registry compound parents: ['BUILD', 'ERROR', 'SET']
- **subcommand candidates emitted: 37** across parents ['BUILD', 'ERROR', 'SET']
- spelling forks (same feature, multiple spellings): 16

## Candidate subcommands

| PARENT | CAN_NAME | HANDLER | evidence |
|---|---|---|---|
| BUILD | INFO | cmd_BUILDVECTORS | compound |
| BUILD | LMDB | cmd_BUILDLMDB | concat,doc |
| BUILD | VECTORS | cmd_BUILDVECTORS | compound,concat,doc |
| ERROR | CLEAR | cmd_ERROR_CLEAR | compound,concat,doc |
| ERROR | STATUS | cmd_ERROR_STATUS | compound,concat,doc |
| ERROR | TEST | cmd_ERROR_TEST | compound,concat,doc |
| SET | ALTERNATE | cmd_SET | ladder |
| SET | BUFFER | cmd_SET | ladder |
| SET | CASE | cmd_SETCASE | ladder,concat,doc |
| SET | CDX | cmd_SETCDX | ladder,concat,doc |
| SET | CNX | cmd_SETCNX | ladder,concat,doc |
| SET | CONSOLE | cmd_SET | ladder |
| SET | DELETED | cmd_SET | ladder |
| SET | DEVDIAG | cmd_SET | ladder |
| SET | DEVICE | cmd_SET | ladder |
| SET | ECHO | cmd_SET | ladder |
| SET | EDITOR | cmd_SET | ladder |
| SET | ERRORSTOP | cmd_SET | ladder |
| SET | FILTER | cmd_SETFILTER | ladder,concat,doc |
| SET | INDEX | cmd_SETINDEX | ladder,concat,doc |
| SET | INDEXTXN | cmd_SET | ladder |
| SET | LANGUAGE | cmd_SET | ladder |
| SET | LMDB | cmd_SETLMDB | ladder,concat,doc |
| SET | LOCALE | cmd_SET | ladder |
| SET | MESSAGE | cmd_SET | ladder |
| SET | NEAR | cmd_SETNEAR | ladder,concat,doc |
| SET | ORDER | cmd_SETORDER | ladder,concat,doc |
| SET | PAGING | cmd_SET | ladder |
| SET | PATH | cmd_SETPATH | ladder,concat,doc |
| SET | POLLING | cmd_SET | ladder |
| SET | PRINT | cmd_SET | ladder |
| SET | RELATION | cmd_SET_RELATIONS | ladder,compound,doc |
| SET | TABLE | cmd_SET | ladder |
| SET | TALK | cmd_SET | ladder |
| SET | TIMER | cmd_SET | ladder |
| SET | UNIQUE | cmd_SET_UNIQUE | ladder,compound,doc |
| SET | WRAP | cmd_SET | ladder |

## Spelling forks to reconcile (fullstack push)

| feature | spellings | evidence |
|---|---|---|
| BUILD LMDB | BUILD LMDB / BUILDLMDB | concat,doc |
| BUILD VECTORS | BUILD VECTORS / BUILDVECTORS | compound,concat,doc |
| ERROR CLEAR | ERROR CLEAR / ERRORCLEAR | compound,concat,doc |
| ERROR STATUS | ERROR STATUS / ERRORSTATUS | compound,concat,doc |
| ERROR TEST | ERROR TEST / ERRORTEST | compound,concat,doc |
| SET CASE | SET CASE / SETCASE | ladder,concat,doc |
| SET CDX | SET CDX / SETCDX | ladder,concat,doc |
| SET CNX | SET CNX / SETCNX | ladder,concat,doc |
| SET FILTER | SET FILTER / SETFILTER | ladder,concat,doc |
| SET INDEX | SET INDEX / SETINDEX | ladder,concat,doc |
| SET LMDB | SET LMDB / SETLMDB | ladder,concat,doc |
| SET NEAR | SET NEAR / SETNEAR | ladder,concat,doc |
| SET ORDER | SET ORDER / SETORDER | ladder,concat,doc |
| SET PATH | SET PATH / SETPATH | ladder,concat,doc |
| SET RELATION | SET RELATION | ladder,compound,doc |
| SET UNIQUE | SET UNIQUE | ladder,compound,doc |

