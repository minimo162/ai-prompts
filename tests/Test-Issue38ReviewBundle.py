#!/usr/bin/env python3
"""Targeted contract checks for the Issue #38 review archive."""

from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "catalog/acceptance/issue38/review/20260917-b73e0b5"
ARCHIVE_PATH = REVIEW_DIR / "issue38-review-b73e0b5.zip"
ARCHIVE_META_PATH = REVIEW_DIR / "archive.json"
MATRIX_PATH = REVIEW_DIR / "case-matrix.json"
SOURCE_CHECKPOINT = "b73e0b5a1a2c3f854ced3046b2a2648ddd0b8184"
GENERATED_ROBIN_SHA = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Issue38ReviewBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.archive_meta = json.loads(ARCHIVE_META_PATH.read_text(encoding="utf-8"))
        cls.archive_bytes = ARCHIVE_PATH.read_bytes()
        cls.archive = zipfile.ZipFile(ARCHIVE_PATH, "r")
        cls.names = cls.archive.namelist()
        cls.manifest = json.loads(cls.archive.read("MANIFEST.json").decode("utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.archive.close()

    def case(self, case_id: str) -> dict[str, object]:
        return next(case for case in self.matrix["cases"] if case["id"] == case_id)

    def test_review_is_non_mutating_and_not_issue_complete(self) -> None:
        self.assertEqual(self.matrix["source_checkpoint"], SOURCE_CHECKPOINT)
        self.assertFalse(self.matrix["issue_complete"])
        self.assertFalse(self.matrix["acceptance_conditions_changed"])
        self.assertEqual(self.matrix["copilot_sends_added"], 0)
        self.assertEqual(self.matrix["pad_runs_added"], 0)
        self.assertEqual(self.matrix["candidate_versions_changed"], 0)
        self.assertEqual(self.matrix["github_writes"], 0)

    def test_ex03_formal_auxiliary_and_guard_are_separate(self) -> None:
        ex03 = self.case("EX03")
        self.assertEqual(
            ex03["decision"]["status"],
            "FORMAL_FAIL_AUXILIARY_TWO_RUN_AND_GUARD_PASS_SEPARATE",
        )
        self.assertFalse(ex03["decision"]["formal_accepted"])
        self.assertTrue(ex03["decision"]["auxiliary_functional_passed"])
        self.assertTrue(ex03["decision"]["auxiliary_guard_passed"])
        guard = next(route for route in ex03["routes"] if route["classification"] == "AUXILIARY_LIVE_GUARD")
        self.assertEqual(guard["type_evaluation"], "NOT_ASSESSED_GUARD_EXITED_BEFORE_WRITE")
        self.assertFalse(guard["write_branch_entered"])

    def test_ex01_types_are_unassessed(self) -> None:
        ex01 = self.case("EX01")
        self.assertEqual(ex01["routes"][0]["type_evaluation"], "NOT_DIRECTLY_OBSERVED")

    def test_legacy_558_is_fully_classified_not_real_corruption(self) -> None:
        legacy = self.matrix["legacy_558"]
        classification = legacy["classification"]
        self.assertEqual(legacy["raw_difference_count"], 558)
        self.assertEqual(
            classification["cell_style_serialization_or_comparison_method_only"], 480
        )
        self.assertEqual(
            classification["row_dimension_serialization_or_comparison_method_only"], 48
        )
        self.assertEqual(
            classification["column_dimension_serialization_or_comparison_method_only"], 30
        )
        self.assertEqual(classification["actual_effective_changes"], 0)
        self.assertEqual(classification["unresolved"], 0)
        self.assertEqual(legacy["intentional_negative"]["detected_effective_changes"], 3)

    def test_archive_hash_and_sidecar_match(self) -> None:
        archive_sha = digest(self.archive_bytes)
        self.assertEqual(self.archive_meta["archive_sha256"], archive_sha)
        sidecar = (REVIEW_DIR / "issue38-review-b73e0b5.zip.sha256").read_text(
            encoding="ascii"
        )
        self.assertEqual(sidecar, f"{archive_sha}  issue38-review-b73e0b5.zip\n")

    def test_archive_has_unique_safe_sorted_names_without_bulk_images(self) -> None:
        self.assertEqual(self.names, sorted(self.names))
        self.assertEqual(len(self.names), len(set(self.names)))
        for name in self.names:
            parts = PurePosixPath(name).parts
            self.assertNotIn("..", parts)
            self.assertFalse(name.startswith("/"))
            self.assertNotIn("\\", name)
            self.assertFalse(name.lower().endswith((".jpg", ".jpeg", ".png")))
            self.assertNotIn("protected-files-before", name)
            self.assertNotIn("protected-files-after", name)
        self.assertLess(len(self.archive_bytes), 10 * 1024 * 1024)

    def test_manifest_covers_every_non_manifest_entry(self) -> None:
        entries = self.manifest["entries"]
        self.assertEqual(self.manifest["source_checkpoint"], SOURCE_CHECKPOINT)
        self.assertFalse(self.manifest["issue38_complete"])
        self.assertEqual(
            self.manifest["entry_count_excluding_manifest"], len(self.names) - 1
        )
        self.assertEqual(len(entries), len(self.names) - 1)
        by_name = {entry["archive_path"]: entry for entry in entries}
        self.assertEqual(set(by_name), set(self.names) - {"MANIFEST.json"})
        for name, entry in by_name.items():
            data = self.archive.read(name)
            self.assertEqual(entry["bytes"], len(data), name)
            self.assertEqual(entry["sha256"], digest(data), name)

    def test_complete_r11_candidate_and_generated_identity(self) -> None:
        candidate_names = [
            name for name in self.names if name.startswith("candidate/20260917-excel-r11/")
        ]
        self.assertEqual(len(candidate_names), 13)
        formal = self.archive.read("generated/EX03-r11-formal-generated.robin")
        auxiliary = self.archive.read("generated/EX03-r11-file-aux1-downloaded.robin")
        self.assertEqual(digest(formal), GENERATED_ROBIN_SHA)
        self.assertEqual(digest(auxiliary), GENERATED_ROBIN_SHA)
        self.assertEqual(formal, auxiliary)

    def test_required_diffs_and_workbooks_are_present(self) -> None:
        required_diffs = {
            "diffs/00-r10-to-r11-embedded-script.diff",
            "diffs/01-ex02-effective-format-comparator-and-tests.diff",
            "diffs/02-ex03-r11-candidate-builder-and-tests.diff",
            "diffs/03-ex03-r11-formal-analysis-and-file-aux-finalization.diff",
            "diffs/04-ex03-r11-existing-output-guard-tools-and-test.diff",
        }
        required_review_tools = {
            "review-tools/tools/Build-Issue38ReviewBundle.py",
            "review-tools/tests/Test-Issue38ReviewBundle.py",
        }
        required_workbooks = {
            "workbooks/EX02/fixtures/input-a.xlsx",
            "workbooks/EX02/fixtures/input-b.xlsx",
            "workbooks/EX02/fixtures/template.xlsx",
            "workbooks/EX02/outputs/run1-result.xlsx",
            "workbooks/EX02/outputs/run2-result.xlsx",
            "workbooks/EX02/negatives/one-cell-type-changed.xlsx",
            "workbooks/EX02/negatives/format-dimensions-changed.xlsx",
            "workbooks/EX03/fixtures/入力い.xlsx",
            "workbooks/EX03/fixtures/入力ろ.xlsx",
            "workbooks/EX03/fixtures/ひな形.xlsx",
            "workbooks/EX03/outputs/run1-result.xlsx",
            "workbooks/EX03/outputs/run2-result.xlsx",
            "workbooks/EX03/guard/existing-output-before.xlsx",
            "workbooks/EX03/guard/existing-output-after.xlsx",
        }
        self.assertTrue(required_diffs.issubset(self.names))
        self.assertTrue(required_review_tools.issubset(self.names))
        self.assertTrue(required_workbooks.issubset(self.names))
        for name in required_diffs:
            self.assertGreater(len(self.archive.read(name)), 100)
        for name in required_workbooks:
            self.assertTrue(self.archive.read(name).startswith(b"PK\x03\x04"), name)

    def test_all_558_classification_is_in_archive(self) -> None:
        path = (
            "evidence/catalog/acceptance/issue38/cycles/EX02-r5-G2/"
            "format-reconciliation/classification.json"
        )
        classification = json.loads(self.archive.read(path).decode("utf-8"))
        self.assertEqual(
            classification["classification_counts"],
            {"SERIALIZATION_OR_COMPARISON_METHOD_ONLY": 558},
        )
        self.assertEqual(
            classification["legacy_failure_counts"],
            {"cell_style": 480, "column_dimension": 30, "row_dimension": 48},
        )
        self.assertEqual(
            classification["decision"]["actual_effective_changes_in_positive_outputs"],
            0,
        )
        self.assertEqual(
            classification["decision"]["unresolved_legacy_failures"],
            0,
        )
        self.assertEqual(
            classification["negative_detection"]["status"],
            "PASS_EXACT_THREE_EFFECTIVE_CHANGES",
        )
        self.assertEqual(
            len(classification["negative_detection"]["effective_differences"]), 3
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
