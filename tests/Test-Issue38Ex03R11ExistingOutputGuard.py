"""Targeted checks for the one-run EX03 r11 FILE-AUX1 existing-output guard."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
FORMAL = BASE / "cycles/EX03-r11-G1"
AUX = BASE / "cycles/EX03-r11-file-aux1"
CYCLE = BASE / "cycles/EX03-r11-file-aux1-existing-output-neg1"
ROBIN_SHA = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(name: str) -> dict:
    return json.loads((CYCLE / name).read_text(encoding="utf-8"))


class Ex03R11ExistingOutputGuardTests(unittest.TestCase):
    def test_fresh_recopy_matches_unmodified_file_aux1_robin(self):
        candidate = AUX / "copilot-downloaded-ex03.robin"
        recopy = CYCLE / "pad-recopy-before-guard-run.robin"
        self.assertEqual(sha(candidate), ROBIN_SHA)
        left = candidate.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\r\n")
        right = recopy.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\r\n")
        self.assertEqual(left, right)
        lines = left.splitlines()
        self.assertEqual(len(lines), 167)
        self.assertEqual(lines[2].strip(), "SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''")
        self.assertEqual(lines[3], "ELSE")
        self.assertEqual(lines[-1], "END")
        excel_indexes = [index for index, line in enumerate(lines) if "Excel." in line]
        self.assertTrue(excel_indexes)
        self.assertTrue(all(3 < index < len(lines) - 1 for index in excel_indexes))
        self.assertEqual(sum("Excel.SaveExcel.SaveAs" in line for line in lines), 1)

    def test_single_live_guard_run_has_direct_branch_and_write_side_observation(self):
        plan = read_json("plan.json")
        observation = read_json("pad-run-observation.json")
        self.assertTrue(plan["relationship"]["separate_from_positive_run_ids"])
        self.assertEqual(plan["limits"]["pad_run_limit"], 1)
        self.assertEqual(observation["runtime"]["run_requests_used"], 1)
        self.assertFalse(observation["runtime"]["retry_issued"])
        self.assertEqual(observation["runtime"]["action_count_visible"], 110)
        self.assertEqual(observation["runtime"]["variable_count_visible"], 45)
        self.assertEqual(observation["direct_branch_observation"]["full_value_in_pad_variable_dialog"], "OUTPUT_EXISTS_NO_WRITE")
        self.assertTrue(observation["direct_branch_observation"]["guard_branch_entered"])
        self.assertEqual(observation["direct_write_side_observation"]["matching_variables"], 12)
        self.assertEqual(observation["direct_write_side_observation"]["false_values"], 12)
        self.assertEqual(observation["direct_write_side_observation"]["work_variable"], "<empty>")
        self.assertFalse(observation["direct_write_side_observation"]["transfer_and_save_side_entered"])
        self.assertEqual(observation["direct_terminal_observation"]["status_bar"], "Ready")
        self.assertTrue(observation["direct_terminal_observation"]["run_button_enabled"])
        self.assertTrue(observation["direct_terminal_observation"]["stop_button_disabled"])

    def test_existing_output_inputs_template_and_work_are_unchanged(self):
        hashes = read_json("hashes-after-live-run.json")
        cleanup = read_json("cleanup.json")
        self.assertTrue(hashes["all_required_files_unchanged"])
        self.assertEqual(hashes["existing_output"]["sha256_before"], hashes["existing_output"]["sha256_after"])
        self.assertEqual(hashes["existing_output"]["last_write_ns_before"], hashes["existing_output"]["last_write_ns_after"])
        for record in hashes["fixed_files"].values():
            self.assertTrue(record["unchanged"])
            self.assertEqual(record["sha256_before"], record["sha256_after"])
        self.assertEqual(sha(CYCLE / "existing-output-before.xlsx"), sha(CYCLE / "existing-output-after.xlsx"))
        self.assertTrue(cleanup["archives_byte_identical"])
        self.assertFalse(cleanup["runtime_output_exists_after_cleanup"])
        self.assertFalse((BASE / "runs/EX03-attempt1/照合結果.xlsx").exists())

    def test_formal_fail_positive_two_run_pass_and_558_classification_stay_separate(self):
        acceptance = read_json("acceptance-status.json")
        formal = json.loads((FORMAL / "acceptance-status.json").read_text(encoding="utf-8"))
        aux = json.loads((AUX / "acceptance-status.json").read_text(encoding="utf-8"))
        self.assertEqual(formal["decision"]["failure_code"], "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD")
        self.assertFalse(acceptance["formal_ex03_r11_g1"]["accepted"])
        self.assertEqual(aux["auxiliary_downloaded_file_validation"]["pad_run_count"], 2)
        self.assertEqual(acceptance["file_aux1_positive"]["pad_runs"], 2)
        self.assertEqual(acceptance["file_aux1_positive"]["legacy_raw_difference_count_each_run"], 558)
        self.assertEqual(acceptance["file_aux1_positive"]["excel_effective_difference_count_each_run"], 0)
        self.assertTrue(acceptance["existing_output_guard"]["status"].startswith("PASS_"))
        self.assertFalse(acceptance["decision"]["issue38_closed_by_guard"])

    def test_screenshots_manifest_and_protected_scope_are_preserved(self):
        observation = read_json("pad-run-observation.json")
        for record in observation["screenshots"].values():
            path = ROOT / record["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(sha(path), record["sha256"])
        protected = read_json("protected-after.json")
        self.assertEqual(protected["mismatch_count"], 0)
        manifest = read_json("artifact-manifest.json")
        self.assertGreaterEqual(len(manifest["artifacts"]), 15)
        for record in manifest["artifacts"]:
            path = ROOT / record["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(sha(path), record["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
