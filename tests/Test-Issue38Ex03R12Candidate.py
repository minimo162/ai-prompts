#!/usr/bin/env python3
"""Non-live gates for the EX03 r12 successor candidate."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03CandidateR12.py"
SPEC = importlib.util.spec_from_file_location("issue38_ex03_r12_builder", BUILDER_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)
VERSION = ROOT / "copilot/versions/20260917-excel-r12"
R11 = ROOT / "copilot/versions/20260917-excel-r11"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def newline_metrics(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "crlf_count": crlf,
        "lf_only_count": raw.count(b"\n") - crlf,
        "final_lf": raw.endswith(b"\n"),
        "final_crlf": raw.endswith(b"\r\n"),
    }


class Issue38Ex03R12CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((VERSION / "manifest.json").read_text(encoding="utf-8"))
        cls.instruction = (VERSION / "agent-instructions.txt").read_text(encoding="utf-8")
        cls.bundle = (VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt").read_text(encoding="utf-8")
        cls.script_path = VERSION / BUILDER.SCRIPT_SUPPORT
        cls.normal_path = VERSION / BUILDER.NORMAL_SUPPORT
        cls.negative_path = VERSION / BUILDER.NEGATIVE_SUPPORT
        cls.script = cls.script_path.read_text(encoding="utf-8")
        cls.normal = cls.normal_path.read_text(encoding="utf-8")
        cls.negative = cls.negative_path.read_text(encoding="utf-8")

    def test_frozen_r11_tree_is_byte_identical_to_base_commit(self):
        prefix = "copilot/versions/20260917-excel-r11"
        tracked = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BUILDER.BASE_COMMIT, prefix],
            cwd=ROOT,
            text=True,
        ).splitlines()
        current = sorted(
            path.relative_to(ROOT).as_posix() for path in R11.rglob("*") if path.is_file()
        )
        self.assertEqual(current, tracked)
        for relative in tracked:
            with self.subTest(relative=relative):
                expected_blob = subprocess.check_output(
                    ["git", "rev-parse", f"{BUILDER.BASE_COMMIT}:{relative}"],
                    cwd=ROOT,
                    text=True,
                ).strip()
                actual_blob = subprocess.check_output(
                    ["git", "hash-object", "--path", relative, str(ROOT / relative)],
                    cwd=ROOT,
                    text=True,
                ).strip()
                self.assertEqual(actual_blob, expected_blob)

    def test_fixed_request_spec_expected_and_protected_inputs_are_unchanged(self):
        actual = {name: sha256(path) for name, path in BUILDER.INPUTS.items()}
        self.assertEqual(actual, BUILDER.EXPECTED)
        self.assertEqual(
            [actual[name] for name in ("fixed_request", "fixed_spec", "fixed_expected")],
            [
                "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
                "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
                "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
            ],
        )

    def test_r4_correction_matches_actual_r11_bytes_without_mutating_r11(self):
        correction = json.loads(BUILDER.CORRECTION.read_text(encoding="utf-8"))
        actual = newline_metrics(BUILDER.INPUTS["r11_robin"])
        self.assertEqual(correction["frozen_manifest"]["sha256"], sha256(R11 / "manifest.json"))
        self.assertFalse(correction["frozen_manifest"]["modified"])
        self.assertEqual(correction["correction"]["recorded_value"], 87)
        self.assertEqual(correction["correction"]["corrected_value"], 57)
        self.assertEqual(correction["correction"]["crlf_count"], 110)
        self.assertEqual(correction["correction"]["lf_only_count"], actual["lf_only_count"])
        self.assertEqual(correction["correction"]["source_sha256"], actual["sha256"])
        self.assertEqual(correction["unaffected_source_candidate_record"]["lf_only_count"], 87)

    def test_manifest_sha_and_newline_metrics_come_from_actual_files(self):
        self.assertTrue(self.manifest["r4_file_provenance"]["all_metrics_computed_from_actual_files"])
        for record in self.manifest["source_files"]:
            path = VERSION / record["path"]
            self.assertEqual(path.stat().st_size, record["bytes"])
            self.assertEqual(sha256(path), record["sha256"])
        for record in self.manifest["support_files"]:
            with self.subTest(path=record["path"]):
                actual = newline_metrics(VERSION / record["path"])
                for key, value in actual.items():
                    self.assertEqual(record[key], value, key)

        provenance = self.manifest["r4_file_provenance"]
        for key, path in (
            ("r11_frozen_recopy", BUILDER.INPUTS["r11_robin"]),
            ("r11_manifest_correction", BUILDER.CORRECTION),
            ("r2r3_fixed_script", BUILDER.INPUTS["r2r3_script"]),
            ("r2r3_fixed_normal", BUILDER.INPUTS["r2r3_normal"]),
            ("r2r3_fixed_negative", BUILDER.INPUTS["r2r3_negative"]),
            ("r2r3_trial_normal_recopy", BUILDER.INPUTS["trial_normal_recopy"]),
            ("r2r3_trial_negative_recopy", BUILDER.INPUTS["trial_negative_recopy"]),
        ):
            with self.subTest(key=key):
                for metric, value in newline_metrics(path).items():
                    self.assertEqual(provenance[key][metric], value, metric)

    def test_support_script_and_embedded_script_differ_only_by_final_lf(self):
        embedded_normal = BUILDER.embedded_script(self.normal)
        embedded_negative = BUILDER.embedded_script(self.negative)
        self.assertTrue(self.script.endswith("\n"))
        self.assertFalse(embedded_normal.endswith("\n"))
        self.assertEqual(embedded_normal + "\n", self.script)
        self.assertEqual(embedded_negative, embedded_normal)
        provenance = self.manifest["r4_file_provenance"]
        self.assertTrue(provenance["support_script_final_lf"])
        self.assertFalse(provenance["embedded_script_final_lf"])
        self.assertTrue(provenance["embedded_equals_support_without_final_lf"])
        self.assertEqual(
            provenance["embedded_script"]["sha256"],
            hashlib.sha256(embedded_normal.encode("utf-8")).hexdigest(),
        )

    def test_json_file_handoff_precedes_work_and_has_no_value_interpolation(self):
        output_guard = self.normal.index("IF (File.IfFile.Exists")
        first_source_read = self.normal.index("Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess")
        first_json_write = self.normal.index("File.WriteText File:")
        work_launch = self.normal.index("Instance=> Work")
        run_script = self.normal.index("Scripting.RunPowershellScript.RunScript")
        self.assertLess(output_guard, first_source_read)
        self.assertLess(first_source_read, first_json_write)
        self.assertLess(first_json_write, work_launch)
        self.assertLess(work_launch, run_script)
        self.assertEqual(self.normal.count("File.WriteText File:"), 8)
        self.assertEqual(self.normal.count("TextToWrite: TextSource"), 7)
        self.assertEqual(self.normal.count("TextToWrite: RunModeJson"), 1)
        self.assertEqual(self.script.count("Get-Content -LiteralPath (Join-Path $jsonRoot 'source-"), 7)
        self.assertEqual(self.script.count("Get-Content -LiteralPath (Join-Path $jsonRoot 'mode.json')"), 1)
        for forbidden in ("%TextSource", "%RunMode", "Invoke-Expression", "ScriptBlock]::Create"):
            self.assertNotIn(forbidden, self.script)
        self.assertNotIn("[double]", self.script)
        self.assertNotIn("[decimal]", self.script)

    def test_success_gate_encloses_all_numeric_writes_and_save_as(self):
        script_at = self.normal.index("Scripting.RunPowershellScript.RunScript")
        gate = self.normal.index(
            f"IF PowershellOutput = {BUILDER.robin_literal(BUILDER.SUCCESS_OUTPUT)} THEN"
        )
        mode_gate = self.normal.index(
            f"IF RunMode = {BUILDER.robin_literal(BUILDER.NORMAL_MODE)} THEN", gate
        )
        numeric_writes = [
            line for line in self.normal.splitlines()
            if "Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource" in line
        ]
        save_lines = [line for line in self.normal.splitlines() if "Excel.SaveExcel.SaveAs" in line]
        self.assertLess(script_at, gate)
        self.assertLess(gate, mode_gate)
        self.assertEqual(len(numeric_writes), 5)
        self.assertTrue(all(line.startswith("            ") for line in numeric_writes))
        self.assertEqual(len(save_lines), 1)
        self.assertTrue(save_lines[0].startswith("            "))
        self.assertEqual(self.normal.count("SET NumericWriteEntered TO True"), 1)
        self.assertEqual(self.normal.count("SET SaveAsEntered TO True"), 1)
        self.assertIn("SET TransferState TO $'''SCRIPT_NOT_SUCCESS_NO_SAVE'''", self.normal)
        self.assertIn("SET TransferState TO $'''MODE_NOT_NORMAL_NO_SAVE'''", self.normal)

    def test_exception_is_after_temporary_format_and_restored_before_error_result(self):
        temporary_format = self.script.index("$cell.NumberFormat = '@'")
        injection = self.script.index("throw 'ISSUE38_INTENTIONAL_AFTER_FORMAT_CHANGE'")
        value_write = self.script.index("$cell.Value2 = [string]$write[3]")
        finally_restore = self.script.index("finally {\n                $cell.NumberFormat = $beforeFormat")
        negative_format_check = self.script.index("throw 'NEGATIVE_FORMAT_NOT_RESTORED'")
        self.assertLess(temporary_format, injection)
        self.assertLess(injection, value_write)
        self.assertLess(value_write, finally_restore)
        self.assertLess(finally_restore, negative_format_check)
        for fragment in (
            "NEGATIVE_VALUE_CHANGED",
            "NEGATIVE_PREFIX_CHANGED",
            "NEGATIVE_FORMULA_CHANGED",
            "format_restored = $true",
            "value_unchanged = $true",
        ):
            self.assertIn(fragment, self.script)

    def test_normal_and_negative_prepared_sources_differ_only_by_mode_assignment(self):
        changed = self.normal.replace(
            "SET RunMode TO $'''NORMAL'''",
            "SET RunMode TO $'''INJECT_AFTER_FORMAT_CHANGE'''",
            1,
        )
        self.assertEqual(changed, self.negative)
        self.assertTrue(
            self.manifest["r4_file_provenance"]["normal_negative_only_mode_assignment_diff"]
        )
        self.assertTrue(
            all(self.manifest["r4_file_provenance"]["r2r3_trial_path_only_correspondence"].values())
        )

    def test_independence_formal_code_block_and_non_inheritance_boundaries(self):
        new_source = self.instruction + self.script + self.normal + self.negative
        for term in BUILDER.FIXED_COMPLETION_TERMS + BUILDER.UNIQUE_GRADER_STRINGS + ["100%"]:
            self.assertNotIn(term, new_source, term)
        for term in BUILDER.FIXED_COMPLETION_TERMS + BUILDER.UNIQUE_GRADER_STRINGS:
            self.assertNotIn(term, self.bundle, term)
        self.assertIn("回答は全工程を一つのtextコードブロックへ入れます", self.instruction)
        self.assertEqual(self.manifest["evidence"]["formal_text_code_block_required_count"], 1)
        self.assertFalse(self.manifest["inherits_live_acceptance"])
        self.assertEqual(self.manifest["evidence"]["copilot_send_count"], 0)
        self.assertEqual(self.manifest["evidence"]["integrated_ex03_run_count"], 0)
        self.assertEqual(self.manifest["evidence"]["r12_pad_save_recopy_count"], 0)
        self.assertFalse(self.manifest["evidence"]["r2r3_trial_results_inherited"])
        self.assertEqual(self.manifest["evidence"]["full_regression"], "NOT_RUN_BY_SCOPE")
        self.assertTrue(self.manifest["evidence"]["legacy_558_failure_preserved"])
        for stale in (
            "source_pad_action_count",
            "synthetic_pad_run_count",
            "source_reused_exact_bytes",
        ):
            self.assertNotIn(stale, self.manifest["evidence"])

    def test_builder_is_reproducible_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="issue38-r12-test-") as temporary:
            rebuilt = Path(temporary) / BUILDER.VERSION
            with contextlib.redirect_stdout(io.StringIO()):
                BUILDER.build(rebuilt)
            committed_files = {
                path.relative_to(VERSION) for path in VERSION.rglob("*") if path.is_file()
            }
            rebuilt_files = {
                path.relative_to(rebuilt) for path in rebuilt.rglob("*") if path.is_file()
            }
            self.assertEqual(rebuilt_files, committed_files)
            for relative in sorted(committed_files):
                with self.subTest(relative=relative):
                    self.assertEqual((rebuilt / relative).read_bytes(), (VERSION / relative).read_bytes())
            with self.assertRaisesRegex(ValueError, "sealed versions must not be overwritten"):
                BUILDER.build(rebuilt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
