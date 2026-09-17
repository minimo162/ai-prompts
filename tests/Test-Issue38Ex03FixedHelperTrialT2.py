"""Evidence-bound checks for the single saved-flow T2 fixed-helper Run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUN = T2 / "run1"
RUNTIME = T1 / "runtime"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue38Ex03FixedHelperTrialT2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity = load(T2 / "pad-recopy.json")
        cls.preflight = load(T2 / "preflight.json")
        cls.pad_run = load(RUN / "pad-run.json")
        cls.pad_variables = load(RUN / "pad-variables.json")
        cls.artifact = load(RUN / "artifact.json")
        cls.typed = load(RUN / "typed-transfer.json")
        cls.legacy = load(RUN / "comparison.json")
        cls.native = load(RUN / "native-styles.json")
        cls.f6 = load(RUN / "f6-native.json")
        cls.result = load(T2 / "result.json")

    def test_saved_flow_is_exact_t1_execution_baseline(self):
        expected = "da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa"
        self.assertEqual(self.identity["comparison"]["current_saved_flow_sha256"], expected)
        self.assertTrue(self.identity["comparison"]["byte_exact_to_t1_baseline"])
        self.assertEqual(sha256(T2 / "pad-recopy-before-run.robin"), expected)
        self.assertEqual(
            (T2 / "pad-recopy-before-run.robin").read_bytes(),
            (T1 / "pad-recopy-mismatch.robin").read_bytes(),
        )
        self.assertEqual(self.preflight["identity"]["unknown_content_difference_count"], 0)
        self.assertTrue(self.preflight["identity"]["decoded_saved_flow_launcher_exact"])
        self.assertTrue(self.preflight["identity"]["other_robin_processing_exact_after_known_difference"])

    def test_fixed_helper_invocation_launcher_and_paths_are_unchanged(self):
        expected = {
            "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
            "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
            "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
        }
        self.assertEqual(
            sha256(PROBE / "EX03-R12-Fixed-StringTransfer.ps1"), expected["helper"]
        )
        self.assertEqual(sha256(T1 / "invocation.json"), expected["invocation"])
        self.assertEqual(sha256(T1 / "launcher.ps1"), expected["launcher"])
        for name, value in expected.items():
            self.assertEqual(self.result["execution_identity"][f"{name}_sha256"], value)
        self.assertTrue(self.result["execution_identity"]["fixed_paths_unchanged"])

    def test_exactly_one_run_completed_with_success_json(self):
        self.assertEqual(self.pad_run["run_index"], 1)
        self.assertEqual(self.pad_run["run_invocations_total"], 1)
        self.assertEqual(self.result["pad"]["run_count"], 1)
        self.assertEqual(self.result["pad"]["repaste_count"], 0)
        self.assertEqual(self.result["pad"]["resave_count"], 0)
        self.assertEqual(
            self.result["pad"]["powershell_stdout"],
            '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}',
        )
        self.assertTrue(self.result["pad"]["terminal"]["normal_termination_observed"])
        self.assertFalse(self.result["pad"]["terminal"]["designer_error_observed"])
        self.assertFalse(self.result["pad"]["stderr"]["empty_stderr_directly_proven"])

    def test_pad_reports_transfer_state_and_all_twelve_type_matches(self):
        self.assertEqual(
            self.pad_variables["transfer_state"]["observed_value"],
            "SAVED_REOPENED_12_JSON_COMPARISONS_READY",
        )
        self.assertEqual(self.pad_variables["counts"], {"true": 12, "false": 0, "total": 12})
        self.assertEqual(len(self.pad_variables["value_type_matches"]), 12)
        self.assertTrue(
            all(
                value == {"observed_value": True, "match": True}
                for value in self.pad_variables["value_type_matches"].values()
            )
        )

    def test_preserved_artifact_is_bound_to_all_comparison_reports(self):
        result_sha = sha256(RUN / "result.xlsx")
        self.assertEqual(self.artifact["output_sha256"], result_sha)
        self.assertEqual(self.typed["output"]["sha256_before"], result_sha)
        self.assertEqual(self.typed["output"]["sha256_after"], result_sha)
        self.assertEqual(self.legacy["output_sha_before"], result_sha)
        self.assertEqual(self.legacy["output_sha_after"], result_sha)
        self.assertEqual(self.native["sha256_before"]["output"], result_sha)
        self.assertEqual(self.native["sha256_after"]["output"], result_sha)
        self.assertEqual(self.f6["output_sha256_before"], result_sha)
        self.assertEqual(self.f6["output_sha256_after"], result_sha)
        self.assertEqual(self.result["artifact"]["result_sha256"], result_sha)

    def test_saved_workbook_value_type_position_and_outside_contract_passes(self):
        self.assertEqual(self.typed["status"], "MATCH_FIXED_EX03_TEXT_NUMBER_SCOPE")
        self.assertEqual(len(self.typed["mappings"]), 12)
        self.assertEqual(self.typed["mismatches"], [])
        self.assertTrue(
            all(
                item["source_matches_expected"]
                and item["target_matches_expected"]
                and item["source_matches_target"]
                for item in self.typed["mappings"]
            )
        )
        self.assertEqual(
            self.legacy["checks"]["target_values_types_positions"],
            {"checked": 12, "mismatches": [], "status": "MATCH_SAVED_XLSX_ONLY"},
        )
        self.assertEqual(
            self.legacy["checks"]["outside_values_types_formulas"],
            {"checked": 468, "mismatches": [], "status": "MATCH_SAVED_XLSX_ONLY"},
        )

    def test_effective_format_and_f6_contract_passes(self):
        self.assertEqual(self.native["status"], "MATCH_EFFECTIVE_FORMAT")
        self.assertEqual(
            self.native["difference_attribute_counts"],
            {"cell_style": 0, "row_dimension": 0, "column_dimension": 0, "sheet_structure": 0},
        )
        self.assertEqual(self.native["bounds"]["checked_cells"], 480)
        self.assertEqual(self.native["bounds"]["checked_rows"], 48)
        self.assertEqual(self.native["bounds"]["checked_columns"], 30)
        self.assertEqual(self.f6["saved_f6"]["value2"], "100%")
        self.assertEqual(self.f6["saved_f6"]["value2_dotnet_type"], "System.String")
        self.assertEqual(self.f6["saved_f6"]["number_format_invariant"], "G/標準")
        self.assertEqual(self.f6["saved_f6"]["prefix_character"], "")
        self.assertFalse(self.f6["saved_f6"]["has_formula"])
        self.assertTrue(all(self.f6["checks"].values()))

    def test_legacy_558_fail_is_preserved_separately(self):
        self.assertEqual(self.legacy["status"], "FAIL")
        self.assertEqual(
            self.legacy["failure_counts"],
            {"styles": 480, "row_dimensions": 48, "column_dimensions": 30},
        )
        self.assertEqual(sum(self.legacy["failure_counts"].values()), 558)
        self.assertEqual(
            self.result["comparison"]["legacy_raw_diagnostic"]["status"],
            "FAIL_PRESERVED_NOT_USED_AS_EFFECTIVE_FORMAT_GATE",
        )

    def test_t1_runtime_and_protected_records_are_restored_and_unchanged(self):
        self.assertEqual(sha256(RUNTIME / "work.xlsx"), EXPECTED_WORK_SHA)
        self.assertFalse((RUNTIME / "照合結果.xlsx").exists())
        self.assertEqual(list(RUNTIME.glob("*.json")), [])
        self.assertEqual(load(T1 / "result.json")["pad"]["run_count"], 0)
        for item in self.preflight["protected_tracked_files"]:
            observed = subprocess.run(
                ["git", "hash-object", f"--path={item['path']}", str(ROOT / item["path"])],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(observed, item["git_blob"], item["path"])

    def test_final_decision_is_auxiliary_only(self):
        self.assertEqual(self.result["decision"], "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1")
        self.assertIn("not formal EX03-r12 acceptance", self.result["scope"])
        self.assertTrue(self.result["preservation"]["t1_fail_run0_records_unchanged"])
        self.assertTrue(self.result["preservation"]["formal_ex03_r12_unchanged"])
        self.assertFalse(self.result["preservation"]["github_write"])

if __name__ == "__main__":
    unittest.main()
