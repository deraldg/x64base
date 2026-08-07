#!/usr/bin/env python3
"""
apply_source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_fix.py

SelfDoc tooling hotfix.

Patches only:
  selfdoc\probes\source_contract_inventory_probe_v1_1.py

Purpose:
  Bind the proven hotfix_004 row-normalization logic at the actual report/writer boundary.

Allowed:
  modify this SelfDoc probe
  create a backup of this SelfDoc probe
  rerun SelfDoc probes
  overwrite generated v1.1 SelfDoc reports
  write validation reports
  refresh evidence

Still protected:
  DotTalk++ src\ or include\ source/header files
  source repair patches
  DBF writes
  HELP DATA rebuild
  CMDHELPCHK changes
  v1.1 default promotion
  moving/deleting project files

Why this exists:
  The previous integrate_hotfix_004 did not bind into the live v1.1 writer path.
  Validation still saw v1.1-malformed_assignment_hotfix_003 and 0/9 Batch 0 rows accepted.

This patch:
  - updates PROBE_VERSION to v1.1-hotfix_004_writer_binding
  - inserts a hotfix_004 final-row normalizer
  - wraps common report writer functions so row lists are normalized at write time
  - updates summary dictionaries opportunistically when rows are available
  - does not edit DotTalk++ source or runtime data
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_hotfix_004_writer_binding"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
OUT_MD = REPORT_DIR / "source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_fix_status.md"
OUT_JSON = REPORT_DIR / "source_contract_inventory_probe_v1_1_hotfix_004_writer_binding_fix_status.json"

EXPECTED_VERSION = "v1.1-hotfix_004_writer_binding"


HOTFIX_BLOCK = r