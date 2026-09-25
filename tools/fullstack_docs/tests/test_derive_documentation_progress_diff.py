#!/usr/bin/env python3
"""field_differences explains a FAIL; it must never be able to create a PASS.

The check's verdict is the TEXT comparison in main(). These tests pin the two
ways an explainer can lie: reporting no differences when it could not parse, and
reporting spurious differences that send someone re-deriving to chase formatting.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_documentation_progress import (  # noqa: E402
    VOLATILE_FIELDS,
    field_differences,
    flatten,
)


def doc(**over):
    base = {
        "as_of_date": "2026-09-14",
        "current_vertical": {
            "run_id": "DOCFLUSH-20260914-001",
            "canonical_harvest_tables_exported": 10,
            "canonical_harvest_tables_carried_stale": 4,
            "website_static_pages_built": 177,
            "measured_fields": ["a", "b"],
        },
    }
    base["current_vertical"].update(over)
    return json.dumps(base, indent=2)


class TestFieldDifferences(unittest.TestCase):
    def test_identical_documents_report_nothing(self):
        self.assertEqual(field_differences(doc(), doc()), [])

    def test_volatile_field_is_never_reported(self):
        a = doc()
        b = a.replace('"as_of_date": "2026-09-14"', '"as_of_date": "2026-09-25"')
        self.assertNotEqual(a, b)
        self.assertEqual(field_differences(a, b), [])
        self.assertIn("as_of_date", VOLATILE_FIELDS)

    def test_the_real_promotion_is_named_with_both_values(self):
        rows = field_differences(
            doc(),
            doc(canonical_harvest_tables_exported=14,
                canonical_harvest_tables_carried_stale=0),
        )
        self.assertEqual(
            rows,
            [("current_vertical.canonical_harvest_tables_carried_stale", 4, 0),
             ("current_vertical.canonical_harvest_tables_exported", 10, 14)],
        )

    def test_a_reordered_name_list_is_not_a_difference(self):
        # measured_fields order is not meaningful. A per-index diff would report
        # every element as changed and bury the field that actually moved.
        self.assertEqual(
            field_differences(doc(), doc(measured_fields=["b", "a"])), []
        )

    def test_a_changed_name_list_IS_a_difference(self):
        rows = field_differences(doc(), doc(measured_fields=["a", "b", "c"]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "current_vertical.measured_fields")

    def test_an_added_field_reports_absent_on_the_side_that_lacks_it(self):
        rows = field_differences(doc(), doc(brand_new_metric=7))
        self.assertEqual(rows, [("current_vertical.brand_new_metric", "<absent>", 7)])

    def test_unparseable_returns_None_not_empty(self):
        # The distinction that matters: None means "cannot say". An empty list
        # printed for a missing artifact would read as clean.
        self.assertIsNone(field_differences("", doc()))
        self.assertIsNone(field_differences("not json at all", doc()))
        self.assertIsNotNone(field_differences(doc(), doc()))

    def test_flatten_emits_dotted_scalar_leaves(self):
        flat = dict(flatten(json.loads(doc())))
        self.assertEqual(flat["current_vertical.run_id"], "DOCFLUSH-20260914-001")
        self.assertEqual(flat["current_vertical.website_static_pages_built"], 177)
        self.assertEqual(flat["as_of_date"], "2026-09-14")


if __name__ == "__main__":
    unittest.main()
