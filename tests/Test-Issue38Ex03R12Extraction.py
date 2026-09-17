#!/usr/bin/env python3
"""Regression gates for the r12-only Robin PowerShell extraction path."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "tools/Analyze-Issue38Ex03R12Generation.py"
LEGACY_EXTRACTOR = ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py"
VERSION = ROOT / "copilot/versions/20260917-excel-r12"
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r12-G1"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ANALYZER = load("issue38_r12_generation_analyzer", ANALYZER_PATH)


class Issue38Ex03R12ExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.teaching = (VERSION / "support/EX03-R12-Prepared-Normal.robin").read_text(
            encoding="utf-8"
        )
        cls.generated = (CYCLE / "generated.robin").read_text(encoding="utf-8")

    def parse(self, robin: str) -> list[dict[str, object]]:
        embedded = ANALYZER.extract_embedded_script(robin)
        return ANALYZER.parser_tool.parse_powershell(embedded)

    def test_normal_teaching_uses_same_extractor_and_has_zero_errors(self):
        embedded = ANALYZER.extract_embedded_script(self.teaching)
        support = (VERSION / "support/EX03-R12-JSON-File-Handoff.ps1.txt").read_text(
            encoding="utf-8"
        )
        self.assertEqual(embedded, support.rstrip("\r\n"))
        self.assertEqual(self.parse(self.teaching), [])

    def test_real_corrupt_generation_reports_only_the_real_missing_parenthesis(self):
        errors = self.parse(self.generated)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            (errors[0]["error_id"], errors[0]["line"], errors[0]["column"]),
            ("MissingEndParenthesisInMethodCall", 137, 47),
        )
        self.assertEqual(errors[0]["token"], "")
        embedded_lines = ANALYZER.extract_embedded_script(self.generated).splitlines()
        self.assertEqual(
            embedded_lines[136],
            "[Console]::Out.Write([string]($result | press)",
        )

    def test_only_the_four_observed_blank_line_deletions_still_parse(self):
        lines = self.teaching.replace("\r\n", "\n").rstrip("\n").split("\n")
        for line_number in sorted((67, 123, 142, 156), reverse=True):
            self.assertEqual(lines[line_number - 1], "")
            del lines[line_number - 1]
        without_four_blank_lines = "\n".join(lines)
        self.assertEqual(self.parse(without_four_blank_lines), [])

    def test_audit_uses_the_same_extractor_for_generated_and_teaching(self):
        result = ANALYZER.audit()
        parser = result["powershell_parser"]
        self.assertEqual(parser["generated_error_count"], 1)
        self.assertEqual(parser["prepared_script_error_count"], 0)
        self.assertTrue(parser["prepared_embedded_matches_support_without_final_newline"])
        self.assertIn("without legacy four-character deindent", parser["extractor"])
        self.assertEqual(
            result["decision"],
            "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD",
        )

    def test_legacy_extractor_is_frozen_for_older_version_paths(self):
        self.assertEqual(
            hashlib.sha256(LEGACY_EXTRACTOR.read_bytes()).hexdigest(),
            "9c8f2cab7e154e38351251327c4f31fe6b53ff0fc5665c8bc8f6504c14545746",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
