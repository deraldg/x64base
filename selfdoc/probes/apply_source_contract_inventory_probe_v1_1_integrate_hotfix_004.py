#!/usr/bin/env python3
"""
apply_source_contract_inventory_probe_v1_1_integrate_hotfix_004.py

SelfDoc tooling hotfix.

Patches only:
  selfdoc\probes\source_contract_inventory_probe_v1_1.py

Purpose:
  Integrate the proven hotfix_004 overlay logic into the v1.1 probe's
  normal post-inventory/final-row path.

Allowed:
  modify this SelfDoc probe
  create a backup of this SelfDoc probe
  rerun SelfDoc reports
  overwrite generated v1.1 SelfDoc reports

Still not allowed:
  edit DotTalk++ src\ or include\ source/header files
  apply source repair patches
  write DBFs
  rebuild HELP DATA
  modify CMDHELPCHK
  promote v1.1 to default
  move/delete project files

Design:
  This patch intentionally minimizes assumptions about the existing generated
  v1.1 probe. It adds a final postprocess layer that runs after inventory rows
  are built and before reports are written.

  The postprocess:
    - inspects the nine Batch 0 capture-only false positives from current source
    - requires marker-anchored parse to be clean
    - requires command/summary/(usage or syntax) shape
    - clears capture-only malformed/shape-review state in the generated row
    - marks those rows CONFIRMED / DO_NOT_REPAIR
    - leaves cmd_help.cpp as STALE_EVIDENCE / DO_NOT_REPAIR
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_integrate_hotfix_004"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
OUT_MD = REPORT_DIR / "source_contract_inventory_probe_v1_1_integrate_hotfix_004_status.md"
OUT_JSON = REPORT_DIR / "source_contract_inventory_probe_v1_1_integrate_hotfix_004_status.json"

EXPECTED_VERSION = "v1.1-integrated_hotfix_004"


HOTFIX_BLOCK = r