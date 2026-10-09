# LabTalk Portal Truth Audit

Generated: 2026-09-15T17:47:48

## Summary

- Sections: 15
- Items: 304
- Runnable items: 33
- Proof-like records: 129
- Missing paths: 18
- Duplicate item IDs: 0
- AI report audit findings: 0

## Missing Paths

| Item | Field | Path |
|---|---|---|
| `project.labtalk.staging` | `root` | `C:\labtalk` |
| `project.labtalk.staging` | `docs` | `C:\labtalk\README.md` |
| `project.labtalk.staging` | `docs` | `C:\labtalk\STAGING_POLICY.md` |
| `project.labtalk.staging` | `docs` | `C:\labtalk\publication\labtalk-website-pipeline.md` |
| `project.labtalk.staging` | `docs` | `C:\labtalk\registries\projects.yaml` |
| `project.labtalk.staging` | `docs` | `C:\labtalk\registries\intake.yaml` |
| `project.db_converter` | `root` | `D:\code\ccode\Side Projects\DB_Converter` |
| `project.db_converter` | `docs` | `D:\code\ccode\Side Projects\DB_Converter\README.md` |
| `project.db_converter` | `launchers` | `D:\code\ccode\Side Projects\DB_Converter\Start-DBConverter.ps1` |
| `project.sqlite_gui` | `root` | `D:\code\ccode\sqlite-gui` |
| `project.x64base.identity` | `docs` | `D:\code\ccode\docs\## AI Portal re-examination.txt` |
| `lesson.student.cursor_versus_set` | `path` | `D:\code\ccode\labtalk\lessons\student\cursor_versus_set_v0.md` |
| `lesson.student.properties_of_valid_data` | `path` | `D:\code\ccode\labtalk\lessons\student\properties_of_valid_data_v0.md` |
| `report.aif_rulings` | `source` | `D:\code\ccode\labtalk\docs\maintenance\AIF_*RULING_SHEET*.md + labtalk\ai_portal\TIER0_STATE.md` |
| `launcher.wx` | `path` | `D:\code\ccode\wx.run.ps1` |
| `launcher.wx_next` | `path` | `D:\code\ccode\wx.next.run.ps1` |
| `launcher.run_wx` | `path` | `D:\code\ccode\run-wx.ps1` |
| `launcher.run_wx_next` | `path` | `D:\code\ccode\run-wx-next.ps1` |

## Duplicate IDs

No duplicate item IDs found.

## AI Report Identity and Provenance

- Schema: `ai-report-audit-v1`
- Enforced closeouts: 131
- Valid closeouts: 131
- Grandfathered closeouts: 9
- Findings: 0

All enforced AI-authored closeouts have valid identity and provenance envelopes.

## Sections

