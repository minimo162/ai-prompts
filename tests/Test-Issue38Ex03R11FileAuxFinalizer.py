#!/usr/bin/env python3
"""Regression tests for the EX03-r11 FILE-AUX1 acceptance aggregator.

The four R1 review negatives are applied to deep-copied JSON objects only.  No
preserved evidence file is edited while reproducing the defect or testing the
fix.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FINALIZER_PATH = ROOT / "tools/Finalize-Issue38Ex03R11FileAux.py"
MODULE_SPEC = importlib.util.spec_from_file_location("issue38_file_aux_finalizer", FINALIZER_PATH)
FINALIZER = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(FINALIZER)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue38Ex03R11FileAuxFinalizerTests(unittest.TestCase):
    def validate_with_mutation(self, report_name: str, mutator, run_number: int = 1):
        target = (FINALIZER.CYCLE / f"run{run_number}" / report_name).resolve()
        original_load = FINALIZER.load

        def load_with_mutation(path: Path):
            value = original_load(path)
            if Path(path).resolve() == target:
                value = copy.deepcopy(value)
                mutator(value)
            return value

        with mock.patch.object(FINALIZER, "load", side_effect=load_with_mutation):
            return FINALIZER.validate_run(run_number)

    def assert_mutation_rejected(self, report_name: str, mutator, run_number: int = 1):
        with self.assertRaises(ValueError):
            self.validate_with_mutation(report_name, mutator, run_number)

    def test_existing_run1_and_run2_records_pass(self):
        for run_number in (1, 2):
            with self.subTest(run=run_number):
                result = FINALIZER.validate_run(run_number)
                self.assertTrue(all(result["checks"].values()))

    def test_r1_negative_typed_report_wrong_output_sha_is_rejected(self):
        def mutate(value):
            value["output"]["sha256_before"] = "0" * 64
            value["output"]["sha256_after"] = "0" * 64

        self.assert_mutation_rejected("typed-transfer.json", mutate)

    def test_r1_negative_typed_report_empty_mappings_is_rejected(self):
        self.assert_mutation_rejected(
            "typed-transfer.json", lambda value: value.__setitem__("mappings", [])
        )

    def test_r1_negative_native_report_wrong_output_sha_is_rejected(self):
        def mutate(value):
            value["sha256_before"]["output"] = "0" * 64
            value["sha256_after"]["output"] = "0" * 64

        self.assert_mutation_rejected("native-styles.json", mutate)

    def test_r1_negative_native_report_empty_bounds_and_counts_is_rejected(self):
        def mutate(value):
            value["bounds"] = {}
            value["difference_attribute_counts"] = {}
            value["difference_location_counts"] = {}

        self.assert_mutation_rejected("native-styles.json", mutate)

    def test_missing_required_keys_are_rejected_even_when_status_remains_pass(self):
        cases = [
            ("typed-transfer.json", lambda value: value.pop("mappings")),
            ("typed-transfer.json", lambda value: value["output"].pop("sha256_before")),
            ("native-styles.json", lambda value: value.pop("bounds")),
            ("native-styles.json", lambda value: value["sha256_before"].pop("output")),
        ]
        for report_name, mutator in cases:
            with self.subTest(report=report_name, mutation=mutator):
                self.assert_mutation_rejected(report_name, mutator)

    def test_case_run_source_and_coordinate_binding_are_enforced(self):
        cases = [
            (
                "typed-transfer.json",
                lambda value: value.__setitem__("kind", "EX02_FIXED_TEXT_NUMBER_TYPED_TRANSFER"),
            ),
            (
                "typed-transfer.json",
                lambda value: value.__setitem__("run_label", "EX03-R11-FILE-AUX1-RUN2"),
            ),
            (
                "typed-transfer.json",
                lambda value: value["mappings"][0].__setitem__("target_cell", "A1"),
            ),
            (
                "native-styles.json",
                lambda value: value["paths"].__setitem__("reference", value["paths"]["output"]),
            ),
        ]
        for report_name, mutator in cases:
            with self.subTest(report=report_name, mutation=mutator):
                self.assert_mutation_rejected(report_name, mutator)

    def test_two_run_record_is_bound_to_both_artifacts(self):
        run1 = FINALIZER.validate_run(1)
        run2 = FINALIZER.validate_run(2)
        report = FINALIZER.load(FINALIZER.CYCLE / "two-run-semantic.json")
        FINALIZER.validate_two_run_report(report, run1, run2)

        wrong_sha = copy.deepcopy(report)
        wrong_sha["run2"]["sha256_before"] = "0" * 64
        with self.assertRaises(ValueError):
            FINALIZER.validate_two_run_report(wrong_sha, run1, run2)

        missing_count = copy.deepcopy(report)
        missing_count.pop("checked_cells")
        with self.assertRaises(ValueError):
            FINALIZER.validate_two_run_report(missing_count, run1, run2)

    def test_validation_does_not_modify_preserved_records(self):
        paths = sorted(
            path
            for run_number in (1, 2)
            for path in (FINALIZER.CYCLE / f"run{run_number}").iterdir()
            if path.is_file()
        )
        before = {path: sha256(path) for path in paths}
        FINALIZER.validate_run(1)
        FINALIZER.validate_run(2)
        after = {path: sha256(path) for path in paths}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
