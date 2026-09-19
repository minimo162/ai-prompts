#!/usr/bin/env python3
"""Focused non-live checks for the fixed-helper Copilot A3 assembly rules."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA3.py"
SPEC = importlib.util.spec_from_file_location(
    "issue38_fixed_helper_copilot_a3_builder",
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
BUNDLE_PATH = CANDIDATE / "knowledge" / builder.A3_BUNDLE_NAME
RULES_PATH = CANDIDATE / "assembly-rules.json"
DELTA_PATH = CANDIDATE / "instruction-delta.json"
COVERAGE_PATH = CANDIDATE / "COVERAGE.md"
PLACEMENT_PATH = CANDIDATE / "PLACEMENT.md"
VERIFICATION_PATH = CANDIDATE / "non-live-verification.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Issue38Ex03FixedHelperCopilotCandidateA3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST_PATH)
        cls.rules = load(RULES_PATH)
        cls.delta = load(DELTA_PATH)
        cls.verification = load(VERIFICATION_PATH)
        cls.instruction = INSTRUCTION_PATH.read_text(encoding="utf-8")
        cls.conditions = CONDITIONS_PATH.read_text(encoding="utf-8")
        cls.body = BODY_PATH.read_text(encoding="utf-8")
        cls.bundle_bytes = BUNDLE_PATH.read_bytes()
        cls.bundle = cls.bundle_bytes.decode("utf-8")

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

    def test_manifest_hashes_payload_and_builder_reproduction(self):
        paths = {
            "instruction": INSTRUCTION_PATH,
            "send_conditions": CONDITIONS_PATH,
            "submitted_body": BODY_PATH,
            "bundle": BUNDLE_PATH,
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
            builder.payload_sha256(CANDIDATE, list(paths.values())),
        )

        with tempfile.TemporaryDirectory(prefix="issue38-fixed-helper-a3-") as temporary:
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

    def test_a2_and_original_evidence_are_unchanged(self):
        for name, expected in builder.EXPECTED_SOURCE_SHA256.items():
            with self.subTest(source=name):
                self.assertEqual(sha256(builder.SOURCES[name]), expected)
                self.assertEqual(
                    self.manifest["source_evidence"][name]["sha256"],
                    expected,
                )
        preserved = self.manifest["preserved_a2_files"]
        self.assertEqual(
            {record["path"] for record in preserved},
            set(builder.PRESERVE_FROM_BASE),
        )
        self.assertTrue(all(record["matches_base_commit"] for record in preserved))
        self.assertFalse(self.manifest["a2_files_modified"])

    def test_raw_components_and_rule_source_lines_match_captured_sources(self):
        records = self.manifest["component_records"]
        self.assertEqual(len(records), 12)
        for component in builder.COMPONENTS:
            with self.subTest(component=component["id"]):
                expected = builder.a2.component_excerpt(component)
                actual = builder.extract_component(self.bundle_bytes, component["id"])
                self.assertEqual(actual, expected)
                record = next(item for item in records if item["id"] == component["id"])
                self.assertEqual(record["excerpt_sha256"], hashlib.sha256(expected).hexdigest())

        captured_lines: set[tuple[str, int]] = set()
        for component in builder.COMPONENTS:
            captured_lines.update(
                (component["source"], line)
                for line in range(component["start_line"], component["end_line"] + 1)
            )
        for rule in builder.ASSEMBLY_RULES:
            for binding in rule["line_bindings"]:
                for line in range(binding["lines"][0], binding["lines"][1] + 1):
                    with self.subTest(rule=rule["id"], line=line):
                        self.assertIn((binding["source"], line), captured_lines)
                        self.assertTrue(builder.source_line(binding["source"], line))

    def test_instruction_submitted_body_and_bundle_are_consistent(self):
        for value in (
            builder.CANDIDATE_ID,
            builder.ROUTE_ID,
            builder.A3_BUNDLE_NAME,
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.instruction)
                self.assertIn(value, self.conditions)
                self.assertIn(value, self.body)
                self.assertIn(value, self.bundle)
        for rule in builder.ASSEMBLY_RULES:
            self.assertIn(rule["id"], self.instruction)
            self.assertIn(rule["id"], self.bundle)

        request = builder.SOURCES["fixed_request"].read_text(encoding="utf-8").rstrip("\r\n")
        self.assertTrue(self.body.startswith(request + "\n\n"))
        self.assertIn("\n\n" + self.conditions.rstrip("\r\n") + "\n\n", self.body)
        self.assertTrue(self.body.endswith(self.instruction.rstrip("\r\n") + "\n"))
        self.assertNotIn(builder.a2.CANDIDATE_ID, self.instruction)
        self.assertNotIn(builder.A2_BUNDLE_NAME, self.instruction)
        self.assertLessEqual(builder.utf16_units(self.instruction), 8000)
        self.assertFalse(INSTRUCTION_PATH.read_bytes().startswith(b"\xef\xbb\xbf"))

        required = (
            "逐語保持の対象はC06_FIXED_LAUNCHER_RUNSCRIPT全体",
            "immutableとされた未変更構文部分だけ",
            "明示的に複製",
            "新しいPAD LOOP",
            "C12末尾ENDが閉じます",
            "完成フローの採取・実行済み原文が教材にないことは生成拒否の理由にしません",
            "component ID、出典命令行、未解決の接続前後",
            "Copilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0",
        )
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, self.instruction)

    def test_instruction_delta_is_limited_and_reconstructs_a3(self):
        before = builder.SOURCES["a2_instruction"].read_text(encoding="utf-8")
        reconstructed = before
        for transform in self.delta["transforms"]:
            self.assertEqual(
                reconstructed.count(transform["before"]),
                transform["occurrences"],
            )
            reconstructed = reconstructed.replace(
                transform["before"],
                transform["after"],
            )
        self.assertEqual(reconstructed, self.instruction)
        self.assertEqual(self.delta["other_transformations"], 0)
        self.assertTrue(self.delta["reconstructs_candidate_exactly"])
        self.assertEqual(
            self.delta["candidate_instruction_sha256"],
            sha256(INSTRUCTION_PATH),
        )

    def test_derived_example_uses_only_listed_substitutions_and_resolved_variables(self):
        records = self.rules["derived_example"]["records"]
        self.assertEqual(records, builder.build_derived_example())
        defined = set(self.rules["derived_example"]["predefined_variables"])
        for index, record in enumerate(records, start=1):
            template = builder.source_line(record["source"], record["source_line"])
            masked = template
            markers: list[tuple[str, str]] = []
            for number, replacement in enumerate(record["mutable_replacements"], start=1):
                marker = f"{{MUTABLE_{number}}}"
                self.assertEqual(masked.count(replacement["source_token"]), 1)
                masked = masked.replace(replacement["source_token"], marker, 1)
                markers.append((marker, replacement["derived_token"]))
            derived = masked
            for marker, value in markers:
                derived = derived.replace(marker, value)
            with self.subTest(line=index):
                self.assertEqual(derived, record["text"])
                self.assertEqual(
                    hashlib.sha256(masked.encode("utf-8")).hexdigest(),
                    record["immutable_skeleton_sha256"],
                )
                self.assertTrue(set(record["references"]).issubset(defined))
                defined.update(record["defines"])
                self.assertFalse(
                    record["text"].lstrip().upper().startswith(("LOOP ", "FOREACH "))
                )
        validation = self.rules["derived_example"]["validation"]
        self.assertEqual(validation["unresolved_references"], [])
        self.assertEqual(validation["new_pad_loop_commands"], 0)
        self.assertTrue(validation["execution_order_valid"])

    def test_control_map_closes_each_branch_and_failure_paths_do_not_save(self):
        self.assertEqual(list(builder.CONTROL_EVENTS), self.rules["control_events"])
        expected = builder.validate_control_events()
        self.assertEqual(self.rules["control_validation"], expected)
        self.assertTrue(expected["balanced"])
        self.assertEqual(
            expected["closed_in_order"],
            ["NORMAL_MODE", "EXACT_SUCCESS", "OUTPUT_GUARD"],
        )
        self.assertEqual(expected["failure_close_count"], 2)
        self.assertEqual(expected["failure_save_as_count"], 0)

    def test_fixed_launcher_remains_byte_exact(self):
        c06 = builder.extract_component(
            self.bundle_bytes,
            "C06_FIXED_LAUNCHER_RUNSCRIPT",
        )
        decoded = builder.a2.embedded_script(
            c06.decode("utf-8").replace("\r\n", "\n")
        )
        launcher = builder.SOURCES["launcher"].read_bytes()
        self.assertEqual(decoded.encode("utf-8") + b"\n", launcher)
        self.assertEqual(
            hashlib.sha256(decoded.encode("utf-8") + b"\n").hexdigest(),
            builder.EXPECTED_SOURCE_SHA256["launcher"],
        )
        fixed = self.manifest["fixed_contract"]
        self.assertEqual(
            fixed["decoded_launcher_terminal_lf_restored_sha256"],
            builder.EXPECTED_SOURCE_SHA256["launcher"],
        )

    def test_teaching_test_independence_and_not_run_scope(self):
        c06 = builder.extract_component(
            self.bundle_bytes,
            "C06_FIXED_LAUNCHER_RUNSCRIPT",
        )
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
        self.assertNotIn(
            builder.SOURCES["t2_pad_recopy"].read_text(encoding="utf-8"),
            self.bundle,
        )
        self.assertNotIn(
            builder.SOURCES["fixed_expected"].read_text(encoding="utf-8"),
            self.bundle,
        )
        self.assertIn(
            "NOT RAW CAPTURE / NOT COMPLETE ROBIN / NOT RUN",
            self.bundle,
        )
        independence = self.manifest["teaching_independence"]
        self.assertEqual(independence["status"], "PASS")
        self.assertFalse(independence["complete_fixed_ex03_robin_in_bundle"])
        self.assertFalse(independence["fixed_expected_or_grader_values_in_bundle"])
        self.assertFalse(independence["fixed_ex03_full_wiring_in_bundle"])
        self.assertTrue(independence["derived_example_is_different_condition"])
        self.assertTrue(independence["derived_example_marked_not_run"])

        scope = self.manifest["scope"]
        for key in (
            "copilot_send_count",
            "pad_save_recopy_count",
            "pad_run_count",
            "excel_run_count",
            "new_capture_count",
            "github_write_count",
        ):
            with self.subTest(scope=key):
                self.assertEqual(scope[key], 0)
        self.assertEqual(scope["full_regression"], "NOT_RUN_BY_SCOPE")
        self.assertEqual(
            self.verification["decision"],
            "PASS_LIMITED_NON_LIVE_ASSEMBLY_RULES_ONLY",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
