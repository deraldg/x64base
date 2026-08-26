# AI Portal Feed Status

Generated from the typed feed, assertion, and current-run registries. Do not hand-edit.

## Current documentation push

| Field | Value |
| --- | --- |
| run_id | `DOCFLUSH-20260825-001` |
| canonical_process | `development_closeout` |
| state | `closed_review_needed` |
| publication_state | `not_entered` |
| next_process | `publication_ascent` |
| next_entry_state | `partial` |
| first_open_entry | `E6` |

## Summary

- Feeds: 6 (0 advisory findings)
- Artifact observations: 53
- Structured assertions: 6 (6 passing, 0 advisory findings)

## Feeds

| Feed | Class | Status | Phase | Evidence | Outputs | Consumers | Findings |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `feed.dottalk.help_store` | help_catalog | `active` | `development_closeout` | `source-evidenced` | 10 | 2 | 0 |
| `feed.dottalk.metadata_metacollect` | metadata_catalog | `degraded` | `development_closeout` | `runtime-proven` | 2 | 2 | 0 |
| `feed.dottalk.manual_accepted` | accepted_manual | `active` | `development_closeout` | `source-evidenced` | 2 | 2 | 0 |
| `feed.portal.current_work` | current_work_projection | `degraded` | `publication_ascent` | `planned` | 2 | 1 | 0 |
| `feed.portal.audit_reports` | portal_audit_projection | `active` | `development_closeout` | `source-evidenced` | 2 | 1 | 0 |
| `feed.portal.status_projection` | portal_status_projection | `active` | `development_closeout` | `source-evidenced` | 2 | 1 | 0 |

## Structured assertions

| Claim | Validity | Expected | Observed | Pass | Findings |
| --- | --- | --- | --- | --- | ---: |
| `assertion.fullstack.current_run` | `perishable` | `DOCFLUSH-20260825-001` | `DOCFLUSH-20260825-001` | true | 0 |
| `assertion.fullstack.canonical_process` | `perishable` | `development_closeout` | `development_closeout` | true | 0 |
| `assertion.fullstack.publication_state` | `perishable` | `not_entered` | `not_entered` | true | 0 |
| `assertion.portal.feed_schema` | `invariant` | `dottalk.portal.feed.v1` | `dottalk.portal.feed.v1` | true | 0 |
| `assertion.portal.fullstack_trigger` | `invariant` | `trigger.fullstack_doc_push` | `["trigger.onboard", "trigger.change_source", "trigger.write_dotscript", "trigger.open_lane", "trigger.commit_or_push", "trigger.publish", "trigger.close_out", "trigger.plan_gates", "trigger.use_devtools", "trigger.understand_why", "trigger.release_or_license", "trigger.persistent_memory", "trigger.where_is", "trigger.read_write_dbf", "trigger.use_reference_authority", "trigger.capture_proof", "trigger.edit_website", "trigger.work_in_sandbox", "trigger.fullstack_doc_push", "trigger.understand_portal_system"]` | true | 0 |
| `assertion.portal.status_feed_registered` | `invariant` | `feed.portal.status_projection` | `["feed.dottalk.help_store", "feed.dottalk.metadata_metacollect", "feed.dottalk.manual_accepted", "feed.portal.current_work", "feed.portal.audit_reports", "feed.portal.status_projection"]` | true | 0 |

## Boundary

This is development-tree status. It is not a promotion, deployment, or public publication receipt.
