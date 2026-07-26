# SYSCMD seed-gap report v1

Feeds the Phase 3B dotref generator. dotref.hpp is the first collection point of
the fullstack document harvest; this lists commands still missing a SYSCMD row.

## Surface sizes

- registry (implemented commands): 236
- dotref.hpp (documented surface): 255
- SYSCMD (already seeded): 40
- SYSARGS (commands with usage rows): 98
- **gap to seed (registry union dotref, minus seeded): 224**

## Gap breakdown

- registry-backed (handler resolved, safe to seed): 194
- registry-backed but handler needs review: 2
- documented-only (in dotref, not in registry -- review): 28
- syntax-ready (SYSARGS usage already present): 74
- symbol-only aliases skipped (not command identities): 1 (!)

## Checklist (candidate rows)

| CAN_NAME | HANDLER | ACTIVE | reg | doc | args | class |
|---|---|:--:|:--:|:--:|:--:|---|
| AGGS | cmd_AGGS | T | Y | Y | Y | registry-backed |
| APPEND_BLANK | cmd_APPEND_BLANK | T | Y | Y | - | registry-backed |
| ARCTICTALK | cmd_FOXTALK | T | Y | Y | - | registry-backed |
| AREA | cmd_AREA | T | Y | Y | - | registry-backed |
| AREA51 | TODO | T | Y | Y | - | registry-backed (handler needs review) |
| ASCEND | cmd_ASCEND | T | Y | Y | - | registry-backed |
| AUTODBF | cmd_AUTODBF | T | Y | Y | - | registry-backed |
| AVERAGE | cmd_AVG | T | Y | Y | - | registry-backed |
| AVG | cmd_AVG | T | Y | Y | - | registry-backed |
| BANG | cmd_BANG | T | Y | Y | Y | registry-backed |
| BBOX | cmd_BBOX | T | Y | Y | - | registry-backed |
| BBS | cmd_BBS | T | Y | - | - | registry-backed |
| BETA | cmd_BETA | T | Y | Y | - | registry-backed |
| BIBLETALK | edu_BIBLETALK | T | Y | Y | - | registry-backed |
| BOOLEAN | edu_BOOLEAN | T | Y | Y | - | registry-backed |
| BOTTOM | cmd_BOTTOM | T | Y | Y | - | registry-backed |
| BROWSE | cmd_BROWSE | T | Y | Y | - | registry-backed |
| BROWSETUI | cmd_BROWSETUI | T | Y | Y | - | registry-backed |
| BROWSETV | cmd_BROWSETV | T | Y | Y | - | registry-backed |
| BUILD INFO | cmd_BUILDVECTORS | T | Y | - | - | registry-backed |
| BUILD VECTORS | cmd_BUILDVECTORS | T | Y | - | - | registry-backed |
| BUILDLMDB | cmd_BUILDLMDB | T | Y | Y | Y | registry-backed |
| BUILDVECTORS | cmd_BUILDVECTORS | T | Y | Y | - | registry-backed |
| CANARY | cmd_CATALOGCANARY | T | Y | - | - | registry-backed |
| CDX | cmd_CDX | T | Y | Y | Y | registry-backed |
| CHRISTMAS | edu_CHRISTMAS | T | Y | Y | - | registry-backed |
| CLOSE | cmd_CLOSE | T | Y | Y | - | registry-backed |
| CMDARGCHK | cmd_CMDARGCHK | T | Y | Y | - | registry-backed |
| CMDHELP | cmd_CMDHELP | T | Y | Y | - | registry-backed |
| CMDHELPCHK | cmd_CMDHELPCHK | T | Y | Y | - | registry-backed |
| CMDREL | cmd_CMDREL | T | Y | - | - | registry-backed |
| CNX | cmd_CNX | T | Y | Y | Y | registry-backed |
| COBOL | cmd_COBOL | T | Y | Y | - | registry-backed |
| CODASYL | cmd_CODASYL | T | Y | Y | Y | registry-backed |
| COLOR | cmd_COLOR | T | Y | Y | - | registry-backed |
| COMMANDSHELP | cmd_CMDHELP | T | Y | Y | - | registry-backed |
| COMMIT | cmd_COMMIT | T | Y | Y | - | registry-backed |
| CONCAT | cmd_CONCAT | T | Y | Y | - | registry-backed |
| COUNT | cmd_COUNT | T | Y | Y | Y | registry-backed |
| DBAREA | cmd_DBAREA | T | Y | Y | - | registry-backed |
| DBAREAS | cmd_DBAREAS | T | Y | Y | Y | registry-backed |
| DDICT | cmd_DDICT | T | Y | Y | - | registry-backed |
| DDL | cmd_DDL | T | Y | Y | Y | registry-backed |
| DEFCMD | cmd_DEFCMD | T | Y | Y | - | registry-backed |
| DEFFN | cmd_DEFFN | T | Y | Y | - | registry-backed |
| DESCEND | cmd_DESCEND | T | Y | Y | - | registry-backed |
| DISPLAY | cmd_DISPLAY | T | Y | Y | Y | registry-backed |
| DOTHELP | cmd_DOTHELP | T | Y | Y | Y | registry-backed |
| DOTSCRIPT | cmd_DOTSCRIPT | T | Y | Y | Y | registry-backed |
| DRAWIO | cmd_DRAWIO | T | Y | Y | Y | registry-backed |
| DUMP | cmd_DUMP | T | Y | Y | - | registry-backed |
| ECHO | cmd_ECHO | T | Y | Y | Y | registry-backed |
| ENDLOOP | cmd_ENDLOOP | T | Y | Y | - | registry-backed |
| ERP | edu_ERP | T | Y | Y | - | registry-backed |
| ERROR CLEAR | cmd_ERROR_CLEAR | T | Y | Y | - | registry-backed |
| ERROR STATUS | cmd_ERROR_STATUS | T | Y | Y | - | registry-backed |
| ERROR TEST | cmd_ERROR_TEST | T | Y | Y | - | registry-backed |
| ERROR_CLEAR | cmd_ERROR_CLEAR | T | Y | Y | - | registry-backed |
| ERROR_STATUS | cmd_ERROR_STATUS | T | Y | Y | - | registry-backed |
| ERROR_TEST | cmd_ERROR_TEST | T | Y | Y | - | registry-backed |
| ERSATZ | cmd_ERSATZ | T | Y | Y | Y | registry-backed |
| EVAL | TODO | T | - | Y | - | documented-only |
| EVALUATE | edu_EVALUATE | T | Y | Y | - | registry-backed |
| EXAMPLE | cmd_EXAMPLE | T | Y | Y | - | registry-backed |
| EXIT | cmd_QUIT | T | Y | Y | - | registry-backed |
| EXITS | cmd_EXITS | T | Y | Y | - | registry-backed |
| EXPFUNCS | cmd_EXPORTFUNCTIONS | T | Y | Y | - | registry-backed |
| EXPORTFUNCTIONS | cmd_EXPORTFUNCTIONS | T | Y | Y | Y | registry-backed |
| EXPORTSQL | cmd_EXPORTSQL | T | Y | Y | - | registry-backed |
| FIELDMGR | cmd_FIELDMGR | T | Y | Y | Y | registry-backed |
| FIELDS | cmd_FIELDS | T | Y | Y | - | registry-backed |
| FORMULA | edu_FORMULA | T | Y | - | - | registry-backed |
| FOXHELP | cmd_FOXHELP | T | Y | Y | Y | registry-backed |
| FOXPRO | cmd_FOXPRO | T | Y | Y | - | registry-backed |
| FOXSTANDARD | cmd_FOXSTANDARD | T | Y | Y | Y | registry-backed |
| FOXTALK | cmd_FOXTALK | T | Y | Y | - | registry-backed |
| GENERIC | cmd_GENERIC | T | Y | Y | - | registry-backed |
| GO | cmd_GO | T | Y | Y | Y | registry-backed |
| GPS | cmd_GPS | T | Y | Y | - | registry-backed |
| HANUKKAH | edu_HANUKKAH | T | Y | Y | - | registry-backed |
| HELP | cmd_HELP | T | Y | Y | Y | registry-backed |
| HIER | cmd_HIER | T | Y | Y | - | registry-backed |
| IDX | edu_IDX | T | Y | Y | Y | registry-backed |
| IMAGE | cmd_IMAGE_DISPLAY | T | Y | Y | Y | registry-backed |
| IMPORTSQL | cmd_IMPORTSQL | T | Y | Y | - | registry-backed |
| INIT | cmd_INIT | T | Y | Y | - | registry-backed |
| LIST | cmd_LIST | T | Y | Y | Y | registry-backed |
| LIST_LMDB | cmd_LIST_LMDB | T | Y | Y | Y | registry-backed |
| LMDB | cmd_LMDB | T | Y | Y | - | registry-backed |
| LMDBDUMP | cmd_LMDB_DUMP | T | Y | Y | - | registry-backed |
| LMDB_UTIL | cmd_LMDB_UTIL | T | Y | Y | - | registry-backed |
| LOCK | cmd_LOCK | T | Y | Y | Y | registry-backed |
| LOOP | cmd_LOOP | T | Y | Y | Y | registry-backed |
| LOOP_BUFFER | cmd_LOOP_BUFFER | T | Y | Y | - | registry-backed |
| MAINT | cmd_MAINT | T | Y | Y | - | registry-backed |
| MANSTAR | cmd_MANSTAR | T | Y | Y | - | registry-backed |
| MANUAL | cmd_MANUAL | T | Y | Y | - | registry-backed |
| MAX | cmd_MAX | T | Y | Y | - | registry-backed |
| MCC | cmd_MCC | T | Y | Y | - | registry-backed |
| MEMO | cmd_MEMO | T | Y | Y | - | registry-backed |
| MIN | cmd_MIN | T | Y | Y | - | registry-backed |
| MSGMGR | cmd_MSGMGR | T | Y | Y | - | registry-backed |
| MULTIREP | cmd_REPLACE_MULTI | T | Y | Y | - | registry-backed |
| NET | cmd_NET | T | Y | - | - | registry-backed |
| NEXT | cmd_NEXT | T | Y | Y | - | registry-backed |
| NORMALIZE | edu_NORMALIZE | T | Y | Y | - | registry-backed |
| PREDHELP | TODO | T | - | Y | - | documented-only |
| PREDICATES | TODO | T | - | Y | - | documented-only |
| PRIOR | cmd_PRIOR | T | Y | Y | - | registry-backed |
| PRN | cmd_PRN | T | Y | Y | Y | registry-backed |
| PROJECTS | cmd_PROJECTS | T | Y | Y | Y | registry-backed |
| PSHELL | cmd_PSHELL | T | Y | Y | Y | registry-backed |
| QUIT | cmd_QUIT | T | Y | Y | - | registry-backed |
| RBROWSE | cmd_RBROWSE | T | Y | Y | - | registry-backed |
| REBUILD | cmd_REBUILD | T | Y | Y | Y | registry-backed |
| RECALL | cmd_RECALL | T | Y | Y | Y | registry-backed |
| RECNO | cmd_RECNO | T | Y | Y | Y | registry-backed |
| RECORD | cmd_RECORD | T | Y | Y | - | registry-backed |
| RECORDVIEW | cmd_RECORDVIEW | T | Y | Y | - | registry-backed |
| REFRESH | cmd_REFRESH | T | Y | Y | - | registry-backed |
| REGRESSION | cmd_REGRESSION | T | Y | Y | - | registry-backed |
| REINDEX | cmd_REINDEX | T | Y | Y | Y | registry-backed |
| REL | cmd_REL | T | Y | Y | - | registry-backed |
| REL ENUM | TODO | T | - | Y | - | documented-only |
| RELATIONS | cmd_RELATIONS_LIST | T | Y | Y | Y | registry-backed |
| REL_LIST | cmd_RELATIONS_LIST | T | Y | Y | - | registry-backed |
| REL_REFRESH | cmd_RELATIONS_REFRESH | T | Y | Y | - | registry-backed |
| RETRO | cmd_RETRO | T | Y | Y | Y | registry-backed |
| ROLLBACK | cmd_ROLLBACK | T | Y | Y | - | registry-backed |
| RULE | cmd_RULE | T | Y | Y | Y | registry-backed |
| SB | TODO | T | - | Y | - | documented-only |
| SCAN_BUFFER | cmd_SCAN_BUFFER | T | Y | Y | - | registry-backed |
| SCHEMA | TODO | T | - | Y | - | documented-only |
| SCHEMAS | cmd_SCHEMAS | T | Y | Y | - | registry-backed |
| SCX | cmd_SCX | T | Y | Y | Y | registry-backed |
| SECHO | TODO | T | - | Y | - | documented-only |
| SECURITY | cmd_SECURITY | T | Y | Y | - | registry-backed |
| SEEK | cmd_SEEK | T | Y | Y | Y | registry-backed |
| SELECT | cmd_SELECT | T | Y | Y | Y | registry-backed |
| SET | cmd_SET | T | Y | Y | Y | registry-backed |
| SET CASE | TODO | T | - | Y | - | documented-only |
| SET CDX | TODO | T | - | Y | Y | documented-only |
| SET CNX | TODO | T | - | Y | Y | documented-only |
| SET FILTER | TODO | T | - | Y | Y | documented-only |
| SET INDEX | TODO | T | - | Y | Y | documented-only |
| SET LMDB | TODO | T | - | Y | - | documented-only |
| SET NEAR | TODO | T | - | Y | - | documented-only |
| SET ORDER | TODO | T | - | Y | Y | documented-only |
| SET PATH | TODO | T | - | Y | Y | documented-only |
| SET RELATION | cmd_SET_RELATIONS | T | Y | Y | Y | registry-backed |
| SET UNIQUE | cmd_SET_UNIQUE | T | Y | Y | Y | registry-backed |
| SET VAR | TODO | T | - | Y | - | documented-only |
| SET VAR! | TODO | T | - | Y | - | documented-only |
| SETCASE | cmd_SETCASE | T | Y | Y | - | registry-backed |
| SETCDX | cmd_SETCDX | T | Y | Y | - | registry-backed |
| SETCNX | cmd_SETCNX | T | Y | Y | - | registry-backed |
| SETFILTER | cmd_SETFILTER | T | Y | Y | - | registry-backed |
| SETINDEX | cmd_SETINDEX | T | Y | Y | - | registry-backed |
| SETLMDB | cmd_SETLMDB | T | Y | Y | - | registry-backed |
| SETNEAR | cmd_SETNEAR | T | Y | Y | - | registry-backed |
| SETORDER | cmd_SETORDER | T | Y | Y | - | registry-backed |
| SETPATH | cmd_SETPATH | T | Y | Y | - | registry-backed |
| SFTP | cmd_SFTP | T | Y | Y | - | registry-backed |
| SHELLO | TODO | T | - | Y | - | documented-only |
| SHOWINI | cmd_SHOWINI | T | Y | Y | Y | registry-backed |
| SHUTDOWN | cmd_SHUTDOWN | T | Y | Y | - | registry-backed |
| SIMPLEBROWSE | cmd_SIMPLE_BROWSER | T | Y | Y | Y | registry-backed |
| SIMPLEBROWSER | TODO | T | - | Y | - | documented-only |
| SIX | cmd_SIX | T | Y | Y | - | registry-backed |
| SKIP | cmd_SKIP | T | Y | Y | Y | registry-backed |
| SM | TODO | T | - | Y | - | documented-only |
| SMART | TODO | T | - | Y | - | documented-only |
| SMARTBROWSE | cmd_SMART_BROWSER | T | Y | Y | - | registry-backed |
| SMARTBROWSER | TODO | T | - | Y | - | documented-only |
| SMARTLIST | cmd_SMARTLIST | T | Y | Y | Y | registry-backed |
| SORT | cmd_SORT | T | Y | Y | Y | registry-backed |
| SQL | cmd_SQL | T | Y | Y | Y | registry-backed |
| SQLERASE | cmd_SQL_ERASE | T | Y | Y | Y | registry-backed |
| SQLHELP | cmd_SQLHELP | T | Y | Y | Y | registry-backed |
| SQLITE | cmd_SQLITE | T | Y | Y | Y | registry-backed |
| SQLSEL | cmd_SQL_SELECT | T | Y | Y | Y | registry-backed |
| SQLVER | cmd_SQLVER | T | Y | Y | - | registry-backed |
| STATUS | cmd_STATUS | T | Y | Y | - | registry-backed |
| STOP_ON_ERROR | cmd_STOP_ON_ERROR | T | Y | Y | - | registry-backed |
| STRCAT | cmd_CONCAT | T | Y | Y | - | registry-backed |
| STRUCT | cmd_STRUCT | T | Y | Y | - | registry-backed |
| STUDENTECHO | TODO | T | - | Y | - | documented-only |
| STUDENTHELLO | TODO | T | - | Y | - | documented-only |
| STU_REPEAT | TODO | T | - | Y | - | documented-only |
| STU_UPPER | TODO | T | - | Y | - | documented-only |
| SUM | cmd_SUM | T | Y | Y | - | registry-backed |
| TABLE | TODO | T | - | Y | - | documented-only |
| TABLEMETA | cmd_TABLEMETA | T | Y | Y | - | registry-backed |
| TABLE_BUFFER | cmd_TABLE_BUFFER | T | Y | Y | - | registry-backed |
| TEST | cmd_TEST | T | Y | Y | Y | registry-backed |
| TEXT | cmd_TEXT | T | Y | Y | - | registry-backed |
| TOP | cmd_TOP | T | Y | Y | - | registry-backed |
| TUPEXPORT | cmd_TUPEXPORT | T | Y | Y | Y | registry-backed |
| TUPLE | cmd_TUPLE | T | Y | Y | Y | registry-backed |
| TUPLEDELTA | cmd_TUPLEDELTA | T | Y | Y | - | registry-backed |
| TUPTALK | cmd_TUPTALK | T | Y | Y | Y | registry-backed |
| TUPVALIDATE | cmd_TUPVALIDATE | T | Y | Y | Y | registry-backed |
| TURBOPACK | cmd_TURBOPACK | T | Y | Y | - | registry-backed |
| TVISION | cmd_TVISION | T | Y | Y | - | registry-backed |
| UNDEFCMD | cmd_UNDEFCMD | T | Y | Y | - | registry-backed |
| UNDEFFN | cmd_UNDEFFN | T | Y | Y | - | registry-backed |
| UNDELETE | cmd_RECALL | T | Y | Y | - | registry-backed |
| UNLOCK | cmd_UNLOCK | T | Y | Y | Y | registry-backed |
| UNTIL | cmd_UNTIL | T | Y | Y | Y | registry-backed |
| UNTIL_BUFFER | cmd_UNTIL_BUFFER | T | Y | Y | - | registry-backed |
| UPDATE | cmd_SQL_UPDATE | T | Y | Y | Y | registry-backed |
| USER | cmd_USER | T | Y | Y | - | registry-backed |
| VALIDATE | cmd_VALIDATE | T | Y | Y | Y | registry-backed |
| VAR | cmd_VAR | T | Y | Y | Y | registry-backed |
| VDISK | cmd_VDISK | T | Y | Y | - | registry-backed |
| VERSION | cmd_VERSION | T | Y | Y | - | registry-backed |
| WA | cmd_WAMREPORT | T | Y | Y | - | registry-backed |
| WEB | cmd_WEB | T | Y | Y | Y | registry-backed |
| WHERE | cmd_WHERE | T | Y | Y | Y | registry-backed |
| WHERECACHE | TODO | T | Y | Y | Y | registry-backed (handler needs review) |
| WHILE_BUFFER | cmd_WHILE_BUFFER | T | Y | Y | - | registry-backed |
| WORKSPACE | cmd_WORKSPACE | T | Y | Y | Y | registry-backed |
| WSREPORT | cmd_WSREPORT | T | Y | Y | - | registry-backed |
| ZIP | cmd_ZIP | T | Y | Y | Y | registry-backed |
