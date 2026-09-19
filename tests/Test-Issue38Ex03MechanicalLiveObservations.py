#!/usr/bin/env python3
"""FR1/FR2 non-live regression: mutate JSON copies, never move/rebuild evidence."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper-mechanical-builder"
SPEC = importlib.util.spec_from_file_location("mechanical_live3_fr_review", PROBE / "Live3Trial.py")
LIVE3 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(LIVE3)
LIVE2 = LIVE3.live2
MISSING = object()
NORMAL_FILES = {
    "run": "pad-run.json", "variables": "pad-variables.json", "artifact": "artifact.json",
    "typed": "typed-transfer.json", "legacy": "comparison.json",
    "native": "native-styles.json", "f6": "f6-native.json",
}
NORMALS = {
    "LIVE2": (LIVE2.RUN, LIVE2.TRIAL_ID, LIVE2.RUN_ID),
    "LIVE3_NORMAL": (LIVE3.NORMAL_RUN, LIVE3.NORMAL_ID, LIVE3.NORMAL_RUN_ID),
}


def change(records, path, value):
    target = records
    for key in path[:-1]:
        target = target[key]
    if value is MISSING:
        del target[path[-1]]
    else:
        target[path[-1]] = copy.deepcopy(value)


class MechanicalLiveObservationTests(unittest.TestCase):
    rejected_cases = 0

    @classmethod
    def setUpClass(cls):
        cls.normals = {
            profile: {key: LIVE2.load(directory / filename) for key, filename in NORMAL_FILES.items()}
            for profile, (directory, _, _) in NORMALS.items()
        }
        cls.guard = {
            "normal": LIVE3.load(LIVE3.NORMAL / "result.json"),
            "preflight": LIVE3.load(LIVE3.GUARD / "preflight.json"),
            "pad_run": LIVE3.load(LIVE3.GUARD / "pad-run.json"),
            "variables": LIVE3.load(LIVE3.GUARD / "pad-variables.json"),
            "hashes": LIVE3.load(LIVE3.GUARD / "hashes-after-run.json"),
        }
        cls.preserved = {
            path: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, path.stat().st_mtime_ns)
            for tree in (LIVE2.TRIAL, LIVE3.CAMPAIGN)
            for path in tree.rglob("*") if path.is_file()
        }

    @classmethod
    def tearDownClass(cls):
        after = {
            path: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, path.stat().st_mtime_ns)
            for tree in (LIVE2.TRIAL, LIVE3.CAMPAIGN)
            for path in tree.rglob("*") if path.is_file()
        }
        if after != cls.preserved:
            raise AssertionError("Existing LIVE2/LIVE3 evidence changed during non-live tests")

    def setUp(self):
        # No live finalizer/capture/preflight is called. Fail fast on accidental
        # preservation, regeneration, process launch or evidence writes.
        for target, name in (
            (LIVE2, "write_json"), (LIVE3, "write_json"), (Path, "write_text"),
            (Path, "write_bytes"), (LIVE3.shutil, "move"), (LIVE3.shutil, "copy2"),
            (LIVE3.subprocess, "Popen"),
        ):
            patcher = mock.patch.object(target, name, side_effect=AssertionError("non-live validator attempted a write/launch"))
            patcher.start()
            self.addCleanup(patcher.stop)

    def validate_normal(self, profile, records):
        directory, trial_id, run_id = NORMALS[profile]
        return LIVE2.validate_normal_records(
            records["run"], records["variables"], records["artifact"], records["typed"],
            records["legacy"], records["native"], records["f6"], directory / "result.xlsx",
            trial_id=trial_id, run_id=run_id, profile=profile,
        )

    def reject(self, profile, path, value):
        original = self.guard if profile == "GUARD" else self.normals[profile]
        records = copy.deepcopy(original)
        change(records, path, value)
        before_validation = copy.deepcopy(records)
        with self.subTest(profile=profile, path=path, value=repr(value)[:90]):
            with self.assertRaises(ValueError):
                if profile == "GUARD":
                    LIVE3.validate_guard_records(**records)
                else:
                    self.validate_normal(profile, records)
            self.assertEqual(records, before_validation, "validation must not repair/overwrite evidence")
            type(self).rejected_cases += 1

    def test_existing_live2_and_live3_normal_records_pass_unchanged(self):
        for profile, records in self.normals.items():
            before = copy.deepcopy(records)
            with self.subTest(profile=profile):
                self.assertEqual(self.validate_normal(profile, records), records["artifact"]["output_sha256"])
                self.assertEqual(records, before)

    def test_existing_guard_passes_without_grading_stale_type_flags(self):
        before = copy.deepcopy(self.guard)
        LIVE3.validate_guard_records(**self.guard)
        self.assertEqual(self.guard, before)
        self.assertTrue(self.guard["variables"]["value_type_matches"].startswith("NOT_EVALUATED"))

    def test_normal_expected_trial_run_and_unmodified_report_label(self):
        for profile in NORMALS:
            for record in ("run", "variables", "artifact"):
                for key in ("trial_id", "run_id"):
                    self.reject(profile, (record, key), "WRONG-TRIAL-RUN")
            for label in ("EX03-R11-FILE-AUX1-RUN1", LIVE3.GUARD_RUN_ID, "WRONG-RUN"):
                self.reject(profile, ("typed", "run_label"), label)

    def test_normal_exact_variable_names_and_nonempty_mapping(self):
        for profile in NORMALS:
            for empty in ({}, []):
                self.reject(profile, ("variables", "value_type_matches"), empty)
            for name in self.normals[profile]["variables"]["value_type_matches"]:
                renamed = copy.deepcopy(self.normals[profile]["variables"]["value_type_matches"])
                renamed[name + "Wrong"] = renamed.pop(name)
                self.reject(profile, ("variables", "value_type_matches"), renamed)
                self.reject(profile, ("variables", "value_type_matches", name), MISSING)

    def test_each_normal_flag_must_be_boolean_true_with_required_keys(self):
        for profile in NORMALS:
            for name in self.normals[profile]["variables"]["value_type_matches"]:
                for key in ("observed_value", "match"):
                    for value in (False, 1, MISSING):
                        self.reject(profile, ("variables", "value_type_matches", name, key), value)

    def test_normal_aggregate_counts_cannot_replace_individual_evidence(self):
        for profile in NORMALS:
            for value in ({}, [], {"true": 11, "false": 1, "total": 12}, {"true": 12.0, "false": 0, "total": 12}):
                self.reject(profile, ("variables", "counts"), value)
            for key in ("true", "false", "total"):
                self.reject(profile, ("variables", "counts", key), MISSING)

    def test_normal_required_keys_and_terminal_observations(self):
        common = {
            "run": ("schema_version", "trial_id", "run_id", "status", "terminal_observation", "powershell"),
            "variables": ("schema_version", "trial_id", "run_id", "status", "probe_state", "counts", "value_type_matches"),
            "artifact": ("schema_version", "trial_id", "run_id", "status", "runtime_output_path", "preserved_output_path", "output_sha256", "output_bytes", "work_sha256", "handoff_sha256"),
            "typed": ("run_label", "mappings", "output"),
            "native": ("bounds", "sha256_before"),
        }
        for profile in NORMALS:
            for record, keys in common.items():
                for key in keys:
                    self.reject(profile, (record, key), MISSING)
            for key in self.normals[profile]["run"]["terminal_observation"]:
                self.reject(profile, ("run", "terminal_observation", key), MISSING)
            for key in ("stdout_observed", "stdout_matches_fixed_success_json", "stderr_empty_not_claimed"):
                self.reject(profile, ("run", "powershell", key), MISSING)
            self.reject(profile, ("run", "terminal_observation", "designer_error_observed"), True)
            self.reject(profile, ("variables", "probe_state", "match"), False)

    def test_normal_artifact_and_comparison_records_are_bound(self):
        cases = [
            (("artifact", "output_sha256"), "0" * 64),
            (("artifact", "output_bytes"), 0),
            (("artifact", "preserved_output_path"), "wrong-run/result.xlsx"),
            (("artifact", "handoff_sha256"), {}),
            (("typed", "output", "sha256_before"), "0" * 64),
            (("typed", "output", "path"), "wrong-run/result.xlsx"),
            (("typed", "mappings"), []),
            (("legacy", "output_sha_before"), "0" * 64),
            (("native", "sha256_before", "output"), "0" * 64),
            (("native", "bounds"), {}),
            (("f6", "output_sha256_before"), "0" * 64),
        ]
        for profile in NORMALS:
            for path, value in cases:
                self.reject(profile, path, value)

    def test_guard_expected_ids_required_keys_and_nonentry_flags(self):
        for record in self.guard:
            for key in ("schema_version", "trial_id", "run_id"):
                self.reject("GUARD", (record, key), MISSING)
            for key in ("trial_id", "run_id"):
                self.reject("GUARD", (record, key), "WRONG-TRIAL-RUN")
        for flag in ("script_gate_passed", "numeric_write_entered", "save_as_entered"):
            self.reject("GUARD", ("variables", flag), MISSING)
            for key in ("observed_value", "expected", "match"):
                self.reject("GUARD", ("variables", flag, key), MISSING)
                self.reject("GUARD", ("variables", flag, key), key != "match")
        for path, value in (
            (("variables", "value_type_matches"), {}),
            (("variables", "value_type_matches"), self.normals["LIVE3_NORMAL"]["variables"]["value_type_matches"]),
            (("variables", "value_type_matches"), MISSING),
            (("variables", "powershell_output"), LIVE3.EXPECTED_SUCCESS),
            (("pad_run", "campaign_run_index"), 1),
            (("preflight", "type_comparison_policy"), "PASS"),
            (("normal", "guard_authorized_to_proceed"), False),
            (("normal", "artifact", "sha256"), "0" * 64),
            (("preflight", "normal_prerequisite", "trial_id"), "WRONG-TRIAL"),
            (("preflight", "normal_prerequisite", "artifact_sha256"), "0" * 64),
        ):
            self.reject("GUARD", path, value)

    def test_guard_nonempty_snapshots_and_artifact_binding(self):
        sample_path = LIVE3.relative(LIVE3.OUTPUT)
        for record, key in (("preflight", "protected_before"), ("hashes", "protected_before"), ("hashes", "protected_after")):
            for value in ({}, [], MISSING):
                self.reject("GUARD", (record, key), value)
            self.reject("GUARD", (record, key, sample_path), MISSING)
            for field in ("path", "sha256", "bytes", "last_write_ns"):
                self.reject("GUARD", (record, key, sample_path, field), MISSING)
            self.reject("GUARD", (record, key, sample_path, "sha256"), "0" * 64)
            self.reject("GUARD", (record, key, sample_path, "last_write_ns"), 1)
        for key in ("existing_output_before_archive_sha256", "existing_output_after_archive_sha256"):
            self.reject("GUARD", ("hashes", key), "0" * 64)
            self.reject("GUARD", ("hashes", key), MISSING)


class A4ReferenceCaseTests(unittest.TestCase):
    def test_three_references_match_git_case_without_renaming_evidence(self):
        path = "catalog/acceptance/issue38/cycles/EX03-R12-FIXED-HELPER-A4-G1/RESULT.md"
        tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", path], cwd=ROOT, text=True).splitlines()
        self.assertEqual(tracked, [path])
        for filename in ("report.md", "status.json", "case-matrix.json"):
            text = (ROOT / "catalog/acceptance/issue38" / filename).read_text(encoding="utf-8")
            self.assertEqual(text.count("cycles/EX03-R12-FIXED-HELPER-A4-G1/RESULT.md"), 1)
            self.assertNotIn("cycles/EX03-r12-fixed-helper-A4-G1/RESULT.md", text)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "positive_controls": 3,
        "negative_mutations_rejected": MechanicalLiveObservationTests.rejected_cases,
        "evidence_files_preserved": len(MechanicalLiveObservationTests.preserved),
        "artifact_regeneration_or_moves": 0,
        "status": "PASS" if result.wasSuccessful() else "FAIL",
    }))
    raise SystemExit(0 if result.wasSuccessful() else 1)
