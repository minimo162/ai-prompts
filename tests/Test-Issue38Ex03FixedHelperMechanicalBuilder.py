#!/usr/bin/env python3
"""Focused non-live tests for the fixed EX03 mechanical Robin builder."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    ROOT
    / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper-mechanical-builder/Build.py"
)
SPEC = importlib.util.spec_from_file_location("issue38_fixed_helper_mechanical_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)

A4_GENERATED = ROOT / "catalog/acceptance/issue38/cycles/EX03-R12-FIXED-HELPER-A4-G1/generated.robin"
A4_ASSESSMENT = ROOT / "catalog/acceptance/issue38/cycles/EX03-R12-FIXED-HELPER-A4-G1/generation-assessment.json"
EXPECTED_A4_GENERATED_SHA256 = "eb5648631466da3431a21cf8df98fb06e5fece8876c3705b6483b4d74b58e290"
EXPECTED_A4_ASSESSMENT_SHA256 = "3313eebe03904b28a8e733d54ffa8aeae9d1f63bb7ceacdcbadb8f48089405d9"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue38Ex03FixedHelperMechanicalBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(builder.WIRING.read_text(encoding="utf-8"))
        cls.result = builder.build()
        cls.robin = cls.result.robin.decode("utf-8")
        cls.verification = cls.result.verification

    def test_fixed_a4_sources_components_rules_and_failed_generation_are_preserved(self):
        for name, expected in builder.EXPECTED_SHA256.items():
            with self.subTest(name=name):
                self.assertEqual(self.verification["inputs"][name]["sha256"], expected)
        self.assertEqual(self.verification["component_sources"]["count"], 12)
        self.assertEqual(
            self.verification["component_sources"]["sha256"],
            builder.EXPECTED_COMPONENT_SHA256,
        )
        self.assertEqual(
            self.verification["assembly_rules"]["ids"],
            list(builder.RULE_COMPONENTS),
        )
        self.assertEqual(sha256(A4_GENERATED), EXPECTED_A4_GENERATED_SHA256)
        self.assertEqual(sha256(A4_ASSESSMENT), EXPECTED_A4_ASSESSMENT_SHA256)
        builder_source = BUILDER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("EX03-R12-FIXED-HELPER-A4-G1/generated.robin", builder_source)
        self.assertNotIn("EX03-R12-FIXED-HELPER-A4-G1/generation-assessment.json", builder_source)

    def test_normal_spec_regenerates_byte_identically(self):
        second = builder.build()
        self.assertEqual(self.result.robin, second.robin)
        self.assertEqual(builder.verification_bytes(self.result), builder.verification_bytes(second))
        self.assertEqual(builder.OUTPUT.read_bytes(), self.result.robin)
        self.assertEqual(builder.VERIFICATION.read_bytes(), builder.verification_bytes(self.result))
        self.assertEqual(
            hashlib.sha256(self.result.robin).hexdigest(),
            self.verification["generated"]["sha256"],
        )

    def test_declared_parameter_replacements_only(self):
        self.assertGreater(len(self.result.replacements), 0)
        for record in self.result.replacements:
            with self.subTest(component=record["component"], slot=record["slot"]):
                self.assertTrue(
                    set(record["parameters"]).issubset(
                        builder.ALLOWED_PARAMETERS[record["component"]]
                    )
                )
        self.assertEqual(
            self.verification["replacement_record_count"],
            len(self.result.replacements),
        )

    def test_exact_8_5_2_12_structure_and_coordinate_references(self):
        structure = self.verification["structure"]
        self.assertEqual(structure["json_file_write_count"], 8)
        self.assertEqual(structure["source_json_file_write_count"], 7)
        self.assertEqual(structure["mode_json_file_write_count"], 1)
        self.assertEqual(structure["numeric_write_count"], 5)
        self.assertEqual(structure["readback_rectangle_count"], 2)
        self.assertEqual(structure["json_value_type_comparison_count"], 12)

        for index, mapping in enumerate(self.spec["text_mappings"], 1):
            with self.subTest(kind="text", index=index):
                self.assertIn(
                    f"SET TextSource{index} TO {mapping['source_reference']}",
                    self.robin,
                )
                self.assertIn(builder.robin_path(mapping["source_json_path"]), self.robin)
                invocation = json.loads(builder.INVOCATION.read_text(encoding="utf-8"))
                self.assertEqual(
                    invocation["text_writes"][index - 1],
                    {
                        "source_index": index,
                        "source_label": mapping["source_reference"],
                        "sheet": mapping["helper_target_sheet"],
                        "cell": mapping["helper_target_cell"],
                    },
                )

        for index, mapping in enumerate(self.spec["numeric_mappings"], 1):
            column, row = builder.split_cell(mapping["target_cell"])
            with self.subTest(kind="numeric", index=index):
                self.assertIn(
                    f"SET NumberSource{index} TO {mapping['source_reference']}",
                    self.robin,
                )
                self.assertIn(
                    f"Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource{index} Column: $'''{column}''' Row: {row}",
                    self.robin,
                )

        for readback in self.spec["readbacks"]:
            start_column, start_row, end_column, end_row = builder.split_range(readback["range"])
            self.assertIn(
                f"StartColumn: $'''{start_column}''' StartRow: {start_row} EndColumn: $'''{end_column}''' EndRow: {end_row} GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> {readback['variable']}",
                self.robin,
            )

        for position in self.spec["comparison_contract"]["positions"]:
            index = position["order"]
            with self.subTest(kind="comparison", index=index):
                self.assertIn(
                    f"SET CompareSource{index} TO {position['source_reference']}",
                    self.robin,
                )
                self.assertIn(
                    f"SET Saved{index} TO {position['saved_reference']}",
                    self.robin,
                )
                self.assertIn(
                    f"SET Position{index}ValueTypeMatch TO CompareSource{index}Json = Saved{index}Json",
                    self.robin,
                )

    def test_guard_success_save_and_failure_close_contract(self):
        structure = self.verification["structure"]
        self.assertTrue(structure["guard_before_inputs_work_and_helper"])
        self.assertTrue(structure["save_as_only_after_exact_success_and_normal"])
        self.assertEqual(structure["save_as_count"], 1)
        self.assertEqual(structure["failure_close_without_save_count"], 2)
        self.assertTrue(structure["balanced_control_blocks"])
        self.assertEqual(structure["new_pad_loop_count"], 0)
        self.assertEqual(structure["forbidden_runtime_token_count"], 0)

    def test_decoded_launcher_is_fixed_and_parses_without_execution(self):
        decoded = builder.embedded_script(self.robin)
        restored = decoded.encode("utf-8") + b"\n"
        self.assertEqual(restored, builder.LAUNCHER.read_bytes())
        self.assertEqual(
            hashlib.sha256(restored).hexdigest(),
            builder.EXPECTED_SHA256["launcher"],
        )
        encoded = base64.b64encode(decoded.encode("utf-8")).decode("ascii")
        parser = f"""
