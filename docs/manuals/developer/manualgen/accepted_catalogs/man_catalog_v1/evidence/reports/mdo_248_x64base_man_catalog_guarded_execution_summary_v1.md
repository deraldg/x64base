# MDO-248 x64base MAN* Catalog Guarded Execution Summary v1.2

Status: X64BASE_MAN_CATALOG_EXECUTION_COMPLETED_DBFS_OBSERVED

## Scope

MDO-248 is authorized only for the staged MAN* manualgen catalog lane. It creates execution-ready DotScript artifacts and can optionally run them against an isolated execution DBF path.

## Preconditions

- MDO-247 status: X64BASE_MAN_CATALOG_EXECUTION_AUTHORITY_DECISION_READY_EXECUTION_NOT_AUTHORIZED
- AuthorizeCatalogExecution: 1
- RunDotTalk: 1
- UseDatarunRuntime: 1
- CopyBuildToBin: 1

## Execution artifacts

- execution directory: D:\code\ccode\docs\manuals\developer\manualgen\generated\x64base_man_catalog_execution_v1
- schema DotScript: docs\manuals\developer\manualgen\generated\x64base_man_catalog_execution_v1\dts\MDO_248_MAN_SCHEMA_EXECUTE_v1.dts
- import DotScript: docs\manuals\developer\manualgen\generated\x64base_man_catalog_execution_v1\dts\MDO_248_MAN_IMPORT_EXECUTE_v1.dts
- validate DotScript: docs\manuals\developer\manualgen\generated\x64base_man_catalog_execution_v1\dts\MDO_248_MAN_VALIDATE_EXECUTE_v1.dts
- field mapping report: reports/mdo_248_field_mapping_v1.csv

## Observed execution

- execution attempted: 1
- DotTalk executable: D:\code\ccode\dottalkpp\bin\dottalkpp.exe
- DotTalk working directory: D:\code\ccode\dottalkpp\data
- DotTalk exit code: -1073741819
- x64base MAN*.dbf files observed: 8
- DBF writes observed in isolated MAN* execution workspace: 8

## Boundary

- HELP mutation: 0
- META mutation: 0
- CMDHELPCHK mutation: 0
- source mutation: 0
- runtime application data mutation: 0
- publication replacement: 0
- media mutation: 0
- protected-system mutations: 0

## Fail reasons

None.
