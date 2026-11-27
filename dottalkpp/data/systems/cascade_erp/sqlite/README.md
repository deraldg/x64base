# Cascade Precision Mfg ERP - Phase 2 Seed Package

This package populates the ERP sample database with the Codex target of 330 sample records.

## Contents

- `cascade_precision_mfg_erp.sqlite` - ready-to-open SQLite database
- `schema.sql` - schema and analytical views
- `seed_data.sql` - data-only seed inserts
- `cascade_precision_mfg_erp_full_dump.sql` - full rebuildable SQLite dump
- `sample_queries.sql` - validation and teaching queries
- `manifest.json` - counts, validation, doctrine
- `data/*.csv` - table exports

## Validation

```text
User tables:        34
Analytical views:   9
Sample records:     330
Foreign keys:       OK
Trial balance:      14794.75 debit / 14794.75 credit
Reorder alerts:     14
Three-way rows:     6
```

## Staging

Recommended project path:

```text
dottalkpp\data\cascade_precision_erp\cascade_precision_mfg_erp.sqlite
```

## DotTalk++ smoke

```text
erp cwd
erp check
erp modules
erp tables
erp views
erp columns Items
erp list Items 10
erp items
erp reorder
erp bom PDU-100
erp workorders
erp threeway
erp trial
```

## Doctrine

`SQLITE` remains generic. ERP-specific behavior belongs under `ERP`.
Future work should make SQLite <-> x64base/LMDB transfer explicit and teachable.
