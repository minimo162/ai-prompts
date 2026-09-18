#!/usr/bin/env python3
"""Focused non-live checks for the fixed-helper Copilot alternate route."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidate.py"
SPEC = importlib.util.spec_from_file_location("issue38_fixed_helper_copilot_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)

CANDIDATE = builder.DESTINATION
MANIFEST_PATH = CANDIDATE / "manifest.json"
INSTRUCTION_PATH = CANDIDATE / "agent-instructions.txt"
BUNDLE_PATH = CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-Bundle.txt"
PLACEMENT_PATH = CANDIDATE / "PLACEMENT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Issue38Ex03FixedHelperCopilotCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST_PATH)
        cls.instruction = INSTRUCTION_PATH.read_text(encoding="utf-8")
        cls.bundle = BUNDLE_PATH.read_text(encoding="utf-8")
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
            "placement": PLACEMENT_PATH,
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

    def test_builder_reproduces_candidate_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="issue38-fixed-helper-candidate-") as temporary:
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

    def test_t2_sources_are_hash_pinned_and_launcher_decodes_exactly(self):
        for name, expected in builder.EXPECTED_SOURCE_SHA256.items():
            with self.subTest(name=name):
                self.assertEqual(sha256(builder.SOURCES[name]), expected)
                record = self.manifest["source_evidence"][name]
                self.assertEqual(record["sha256"], expected)
                self.assertFalse(record["copilot_attachment"])
        launcher = builder.SOURCES["launcher"].read_text(encoding="utf-8").rstrip("\r\n")
        t2 = builder.SOURCES["t2_pad_recopy"].read_text(encoding="utf-8")
        self.assertEqual(builder.embedded_script(t2), launcher)
        self.assertEqual(t2.count("File.WriteText File:"), 8)
        self.assertEqual(t2.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource"), 5)
        self.assertEqual(t2.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson"), 12)

    def test_instruction_preserves_formal_block_safety_and_fixed_route_boundary(self):
        for required in (
            "Markdownのコードブロックを1つだけ使い、言語指定は `text`",
            "全工程のRobinだけを正確に1個のMarkdown `text` コードブロック",
            "helper本体とinvocation JSONは生成またはインライン展開しません",
            "期待SHAは検証者管理であり、回答や依頼本文から再計算、提案、変更しません",
            "通常の日本語依頼からhelperやinvocationなどの実行設定まで自動生成する試験ではありません",
            "事前配置invocationが指定するruntimeを優先します",
            "正式r12の依頼パス適合や実行結果として扱いません",
            builder.EXPECTED_SUCCESS,
            "既存output時はJSON生成、work起動、helper実行より前に停止",
            "network、delete、上書き、Invoke-Expression",
            "Copilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0",
        ):
            self.assertIn(required, self.instruction)
        self.assertLessEqual(builder.utf16_units(self.instruction), 8000)
        self.assertFalse(INSTRUCTION_PATH.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_bundle_contains_fixed_launcher_but_not_helper_invocation_or_t2_answer(self):
        launcher = builder.SOURCES["launcher"].read_text(encoding="utf-8").rstrip("\r\n")
        helper = builder.SOURCES["helper"].read_text(encoding="utf-8")
        invocation = builder.SOURCES["invocation"].read_text(encoding="utf-8")
        t2 = builder.SOURCES["t2_pad_recopy"].read_text(encoding="utf-8")
        self.assertEqual(self.bundle.count(launcher), 1)
        self.assertNotIn(helper, self.bundle)
        self.assertNotIn(invocation, self.bundle)
        self.assertNotIn(t2, self.bundle)
        self.assertNotIn("$mappings.Count -ne 7", self.bundle)
        self.assertNotIn("GetActiveObject('Excel.Application')", self.bundle)
        boundary = self.manifest["teaching_independence"]
        self.assertFalse(boundary["complete_fixed_ex03_robin_in_bundle"])
        self.assertFalse(boundary["fixed_expected_or_grader_values_in_bundle"])

    def test_teaching_fragments_are_independent_incomplete_and_without_grader_terms(self):
        teaching = self.bundle.split("INDEPENDENT TEACHING FRAGMENTS BEGIN\n", 1)[1].split(
            "INDEPENDENT TEACHING FRAGMENTS END", 1
        )[0]
        self.assertIn("lesson-source.xlsx", teaching)
        self.assertIn("StartColumn: $'''H'''", teaching)
        self.assertIn("EndColumn: $'''I'''", teaching)
        self.assertIn("STATIC_FRAGMENT_ONLY_NOT_COMPLETE_NOT_RUN", teaching)
        for forbidden in (
            "入力い.xlsx",
            "入力ろ.xlsx",
            "受取明細",
            "追加項目",
            "集計先",
            "追記先",
            "EX03-attempt1",
            "_ValueTypeMatch",
            "Data1[0][0]",
            "100%",
            "項目甲",
            "Excel.SaveExcel.SaveAs",
            "春",
            "夏",
            "秋",
            "項目乙",
            "日本語",
            "21",
            "-4.5",
            "42",
            "6.25",
        ):
            self.assertNotIn(forbidden, teaching, forbidden)
        for fixed_string in ("春", "夏", "秋", "項目甲", "項目乙", "日本語", "100%"):
            self.assertNotIn(fixed_string, self.bundle, fixed_string)

    def test_preplaced_and_generated_responsibilities_are_explicit(self):
        preplaced = self.manifest["preplaced_by_verifier"]
        generated = self.manifest["copilot_generated"]
        copilot_input = self.manifest["copilot_input"]
        self.assertEqual(preplaced["helper"]["expected_sha256_owner"], "VERIFIER")
        self.assertEqual(preplaced["invocation"]["expected_sha256_owner"], "VERIFIER")
        self.assertFalse(preplaced["automatic_execution_configuration_from_japanese_request"])
        self.assertFalse(generated["helper_body"])
        self.assertFalse(generated["invocation_json"])
        self.assertFalse(generated["helper_or_invocation_expected_sha_derived_or_changed"])
        self.assertTrue(generated["verifier_owned_expected_sha_literals_copied_in_fixed_launcher"])
        self.assertTrue(generated["fixed_launcher_inside_one_runscript"])
        self.assertTrue(generated["pad_before_and_after_actions"])
        self.assertTrue(copilot_input["fixed_request_verbatim"])
        self.assertTrue(
            copilot_input["fixed_request_logical_input_sheet_range_target_and_expectations_preserved"]
        )
        self.assertEqual(
            copilot_input["runtime_path_source"],
            "VERIFIER_PREPLACED_INVOCATION_FOR_ALTERNATE_ROUTE",
        )
        self.assertFalse(copilot_input["formal_request_runtime_path_compliance_claimed"])
        for required in (
            "Copilot must not create or modify them",
            "does **not** test automatic",
            "does not claim formal request-path",
            "Copilot generates only",
            "It copies the fixed launcher including",
            "does not derive or change those literals",
        ):
            self.assertIn(required, self.placement)

    def test_formal_r12_fail_t2_auxiliary_scope_and_no_live_work_are_preserved(self):
        preserved = self.manifest["preserved_boundaries"]
        scope = self.manifest["scope"]
        self.assertEqual(
            preserved["formal_r12_status"],
            "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD",
        )
        self.assertFalse(preserved["formal_r12_accepted"])
        self.assertEqual(preserved["t2_decision"], "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1")
        self.assertIn("not formal EX03-r12 acceptance", preserved["t2_scope"])
        self.assertEqual(scope["copilot_send_count"], 0)
        self.assertEqual(scope["pad_run_count"], 0)
        self.assertEqual(scope["excel_run_count"], 0)
        self.assertEqual(scope["successful_probe_rerun"], 0)
        self.assertEqual(scope["full_regression"], "NOT_RUN_BY_SCOPE")
        self.assertEqual(scope["github_write_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
