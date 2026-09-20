# Source Contract Vocabulary Contract v1

Status: active descriptive contract.

## Purpose

Preserve the field and alias vocabulary discovered by the historical SelfDoc
source-contract inventory probe v1.1 without making that probe a default
collector or granting it authority to mutate source, COMMENTS, HELP, or manual
catalogs.

## Authorities

- Machine-readable vocabulary: `selfdoc/source_contract_vocabulary_v1.json`
- Historical source: `selfdoc/probes/source_contract_inventory_probe_v1_1.py`
- Validator and deterministic builder: `tools/selfdoc/validate_source_contract_vocabulary.py`
- Probe and current-tool lineage: `selfdoc/source_contract_probe_lineage_v1.json`
- Lineage validator: `tools/selfdoc/validate_documentation_lineages.py`

The registry is descriptive classifier vocabulary. It does not establish that
a field is true for a command, and it does not promote harvested values.

## Lifecycle

The v1.1 probe remains `HISTORICAL` and is not allowed as a default execution
path. Its unique core, recommended, extension, and alias constants are migrated
verbatim into the registry. Any change to those preserved values must be
reviewed as vocabulary drift, not silently absorbed during a reharvest.

## Safety Boundary

The builder may write only the vocabulary JSON when explicitly invoked with
`--write`. Validation is read-only. Neither mode may edit source comments,
reload COMMENTS, rebuild HELP, or promote manual or messaging catalogs.

## Verification

Run from the repository root:

```powershell
python tools/selfdoc/validate_source_contract_vocabulary.py
python tools/selfdoc/validate_documentation_lineages.py
python -m unittest tools.selfdoc.tests.test_source_contract_vocabulary
```
