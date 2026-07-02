SYSTEM_METADATA_v4_safe10_FIXED bundle

Run order:
  DO SYSTEM_METADATA_SCHEMA_v4_safe10_FIXED
  DO SYSTEM_METADATA_SEED_v4_safe10_FIXED
  DO SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED

Physical table names used by the fixed scripts:
  SYSCMD     -> SYSTEM_COMMANDS
  SYSENTVAR  -> SYSTEM_ENTRY_VARIANTS
  SYSSUBCMD  -> SYSTEM_SUBCOMMANDS
  SYSFUNC    -> SYSTEM_FUNCTIONS
  SYSMSG     -> SYSTEM_MESSAGES
  SYSHELP    -> SYSTEM_HELP_TEXT
  SYSARGS    -> SYSTEM_ARGUMENTS
  SYSFLDDIC  -> SYSTEM_FIELD_DICT

Notes:
  - Field tokens remain <= 10 visible characters.
  - The scripts use the canonical metadata lane (`DO metadata`).
  - Schema cleanup includes DBF/CDX/DTX sidecars.
