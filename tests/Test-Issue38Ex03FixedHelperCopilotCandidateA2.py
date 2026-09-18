#!/usr/bin/env python3
"""Focused non-live checks for the fixed-helper Copilot A2 teaching candidate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA2.py"
SPEC = importlib.util.spec_from_file_location("issue38_fixed_helper_copilot_a2_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)

CANDIDATE = builder.DESTINATION
MANIFEST_PATH = CANDIDATE / "manifest.json"
INSTRUCTION_PATH = CANDIDATE / "agent-instructions.txt"
BUNDLE_PATH = CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-A2-Bundle.txt"
COVERAGE_PATH = CANDIDATE / "COVERAGE.md"
PLACEMENT_PATH = CANDIDATE / "PLACEMENT.md"
VERIFICATION_PATH = CANDIDATE / "non-live-verification.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Issue38Ex03FixedHelperCopilotCandidateA2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST_PATH)
        cls.verification = load(VERIFICATION_PATH)
        cls.instruction = INSTRUCTION_PATH.read_text(encoding="utf-8")
        cls.bundle_bytes = BUNDLE_PATH.read_bytes()
        cls.bundle = cls.bundle_bytes.decode("utf-8")
        cls.coverage = COVERAGE_PATH.read_text(encoding="utf-8")
        cls.placement = PLACEMENT_PATH.read_text(encoding="utf-8")

    def test_candidate_and_route_ids_were_unused_at_base_commit(self):
        for value in (builder.CANDIDATE_ID, builder.ROUTE_ID):
            completed = subprocess.run(
                ["git", "grep", "-F", value, builder.BASE_COMMIT, "--"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)

    def test_manifest_artifact_hashes_and_payload_digest_match(self):
        self.assertEqual(self.manifest["candidate_id"], builder.CANDIDATE_ID)
        self.assertEqual(self.manifest["route_id"], builder.ROUTE_ID)
        paths = {
            "instruction": INSTRUCTION_PATH,
            "bundle": BUNDLE_PATH,
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
            builder.payload_sha256(CANDIDATE, list(paths.values())),
        )

    def test_builder_reproduces_every_candidate_file_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="issue38-fixed-helper-a2-") as temporary:
            rebuilt = Path(temporary) / builder.CANDIDATE_ID
            rebuilt_manifest = builder.build(rebuilt)
            expected_files = sorted(
                path.relative_to(CANDIDATE) for path in CANDIDATE.rglob("*") if path.is_file()
            )
            rebuilt_files = sorted(
                path.relative_to(rebuilt) for path in rebuilt.rglob("*") if path.is_file()
            )
            self.assertEqual(rebuilt_files, expected_files)
            for relative_path in expected_files:
                with self.subTest(path=relative_path.as_posix()):
                    self.assertEqual(
                        (rebuilt / relative_path).read_bytes(),
                        (CANDIDATE / relative_path).read_bytes(),
                    )
            self.assertEqual(rebuilt_manifest, self.manifest)

    def test_all_protected_sources_and_a1_evidence_are_hash_pinned(self):
        for name, expected in builder.EXPECTED_SOURCE_SHA256.items():
            with self.subTest(name=name):
                self.assertEqual(sha256(builder.SOURCES[name]), expected)
                source = self.manifest["source_evidence"][name]
                self.assertEqual(source["sha256"], expected)
                self.assertFalse(source["copilot_attachment"])
        self.assertFalse(self.manifest["a1_files_modified"])
        self.assertTrue(
            self.verification["checks"][
                "a1_instruction_bundle_manifest_placement_response_assessment_unchanged"
            ]
        )

    def test_internal_index_contains_every_exact_raw_component(self):
        records = self.manifest["component_records"]
        self.assertEqual(len(records), 12)
        self.assertEqual(
            {record["id"] for record in records},
            {component["id"] for component in builder.COMPONENTS},
        )
        self.assertIn("IN-BUNDLE INDEX", self.bundle)
        for component in builder.COMPONENTS:
            component_id = component["id"]
            with self.subTest(component=component_id):
                expected = builder.component_excerpt(component)
                actual = builder.extract_component(self.bundle_bytes, component_id)
                self.assertEqual(actual, expected)
                self.assertEqual(hashlib.sha256(actual).hexdigest(), next(
                    record["excerpt_sha256"] for record in records if record["id"] == component_id
                ))
                self.assertIn(f"[{component_id}]", self.bundle)
                self.assertIn(builder.relative(builder.SOURCES[component["source"]]), self.bundle)

    def test_complete_fixed_launcher_runscript_decodes_to_fixed_sha(self):
        component = next(
            item for item in builder.COMPONENTS if item["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT"
        )
        raw = builder.extract_component(self.bundle_bytes, component["id"])
        normalized = raw.decode("utf-8").replace("\r\n", "\n")
        decoded = builder.embedded_script(normalized)
        launcher_bytes = builder.SOURCES["launcher"].read_bytes()
        self.assertTrue(launcher_bytes.endswith(b"\n"))
        self.assertNotIn(b"\r\n", launcher_bytes)
        self.assertEqual(decoded.encode("utf-8") + b"\n", launcher_bytes)
        self.assertEqual(
            hashlib.sha256(decoded.encode("utf-8") + b"\n").hexdigest(),
            builder.EXPECTED_SOURCE_SHA256["launcher"],
        )
        self.assertEqual(component["mutable_parameters"], [])

    def test_every_requested_stage_is_covered_without_claiming_composed_execution(self):
        coverage = self.manifest["requirement_coverage"]
        expected = {
            "state initialization",
            "existing-output no-write guard",
            "read-only input, sheet activation, TypedValues read",
            "JSON primitive conversion and UTF-8 handoff save",
            "editable work-copy open",
            "complete RunScript with fixed launcher",
            "exact-success and NORMAL branching",
            "explicit target-sheet activation and numeric WriteCell",
            "SaveAs and close/reopen readback",
            "saved value/type comparison through JSON",
            "failure close/no-save",
        }
        self.assertEqual({item["requirement"] for item in coverage}, expected)
        self.assertTrue(all(item["status"] == "COVERED" for item in coverage))
        self.assertEqual(self.manifest["missing_required_steps"], [])
        self.assertEqual(self.verification["checks"]["missing_required_steps"], [])
        self.assertIn("Missing required syntax steps: none", self.coverage)
        self.assertIn("A2 composition NOT_RUN", self.coverage)

    def test_instruction_resolves_a1_index_and_generation_precondition_conflict(self):
        required = (
            "同じbundle内に続く `RAW_COMPONENT` 原文だけを参照します",
            "外部索引を前提にしません",
            "再利用、組合せ",
            "明示したパラメーター変更",
            "必要回数への反復",
            "NOT_RUN_NEW_COMBINATION",
            "組合せ後の実行証跡が教材にないことは、生成拒否の理由にしません",
            "完成フローの過去実行証跡は生成前の必須条件ではありません",
            "実際に根拠がない工程が残る場合だけRobinを出さず、その不足工程だけ",
            "掲載済み工程を、完成回答がないことだけで不足扱いにしません",
            "C06_FIXED_LAUNCHER_RUNSCRIPT",
            "全工程のRobinだけを正確に1個のMarkdown `text` コードブロック",
            "Copilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0",
        )
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, self.instruction)
        self.assertNotIn("PAD-Robin-00-Index.txt", self.instruction)
        self.assertLessEqual(builder.utf16_units(self.instruction), 8000)
        self.assertFalse(INSTRUCTION_PATH.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_bundle_is_self_contained_but_does_not_leak_fixed_answer_or_grading(self):
        for text in (
            "IN-BUNDLE INDEX",
            "REQUIREMENT TO COMPONENT COVERAGE",
            "NEW COMPOSITION PARAMETERS — NOT ROBIN / NOT CAPTURED / NOT RUN",
            "RAW COMPONENTS",
            "NOT_RUN_NEW_COMBINATION",
        ):
            self.assertIn(text, self.bundle)

        self.assertNotIn(builder.SOURCES["helper"].read_text(encoding="utf-8"), self.bundle)
        self.assertNotIn(builder.SOURCES["invocation"].read_text(encoding="utf-8"), self.bundle)
        self.assertNotIn(builder.SOURCES["t2_pad_recopy"].read_text(encoding="utf-8"), self.bundle)
        self.assertNotIn(builder.SOURCES["r2r3_normal_recopy"].read_text(encoding="utf-8"), self.bundle)
        self.assertNotIn(builder.SOURCES["fixed_expected"].read_text(encoding="utf-8"), self.bundle)

        c06 = builder.extract_component(self.bundle_bytes, "C06_FIXED_LAUNCHER_RUNSCRIPT")
        independent = self.bundle_bytes.replace(c06, b"[FIXED_C06_REMOVED]\n").decode("utf-8")
        for forbidden in (
            "入力い.xlsx",
            "入力ろ.xlsx",
            "受取明細",
            "追加項目",
            "集計先",
            "追記先",
            "EX03-attempt1",
            "項目甲",
            "項目乙",
            "日本語",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, independent)

        independence = self.manifest["teaching_independence"]
        self.assertEqual(independence["status"], "PASS")
        self.assertFalse(independence["complete_fixed_ex03_robin_in_bundle"])
        self.assertFalse(independence["fixed_expected_or_grader_values_in_bundle"])
        self.assertFalse(independence["fixed_ex03_full_wiring_in_bundle"])
        self.assertTrue(independence["contracted_fixed_launcher_runscript_in_bundle"])
        self.assertTrue(independence["generic_captured_components_in_bundle"])

    def test_fixed_contract_and_historical_boundaries_are_unchanged(self):
        fixed = self.manifest["fixed_contract"]
        self.assertEqual(fixed["helper_sha256"], builder.EXPECTED_SOURCE_SHA256["helper"])
        self.assertEqual(fixed["invocation_sha256"], builder.EXPECTED_SOURCE_SHA256["invocation"])
        self.assertEqual(fixed["launcher_sha256"], builder.EXPECTED_SOURCE_SHA256["launcher"])
        self.assertEqual(fixed["success_output"], builder.EXPECTED_SUCCESS)
        self.assertEqual(fixed["source_json_write_count"], 7)
        self.assertEqual(fixed["mode_json_write_count"], 1)
        self.assertEqual(fixed["numeric_write_count"], 5)
        self.assertEqual(fixed["save_as_count"], 1)
        self.assertEqual(fixed["saved_value_type_comparison_count"], 12)
        self.assertFalse(
            fixed["helper_invocation_launcher_runtime_path_fixed_request_expected_and_output_format_changed"]
        )

        preserved = self.manifest["preserved_boundaries"]
        self.assertEqual(
            preserved["formal_r12_status"],
            "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD",
        )
        self.assertFalse(preserved["formal_r12_accepted"])
        self.assertEqual(preserved["t2_decision"], "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1")
        self.assertEqual(preserved["a1_result"], "REFUSED_NO_CODE_BLOCK_PAD_NOT_RUN")
        self.assertEqual(preserved["legacy_558_difference_record"], "PRESERVED_NOT_RECLASSIFIED")

    def test_no_live_or_out_of_scope_work_is_claimed(self):
        scope = self.manifest["scope"]
        for key in (
            "copilot_send_count",
            "pad_save_recopy_count",
            "pad_run_count",
            "excel_run_count",
            "new_capture_count",
            "successful_probe_rerun_count",
            "github_write_count",
        ):
            with self.subTest(key=key):
                self.assertEqual(scope[key], 0)
        self.assertEqual(scope["full_regression"], "NOT_RUN_BY_SCOPE")
        self.assertEqual(self.verification["decision"], "PASS_TEACHING_PREPARATION_NON_LIVE_ONLY")
        self.assertIn("teaching preparation only", self.placement)
        self.assertIn("were not run", self.placement)


if __name__ == "__main__":
    unittest.main(verbosity=2)
