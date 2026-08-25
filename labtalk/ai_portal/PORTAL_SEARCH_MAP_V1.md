# Portal search map -- go straight there, do not scan (portal doctrine)

**Status:** maintained navigation index. Owner: member.derald. Date 2026-08-08. Registered as
recall node `doc.search_map`; reached from `trigger.where_is` and `trigger.onboard`.

## Why this exists

Broad `find` / `grep` over the tree is slow (worse across the mount -- it times out) and wasteful.
It is the thesis's binding constraint in disguise: "a memory that cannot be reached is,
functionally, a memory that does not exist" (5.1). The recall graph already fixes this for
doctrine; this map extends it to **code and registry targets** an agent commonly needs. Navigate
by pointer, not by scan.

Pointers are **file + symbol/section** (durable), not raw line numbers (perishable, AIF-082). A
`~Lnn` hint may be given, but trust the symbol and re-measure the line.

## The maintenance rule (the anti-scan discipline)

**When you had to do a broad grep/find to locate something, add a row here.** That is the search
analog of "synapse it": the target that just cost you a scan becomes a one-hop crosslink for the
next agent. A scan you did not record is a scan the next agent repeats.

## Targets

| Looking for | Go straight to | Crosslinks |
| --- | --- | --- |
| BBS POST/REPLY grammar, attribution | `src/cli/cmd_bbs.cpp` -- `bbs_usage`, `do_post`, `split_subject_body`, `current_member` (~L91-163) | `docs/maintenance/DESIGN_bbs_pseudochat_two_lanes.md`; `docs/maintenance/LANE_L1_WRITE_ADAPTER_ASSIGNMENT_GROK_V1.md` |
| BBS store / post_new / kind | `src/bbs/bbs_store.cpp`, `src/bbs/bbs_server.cpp` | AIF-075 provenance |
| Coordination: quip, claim-aif, wake, roster | `tools/coordination/session_coordinator.py` -- `main` subparsers (~L444-456) | `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`; `COORDINATION_DEVELOPER_MANUAL_V1.md` |
| Project id registry (for report-audit) | `labtalk/registries/projects.yaml` (id -> root) | policy `labtalk/registries/ai_report_audit.yaml` |
| Report-audit envelope + validator | `labtalk/ai_portal/audit_trail.py` -- `validate_closeout`, `audit_closeouts`; contract `AI_REPORT_AUDIT_CONTRACT_V1.md` | run `python3 labtalk/ai_portal/audit_trail.py` |
| Seed budget gate + rule | `tools/staging/check_seed_budget.py`; `labtalk/ai_portal/TIER1_MAINTENANCE_CONTRACT_V1.md` | `AI_TIER1_SEED_V1.md` |
| Recall graph, resolver, synapse | `labtalk/registries/portal_recall_graph.yaml`; `labtalk/ai_portal/recall.py`; `SYNAPSE_CONCEPT_V1.md` | `AI_GLOSSARY_V1.md` |
| Editions / build / licensing | `docs/maintenance/licensing/EDITIONS_LICENSING_GROUND_TRUTH_V1.md` | `CMakeLists.txt` `DOTTALK_PRODUCT` (~L139-166); `config/package/*.manifest` |
| Two-atom ontology, coined terms | `docs/maintenance/COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md`; `AI_GLOSSARY_V1.md` | `SEED_RISE_PLAN_TWO_ATOM_V1.md` |
| Consolidation / triage value function | `tools/memory/README.md`, `consolidate.py`, `promote.py` | `FRONTAL_MEM_POINTER_V1.md` |
| Triage program dev lane (optimization PDLC) | `docs/maintenance/TRIAGE_OPTIMIZATION_PDLC_LANE_V1.md` | parent `project.ai_friendly.agent_memory`; M0 = `tools/memory/consolidate.py` |
| Root persistent-memory thesis | `labtalk/ai_portal/FRONTAL_MEM_POINTER_V1.md` (`trigger.persistent_memory`) | Frontal_Mem folder (`thesis_persistent_memory.md`) |
| Pre-push gate / portal gates | `tools/staging/prepush_gate.py` | `AI_SESSION_COORDINATION_PROTOCOL_V1.md` |
| Grok coworker lane (Lane 1 write adapter) | `docs/maintenance/GROK_PUSH_L1_WRITE_ADAPTER_V1.md`; spec `LANE_L1_WRITE_ADAPTER_ASSIGNMENT_GROK_V1.md` | `tools/memory/promote.py`; `assign_grok_pseudochat.dts` |
| Identity / members / agent login token (the lightweight member layer) | `src/cli/cmd_user.cpp` -- `USER LOGIN`/`AS`/`TOKEN`; `src/identity/identity_admin.cpp` -- `current_member`, `login` | AIF-075 attribution; `docs/maintenance/GOOD_NEIGHBOR_POLICY_V1.md`; team model in `AI_GLOSSARY_V1.md` |
| Site auth gateway / private-area + search design | `docs/maintenance/PRIVATE_SITE_AUTH_AND_SEARCH_SCOPE_V1.md` | gateway `tools/reports/serve_dynamic_reports.py`; auth `src/bbs/bbs_server.cpp`, `src/identity/identity_admin.cpp` |
| dottalkpp.com lean site (AIF-107 entry surface) | lane `docs/maintenance/AIF_107_LOW_KEY_ENTRY_SURFACE_LANE_V1.md`; closeout `SESSION_CLOSEOUT_LEAN_SITE_DEPLOY_2026-08-11.md` | source repo `deraldg/dottalkpp` at `D:\dev\dottalkpp-lean` (`build_lean_site.py` is the truth; emitted HTML never hand-edited; `check_site.py` gates); estate map in AI_README "Website And Publication Locations" |
| Build/run dottalkpp OUTSIDE Windows (sandbox, container, WSL) | `docs/agents/HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md` -- the recipe and its traps | `.github/workflows/ci.yml` job `ubuntu-core` (the build is CI-tested on every push to main); `CMakePresets.json` -- `core-base`, `core`, `core-vcpkg`, `wsl*`; `vcpkg.json` for the four core deps; recall `trigger.work_in_sandbox`. **`AI_README.md` "A sandbox is not the WSL host" says builds are impossible; that claim was measured false 2026-08-12 -- read the handoff, not the table.** |
| CMDHELP command rows: where `supported` comes from, and the "curated DOTREF help is pending" placeholder | `src/cli/cmdhelp.cpp` -- `collect_commands`, `generated_pending_summary`, `is_expression_function_name` | catalogs `include/dotref.hpp`, `foxref.hpp`, `edref.hpp` (compiled IN -- a stale exe publishes a stale catalog); registry `src/cli/shell_commands.cpp`; ordering gate `tools/coordination/help_build_order_check.py` |


## How to use instead of grep

1. Resolve by intent first: `python3 labtalk/ai_portal/recall.py <trigger>` returns the smallest
   working set, measured. `trigger.where_is` surfaces this map.
2. If the target is in the table, open the named file at the named symbol -- do not scan.
3. Only grep when the target is NOT here, and then **add a row** so the next agent does not.
