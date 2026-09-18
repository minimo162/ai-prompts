#!/usr/bin/env python3
"""Focused non-live checks for the fixed-helper Copilot A4 wiring candidate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA4.py"
SPEC = importlib.util.spec_from_file_location(
    "issue38_fixed_helper_copilot_a4_builder",
    BUILDER_PATH,
)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)

CANDIDATE = builder.DESTINATION
MANIFEST_PATH = CANDIDATE / "manifest.json"
INSTRUCTION_PATH = CANDIDATE / "agent-instructions.txt"
CONDITIONS_PATH = CANDIDATE / "send-conditions.txt"
BODY_PATH = CANDIDATE / "submitted-body.txt"
BUNDLE_PATH = CANDIDATE / "knowledge" / builder.A4_BUNDLE_NAME
WIRING_PATH = CANDIDATE / "wiring-spec.json"
RULES_PATH = CANDIDATE / "assembly-rules.json"
DELTA_PATH = CANDIDATE / "instruction-delta.json"
COVERAGE_PATH = CANDIDATE / "COVERAGE.md"
PLACEMENT_PATH = CANDIDATE / "PLACEMENT.md"
VERIFICATION_PATH = CANDIDATE / "non-live-verification.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Issue38Ex03FixedHelperCopilotCandidateA4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST_PATH)
        cls.wiring = load(WIRING_PATH)
        cls.rules = load(RULES_PATH)
        cls.delta = load(DELTA_PATH)
        cls.verification = load(VERIFICATION_PATH)
        cls.instruction = INSTRUCTION_PATH.read_text(encoding="utf-8")
        cls.conditions = CONDITIONS_PATH.read_text(encoding="utf-8")
        cls.body = BODY_PATH.read_text(encoding="utf-8")
        cls.bundle_bytes = BUNDLE_PATH.read_bytes()
        cls.bundle = cls.bundle_bytes.decode("utf-8")

    def test_candidate_and_route_were_unused_at_base_commit(self):
        for value in (builder.CANDIDATE_ID, builder.ROUTE_ID):
            completed = subprocess.run(
                ["git", "grep", "-F", value, builder.BASE_COMMIT, "--"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)

    def test_manifest_hashes_payload_and_builder_reproduction(self):
        paths = {
            "instruction": INSTRUCTION_PATH,
            "send_conditions": CONDITIONS_PATH,
            "submitted_body": BODY_PATH,
            "bundle": BUNDLE_PATH,
            "wiring_spec": WIRING_PATH,
            "assembly_rules": RULES_PATH,
            "instruction_delta": DELTA_PATH,
            "coverage": COVERAGE_PATH,
            "placement": PLACEMENT_PATH,
            "non_live_verification": VERIFICATION_PATH,
        }
        for name, path in paths.items():
            with self.subTest(name=name):
                record = self.manifest["artifacts"][name]
                self.assertEqual(record["sha256"], sha256(path))
                self.assertEqual(record["bytes"], path.stat().st_size)
        self.assertEqual(
            self.manifest["candidate_payload_sha256"],
            builder.payload_sha256(CANDIDATE, paths.values()),
        )

        with tempfile.TemporaryDirectory(prefix="issue38-fixed-helper-a4-") as temporary:
            rebuilt = Path(temporary) / builder.CANDIDATE_ID
            rebuilt_manifest = builder.build(rebuilt)
            expected_files = sorted(
                path.relative_to(CANDIDATE)
                for path in CANDIDATE.rglob("*")
                if path.is_file()
            )
            rebuilt_files = sorted(
                path.relative_to(rebuilt)
                for path in rebuilt.rglob("*")
                if path.is_file()
            )
            self.assertEqual(rebuilt_files, expected_files)
            for relative_path in expected_files:
                with self.subTest(path=relative_path.as_posix()):
                    self.assertEqual(
                        (rebuilt / relative_path).read_bytes(),
                        (CANDIDATE / relative_path).read_bytes(),
                    )
            self.assertEqual(rebuilt_manifest, self.manifest)

    def test_a1_a2_a3_formal_r12_t2_and_fixed_evidence_are_preserved(self):
        current = builder.protected_snapshot()
        self.assertEqual(current, self.manifest["protected_snapshot"])
        self.assertTrue(current["all_match_base_commit"])
        self.assertGreater(current["file_count"], 0)
        for name in (
            "helper",
            "fixed_request",
            "fixed_spec",
            "fixed_expected",
            "formal_r12_status",
            "t2_result",
            "a3_manifest",
            "a3_response",
            "a3_assessment",
        ):
            with self.subTest(source=name):
                self.assertEqual(
                    self.manifest["source_evidence"][name]["sha256"],
                    sha256(builder.SOURCES[name]),
                )
        self.assertFalse(self.manifest["a1_a2_a3_modified"])
        self.assertFalse(self.manifest["inherits_t2_auxiliary_pass"])

    def test_wiring_spec_has_exact_coverage_disjointness_and_order(self):
        self.assertEqual(self.wiring, builder.WIRING_SPEC)
        validation = builder.validate_wiring_spec(self.wiring)
        self.assertEqual(validation["text_count"], 7)
        self.assertEqual(validation["numeric_count"], 5)
        self.assertEqual(validation["readback_count"], 2)
        self.assertEqual(validation["comparison_count"], 12)
        self.assertEqual(validation["source_coverage_count"], 12)
        self.assertEqual(validation["target_coverage_count"], 12)
        self.assertEqual(validation["text_numeric_source_overlap"], 0)
        self.assertEqual(validation["text_numeric_target_overlap"], 0)

        text = self.wiring["text_mappings"]
        self.assertEqual(
            [item["helper_source_index"] for item in text],
            list(range(1, 8)),
        )
        self.assertEqual(
            [item["source_json_file"] for item in text],
            [f"source-{index}.json" for index in range(1, 8)],
        )
        self.assertEqual(
            [item["variable"] for item in self.wiring["readbacks"]],
            ["Readback1", "Readback2"],
        )
        comparisons = self.wiring["comparison_contract"]["positions"]
        self.assertEqual([item["order"] for item in comparisons], list(range(1, 13)))
        self.assertTrue(all(item["source_and_saved_positions_immutable"] for item in comparisons))
        self.assertTrue(all(item["per_position_variable_names_may_be_generated"] for item in comparisons))

    def test_bundle_contains_the_exact_machine_and_human_wiring_spec(self):
        begin = "A4_WIRING_SPEC_JSON_BEGIN\n"
        end = "\nA4_WIRING_SPEC_JSON_END"
        self.assertEqual(self.bundle.count(begin), 1)
        self.assertEqual(self.bundle.count(end), 1)
        start = self.bundle.index(begin) + len(begin)
        finish = self.bundle.index(end, start)
        self.assertEqual(json.loads(self.bundle[start:finish]), self.wiring)
        for heading in (
            "TEXT: input cell / DataTable index -> JSON file -> helper source_index -> target",
            "NUMERIC: input cell / DataTable index -> target",
            "READBACKS",
            "COMPARISON ORDER (source -> saved position)",
            "RUNTIME RELATION",
        ):
            self.assertIn(heading, self.bundle)
        for mapping in self.wiring["text_mappings"]:
            self.assertIn(mapping["source_reference"], self.bundle)
            self.assertIn(mapping["source_json_file"], self.bundle)
            self.assertIn(
                f"{mapping['helper_target_sheet']}!{mapping['helper_target_cell']}",
                self.bundle,
            )

    def test_invocation_and_runtime_are_exact_wiring_projections(self):
        invocation = load(builder.INVOCATION)
        self.assertEqual(invocation, builder.INVOCATION_OBJECT)
        self.assertEqual(sha256(builder.INVOCATION), builder.EXPECTED_INVOCATION_SHA256)
        self.assertEqual(invocation["target_workbook"], str(builder.FIXED_WORK))
        self.assertEqual(invocation["json_root"], str(builder.A4_JSON_ROOT))
        projected = [
            {
                "source_index": item["helper_source_index"],
                "source_label": item["source_reference"],
                "sheet": item["helper_target_sheet"],
                "cell": item["helper_target_cell"],
            }
            for item in self.wiring["text_mappings"]
        ]
        self.assertEqual(invocation["text_writes"], projected)
        runtime = self.wiring["runtime"]
        self.assertEqual(runtime["fixed_work_absolute"], invocation["target_workbook"])
        self.assertEqual(runtime["a4_json_root_absolute"], invocation["json_root"])
        self.assertEqual(runtime["fixed_output_absolute"], str(builder.FIXED_OUTPUT))

    def test_c06_uses_captured_wrapper_and_decodes_to_fixed_a4_launcher(self):
        c06 = builder.extract_component(
            self.bundle_bytes,
            "C06_FIXED_LAUNCHER_RUNSCRIPT",
        )
        self.assertEqual(c06, builder.render_a4_c06())
        decoded = builder.a3.a2.embedded_script(c06.decode("utf-8"))
        self.assertEqual(decoded.encode("utf-8") + b"\n", builder.LAUNCHER.read_bytes())
        self.assertEqual(
            hashlib.sha256(decoded.encode("utf-8") + b"\n").hexdigest(),
            builder.EXPECTED_LAUNCHER_SHA256,
        )
        derivation = builder.validate_c06_derivation()
        self.assertTrue(derivation["captured_prefix_and_suffix_exact"])
        self.assertEqual(derivation["execution_status"], "NOT_RUN_A4")
        self.assertEqual(sha256(builder.HELPER), builder.EXPECTED_HELPER_SHA256)

    def test_launcher_parses_without_executing_and_pins_helper_and_invocation(self):
        parser = (
            "$tokens=$null; $errors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile('"
            + str(builder.LAUNCHER).replace("'", "''")
            + "',[ref]$tokens,[ref]$errors) | Out-Null; "
            "if($errors.Count -ne 0){$errors | ForEach-Object {$_.Message}; exit 1}"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", parser],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        launcher = builder.LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(builder.EXPECTED_HELPER_SHA256, launcher)
        self.assertIn(builder.EXPECTED_INVOCATION_SHA256, launcher)
        self.assertIn(str(builder.INVOCATION), launcher)
        self.assertNotIn("Invoke-Expression", launcher)

    def test_instruction_body_bundle_and_delta_are_consistent(self):
        for value in (
            builder.CANDIDATE_ID,
            builder.ROUTE_ID,
            builder.A4_BUNDLE_NAME,
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.instruction)
                self.assertIn(value, self.conditions)
                self.assertIn(value, self.body)
                self.assertIn(value, self.bundle)
        request = builder.SOURCES["fixed_request"].read_text(encoding="utf-8").rstrip("\r\n")
        self.assertTrue(self.body.startswith(request + "\n\n"))
        self.assertIn("\n\n" + self.conditions.rstrip("\r\n") + "\n\n", self.body)
        self.assertTrue(self.body.endswith(self.instruction.rstrip("\r\n") + "\n"))
        self.assertNotIn(builder.a3.CANDIDATE_ID, self.instruction)
        self.assertNotIn(builder.A3_BUNDLE_NAME, self.instruction)
        self.assertNotIn("`RAW_COMPONENT`", self.instruction)
        self.assertIn("`COMPONENT`", self.instruction)
        self.assertLessEqual(builder.utf16_units(self.instruction), 8000)
        self.assertFalse(INSTRUCTION_PATH.read_bytes().startswith(b"\xef\xbb\xbf"))
        for required in (
            "A4 WIRING SPEC",
            "完成Robinが教材にないことだけを理由に拒否しません",
            "未知の命令、引数、列挙値、制御構造を捏造しません",
            str(builder.FIXED_WORK),
            str(builder.FIXED_OUTPUT),
            str(builder.A4_JSON_ROOT),
            "Copilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0",
        ):
            self.assertIn(required, self.instruction)

        reconstructed = builder.SOURCES["a3_instruction"].read_text(encoding="utf-8")
        for transform in self.delta["transforms"]:
            self.assertEqual(reconstructed.count(transform["before"]), transform["occurrences"])
            reconstructed = reconstructed.replace(transform["before"], transform["after"])
        self.assertEqual(reconstructed, self.instruction)
        self.assertEqual(self.delta["other_transformations"], 0)

    def test_no_complete_robin_grader_values_or_live_claims_were_added(self):
        self.assertFalse(any(path.suffix.lower() == ".robin" for path in CANDIDATE.rglob("*")))
        self.assertNotIn(builder.SOURCES["a3_bundle"].read_bytes(), self.bundle_bytes)
        self.assertNotIn(builder.SOURCES["fixed_expected"].read_bytes(), self.bundle_bytes)
        self.assertNotIn(builder.SOURCES["fixed_expected"].read_bytes(), BODY_PATH.read_bytes())
        self.assertNotIn(builder.HELPER.read_bytes(), self.bundle_bytes)
        self.assertNotIn(builder.INVOCATION.read_bytes(), self.bundle_bytes)
        self.assertFalse(self.wiring["generation_contract"]["cell_or_grader_values_included"])
        self.assertEqual(
            self.wiring["status"],
            "SPECIFICATION_ONLY_NOT_COMPLETE_ROBIN_NOT_CAPTURED_NOT_RUN",
        )
        independence = self.manifest["teaching_independence"]
        self.assertFalse(independence["complete_fixed_ex03_robin_in_bundle"])
        self.assertFalse(independence["fixed_expected_or_grader_values_in_bundle"])
        self.assertTrue(independence["fixed_ex03_wiring_spec_in_bundle"])
        self.assertEqual(independence["a4_launcher_execution_status"], "NOT_RUN")
        for key in (
            "copilot_send_count",
            "pad_save_recopy_count",
            "pad_run_count",
            "excel_run_count",
            "new_capture_count",
            "github_write_count",
        ):
            self.assertEqual(self.manifest["scope"][key], 0)
        self.assertEqual(self.manifest["scope"]["full_regression"], "NOT_RUN_BY_SCOPE")
        self.assertEqual(
            self.verification["decision"],
            "PASS_LIMITED_NON_LIVE_A4_WIRING_PREPARATION_ONLY",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
