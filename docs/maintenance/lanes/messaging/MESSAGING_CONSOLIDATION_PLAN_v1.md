# Messaging Consolidation Plan v1

## Problem

DotTalk++ appears to have more than one partial message mechanism:

1. A richer `helpdata_messages.*` lane under the HELP/helpdata namespace.
2. A smaller `message_catalog.*` lane under a separate message namespace.
3. Output helper files such as `list_messaging.*` that contain direct user-facing strings but are not catalogs.

The risk is growing two incompatible message systems while also leaving hard-coded output text scattered through command and rendering code.

## Proposed consolidation

1. Treat `helpdata_messages.*` as the preferred compiled seed.
2. Treat `message_catalog.*` as an older/minimal catalog requiring explicit merge/retire review.
3. Treat `list_messaging.*` as an extraction candidate.
4. Build the x64base `MSG*` schema around the richer concepts already present in `helpdata_messages.*`.
5. Use `SET LANGUAGE` / `SET LOCALE` as the current runtime message-locale selector.

## Do not do yet

- Do not replace arbitrary `std::cout` text yet.
- Do not create MSG* DBFs yet.
- Do not mutate HELP/CMDHELPCHK/META.
- Do not merge the two message catalogs without a report-only crosswalk.