$source = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}'))
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors) | Out-Null
if ($errors.Count -ne 0) {{ $errors | ForEach-Object {{ $_.Message }}; exit 1 }}
"""
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", parser],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_missing_mapping_is_rejected_before_output(self):
        cases = []
        missing_text = copy.deepcopy(self.spec)
        missing_text["text_mappings"].pop()
        cases.append(missing_text)
        missing_comparison = copy.deepcopy(self.spec)
        missing_comparison["comparison_contract"]["positions"].pop()
        cases.append(missing_comparison)
        for broken in cases:
            with self.subTest(counts=(len(broken["text_mappings"]), len(broken["comparison_contract"]["positions"]))):
                with tempfile.TemporaryDirectory(prefix="issue38-builder-missing-") as temporary:
                    absent = Path(temporary) / "must-not-exist.robin"
                    with self.assertRaisesRegex(builder.BuildError, "mapping count missing"):
                        result = builder.build(wiring_override=broken)
                        absent.write_bytes(result.robin)
                    self.assertFalse(absent.exists())

    def test_duplicate_source_and_target_mappings_are_rejected_before_output(self):
        cases = []
        duplicate_source = copy.deepcopy(self.spec)
        first = duplicate_source["text_mappings"][0]
        second = duplicate_source["text_mappings"][1]
        for key in (
            "input_id", "input_workbook", "input_sheet", "input_cell",
            "data_table_variable", "data_table_index", "source_reference",
        ):
            second[key] = copy.deepcopy(first[key])
        cases.append(("duplicate source mapping", duplicate_source))

        duplicate_target = copy.deepcopy(self.spec)
        duplicate_target["text_mappings"][1]["helper_target_sheet"] = duplicate_target["text_mappings"][0]["helper_target_sheet"]
        duplicate_target["text_mappings"][1]["helper_target_cell"] = duplicate_target["text_mappings"][0]["helper_target_cell"]
        cases.append(("duplicate target mapping", duplicate_target))

        for message, broken in cases:
            with self.subTest(message=message):
                with tempfile.TemporaryDirectory(prefix="issue38-builder-duplicate-") as temporary:
                    absent = Path(temporary) / "must-not-exist.robin"
                    with self.assertRaisesRegex(builder.BuildError, message):
                        result = builder.build(wiring_override=broken)
                        absent.write_bytes(result.robin)
                    self.assertFalse(absent.exists())

    def test_tampered_launcher_is_rejected_before_output(self):
        tampered = builder.LAUNCHER.read_bytes().replace(b"HELPER_NOT_FOUND", b"HELPER_NOT_F0UND", 1)
        self.assertNotEqual(tampered, builder.LAUNCHER.read_bytes())
        with tempfile.TemporaryDirectory(prefix="issue38-builder-launcher-") as temporary:
            absent = Path(temporary) / "must-not-exist.robin"
            with self.assertRaisesRegex(builder.BuildError, "fixed launcher SHA mismatch before generation"):
                result = builder.build(launcher_override=tampered)
                absent.write_bytes(result.robin)
            self.assertFalse(absent.exists())

    def test_no_grader_values_a4_repair_or_live_acceptance_claim(self):
        for value in ("春", "夏", "秋", "項目甲", "項目乙", "日本語", "100%"):
            with self.subTest(value=value):
                self.assertNotIn(value, self.robin)
        boundaries = self.verification["boundaries"]
        self.assertFalse(boundaries["fixed_expected_values_used_for_generation"])
        self.assertFalse(boundaries["a4_copilot_generated_robin_used_for_generation"])
        self.assertFalse(boundaries["a4_generated_robin_modified"])
        self.assertFalse(boundaries["helper_invocation_launcher_or_wiring_modified"])
        self.assertEqual(boundaries["copilot_send_count"], 0)
        self.assertEqual(boundaries["pad_run_count"], 0)
        self.assertEqual(boundaries["excel_run_count"], 0)
        self.assertFalse(boundaries["copilot_generation_pass_inherited"])
        self.assertFalse(boundaries["ex03_acceptance_pass_claimed"])

    def test_cli_check_reproduces_committed_files(self):
        completed = subprocess.run(
            ["python", str(BUILDER_PATH), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertEqual(summary["operation"], "CHECK_BYTE_IDENTICAL")
        self.assertEqual(summary["generated_sha256"], self.verification["generated"]["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
