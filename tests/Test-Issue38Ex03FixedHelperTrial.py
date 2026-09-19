"""Focused non-live gates for the one-run EX03 r12 fixed-helper trial."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper"
TRIAL = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
RUNTIME = TRIAL / "runtime"
PREFLIGHT = json.loads((TRIAL / "preflight.json").read_text(encoding="utf-8"))
CANDIDATE = (TRIAL / "candidate.robin").read_text(encoding="utf-8")
MISMATCH = json.loads((TRIAL / "pad-recopy-mismatch.json").read_text(encoding="utf-8"))
ANALYSIS = json.loads(
    (TRIAL / "pad-recopy-diff-analysis.json").read_text(encoding="utf-8")
)
RESULT = json.loads((TRIAL / "result.json").read_text(encoding="utf-8"))

BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03CandidateR12.py"
SPEC = importlib.util.spec_from_file_location("issue38_r12_trial_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue38Ex03FixedHelperTrialTests(unittest.TestCase):
    def test_baseline_and_one_run_scope_are_fixed(self):
        self.assertEqual(
            PREFLIGHT["baseline_commit"],
            "1f1e752eb82413b07437135a70eb7349dca313f0",
        )
        plan = json.loads((TRIAL / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["authorization"], {
            "normal_pad_runs": 1,
            "reruns": 0,
            "copilot_sends": 0,
        })

    def test_helper_invocation_launcher_and_candidate_hashes_match_preflight(self):
        for name in ("helper", "invocation", "launcher", "candidate"):
            record = PREFLIGHT["files"][name]
            self.assertEqual(sha256(ROOT / record["path"]), record["sha256"])

    def test_work_is_exact_template_copy_and_output_is_absent(self):
        self.assertEqual(
            sha256(RUNTIME / "work.xlsx"),
            PREFLIGHT["fixed_sha256"]["template"],
        )
        self.assertFalse((RUNTIME / "照合結果.xlsx").exists())

    def test_invocation_is_bound_only_to_dedicated_runtime(self):
        invocation = json.loads((TRIAL / "invocation.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(invocation["target_workbook"]), RUNTIME / "work.xlsx")
        self.assertEqual(Path(invocation["json_root"]), RUNTIME)
        self.assertEqual(len(invocation["text_writes"]), 7)

    def test_launcher_pins_real_helper_and_trial_invocation(self):
        launcher = (TRIAL / "launcher.ps1").read_text(encoding="utf-8")
        self.assertIn(str(PROBE / "EX03-R12-Fixed-StringTransfer.ps1"), launcher)
        self.assertIn(str(TRIAL / "invocation.json"), launcher)
        self.assertIn(PREFLIGHT["files"]["helper"]["sha256"], launcher)
        self.assertIn(PREFLIGHT["files"]["invocation"]["sha256"], launcher)

    def test_embedded_launcher_is_exact(self):
        embedded = builder.embedded_script(CANDIDATE)
        launcher = (TRIAL / "launcher.ps1").read_text(encoding="utf-8").rstrip("\r\n")
        self.assertEqual(embedded, launcher)

    def test_fixed_success_gate_precedes_writes_and_save(self):
        success = CANDIDATE.index(
            "IF PowershellOutput = $'''{\\\"status\\\":\\\"OK\\\",\\\"mode\\\":\\\"NORMAL\\\",\\\"text_writes\\\":7,\\\"formats_restored\\\":true}''' THEN"
        )
        mode = CANDIDATE.index("IF RunMode = $'''NORMAL''' THEN", success)
        numeric = CANDIDATE.index("Excel.WriteToExcel.WriteCell", mode)
        save_as = CANDIDATE.index("Excel.SaveExcel.SaveAs", numeric)
        self.assertLess(success, mode)
        self.assertLess(mode, numeric)
        self.assertLess(numeric, save_as)

    def test_fixed_twelve_cell_readback_shape_is_preserved(self):
        self.assertEqual(CANDIDATE.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson"), 12)
        self.assertIn(
            "SET 追記先_F6_ValueTypeMatch TO SourceCellJson = SavedCellJson",
            CANDIDATE,
        )
        self.assertEqual(CANDIDATE.count("Excel.SaveExcel.SaveAs"), 1)

    def test_stub_evidence_is_reused_without_execution(self):
        behavior = PREFLIGHT["return_behavior"]
        self.assertTrue(behavior["existing_stub_evidence_reused_without_rerun"])
        self.assertTrue(behavior["final_output_is_one_success_json"])
        self.assertEqual(
            behavior["stub_stdout"],
            '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}',
        )

    def test_pad_recopy_mismatch_fails_closed_before_any_run(self):
        self.assertEqual(
            MISMATCH["decision"],
            "STOP_PAD_RECOPY_NOT_BYTE_EXACT_NO_RUN",
        )
        self.assertFalse(MISMATCH["comparison"]["exact_text_and_utf8_bytes"])
        self.assertEqual(MISMATCH["observation"]["pad_run_count"], 0)
        self.assertEqual(MISMATCH["observation"]["helper_execution_count"], 0)
        self.assertEqual(MISMATCH["observation"]["excel_execution_count"], 0)
        self.assertEqual(
            RESULT["decision"],
            "STOPPED_PRE_RUN_PAD_RECOPY_NOT_EXACT",
        )
        self.assertEqual(RESULT["pad"]["run_count"], 0)
        self.assertEqual(RESULT["execution"]["output"], "ABSENT")

    def test_recopy_has_one_preserved_hunk_and_only_decoded_launcher_matches(self):
        self.assertEqual(ANALYSIS["content_diff_hunk_count"], 1)
        self.assertTrue(ANALYSIS["classification"]["decoded_embedded_launcher_exact"])
        self.assertTrue(
            ANALYSIS["classification"][
                "semantic_equivalence_does_not_satisfy_byte_exact_gate"
            ]
        )
        hunk = ANALYSIS[
            "content_diff_hunks_ignoring_line_endings_and_final_newline"
        ][0]
        self.assertEqual(hunk["candidate_lines"], [48, 48])
        self.assertEqual(hunk["recopy_lines"], [48, 48])
        self.assertNotEqual(hunk["candidate"], hunk["recopy"])

    def test_stop_preserves_template_and_leaves_handoff_absent(self):
        self.assertTrue(RESULT["preservation"]["work_still_exact_template"])
        self.assertEqual(
            RESULT["sha256"]["work"],
            RESULT["sha256"]["template"],
        )
        self.assertTrue(RESULT["preservation"]["json_handoff_files_absent"])
        self.assertFalse((RUNTIME / "source-1.json").exists())
        self.assertFalse((RUNTIME / "mode.json").exists())
        self.assertFalse((RUNTIME / "照合結果.xlsx").exists())
        self.assertTrue(all(value == "NOT_RUN" for key, value in RESULT["comparison"].items() if key != "reason"))

    def test_formal_r12_protected_files_remain_at_baseline_blobs(self):
        baseline = PREFLIGHT["baseline_commit"]
        for path, expected_blob in PREFLIGHT["protected_baseline_blobs"].items():
            observed = subprocess.run(
                ["git", "rev-parse", f"{baseline}:{path}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(observed, expected_blob, path)
            unchanged = subprocess.run(
                ["git", "diff", "--quiet", baseline, "--", path],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(unchanged.returncode, 0, path)


if __name__ == "__main__":
    unittest.main()