| Section | Registry |
|---|---|
| `portal.docs` | inline |
| `portal.ai_friendly` | inline |
| `portal.ai_portal_work` | ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml` |
| `portal.agent_assignment_links` | ok: `D:\code\ccode\labtalk\registries\agent_assignment_links.yaml` |
| `portal.apps` | ok: `D:\code\ccode\labtalk\registries\apps.yaml` |
| `portal.projects` | ok: `D:\code\ccode\labtalk\registries\projects.yaml` |
| `portal.lms` | ok: `D:\code\ccode\labtalk\registries\lms.yaml` |
| `portal.labs` | ok: `D:\code\ccode\labtalk\registries\labs.yaml` |
| `portal.lessons` | ok: `D:\code\ccode\labtalk\registries\lessons.yaml` |
| `portal.concepts` | ok: `D:\code\ccode\labtalk\registries\concepts.yaml` |
| `portal.proofs` | ok: `D:\code\ccode\labtalk\registries\proofs.yaml` |
| `portal.reports` | inline |
| `portal.diagrams` | inline |
| `portal.runtime` | inline |
| `portal.launchers` | inline |

## Items

| Item | Section | Kind | Paths |
|---|---|---|---|
| `doc.readme` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\README.md` |
| `doc.campus_architecture` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\LABTALK_CAMPUS_ARCHITECTURE_v0.md` |
| `doc.education_map` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\LABTALK_EDUCATION_MAP_v0.md` |
| `doc.portal_concept` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\LABTALK_PORTAL_CONCEPT_v0.md` |
| `doc.sdlc_framework` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\LABTALK_SDLC_FRAMEWORK_v0.md` |
| `doc.dottalkpp_sdlc_charter` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\DOTTALKPP_SDLC_CHARTER_v0.md` |
| `doc.sdlc_pdlc_planning` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\docs\planning\SDLC_PDLC_PLANNING_ADOPTION_v0.md` |
| `doc.developer_profile` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\LABTALK_DEVELOPER_PROFILE_v0.md` |
| `doc.database_literacy_starter` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\labs\database_literacy_starter\LAB_DATABASE_LITERACY_STARTER_v0.md` |
| `doc.selfdoc_comments_to_contracts` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\labs\self_documenting_systems\LAB_SELFDOC_COMMENTS_TO_CONTRACTS_v0.md` |
| `doc.manualgen_product_map` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\products\manualgen_product_map_v0.md` |
| `doc.manualgen_product_board` | `portal.docs` | `html` | `path` ok: `D:\code\ccode\labtalk\products\manualgen_product_board_v0.html` |
| `doc.manualgen_product_preservation` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\products\manualgen_product_preservation_v0.md` |
| `doc.x64base_project_truth` | `portal.docs` | `mdx` | `path` ok: `D:\dev\x64base-site\content\docs\dev\project-truth.mdx` |
| `doc.x64base_labtalk_sdlc` | `portal.docs` | `mdx` | `path` ok: `D:\dev\x64base-site\content\docs\labtalk\sdlc.mdx` |
| `doc.x64base_selfdoc_lane` | `portal.docs` | `mdx` | `path` ok: `D:\dev\x64base-site\content\docs\labtalk\selfdoc-lane.mdx` |
| `doc.x64base_selfdoc_publication` | `portal.docs` | `mdx` | `path` ok: `D:\dev\x64base-site\content\docs\dev\selfdoc-website-publication.mdx` |
| `doc.portal_truth_audit` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\labtalk\reports\portal\portal_truth_audit_latest.md` |
| `doc.x64base_campus_mission_vision` | `portal.docs` | `markdown` | `path` ok: `D:\code\ccode\dottalkpp\docs\architecture\X64BASE_LABORATORY_CAMPUS_MISSION_VISION_V1.md` |
| `doc.ai_portal_root_entry` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\AI_PORTAL.md` |
| `doc.ai_root_readme` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\AI_README.md` |
| `doc.ai_rules` | `portal.ai_friendly` | `text` | `path` ok: `D:\code\ccode\rules\rules.txt` |
| `doc.ai_readme_clobber_rule` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\rules\README_CLOBBER_PROTECTION_RULE.md` |
| `doc.ai_assimilation_portal` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_PORTAL_V1.md` |
| `doc.ai_assimilation_book` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_BOOK_V1.md` |
| `doc.ai_friendly_dashboard` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\docs\ai-friendly\AI_FRIENDLY_DASHBOARD_V1.md` |
| `doc.ai_friendly_manifest` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\docs\ai-friendly\AI_FRIENDLY_LANE_MANIFEST_V1.md` |
| `doc.ai_friendly_workflow` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\docs\ai-friendly\AI_FRIENDLY_WORKFLOW_V1.md` |
| `doc.ai_interaction_intake` | `portal.ai_friendly` | `markdown` | `path` ok: `D:\code\ccode\docs\ai-friendly\AI_INTERACTION_INTAKE_QUEUE_V1.md` |
| `runtime.maint_ai` | `portal.ai_friendly` | `dottalk_command` | none |
| `runtime.maint_ai_assimilate` | `portal.ai_friendly` | `dottalk_command` | none |
| `runtime.maint_ai_visibility` | `portal.ai_friendly` | `dottalk_command` | none |
| `seed.ai_portal.development_source_authority.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `seed.ai_portal.branch_continuity.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `seed.ai_portal.publication_chain.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `seed.ai_portal.permission_boundary.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `seed.ai_portal.dottalkpp_runtime_learning.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`<br>`evidence` ok: `D:\code\ccode\DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`<br>`evidence` ok: `D:\code\ccode\src\cli\cmd_dotscript.cpp`<br>`evidence` ok: `D:\code\ccode\docs\maintenance\MAINTENANCE_SCRIPT_ROOT_POLICY_v1.md` |
| `seed.ai_portal.dotscript_no_guessing.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md` |
| `seed.ai_portal.dotscript_execution_gate.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md` |
| `seed.ai_portal.source_mutation_contract_preflight.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`<br>`evidence` ok: `D:\code\ccode\docs\contracts\README.md`<br>`evidence` ok: `D:\code\ccode\docs\contracts\CONTRACT_REGISTRY_V1.md`<br>`evidence` ok: `D:\code\ccode\docs\contracts\CONTRACT_LIFECYCLE_V1.md`<br>`evidence` ok: `D:\code\ccode\docs\contracts\CONTRACT_INTAKE_QUEUE_V1.md` |
| `seed.ai_portal.external_ai_change_package.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\EXTERNAL_AI_CHANGE_PACKAGE_V1.md` |
| `seed.ai_portal.sdlc_fast_start.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\SDLC_FAST_START_SEED_V1.md`<br>`evidence` ok: `D:\code\ccode\docs\maintenance\DOTTALKPP_SDLC_CHARTER_v0.md`<br>`evidence` ok: `D:\code\ccode\labtalk\LABTALK_SDLC_FRAMEWORK_v0.md`<br>`evidence` ok: `D:\code\ccode\docs\planning\SDLC_PDLC_PLANNING_ADOPTION_v0.md` |
| `seed.ai_portal.scope_calibration.v1` | `portal.ai_portal_work` | `mandatory_context_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\SCOPE_CALIBRATION_SEED_V1.md` |
| `recipe.ai_portal.x64base_development_change.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `recipe.ai_portal.x64base_stage_and_publish.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `recipe.ai_portal.reconcile_public_only_change.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `recipe.ai_portal.x64base_public_documentation.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| `recipe.ai_portal.dotscript_authoring_readiness.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md` |
| `recipe.ai_portal.source_mutation_contract_preflight.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md` |
| `recipe.ai_portal.external_ai_change_package_intake.v1` | `portal.ai_portal_work` | `task_recipe_seed` | `path` ok: `D:\code\ccode\labtalk\ai_portal\EXTERNAL_AI_CHANGE_PACKAGE_V1.md` |
| `probe.ai_portal.dotscript_startup_readiness.v1` | `portal.ai_portal_work` | `dottalk_script` | `script` ok: `D:\code\ccode\labtalk\ai_portal\probes\dotscript_startup_readiness_v1.dts` |
| `probe.ai_portal.maint_ai_portal_readback.v1` | `portal.ai_portal_work` | `dottalk_script` | `script` ok: `D:\code\ccode\labtalk\ai_portal\probes\maint_ai_portal_readback_v1.dts` |
| `report.ai_portal.reonboarding_assessment.2026_07_29` | `portal.ai_portal_work` | `onboarding_assessment` | `path` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md` |
| `lane.ai_portal.hardening` | `portal.ai_portal_work` | `work_lane` | `path` ok: `D:\code\ccode\labtalk\ai_portal\README.md` |
| `concept.ai_portal.seed_connection_prototype.v1` | `portal.ai_portal_work` | `prototype_direction` | `path` ok: `D:\code\ccode\labtalk\ai_portal\SEED_CONNECTION_PROTOTYPE_NOTE_V1.md` |
| `plan.ai_portal.hardening.v1` | `portal.ai_portal_work` | `lane_plan` | `path` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_HARDENING_LANE_V1.md` |
| `aiportal.gate.aph0` | `portal.ai_portal_work` | `lane_gate` | none |
| `aiportal.gate.aph1` | `portal.ai_portal_work` | `lane_gate` | none |
| `aiportal.gate.aph2` | `portal.ai_portal_work` | `lane_gate` | none |
| `aiportal.gate.aph3` | `portal.ai_portal_work` | `lane_gate` | none |
| `aiportal.gate.aph4` | `portal.ai_portal_work` | `lane_gate` | none |
| `aiportal.gate.aph5` | `portal.ai_portal_work` | `lane_gate` | none |
| `aiportal.gate.aph6` | `portal.ai_portal_work` | `lane_gate` | none |
| `agent_assignment_link.contract` | `portal.agent_assignment_links` | `markdown` | `path` ok: `D:\code\ccode\docs\contracts\AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md` |
| `agent_assignment_link.maintenance_manual` | `portal.agent_assignment_links` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\AI_AGENT_ASSIGNMENT_LINK_MAINTENANCE_MANUAL_V1.md` |
| `agent_assignment_link.pfd` | `portal.agent_assignment_links` | `diagram` | `path` ok: `D:\code\ccode\labtalk\diagrams\ai_agent_assignment_link_pfd_v1.mmd` |
| `agent_assignment_link.dfd` | `portal.agent_assignment_links` | `diagram` | `path` ok: `D:\code\ccode\labtalk\diagrams\ai_agent_assignment_link_dfd_v1.mmd` |
| `agent_assignment_link.schema` | `portal.agent_assignment_links` | `json` | `path` ok: `D:\code\ccode\dottalkpp\data\schemas\syschatlnk_v1.schema.json` |
| `agent_assignment_link.regression` | `portal.agent_assignment_links` | `dottalk_script` | `path` ok: `D:\code\ccode\dottalkpp\data\scripts\ddl\syschatlnk_x64_regression.dts`<br>`script` ok: `D:\code\ccode\dottalkpp\data\scripts\ddl\syschatlnk_x64_regression.dts` |
| `agent_assignment_link.relational_plan` | `portal.agent_assignment_links` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md` |
| `agent_assignment_link.relational_erd` | `portal.agent_assignment_links` | `diagram` | `path` ok: `D:\code\ccode\labtalk\diagrams\ai_portal_bbs_pseudo_chat_relational_erd_v1.mmd` |
| `agent_assignment_link.relational_dfd` | `portal.agent_assignment_links` | `diagram` | `path` ok: `D:\code\ccode\labtalk\diagrams\ai_portal_bbs_pseudo_chat_relational_dfd_v1.mmd` |
| `agent_assignment_link.relational_pfd` | `portal.agent_assignment_links` | `diagram` | `path` ok: `D:\code\ccode\labtalk\diagrams\ai_portal_bbs_pseudo_chat_relational_pfd_v1.mmd` |
| `agent_assignment_link.aif_lane` | `portal.agent_assignment_links` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\AI_SYSTEMS_INTEGRATION_SDLC_CHARTER_V1.md` |
| `agent_assignment_link.system_crosswalk` | `portal.agent_assignment_links` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\AI_SYSTEMS_CROSSWALK_V1.md` |
| `agent_assignment_link.run` | `portal.agent_assignment_links` | `yaml` | `path` ok: `D:\code\ccode\labtalk\registries\runs.d\AIPR-20260816-001.yaml` |
| `agent_assignment_link.relational_plan_run` | `portal.agent_assignment_links` | `yaml` | `path` ok: `D:\code\ccode\labtalk\registries\runs.d\AIPR-20260816-002.yaml` |
| `agent_assignment_link.closeout` | `portal.agent_assignment_links` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_AGENT_ASSIGNMENT_LINK_AIF086_2026-08-16.md` |
| `agent_assignment_link.proof_registry` | `portal.agent_assignment_links` | `yaml` | `path` ok: `D:\code\ccode\labtalk\registries\proofs.d\proof.ai.agent_assignment_link_x64.yaml` |
| `agent_assignment_link.proof_transcript` | `portal.agent_assignment_links` | `text` | `path` ok: `D:\code\ccode\labtalk\proofs\runs\20260816_101951_agent_assignment_link_regression.txt` |
| `agent_assignment_link.identity_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.conversation_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.bbs_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.ui_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.v2_participant_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.v2_provider_ui_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.v2_bbs_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `agent_assignment_link.v2_message_provenance_route` | `portal.agent_assignment_links` | `relation_route` | none |
| `app.dottalkpp.sql_family` | `portal.apps` | `query_surface` | `root` ok: `D:\code\ccode\src\cli` |
| `app.dottalkpp.runtime` | `portal.apps` | `runtime_lab` | `root` ok: `D:\code\ccode\src` |
| `app.dottalkpp.help` | `portal.apps` | `help_lab` | `root` ok: `D:\code\ccode\src\cli` |
| `app.dottalkpp.selfdoc` | `portal.apps` | `proof_lab` | `root` ok: `D:\code\ccode` |
| `app.dottalkpp.ai_friendly` | `portal.apps` | `ai_visibility_lab` | `root` ok: `D:\code\ccode\docs\ai-friendly` |
| `app.labtalk.ai_portal` | `portal.apps` | `experimental_context_lab` | `root` ok: `D:\code\ccode\labtalk\ai_portal` |
| `app.labtalk.case_library` | `portal.apps` | `case_library` | `root` ok: `D:\code\ccode\docs\cases` |
| `app.labtalk.dataset_library` | `portal.apps` | `dataset_library` | `root` ok: `D:\code\ccode\dottalkpp\data` |
| `app.labtalk.afb` | `portal.apps` | `local_ai_lab` | `root` ok: `D:\code` |
| `project.x64base.runtime` | `portal.projects` | `runtime_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\README.md`<br>`docs` ok: `D:\code\ccode\AI_PORTAL.md`<br>`docs` ok: `D:\code\ccode\docs\governance\REPO_BOUNDARIES_RUNTIME_GUI_LABTALK_v1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTTALKPP_SDLC_CHARTER_v0.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DDL_SCHEMA_PDLC_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\SQLSEL_PDLC_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\BUFFER_VISIBILITY_TWO_FAMILIES_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\EVALUATOR_DIFFERENTIAL_HARNESS_SCOPE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\EXPORT_SDF_PDLC_CLOSEOUT_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\X32_TRADITIONAL_XBASE_SUPPORT_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\ARCTICTALK_RETRO_TUI_WORKBENCH_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\RETRO_LANE_CHARTER_20260726.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\RETRO_LANE_PROPOSAL_V2_20260726.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\MEMO_OBJECT_CHALLENGE_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\MEMO_RESIDENT_MINIDB_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AI_MEMO_WAL_ATOMICITY_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\WORKSPACE_MEMO_RESIDENCE_PLAN_V1.md` |
| `project.x64base.sqlsel` | `portal.projects` | `pdlc_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\SQLSEL_PDLC_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\manuals\user\sqlsel.md` |
| `project.x64base.public_staging` | `portal.projects` | `publication_staging_project` | `root` ok: `C:\x64base` |
| `project.labtalk.campus` | `portal.projects` | `campus_project` | `root` ok: `D:\code\ccode\labtalk`<br>`docs` ok: `D:\code\ccode\labtalk\README.md`<br>`docs` ok: `D:\code\ccode\labtalk\portal\README.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\README.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\ROOT_AI_PORTAL_ENTRY_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\SDLC_FAST_START_SEED_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\EXTERNAL_AI_CHANGE_PACKAGE_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_HARDENING_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\LABTALK_CAMPUS_ARCHITECTURE_v0.md` |
| `project.labtalk.lms` | `portal.projects` | `integration_project` | `root` ok: `D:\code\ccode\labtalk\lms`<br>`docs` ok: `D:\code\ccode\labtalk\lms\README.md`<br>`docs` ok: `D:\code\ccode\labtalk\lms\contracts\lms_message_v1.schema.json` |
| `project.labtalk.staging` | `portal.projects` | `staging_project` | `root` missing: `C:\labtalk`<br>`docs` missing: `C:\labtalk\README.md`<br>`docs` missing: `C:\labtalk\STAGING_POLICY.md`<br>`docs` missing: `C:\labtalk\publication\labtalk-website-pipeline.md`<br>`docs` missing: `C:\labtalk\registries\projects.yaml`<br>`docs` missing: `C:\labtalk\registries\intake.yaml` |
| `project.x64base.website` | `portal.projects` | `publication_project` | `root` ok: `D:\dev\x64base-site`<br>`docs` ok: `D:\dev\x64base-site\README.md`<br>`docs` ok: `D:\code\ccode\docs\contracts\WEBSITE_SELFDOC_PUBLICATION_CONTRACT_V1.md` |
| `project.ai_friendly` | `portal.projects` | `knowledge_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\AI_PORTAL.md`<br>`docs` ok: `D:\code\ccode\AI_README.md`<br>`docs` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_PORTAL_V1.md`<br>`docs` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_BOOK_V1.md`<br>`docs` ok: `D:\code\ccode\docs\ai-friendly\AI_FRIENDLY_DASHBOARD_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_HARDENING_LANE_V1.md` |
| `project.ai_friendly.agent_memory` | `portal.projects` | `knowledge_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\EXTERNAL_AGENT_MEMORY_LANE_V1.md` |
| `project.ai_systems.integration` | `portal.projects` | `sdlc_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AI_SYSTEMS_INTEGRATION_SDLC_CHARTER_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AI_SYSTEMS_CROSSWALK_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AI_SYSTEMS_INTEGRATION_DISCOVERY_AND_NEEDS_ASSESSMENT_M1_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AI_SYSTEMS_INTEGRATION_REQUIREMENTS_V1.md`<br>`docs` ok: `D:\code\ccode\docs\contracts\AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AI_AGENT_ASSIGNMENT_LINK_MAINTENANCE_MANUAL_V1.md`<br>`docs` ok: `D:\code\ccode\dottalkpp\data\schemas\syschatlnk_v1.schema.json`<br>`docs` ok: `D:\code\ccode\labtalk\registries\agent_assignment_links.yaml`<br>`docs` ok: `D:\code\ccode\labtalk\diagrams\ai_agent_assignment_link_pfd_v1.mmd`<br>`docs` ok: `D:\code\ccode\labtalk\diagrams\ai_agent_assignment_link_dfd_v1.mmd`<br>`docs` ok: `D:\code\ccode\docs\contracts\TRESPASS_AND_DELEGATED_AUTHORIZATION_CONTRACT_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_SYSTEMS_INTEGRATION_SDLC_M0_2026-08-03.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_SYSTEMS_INTEGRATION_SDLC_M1_2026-08-03.md`<br>`docs` ok: `D:\code\ccode\labtalk\LABTALK_SDLC_FRAMEWORK_v0.md` |
| `project.bbs.cooperation` | `portal.projects` | `integration_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\BBS_AGENCY_LEGS_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\ai-friendly\AGENCY_MODEL_V1.md`<br>`docs` ok: `D:\code\ccode\docs\ai-friendly\PSEUDO_CHAT_BOARD.md` |
| `project.pycrud` | `portal.projects` | `companion_app_project` | `root` ok: `D:\code\ccode\pycrud`<br>`docs` ok: `D:\code\ccode\pycrud\README.md`<br>`docs` ok: `D:\code\ccode\pycrud\pydottalk_api\README.md`<br>`launchers` ok: `D:\code\ccode\run-pycrud.ps1` |
| `project.pydottalk` | `portal.projects` | `binding_project` | `root` ok: `D:\code\ccode\bindings\pydottalk`<br>`docs` ok: `D:\code\ccode\bindings\PYDOTTALK_STARTER_README.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\PYDOTTALK_SDLC_CHARTER_v0.md`<br>`docs` ok: `D:\code\ccode\docs\contracts\PYTHON_BINDING_TRUST_CONTRACT_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\PYDOTTALK_CAPABILITY_REVIEW_AND_CRUD_READINESS_V1.md`<br>`launchers` ok: `D:\code\ccode\build_pydottalk.ps1`<br>`launchers` ok: `D:\code\ccode\run-pydottalk.ps1` |
| `project.db_converter` | `portal.projects` | `migration_project` | `root` missing: `D:\code\ccode\Side Projects\DB_Converter`<br>`docs` missing: `D:\code\ccode\Side Projects\DB_Converter\README.md`<br>`launchers` missing: `D:\code\ccode\Side Projects\DB_Converter\Start-DBConverter.ps1` |
| `project.dottalk_webui` | `portal.projects` | `web_ui_project` | `root` ok: `D:\code\ccode\dottalk-webui`<br>`docs` ok: `D:\code\ccode\dottalk-webui\selfdoc-lane.html` |
| `project.sqlite_gui` | `portal.projects` | `gui_project` | `root` missing: `D:\code\ccode\sqlite-gui` |
| `project.x64base.dotscript` | `portal.projects` | `language_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTSCRIPT_ARRAYS_SPEC_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTSCRIPT_ARRAYS_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTSCRIPT_STOP_ON_ERROR_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTSCRIPT_FUNCTION_SURFACE_PRIOR_ART_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTSCRIPT_BUILD_PLAN_V1.md` |
| `project.labtalk.pdlc` | `portal.projects` | `methodology_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\PDLC_STUDENT_WORKING_MODEL_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\SCOPE_CALIBRATION_SEED_V1.md` |
| `project.labtalk.historical_database_migration` | `portal.projects` | `pdlc_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\HISTORICAL_DATABASE_MIGRATION_PDLC_PROJECT_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\CASCADE_ERP_METADATA_ETL_LEARNING_GOLD_STANDARD_LANE_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\LABTALK_SDLC_FRAMEWORK_v0.md`<br>`docs` ok: `D:\code\ccode\labtalk\registries\projects.yaml` |
| `project.labtalk.sdlc` | `portal.projects` | `methodology_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\DOTTALKPP_SDLC_CHARTER_v0.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`<br>`docs` ok: `D:\code\ccode\labtalk\ai_portal\SCOPE_CALIBRATION_SEED_V1.md`<br>`docs` ok: `D:\code\ccode\AI_PORTAL.md` |
| `project.x64base.identity` | `portal.projects` | `governance_project` | `root` ok: `D:\code\ccode`<br>`docs` ok: `D:\code\ccode\docs\maintenance\IDENTITY_RBAC_MANAGEMENT_LANE_V1.md`<br>`docs` missing: `D:\code\ccode\docs\## AI Portal re-examination.txt`<br>`docs` ok: `D:\code\ccode\src\cli\cmd_security.cpp`<br>`docs` ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml` |
| `project.x64base.gui` | `portal.projects` | `gui_project` | `root` ok: `D:\code\ccode\gui`<br>`docs` ok: `D:\code\ccode\gui\README.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AIF120_DESIGN_TABLE_CONTRACT_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AIF120_LANE_STATUS_AND_FIXTURES_V1.md`<br>`docs` ok: `D:\code\ccode\docs\maintenance\AIF120_PROJECT_PROMOTION_V1.md` |
| `lms.lane.overview` | `portal.lms` | `markdown` | `path` ok: `D:\code\ccode\labtalk\lms\README.md` |
| `lms.message.contract` | `portal.lms` | `json_schema` | `path` ok: `D:\code\ccode\labtalk\lms\contracts\lms_message_v1.schema.json` |
| `lms.outbox` | `portal.lms` | `directory` | `path` ok: `D:\code\ccode\labtalk\lms\queue\outbox` |
| `lms.pipe.status` | `portal.lms` | `python_tool` | `script` ok: `D:\code\ccode\src\labtalk\lms\cli.py` |
| `lms.moodle.transport` | `portal.lms` | `reserved_integration` | none |
| `lab.database_literacy.starter` | `portal.labs` | `registry_item` | `script` ok: `D:\code\ccode\labtalk\labs\database_literacy_starter\database_literacy_starter_v0.dts`<br>`evidence` ok: `D:\code\ccode\include\edref.hpp`<br>`evidence` ok: `D:\code\ccode\docs\cases\CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB.md`<br>`evidence` ok: `D:\code\ccode\docs\cases\CASE_ENG_020_SEEK_VS_SCAN.md` |
| `lab.selfdoc.comments_to_contracts` | `portal.labs` | `registry_item` | `script` ok: `D:\code\ccode\labtalk\labs\self_documenting_systems\run_selfdoc_first_lab.ps1`<br>`evidence` ok: `D:\code\ccode\src\cli\cmdhelp.cpp`<br>`evidence` ok: `D:\code\ccode\src\cli\command_helpchk.cpp`<br>`evidence` ok: `D:\code\ccode\tools\contracts\contract_scan.py`<br>`evidence` ok: `D:\code\ccode\tools\comments\upsert_source_comment_contract.py` |
| `lab.history.data_systems_trail` | `portal.labs` | `registry_item` | none |
| `lab.database.acid_contract` | `portal.labs` | `registry_item` | `evidence` ok: `D:\code\ccode\labtalk\docs\acid\acid_test_results_beta-0.json` |
| `lesson.career.a_documented_option_is_not_an_honoured_option` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\a_documented_option_is_not_an_honoured_option_v0.md` |
| `lesson.career.a_gitignored_path_is_invisible_to_your_sweep` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\a_gitignored_path_is_invisible_to_your_sweep_v0.md` |
| `lesson.career.a_script_never_run_is_not_evidence` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\a_script_never_run_is_not_evidence_v0.md` |
| `lesson.career.a_wrong_answer_that_looks_right` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\a_wrong_answer_that_looks_right_v0.md` |
| `lesson.career.discovery_by_documentation` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\discovery_by_documentation_v0.md` |
| `lesson.career.entities_and_the_bridge` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\entities_and_the_bridge_v0.md` |
| `lesson.career.legacy_systems_as_labs` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\legacy_systems_as_labs_v0.md`<br>`evidence` ok: `D:\code\ccode\docs\media\LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx` |
| `lesson.career.proof_first_development` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\proof_first_development_v0.md` |
| `lesson.career.the_tree_already_has_it` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\career\the_tree_already_has_it_v0.md` |
| `lesson.student.agency_who_may_act` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\student\agency_who_may_act_v0.md` |
| `lesson.student.cursor_versus_set` | `portal.lessons` | `lesson` | `path` missing: `D:\code\ccode\labtalk\lessons\student\cursor_versus_set_v0.md` |
| `lesson.student.database_history_trail` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\student\data_systems_history_trail_v0.md`<br>`evidence` ok: `D:\code\ccode\docs\media\LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx`<br>`evidence` ok: `D:\code\ccode\labtalk\LABTALK_EDUCATION_MAP_v0.md` |
| `lesson.student.properties_of_valid_data` | `portal.lessons` | `lesson` | `path` missing: `D:\code\ccode\labtalk\lessons\student\properties_of_valid_data_v0.md` |
| `lesson.student.records_fields_tables` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\student\records_fields_tables_v0.md` |
| `lesson.student.selfdoc_comments_to_help` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\student\comments_to_contracts_to_help_v0.md` |
| `lesson.student.three_things_called_a_set` | `portal.lessons` | `lesson` | `path` ok: `D:\code\ccode\labtalk\lessons\student\three_things_called_a_set_v0.md` |
| `concept.database.table` | `portal.concepts` | `registry_item` | none |
| `concept.database.record` | `portal.concepts` | `registry_item` | none |
| `concept.database.field` | `portal.concepts` | `registry_item` | none |
| `concept.database.schema` | `portal.concepts` | `registry_item` | none |
| `concept.database.index` | `portal.concepts` | `registry_item` | none |
| `concept.database.network` | `portal.concepts` | `registry_item` | none |
| `concept.database.xbase` | `portal.concepts` | `registry_item` | none |
| `concept.runtime.state` | `portal.concepts` | `registry_item` | none |
| `concept.runtime.command_shell` | `portal.concepts` | `registry_item` | none |
| `concept.source.comments` | `portal.concepts` | `registry_item` | none |
| `concept.contract.usage` | `portal.concepts` | `registry_item` | none |
| `concept.help.runtime` | `portal.concepts` | `registry_item` | none |
| `concept.selfdoc.validation` | `portal.concepts` | `registry_item` | none |
| `concept.metadata.catalog` | `portal.concepts` | `registry_item` | none |
| `concept.storage.file` | `portal.concepts` | `registry_item` | none |
| `concept.storage.fixed_record` | `portal.concepts` | `registry_item` | none |
| `concept.case.history` | `portal.concepts` | `registry_item` | none |
| `concept.case.engineering` | `portal.concepts` | `registry_item` | none |
| `concept.evidence.review` | `portal.concepts` | `registry_item` | none |
| `concept.ai_literacy.explainability` | `portal.concepts` | `registry_item` | none |
| `concept.ai_friendly.assimilation` | `portal.concepts` | `registry_item` | none |
| `concept.ai_friendly.visibility` | `portal.concepts` | `registry_item` | none |
| `concept.database.acid` | `portal.concepts` | `registry_item` | none |
| `concept.database.atomicity` | `portal.concepts` | `registry_item` | none |
| `concept.database.consistency` | `portal.concepts` | `registry_item` | none |
| `concept.database.isolation` | `portal.concepts` | `registry_item` | none |
| `concept.database.durability` | `portal.concepts` | `registry_item` | none |
| `concept.agency` | `portal.concepts` | `registry_item` | none |
| `concept.agency.identity` | `portal.concepts` | `registry_item` | none |
| `concept.agency.authority` | `portal.concepts` | `registry_item` | none |
| `concept.agency.authentication` | `portal.concepts` | `registry_item` | none |
| `concept.agency.accountability` | `portal.concepts` | `registry_item` | none |
| `concept.agency.capability_vs_agency` | `portal.concepts` | `registry_item` | none |
| `concept.agency.influence_vs_authority` | `portal.concepts` | `registry_item` | none |
| `concept.agency.delegation` | `portal.concepts` | `registry_item` | none |
| `concept.agency.serialization` | `portal.concepts` | `registry_item` | none |
| `idea` | `portal.proofs` | `registry_item` | none |
| `design_intended` | `portal.proofs` | `registry_item` | none |
| `source_defined` | `portal.proofs` | `registry_item` | none |
| `runtime_observed` | `portal.proofs` | `registry_item` | none |
| `help_documented` | `portal.proofs` | `registry_item` | none |
| `validated` | `portal.proofs` | `registry_item` | none |
| `case_registered` | `portal.proofs` | `registry_item` | none |
| `runtime_lab_candidate` | `portal.proofs` | `registry_item` | none |
| `student_ready` | `portal.proofs` | `registry_item` | none |
| `simulated` | `portal.proofs` | `registry_item` | none |
| `historical_review_needed` | `portal.proofs` | `registry_item` | none |
| `proof.agency.model` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\ai-friendly\AGENCY_MODEL_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\lessons\student\agency_who_may_act_v0.md`<br>`related` ok: `D:\code\ccode\docs\ai-friendly\AI_ROLES_TAXONOMY_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_ENGINEERING_STANDARDS_SEED_V1.md` |
| `proof.ai.agent_assignment_link_x64` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260816_101951_agent_assignment_link_regression.txt`<br>`related` ok: `D:\code\ccode\docs\contracts\AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\AI_AGENT_ASSIGNMENT_LINK_MAINTENANCE_MANUAL_V1.md`<br>`related` ok: `D:\code\ccode\dottalkpp\data\schemas\syschatlnk_v1.schema.json`<br>`related` ok: `D:\code\ccode\dottalkpp\data\scripts\ddl\syschatlnk_x64_regression.dts`<br>`related` ok: `D:\code\ccode\labtalk\diagrams\ai_agent_assignment_link_pfd_v1.mmd`<br>`related` ok: `D:\code\ccode\labtalk\diagrams\ai_agent_assignment_link_dfd_v1.mmd` |
| `proof.ai.portal_live_fragment_maintenance` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260816_230404_ai_portal_live_maintenance.txt`<br>`related` ok: `D:\code\ccode\tools\reports\serve_dynamic_reports.py`<br>`related` ok: `D:\code\ccode\tools\reports\build_reports.py`<br>`related` ok: `D:\code\ccode\tools\registries\registry_fragments.py`<br>`related` ok: `D:\code\ccode\tools\dbf\crud.py`<br>`related` ok: `D:\code\ccode\tools\dbf\maint_server.py`<br>`related` ok: `D:\code\ccode\tools\dbf\maint_console.html`<br>`related` ok: `D:\code\ccode\start-ai.ps1`<br>`related` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_PORTAL_LIVE_MAINTENANCE_AIF086_2026-08-16.md` |
| `proof.ai.roles_taxonomy` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\ai-friendly\AI_ROLES_TAXONOMY_V1.md` |
| `proof.ai_friendly.assimilation_docs_seed` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_PORTAL_V1.md`<br>`related` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_BOOK_V1.md`<br>`related` ok: `D:\code\ccode\docs\ai-friendly\AI_FRIENDLY_DASHBOARD_V1.md`<br>`related` ok: `D:\code\ccode\src\cli\cmd_maint.cpp` |
| `proof.ai_friendly.maint_ai_assimilate.first_run` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260705_182913_runtime_maint_ai_assimilate.txt`<br>`related` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_PORTAL_V1.md`<br>`related` ok: `D:\code\ccode\docs\ai-friendly\AI_ASSIMILATION_BOOK_V1.md`<br>`related` ok: `D:\code\ccode\src\cli\cmd_maint.cpp` |
| `proof.ai_portal.cold_resume_retention` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\AI_PORTAL_COLD_RESUME_RETENTION_20260812_V1.md`<br>`related` ok: `D:\code\ccode\docs\agents\HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_TIER1_SEED_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\DEVELOPMENT_ACCELERATION_ANALYSIS_LANE_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\BETA1_E1_GATE_FALSIFICATION_FINDINGS_2026-08-09.md` |
| `proof.ai_portal.discoverability_caught_its_own_author` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\labtalk\ai_portal\INTAKE_DISCOVERABILITY_GAP_AND_FIX_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_report_index.yaml`<br>`related` ok: `D:\code\ccode\docs\maintenance\PHASE7_MANUAL_WEB_ASCENT_PICKUP_V1.md`<br>`related` ok: `D:\code\ccode\docs\agents\CURRENT_TARGET.md` |
| `proof.ai_portal.dotscript_startup_readiness.v1` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260712_195729_probe_ai_portal_dotscript_startup_readiness_v1.txt`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\probes\dotscript_startup_readiness_v1.dts`<br>`related` ok: `D:\code\ccode\src\cli\cmd_dotscript.cpp` |
| `proof.ai_portal.engineering_standards_seed` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\ai_portal\AI_ENGINEERING_STANDARDS_SEED_V1.md`<br>`related` ok: `D:\code\ccode\AI_README.md`<br>`related` ok: `D:\code\ccode\AI_PORTAL.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\ROOT_AI_PORTAL_ENTRY_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_HARDENING_LANE_V1.md` |
| `proof.ai_portal.lane_registered` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_HARDENING_LANE_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml`<br>`related` ok: `D:\code\ccode\dottalkpp\docs\architecture\X64BASE_LABORATORY_CAMPUS_MISSION_VISION_V1.md` |
| `proof.ai_portal.root_entry_and_external_package.v1` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\AI_PORTAL.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\ROOT_AI_PORTAL_ENTRY_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\SDLC_FAST_START_SEED_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\EXTERNAL_AI_CHANGE_PACKAGE_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml` |
| `proof.ai_portal.sdlc_fast_start.v1` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\ai_portal\SDLC_FAST_START_SEED_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\DOTTALKPP_SDLC_CHARTER_v0.md`<br>`related` ok: `D:\code\ccode\labtalk\LABTALK_SDLC_FRAMEWORK_v0.md`<br>`related` ok: `D:\code\ccode\docs\planning\SDLC_PDLC_PLANNING_ADOPTION_v0.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml` |
| `proof.ai_portal.seed_connection_prototype_direction.v1` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\ai_portal\SEED_CONNECTION_PROTOTYPE_NOTE_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\README.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_PORTAL_HARDENING_LANE_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml` |
| `proof.ai_portal.source_mutation_contract_gate.v1` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\ai_portal\SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`<br>`related` ok: `D:\code\ccode\docs\contracts\README.md`<br>`related` ok: `D:\code\ccode\docs\contracts\CONTRACT_REGISTRY_V1.md`<br>`related` ok: `D:\code\ccode\docs\contracts\CONTRACT_LIFECYCLE_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_portal.yaml` |
| `proof.aif078.slot_cost_measured_per_toolchain` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260801_aif078_g0_slot_cost_msvc.txt`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\20260801_aif078_g0_slot_cost_gcc.txt`<br>`related` ok: `D:\code\ccode\config\build_vectors.cmake`<br>`related` ok: `D:\code\ccode\include\xbase.hpp`<br>`related` ok: `D:\code\ccode\src\xbase\dbf_file.cpp`<br>`related` ok: `D:\code\ccode\src\cli\shell.cpp`<br>`related` ok: `D:\code\ccode\docs\maintenance\WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md` |
| `proof.aif078.workspace_path_preserves_depth1` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260801_aif078_q7_workspace_path_msvc.txt`<br>`related` ok: `D:\code\ccode\include\reference\data_address.hpp`<br>`related` ok: `D:\code\ccode\src\reference\data_address.cpp`<br>`related` ok: `D:\code\ccode\src\tests\test_pdlc_foundation_smoke.cpp`<br>`related` ok: `D:\code\ccode\docs\maintenance\WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md` |
| `proof.aside.diagnostic_removed_and_called_a_fix` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\tools\fullstack_docs\ecoschema_map.py`<br>`related` ok: `D:\code\ccode\docs\maintenance\ECOSCHEMA_MAP_V1.html`<br>`related` ok: `D:\code\ccode\labtalk\registries\proofs.d\proof.memo.zoo_orthogonality.yaml` |
| `proof.aside.rule_caught_its_own_author` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\labtalk\ai_portal\AI_GLOSSARY_V1.md`<br>`related` ok: `D:\code\ccode\tools\ps\py12_guard.ps1`<br>`related` ok: `D:\code\ccode\tools\staging\check_host_python.py` |
| `proof.bbs.guest` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\ai-friendly\AI_BBS_LOUNGE_ROOM_V1.md` |
| `proof.bbs.m1_board` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md` |
| `proof.bbs.m2_net_egress` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md` |
| `proof.bbs.m3_argon2` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md` |
| `proof.bbs.m4_serve` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md` |
| `proof.bbs.m6_daemon` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\AI_BBS_M6_STANDALONE_DAEMON_V1.md` |
| `proof.bbs.worklog` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\ai-friendly\AI_BBS_WORKLOG_HANDOFF_LANE_V1.md` |
| `proof.build.gcc_linux_warning_baseline` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260730_wsl_gcc_build_warnings.txt`<br>`related` ok: `D:\code\ccode\src\cnx\cnx_file.cpp`<br>`related` ok: `D:\code\ccode\src\identity\identity_dbf_store.cpp`<br>`related` ok: `D:\code\ccode\include\value_normalize.hpp`<br>`related` ok: `D:\code\ccode\src\xbase\field_codec.cpp`<br>`related` ok: `D:\code\ccode\include\cli\expr\fn_string.hpp` |
| `proof.case.registry_exists` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\cases\REGISTRY_CASES_v0.csv` |
| `proof.cnx_orthogonality_recno_permutation` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\src\cli\cmd_setorder.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_rebuild.cpp`<br>`related` ok: `D:\code\ccode\docs\maintenance\TICKET_CNX_ON_X64_WARN_NOT_REFUSE_AND_WORKSPACE_OPEN_INDEX_SOURCE_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\TICKET_CDX_ON_V32_WARN_NOT_REFUSE_MIRROR_V1.md` |
| `proof.codev.system_corrects_its_extender` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_SQLSEL_P0_P1_2026-07-29.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\ai_report_audit.yaml`<br>`related` ok: `D:\code\ccode\AI_README.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\AI_REPORT_AUDIT_V2_SPEC.md` |
| `proof.contract.dottalk_file_fulltree` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_AIF050_FULLTREE_BACKFILL_2026-07-25.md`<br>`related` ok: `D:\code\ccode\tools\fullstack_docs\source_census.py`<br>`related` ok: `D:\code\ccode\docs\maintenance\AI_RUN_TRACEABILITY_LANE_V1.md` |
| `proof.edref.storage_was_already_decided` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\include\edref.hpp`<br>`related` ok: `D:\code\ccode\dottalkpp\data\help\HELP_TOPIC.dbf`<br>`related` ok: `D:\code\ccode\config\package\lean.manifest`<br>`related` ok: `D:\code\ccode\config\package\educational.manifest`<br>`related` ok: `D:\code\ccode\src\help\helpdata_export_dbf.cpp`<br>`related` ok: `D:\code\ccode\tools\fullstack_docs\edrefcheck_v1.py` |
| `proof.edref.topic_exists` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\include\edref.hpp` |
| `proof.engine.append_blank_catalog_drift` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260804_append_blank_catalog_drift_ram.txt`<br>`related` ok: `D:\code\ccode\docs\maintenance\COMMAND_CATALOG_RUNTIME_DRIFT_PDLC_LANE_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\PYDOTTALK_CAPABILITY_REVIEW_AND_CRUD_READINESS_V1.md`<br>`related` ok: `D:\code\ccode\src\cli\cmd_append.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_append_blank.cpp`<br>`related` ok: `D:\code\ccode\dottalkpp\data\scripts\mem_proof.dts` |
| `proof.engine.key_metadata_survives_workspace_roundtrip` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_key_metadata_roundtrip.txt`<br>`related` ok: `D:\code\ccode\include\cli\unique_registry.hpp`<br>`related` ok: `D:\code\ccode\src\cli\unique_registry.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_setunique.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_workspace.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_validate_unique.cpp` |
| `proof.engine.scan_limit_reports_truncation` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_rel_scanlimit_honesty.txt`<br>`related` ok: `D:\code\ccode\src\cli\set_relations.cpp`<br>`related` ok: `D:\code\ccode\src\cli\set_relations.hpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_rel.cpp` |
| `proof.engine.two_read_families_buffer_visibility` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_smartbrowser_tuple_filter_interactive.txt`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_buffer_visibility_probe.txt`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_buffer_visibility_probe_v2.txt`<br>`related` ok: `D:\code\ccode\src\cli\expr_tuple_glue.hpp`<br>`related` ok: `D:\code\ccode\src\cli\db_tuple_stream.cpp`<br>`related` ok: `D:\code\ccode\src\cli\smartlist_output.cpp`<br>`related` ok: `D:\code\ccode\src\cli\sqlsel_statement.cpp` |
| `proof.engine.typed_equality_crosses_declared_types` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_rdb_truth_typed_equality.txt`<br>`related` ok: `D:\code\ccode\src\cli\set_relations.cpp`<br>`related` ok: `D:\code\ccode\dottalkpp\data\scripts\rdb_truth_check_v1.py` |
| `proof.evidence.layer_versioned` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\AI_EVIDENCE_LAYER_VERSIONING_LANE_V1.md` |
| `proof.export.sdf.fixed_width_export` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260727_export_sdf_regression.txt`<br>`related` ok: `D:\code\ccode\src\cli\cmd_export.cpp`<br>`related` ok: `D:\code\ccode\include\cli\fixed_width_row.hpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_tuptalk.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_regression.cpp`<br>`related` ok: `D:\code\ccode\src\help\helpdata_messages.cpp`<br>`related` ok: `D:\code\ccode\include\dotref.hpp` |
| `proof.golden_rule_verify_before_assert` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\labtalk\ai_portal\AI_GLOSSARY_V1.md`<br>`related` ok: `D:\code\ccode\tools\reports\serve_dynamic_reports.py`<br>`related` ok: `D:\code\ccode\start-ai.ps1`<br>`related` ok: `D:\code\ccode\tools\reports\bbs_auth_relay.py` |
| `proof.governance.availability_is_not_adoption` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\AIF112_OWNER_RULING_D1_D3_AND_DOGFOOD_DEFINITION_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\external_ai_intake\aif112_document_control_acceptance_2026-08-15\ACCEPTANCE_NOTE.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\external_ai_intake\aif112_phase0_decisions_2026-08-15\PHASE0_DECISIONS.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\AIF112_PRIOR_ART_INVENTORY_AND_DBF_REVISION_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_GLOSSARY_V1.md` |
| `proof.grok_lane1_coworker_kind_collision` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\docs\maintenance\LANE_L1_WRITE_ADAPTER_ASSIGNMENT_GROK_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\GROK_PUSH_L1_WRITE_ADAPTER_V1.md`<br>`related` ok: `D:\code\ccode\include\bbs\bbs_schema.hpp`<br>`related` ok: `D:\code\ccode\tools\memory\promote.py` |
| `proof.help.cmdhelp_source_exists` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\src\cli\cmdhelp.cpp` |
| `proof.lab.database_literacy_starter.first_run` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260702_155913_runtime_database_literacy_starter.txt` |
| `proof.lab.selfdoc.comments_to_contracts.first_run` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260704_075057_runtime_selfdoc_comments_to_contracts_first_lab.txt`<br>`related` ok: `D:\code\ccode\labtalk\reports\selfdoc\lab_selfdoc_first_crosswalk_v0.md` |
| `proof.lmdb.mapsize_ladder_honoured_after_fix` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260727_aif065_tiny_survives_attach_postfix.txt`<br>`related` ok: `D:\code\ccode\src\xindex\lmdb_backend.cpp`<br>`related` ok: `D:\code\ccode\tools\proofs\run_proof.ps1`<br>`related` ok: `D:\code\ccode\docs\maintenance\LMDB_MAPSIZE_OVERRIDE_LANE_V1.md` |
| `proof.lmdb.mapsize_override_on_attach` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260727_aif065_mapsize_attach.txt`<br>`related` ok: `D:\code\ccode\src\xindex\cdx_backend.cpp`<br>`related` ok: `D:\code\ccode\src\xindex\lmdb_backend.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_buildlmdb.cpp` |
| `proof.lmdb.mapsize_override_replication_sysfunc` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260727_aif065_mapsize_tiny_survives_attach.txt`<br>`related` ok: `D:\code\ccode\tools\proofs\run_proof.ps1`<br>`related` ok: `D:\code\ccode\src\xindex\cdx_backend.cpp` |
| `proof.memo.object_challenge` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\MEMO_OBJECT_CHALLENGE_LANE_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1.md`<br>`related` ok: `D:\code\ccode\src\memo\memo_zoo.cpp`<br>`related` ok: `D:\code\ccode\docs\maintenance\MEMO_RESIDENT_MINIDB_V1.md` |
| `proof.memo.zoo_orthogonality` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1.md`<br>`related` ok: `D:\code\ccode\src\memo\memo_zoo.cpp`<br>`related` ok: `D:\code\ccode\src\memo\memo_ref.cpp`<br>`related` ok: `D:\code\ccode\docs\maintenance\MEMO_OBJECT_CHALLENGE_LANE_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\MEMO_RESIDENT_MINIDB_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md` |
| `proof.owner_dogfood_caught_cross_slot_leak` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\src\cli\cmd_workspace.cpp`<br>`related` ok: `D:\code\ccode\dottalkpp\data\scripts\index_x64_cnx_smoke.dts`<br>`related` ok: `D:\code\ccode\docs\maintenance\TICKET_CNX_ON_X64_WARN_NOT_REFUSE_AND_WORKSPACE_OPEN_INDEX_SOURCE_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\GATE_GOVERNANCE_LANE_V1.md` |
| `proof.pdlc.cobol_fixed_record.hop_closed` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260726T233000Z_pdlc_cobol_fixed_record_hop.txt`<br>`related` ok: `D:\code\ccode\tests\conversion\12_cobol_fixed_record_v1.dts`<br>`related` ok: `D:\code\ccode\dottalkpp\data\projects\cobol\src\first_cobol_test.cob`<br>`related` ok: `D:\code\ccode\src\edu\edu_cobol.cpp` |
| `proof.pdlc.csv_to_x64base.type_fidelity` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260726T233000Z_pdlc_csv_to_x64base_type_fidelity.txt`<br>`related` ok: `D:\code\ccode\tests\conversion\02_csv_to_dbf_v2.dts`<br>`related` ok: `D:\code\ccode\tests\conversion\10_crosswalk_cascade_items_v1.dts` |
| `proof.pdlc.dbf_csv_dbf.roundtrip_lossless` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260726T233000Z_pdlc_dbf_csv_dbf_roundtrip.txt`<br>`related` ok: `D:\code\ccode\tests\conversion\05_roundtrip_dbf_csv_dbf_v2.dts`<br>`related` ok: `D:\code\ccode\tests\conversion\README_SUITE_REPAIR_V1.md` |
| `proof.pdlc.dialect_ladder.dbase3_to_x64` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260726T233000Z_pdlc_historical_dialect_ladder.txt`<br>`related` ok: `D:\code\ccode\tests\conversion\11_historical_dialect_ladder_v1.dts`<br>`related` ok: `D:\code\ccode\src\cli\cmd_copy.cpp` |
| `proof.peer_review.header_only_findings` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\PEER_REVIEW_HEADER_ONLY_FINDINGS_20260813_V1.md`<br>`related` ok: `D:\code\ccode\docs\agents\HANDOFF_CLAUDE_COWORK_SITE_PUBLISH_ECO_2026-08-13.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\peer_design_review\PDR-001_workspace_scanner_wbak_2026-08-12\SESSION_V1.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\BETA1_EXIT_GATE_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\proofs\AI_PORTAL_COLD_RESUME_RETENTION_20260812_V1.md` |
| `proof.portal.truth_audit.latest` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\reports\portal\portal_truth_audit_latest.md`<br>`related` ok: `D:\code\ccode\labtalk\reports\portal\portal_truth_audit_latest.json` |
| `proof.product.manualgen.board_preserved` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\products\manualgen_product_preservation_v0.md`<br>`related` ok: `D:\code\ccode\labtalk\products\manualgen_product_board_v0.html`<br>`related` ok: `D:\code\ccode\labtalk\products\manualgen_product_map_v0.md`<br>`related` ok: `D:\code\ccode\tools\manualgen\README.md`<br>`related` ok: `D:\code\ccode\docs\manuals\developer\manualgen\reports\mdo_226_validate_summary_v1.csv`<br>`related` ok: `D:\code\ccode\docs\manuals\developer\manualgen\reports\mdo_226_build_dry_run_summary_v1.csv` |
| `proof.selfdoc.comments_workflow_exists` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\COMMENTS_HELP_PROOF_WORKFLOW_v1.md` |
| `proof.site.invalid_opacity_renders_nothing` | `portal.proofs` | `registry_item` | `related` ok: `D:\dev\x64base-site\app\page.tsx`<br>`related` ok: `D:\dev\x64base-site\app\globals.css`<br>`related` ok: `D:\dev\x64base-site\tailwind.config.ts`<br>`related` ok: `D:\code\ccode\labtalk\registries\proofs.d\proof.tooling.catalog_state_blindness.yaml` |
| `proof.sqlsel.select_statement_matches_sqlite` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\20260729_aif074_sqlsel_select_v1_oracle.txt`<br>`related` ok: `D:\code\ccode\src\cli\sqlsel_statement.cpp`<br>`related` ok: `D:\code\ccode\src\cli\sqlsel_statement.hpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_sql_select.cpp`<br>`related` ok: `D:\code\ccode\src\cli\workarea_util.cpp`<br>`related` ok: `D:\code\ccode\src\cli\tuple_builder.cpp` |
| `proof.tooling.catalog_state_blindness` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\include\devref.hpp`<br>`related` ok: `D:\code\ccode\tools\fullstack_docs\refcheck_v1.py`<br>`related` ok: `D:\code\ccode\tools\fullstack_docs\edrefcheck_v1.py`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_TIER1_SEED_V1.md`<br>`related` ok: `D:\code\ccode\labtalk\registries\proofs.d\proof.tooling.local_path_detector_consolidation.yaml` |
| `proof.tooling.cross_platform` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_CROSS_PLATFORM_TOOLING_2026-08-02.md`<br>`related` ok: `D:\code\ccode\tools\lanes\lane.py`<br>`related` ok: `D:\code\ccode\tools\git\restore_lfs.py`<br>`related` ok: `D:\code\ccode\tools\reports\stage_public.py`<br>`related` ok: `D:\code\ccode\tools\registries\registry_fragments.py`<br>`related` ok: `D:\code\ccode\labtalk\ai_portal\AI_ENGINEERING_STANDARDS_SEED_V1.md` |
| `proof.tooling.local_path_detector_consolidation` | `portal.proofs` | `registry_item` | `related` ok: `D:\code\ccode\tools\common\local_paths.json`<br>`related` ok: `D:\code\ccode\tools\common\local_paths.py`<br>`related` ok: `D:\code\ccode\tools\staging\rebuild-staging.ps1`<br>`related` ok: `D:\code\ccode\tools\reports\stage_public.py`<br>`related` ok: `D:\code\ccode\tools\fullstack_docs\ecoschema_map.py`<br>`related` ok: `D:\code\ccode\labtalk\registries\proofs.d\proof.aside.diagnostic_removed_and_called_a_fix.yaml` |
| `proof.wal.dbf_record` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`<br>`related` ok: `D:\code\ccode\src\cli\table_state.cpp`<br>`related` ok: `D:\code\ccode\include\cli\table_state.hpp`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\wal_phaseA_proof_teed_20260719T080435Z.log`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\wal_phaseB_verify_teed_20260719T081647Z.log`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\wal_phaseC_proof_teed_20260719T082345Z.log` |
| `proof.wal.memo_atomicity` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\AI_MEMO_WAL_ATOMICITY_LANE_V1.md` |
| `proof.workspace.writeback` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\labtalk\proofs\runs\workspace_writeback_pathfix_proof_20260812T195516Z.log`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\workspace_writeback_proof_windows_20260812T180000Z.log`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\workspace_writeback_proof_teed_20260812T174605Z.log`<br>`related` ok: `D:\code\ccode\labtalk\proofs\runs\workspace_writeback_proof_teed_20260812T174605Z.CORRECTION.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\SESSION_CLOSEOUT_WORKSPACE_WRITEBACK_REGRESSION_2026-08-12.md`<br>`related` ok: `D:\code\ccode\docs\maintenance\MEMO_RESIDENT_MINIDB_V1.md`<br>`related` ok: `D:\code\ccode\dottalkpp\data\scripts\workspace_writeback.dts`<br>`related` ok: `D:\code\ccode\src\cli\cmd_workspace.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_erase.cpp`<br>`related` ok: `D:\code\ccode\src\cli\expr\fn_string.cpp`<br>`related` ok: `D:\code\ccode\src\cli\expr\function_catalog.cpp`<br>`related` ok: `D:\code\ccode\src\cli\cmd_regression.cpp` |
| `proof.worktree.lane_isolation` | `portal.proofs` | `registry_item` | `source` ok: `D:\code\ccode\docs\maintenance\AI_WORKTREE_LANE_ISOLATION_LANE_V1.md`<br>`related` ok: `D:\code\ccode\docs\ai-friendly\AI_GITLOCK_HOT_POTATO_LANE_V1.md` |
| `report.index` | `portal.reports` | `html` | `path` ok: `D:\code\ccode\docs\reports\index.html` |
| `report.ai_portal` | `portal.reports` | `html` | `path` ok: `D:\code\ccode\docs\reports\AI_PORTAL_REPORT.html` |
| `report.bbs_boards` | `portal.reports` | `html` | `path` ok: `D:\code\ccode\docs\reports\BBS_BOARDS_REPORT.html` |
| `report.bbs_access` | `portal.reports` | `html` | `path` ok: `D:\code\ccode\docs\reports\BBS_ACCESS_REPORT.html` |
| `report.aif_rulings` | `portal.reports` | `html` | `path` ok: `D:\code\ccode\docs\reports\AIF_RULINGS_REPORT.html`<br>`source` missing: `D:\code\ccode\labtalk\docs\maintenance\AIF_*RULING_SHEET*.md + labtalk\ai_portal\TIER0_STATE.md` |
| `diagram.selfdoc_contract_lane_drawio` | `portal.diagrams` | `diagram` | `path` ok: `D:\code\ccode\labtalk\diagrams\selfdoc_contract_lane_v1.drawio` |
| `diagram.labtalk_sdlc` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\LABTALK_SDLC_DIAGRAMS_v0.md` |
| `diagram.dottalkpp_sdlc` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\docs\maintenance\diagrams\DOTTALKPP_SDLC_DIAGRAMS_v0.md` |
| `diagram.selfdoc_contract_lane_mermaid` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\selfdoc_contract_lane_v1.mmd` |
| `diagram.selfdoc_mdo_dataflow_map` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\SELFDOC_MDO_DATAFLOW_MAP_v0.md` |
| `diagram.selfdoc_mdo_authority_dataflow` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\selfdoc_mdo_authority_dataflow_v0.mmd` |
| `diagram.selfdoc_probe_pipeline_dataflow` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\selfdoc_probe_pipeline_dataflow_v0.mmd` |
| `diagram.selfdoc_metacollect_metadata_dataflow` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\selfdoc_metacollect_metadata_dataflow_v0.mmd` |
| `diagram.mdo_manualgen_publication_dataflow` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\mdo_manualgen_publication_dataflow_v0.mmd` |
| `diagram.mdo_guarded_help_cmdhelpchk_dataflow` | `portal.diagrams` | `markdown` | `path` ok: `D:\code\ccode\labtalk\diagrams\mdo_guarded_help_cmdhelpchk_dataflow_v0.mmd` |
| `diagram.selfdoc_contract_lane_webui` | `portal.diagrams` | `html` | `path` ok: `D:\code\ccode\dottalk-webui\selfdoc-lane.html` |
| `diagram.x64base_labtalk_sdlc_operational` | `portal.diagrams` | `image` | `path` ok: `D:\dev\x64base-site\public\images\sdlc\laboratory-campus-operational-sdlc.svg` |
| `diagram.x64base_selfdoc_contract_lane` | `portal.diagrams` | `markdown` | `path` ok: `D:\dev\x64base-site\public\diagrams\selfdoc\selfdoc_contract_lane_v1.mmd` |
| `runtime.database_literacy_starter` | `portal.runtime` | `dottalk_script` | `script` ok: `D:\code\ccode\labtalk\labs\database_literacy_starter\database_literacy_starter_v0.dts` |
| `runtime.help` | `portal.runtime` | `dottalk_command` | none |
| `runtime.case_list` | `portal.runtime` | `dottalk_command` | none |
| `runtime.cmdhelp` | `portal.runtime` | `dottalk_command` | none |
| `runtime.selfdoc.comments_to_contracts.first_lab` | `portal.runtime` | `lab_script` | `script` ok: `D:\code\ccode\labtalk\labs\self_documenting_systems\run_selfdoc_first_lab.ps1` |
| `launcher.cli` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\datarun.ps1` |
| `launcher.erp` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\erprun.ps1` |
| `launcher.bible` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\biblerun.ps1` |
| `launcher.wx` | `portal.launchers` | `powershell_launcher` | `path` missing: `D:\code\ccode\wx.run.ps1` |
| `launcher.wx_next` | `portal.launchers` | `powershell_launcher` | `path` missing: `D:\code\ccode\wx.next.run.ps1` |
| `launcher.tk` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\tk.run.ps1` |
| `launcher.tk_wsl` | `portal.launchers` | `wsl_launcher` | `script` ok: `D:\code\ccode\tk.run.sh` |
| `launcher.run_cli` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\run-cli.ps1` |
| `launcher.run_erp` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\run-erp.ps1` |
| `launcher.run_bible` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\run-bible.ps1` |
| `launcher.run_wx` | `portal.launchers` | `powershell_launcher` | `path` missing: `D:\code\ccode\run-wx.ps1` |
| `launcher.run_wx_next` | `portal.launchers` | `powershell_launcher` | `path` missing: `D:\code\ccode\run-wx-next.ps1` |
| `launcher.arctictalk_runtime` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\arctictalk.datarun.ps1` |
| `launcher.arctictalk_runtime_wsl` | `portal.launchers` | `wsl_launcher` | `script` ok: `D:\code\ccode\arctictalk.datarun.sh` |
| `launcher.artic_runtime` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\artic.datarun.ps1` |
| `launcher.artic_runtime_wsl` | `portal.launchers` | `wsl_launcher` | `script` ok: `D:\code\ccode\artic.datarun.sh` |
| `launcher.pydottalk` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\run-pydottalk.ps1` |
| `launcher.pycrud` | `portal.launchers` | `powershell_launcher` | `path` ok: `D:\code\ccode\run-pycrud.ps1` |
| `launcher.wsl_build` | `portal.launchers` | `wsl_launcher` | `script` ok: `D:\code\ccode\wsl_build_dottalkpp.sh` |
| `launcher.wsl_cli` | `portal.launchers` | `wsl_launcher` | `script` ok: `D:\code\ccode\datarun_wsl.sh` |
| `launcher.wsl_runtime` | `portal.launchers` | `wsl_launcher` | `script` ok: `D:\code\ccode\wslrun.sh` |

## Diagram Provenance

| Diagram | State | Sources |
|---|---|---|
| `agent_assignment_link.pfd` | `provenance_ok` | `D:\code\ccode\docs\contracts\AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md`<br>`D:\code\ccode\docs\maintenance\AI_AGENT_ASSIGNMENT_LINK_MAINTENANCE_MANUAL_V1.md` |
| `agent_assignment_link.dfd` | `provenance_ok` | `D:\code\ccode\docs\contracts\AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md`<br>`D:\code\ccode\dottalkpp\data\schemas\syschatlnk_v1.schema.json` |
| `agent_assignment_link.relational_erd` | `provenance_ok` | `D:\code\ccode\docs\maintenance\AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md`<br>`D:\code\ccode\docs\contracts\AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md` |
| `agent_assignment_link.relational_dfd` | `provenance_ok` | `D:\code\ccode\docs\maintenance\AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md`<br>`D:\code\ccode\docs\maintenance\AI_BBS_OPERATIONS_RUNBOOK_V1.md` |
| `agent_assignment_link.relational_pfd` | `provenance_ok` | `D:\code\ccode\docs\maintenance\AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md` |
| `diagram.selfdoc_contract_lane_drawio` | `provenance_ok` | `D:\code\ccode\tools\diagram\diagram_seed_selfdoc_lane_v1.meta` |
| `diagram.labtalk_sdlc` | `provenance_missing` | none |
| `diagram.dottalkpp_sdlc` | `provenance_missing` | none |
| `diagram.selfdoc_contract_lane_mermaid` | `provenance_ok` | `D:\code\ccode\tools\diagram\diagram_seed_selfdoc_lane_v1.meta` |
| `diagram.selfdoc_mdo_dataflow_map` | `provenance_missing` | none |
| `diagram.selfdoc_mdo_authority_dataflow` | `provenance_missing` | none |
| `diagram.selfdoc_probe_pipeline_dataflow` | `provenance_missing` | none |
| `diagram.selfdoc_metacollect_metadata_dataflow` | `provenance_missing` | none |
| `diagram.mdo_manualgen_publication_dataflow` | `provenance_missing` | none |
| `diagram.mdo_guarded_help_cmdhelpchk_dataflow` | `provenance_missing` | none |
| `diagram.selfdoc_contract_lane_webui` | `provenance_missing` | none |
| `diagram.x64base_labtalk_sdlc_operational` | `provenance_missing` | none |
| `diagram.x64base_selfdoc_contract_lane` | `provenance_missing` | none |
