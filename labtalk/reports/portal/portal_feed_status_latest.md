# AI Portal Feed Status

Generated from the typed feed, assertion, and current-run registries. Do not hand-edit.

## Current documentation push

| Field | Value |
| --- | --- |
| run_id | `DDICT-INTEGRATION-20261009` |
| canonical_process | `development_closeout` |
| state | `integration_candidate_review` |
| publication_state | `not_entered` |
| next_process | `catalog_data_review` |
| next_entry_state | `review` |
| first_open_entry | `DDICT_DATA_REVIEW` |

## Summary

- Feeds: 7 (5 advisory findings)
- Artifact observations: 61
- Structured assertions: 6 (3 passing, 4 advisory findings)

## Feeds

| Feed | Class | Status | Phase | Evidence | Outputs | Consumers | Findings |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `feed.dottalk.ddict` | data_dictionary_catalog | `degraded` | `development_closeout` | `source-evidenced` | 1 | 4 | 5 |
| `feed.dottalk.help_store` | help_catalog | `active` | `development_closeout` | `source-evidenced` | 10 | 2 | 0 |
| `feed.dottalk.metadata_metacollect` | metadata_catalog | `degraded` | `development_closeout` | `runtime-proven` | 2 | 2 | 0 |
| `feed.dottalk.manual_accepted` | accepted_manual | `active` | `development_closeout` | `source-evidenced` | 2 | 2 | 0 |
| `feed.portal.current_work` | current_work_projection | `degraded` | `publication_ascent` | `planned` | 2 | 1 | 0 |
| `feed.portal.audit_reports` | portal_audit_projection | `active` | `development_closeout` | `source-evidenced` | 2 | 1 | 0 |
| `feed.portal.status_projection` | portal_status_projection | `active` | `development_closeout` | `source-evidenced` | 2 | 1 | 0 |

## Structured assertions

| Claim | Validity | Expected | Observed | Pass | Findings |
| --- | --- | --- | --- | --- | ---: |
| `assertion.fullstack.current_run` | `perishable` | `DOCFLUSH-20260825-001` | `DDICT-INTEGRATION-20261009` | false | 2 |
| `assertion.fullstack.canonical_process` | `perishable` | `development_closeout` | `development_closeout` | true | 1 |
| `assertion.fullstack.publication_state` | `perishable` | `not_entered` | `not_entered` | true | 1 |
| `assertion.portal.feed_schema` | `invariant` | `dottalk.portal.feed.v1` | `dottalk.portal.feed.v1` | true | 0 |
| `assertion.portal.fullstack_trigger` | `invariant` | `trigger.fullstack_doc_push` | `["trigger.onboard", "trigger.change_source", "trigger.write_dotscript", "trigger.open_lane", "trigger.commit_or_push", "trigger.publish", "trigger.close_out", "trigger.plan_gates", "trigger.use_devtools", "trigger.understand_why", "trigger.release_or_license", "trigger.persistent_memory", "trigger.memory_retention", "trigger.portal_history", "trigger.where_is", "trigger.read_write_dbf", "trigger.use_reference_authority", "trigger.capture_proof", "trigger.edit_website", "trigger.work_in_sandbox", "trigger.fullstack_doc_push", "trigger.ddict", "trigger.understand_portal_system"]` | true | 0 |
| `assertion.portal.status_feed_registered` | `invariant` | `feed.portal.status_projection` | `["feed.dottalk.ddict", "feed.dottalk.help_store", "feed.dottalk.metadata_metacollect", "feed.dottalk.manual_accepted", "feed.portal.current_work", "feed.portal.audit_reports", "feed.portal.status_projection"]` | true | 0 |

## Boundary

This is development-tree status. It is not a promotion, deployment, or public publication receipt.
