# Messaging Blackbox Inventory v1

## Purpose

This document captures the current partial messaging system evidence and frames it as a DotTalk++ SelfDoc / Maintenance / Blackbox lane.

Messaging is the transformation from scattered user-visible text into catalog-backed, typed, localizable runtime information.

## Observed related code families

- `helpdata_messages.*` appears to be the strongest existing seed for the message/localization system. It models message identity, owner/category/severity, localized text, locale normalization, fallback, and placeholder formatting.
- `message_catalog.*` appears to be a smaller or older parallel message catalog. It should be reviewed for merge/retire rather than allowed to grow independently.
- `list_messaging.*` is not a message catalog. It is LIST/BROWSER output rendering and should be treated as a future message-extraction candidate.
- `cmd_set.cpp` already contains the runtime language/locale control point through `SET LANGUAGE` / `SET LOCALE`, selecting message-rendering locale rather than full region behavior.

## Current doctrine

Messaging standardizes what the system says.
Language catalogs adapt what the system says to the reader.
The Blackbox model explains the transformation: data goes in, processing happens, information comes out.

## Safety boundary

This capture plan performs no code rewrite and no catalog creation. Source-string replacement should be a later guarded lane after inventory, schema design, extraction, and review.
