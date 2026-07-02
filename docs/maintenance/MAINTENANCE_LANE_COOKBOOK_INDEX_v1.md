# Maintenance Lane Cookbook Index v1

This index lists the DotTalk++ maintenance / Blackbox lanes. Each lane follows the same model: data in, blackbox process, information out, and controls.

Shared workflow:

- `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

| Lane | Runtime surface | Primary next step |
|---|---|---|
| comments | comments workspace; BBOX crosswalk/reference surface | comments-to-HELP crosswalk audit |
| help | HELP; DOTHELP; CMDHELP | HELP/CMDHELP/DOTREF pipeline cookbook and router audit |
| cmdhelpchk | CMDHELPCHK | CMDHELPCHK v2 crosswalk alignment |
| manualgen | MANUAL | manualgen cookbook integration with maintenance root |
| datadict | DDICT | data dictionary system manifest stationing |
| messaging | SET LANGUAGE/LOCALE; future MSG inspector | messaging source extraction/readiness review |
| contracts | MAINT CONTRACTS | generated contract inventory and registry drift review |
| blackbox | BBOX | BBOX help/doc alignment against live command |
| maintenance | MAINT | MAINT help/doc alignment against live command |

No executable maintenance scripts are introduced by MDO-303. This is cookbook seeding only.
