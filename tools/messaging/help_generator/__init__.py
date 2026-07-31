"""Cross-platform generated HELP maintenance utilities.

Phase 22AE.6.5.10EN-B v1.1 repairs the initial EN-B tooling so the
Python 3.12 maintenance package can prove itself cross-platform before any
future active HELP apply.

Boundary: this package prepares, validates, and reviews generated HELP artifacts.
It does not apply active HELP rows, mutate CMDHELPCHK, alter source command docs,
change latest pointers, or rebuild CDX/LMDB without a separate guarded gate.
"""

from .status import utc_stamp, sha256_file
from .schema import HELP_SCHEMA, validate_rows_by_table
from .candidate_rows import CommandCandidate, build_generated_candidate_rows
from .runtime_smoke import write_runtime_smoke
from .transcript_review import review_runtime_transcript

__all__ = [
    "CommandCandidate",
    "HELP_SCHEMA",
    "build_generated_candidate_rows",
    "validate_rows_by_table",
    "write_runtime_smoke",
    "review_runtime_transcript",
    "utc_stamp",
    "sha256_file",
]
