#!/usr/bin/env python3
"""Evidence gates for the bounded EX03 R2/R3 postfix live trial."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r2-r3-string-stop"
TRIAL = PROBE / "trials/EX03-R2R3-POSTFIX-20260917-T1"
BASELINE = "1f929d6c4e1ba5bc4d963374e3e322c7a52649c1"
EXPECTED_NEGATIVE_OUTPUT = (
    '{"status":"EXPECTED_ERROR","mode":"INJECT_AFTER_FORMAT_CHANGE",'
    '"format_restored":true,"value_unchanged":true}'
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue38Ex03R2R3PostfixTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preflight = load(TRIAL / "preflight.json")
        cls.final = load(TRIAL / "final-verification.json")
        cls.normal_gate = load(TRIAL / "normal/normal-gate.json")
        cls.normal_observation = load(TRIAL / "normal/pad-observation.json")
        cls.negative_observation = load(TRIAL / "negative/pad-observation.json")

    def test_preflight_is_bound_to_baseline_and_actual_decimal_json(self):
        self.assertEqual(self.preflight["result"], "PASS_READY_FOR_NORMAL_ONE_RUN_ONLY")
        self.assertEqual(self.preflight["baseline_commit"], BASELINE)
        type_probe = self.preflight["windows_powershell_non_live_type_probe"]
        self.assertEqual(type_probe["ps_version"], "5.1.26100.9444")
        self.assertEqual(type_probe["ps_edition"], "Desktop")
        self.assertEqual(type_probe["number_type"], "System.Decimal")
        self.assertFalse(type_probe["is_double"])
        self.assertTrue(type_probe["is_decimal"])
        self.assertTrue(type_probe["accepted"])
        source = PROBE / "runtime/source-4.json"
        self.assertEqual(sha256(source), self.preflight["actual_json_source"]["sha256"])
        self.assertEqual(source.read_bytes().decode("utf-8-sig"), '{"probe":42.5}')

    def test_full_fixed_and_execution_sha256_values_match_files(self):
        fixed_paths = {
            "source.xlsx": PROBE / "source.xlsx",
            "template.xlsx": PROBE / "template.xlsx",
            "embedded-safe.ps1.txt": PROBE / "embedded-safe.ps1.txt",
            "candidate-normal-postfix.robin": PROBE / "candidate-normal-postfix.robin",
            "candidate-negative-postfix.robin": PROBE / "candidate-negative-postfix.robin",
        }
        for key, path in fixed_paths.items():
            with self.subTest(key=key):
                self.assertEqual(sha256(path), self.preflight["fixed_sha256"][key])
        for phase in ("normal", "negative"):
            record = self.preflight["phases"][phase]
            self.assertEqual(sha256(TRIAL / phase / "candidate.robin"), record["candidate_sha256"])
            self.assertEqual(
                sha256(TRIAL / phase / "embedded-safe-pathbound.ps1.txt"),
                record["embedded_script_sha256"],
            )

    def test_path_isolation_is_the_only_trial_candidate_change(self):
        for phase, fixed_name in (
            ("normal", "candidate-normal-postfix.robin"),
            ("negative", "candidate-negative-postfix.robin"),
        ):
            with self.subTest(phase=phase):
                trial_runtime = str((TRIAL / phase / "runtime").resolve()).replace("\\", "\\\\")
                fixed_runtime = str((PROBE / "runtime").resolve()).replace("\\", "\\\\")
                trial_text = (TRIAL / phase / "candidate.robin").read_text(encoding="utf-8")
                normalized = trial_text.replace(trial_runtime, fixed_runtime)
                self.assertEqual(normalized, (PROBE / fixed_name).read_text(encoding="utf-8"))
                self.assertEqual(trial_text.count(trial_runtime), 11)
                self.assertTrue(self.preflight["phases"][phase]["normalized_exact_fixed_script"])
                self.assertEqual(self.preflight["phases"][phase]["ast_error_count"], 0)

    def test_each_saved_flow_is_exactly_recopied_and_run_once(self):
        for phase, observation in (
            ("normal", self.normal_observation),
            ("negative", self.negative_observation),
        ):
            with self.subTest(phase=phase):
                candidate = TRIAL / phase / "candidate.robin"
                recopy = TRIAL / phase / "pad-recopy-before-run.robin"
                self.assertEqual(candidate.read_bytes(), recopy.read_bytes())
                self.assertEqual(observation["flow"]["candidate_sha256"], sha256(candidate))
                self.assertEqual(observation["flow"]["saved_recopy_sha256"], sha256(recopy))
                self.assertTrue(observation["flow"]["saved_recopy_exact"])
                self.assertEqual(observation["flow"]["action_count"], 63)
                self.assertFalse(observation["flow"]["power_fx_enabled"])
                for key in ("paste_invocations", "save_invocations", "recopy_invocations", "run_invocations"):
                    self.assertEqual(observation["flow"][key], 1, key)

    def test_normal_saved_reopened_values_types_formats_prefix_and_formulas_pass(self):
        self.assertEqual(self.normal_gate["result"], "PASS_NORMAL_GATE_NEGATIVE_ONE_RUN_AUTHORIZED")
        result = TRIAL / "normal/runtime/result.xlsx"
        preserved = TRIAL / "normal/preserved-result.xlsx"
        self.assertEqual(sha256(result), "a712dffdc1f9d41f0b5e034c1e8366ef4001631f3eb139d5dc8dcbe060464af3")
        self.assertEqual(result.read_bytes(), preserved.read_bytes())
        run = self.normal_observation["run"]
        self.assertEqual(run["terminal"], "READY")
        self.assertTrue(run["script_gate_passed"])
        self.assertTrue(run["numeric_write_entered"])
        self.assertTrue(run["save_as_entered"])
        self.assertEqual((run["readback_rows"], run["readback_columns"]), (1, 4))
        self.assertTrue(all(run[f"source{index}_vs_saved"] for index in range(1, 5)))

        com = load(TRIAL / "normal/excel-com-inspection.json")
        expected = [
            ("A2", "O'Brien", "System.String"),
            ("B2", 'He said "Go"\nSecond line \'quoted\'', "System.String"),
            ("C2", "100%", "System.String"),
            ("D2", 42.5, "System.Double"),
        ]
        for actual, template, (address, value, value_type) in zip(
            com["result"]["cells"], com["template"]["cells"], expected, strict=True
        ):
            self.assertEqual(actual["address"], address)
            self.assertEqual(actual["value"], value)
            self.assertEqual(actual["value_type"], value_type)
            for key in ("number_format", "number_format_local", "prefix", "has_formula"):
                self.assertEqual(actual[key], template[key])
        self.assertTrue(com["all_number_format_prefix_formula_equal"])
        self.assertTrue(com["result"]["result_xlsx_unchanged"])

    def test_forced_exception_restores_state_and_cannot_save(self):
        run = self.negative_observation["run"]
        self.assertEqual(run["terminal"], "READY")
        self.assertEqual(run["powershell_output"], EXPECTED_NEGATIVE_OUTPUT)
        self.assertEqual(run["probe_state"], "SCRIPT_NOT_SUCCESS_NO_SAVE")
        self.assertFalse(run["script_gate_passed"])
        self.assertFalse(run["numeric_write_entered"])
        self.assertFalse(run["save_as_entered"])
        self.assertEqual((run["readback_rows"], run["readback_columns"]), (0, 0))
        self.assertFalse((TRIAL / "negative/runtime/result.xlsx").exists())
        self.assertEqual(
            sha256(TRIAL / "negative/runtime/work.xlsx"),
            sha256(PROBE / "template.xlsx"),
        )
        final_negative = self.final["negative"]
        self.assertTrue(final_negative["format_restored_directly_observed_by_script"])
        self.assertTrue(final_negative["value_unchanged_directly_observed_by_script"])
        self.assertFalse(final_negative["pre_type_check_stop"])
        self.assertFalse(final_negative["success_gate_passed"])
        self.assertFalse(final_negative["completed_output_exists"])

    def test_old_evidence_blobs_are_unchanged(self):
        changed = []
        for name, expected_blob in self.preflight["baseline_probe_blobs"].items():
            actual_blob = subprocess.check_output(
                ["git", "hash-object", f"--path={name}", str(ROOT / name)],
                cwd=ROOT,
                text=True,
            ).strip()
            if actual_blob != expected_blob:
                changed.append(name)
        self.assertEqual(changed, [])
        self.assertEqual(len(self.preflight["baseline_probe_blobs"]), 27)
        self.assertTrue(self.final["old_evidence"]["unchanged"])
        self.assertEqual(self.final["old_evidence"]["checked"], 27)


if __name__ == "__main__":
    unittest.main(verbosity=2)
