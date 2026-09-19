#!/usr/bin/env python3
"""Freeze the single-send, at-most-two-run EX03 r8 live-acceptance cycle."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r8-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260916-excel-r8"
BASE_COMMIT = "eb8693c5157563bbc69d47d8410093ca30565a30"

EXPECTED = {
    "manifest": "9025c8869b84d27e4f39512ce157a114a5231041e641ae12ef36c061eae29d3e",
    "instruction": "57f0cdb656e919f8fd83252a6adcd4d12788dac9bf6833db2f2e942eada23bcb",
    "bundle": "164c99e59204efd863f4fe283e8f84ce2902ee760ab90e45cf7c5336631aaddb",
    "robin_support": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "script_support": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

FIXED_COMPLETION_TERMS = [
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\fixtures\\EX03\\入力い.xlsx",
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\fixtures\\EX03\\入力ろ.xlsx",
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\runs\\EX03-attempt1\\work.xlsx",
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\runs\\EX03-attempt1\\照合結果.xlsx",
    "受取明細",
    "追加項目",
    "集計先",
    "追記先",
]
GRADER_ONLY_VALUES = ["春", "夏", "秋", "項目甲", "項目乙", "-4.5", "6.25", "100%"]
INDEPENDENT_EXAMPLE_TERMS = [
    "source-one.xlsx",
    "source-two.xlsx",
    "work-copy.xlsx",
    "example-result.xlsx",
    "教材入力一",
    "教材入力二",
    "教材出力一",
    "教材出力二",
]


def load_oracle():
    spec = importlib.util.spec_from_file_location(
        "issue38_excel_oracle", ROOT / "tools/Verify-Issue38Excel.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load_oracle()


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def write_bytes(path: Path, value: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(value)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def protected_paths() -> list[Path]:
    fixed = [
        BASE / "expected.json",
        BASE / "spec.json",
        BASE / "freeze.json",
        BASE / "requests/EX03.txt",
        BASE / "fixtures/EX03/入力い.xlsx",
        BASE / "fixtures/EX03/入力ろ.xlsx",
        BASE / "fixtures/EX03/ひな形.xlsx",
        RUN / "work.xlsx",
        RUN / "preparation.json",
    ]
    trees = [
        ROOT / "copilot/versions/20260916-excel-r6",
        ROOT / "copilot/versions/20260916-excel-r7",
        VERSION,
        BASE / "cycles/EX03-r5-G1",
        BASE / "cycles/EX03-r6-G1",
        BASE / "probes/ex03-r7-robin-source",
        BASE / "probes/ex03-r8-independent-source",
        BASE / "probes/percent-text-write",
    ]
    paths = list(fixed)
    for tree in trees:
        paths.extend(sorted(path for path in tree.rglob("*") if path.is_file()))
    unique = {path.resolve(): path for path in paths}
    return [unique[key] for key in sorted(unique, key=lambda item: str(item).lower())]


def prepare() -> dict[str, object]:
    if CYCLE.exists():
        raise ValueError(f"Cycle already exists; refusing overwrite: {CYCLE}")
    head = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != BASE_COMMIT:
        raise ValueError(f"Expected base commit {BASE_COMMIT}, found {head}")
    oracle.check_frozen()

    manifest_path = VERSION / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    instruction_path = VERSION / manifest["instruction_path"]
    bundle_path = VERSION / manifest["bundle_path"]
    support = {Path(record["path"]).suffix: record for record in manifest["support_files"]}
    robin_record = support[".robin"]
    script_record = support[".txt"]
    robin_path = VERSION / robin_record["path"]
    script_path = VERSION / script_record["path"]

    actual_package = {
        "manifest": sha(manifest_path),
        "instruction": sha(instruction_path),
        "bundle": sha(bundle_path),
        "robin_support": sha(robin_path),
        "script_support": sha(script_path),
    }
    for key, actual in actual_package.items():
        if actual != EXPECTED[key]:
            raise ValueError(f"r8 {key} hash mismatch: {actual}")
    if manifest["version"] != "20260916-excel-r8":
        raise ValueError("Unexpected candidate version")
    if manifest["inherits_live_acceptance"]:
        raise ValueError("r8 must not inherit live acceptance")
    if manifest["evidence"]["teaching_test_independence"] != (
        "PASS_R8_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT"
    ):
        raise ValueError("r8 independence evidence is not passing")
    for record in manifest["source_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r8 source mismatch: " + record["path"])
    for path, expected in manifest["evidence_inputs"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("r8 evidence input changed: " + path)

    request_path = BASE / "requests/EX03.txt"
    spec_path = BASE / "spec.json"
    expected_path = BASE / "expected.json"
    input_a_path = BASE / "fixtures/EX03/入力い.xlsx"
    input_b_path = BASE / "fixtures/EX03/入力ろ.xlsx"
    template_path = BASE / "fixtures/EX03/ひな形.xlsx"
    work_path = RUN / "work.xlsx"
    output_path = RUN / "照合結果.xlsx"
    fixed_actual = {
        "request": sha(request_path),
        "spec": sha(spec_path),
        "expected": sha(expected_path),
        "input_a": sha(input_a_path),
        "input_b": sha(input_b_path),
        "template": sha(template_path),
    }
    for key, actual in fixed_actual.items():
        if actual != EXPECTED[key]:
            raise ValueError(f"Fixed {key} hash mismatch: {actual}")
    if not work_path.is_file() or sha(work_path) != EXPECTED["template"]:
        raise ValueError("EX03 work copy must exist and match the frozen template")
    if output_path.exists():
        raise ValueError("EX03 output must be absent before staging the single live request")

    body = instruction_path.read_bytes() + b"\n" + request_path.read_bytes() + b"\n"
    body_text = body.decode("utf-8")
    leaked_values = [value for value in GRADER_ONLY_VALUES if value in body_text]
    if leaked_values:
        raise ValueError(f"Grader-only values leaked into submitted body: {leaked_values}")
    leaked_example = [value for value in INDEPENDENT_EXAMPLE_TERMS if value in body_text]
    if leaked_example:
        raise ValueError(f"Independent example data leaked into submitted body: {leaked_example}")
    bundle_text = bundle_path.read_text(encoding="utf-8")
    fixed_bundle_leaks = [value for value in FIXED_COMPLETION_TERMS if value in bundle_text]
    if fixed_bundle_leaks:
        raise ValueError(f"Fixed EX03 complete-answer terms leaked into r8 bundle: {fixed_bundle_leaks}")
    unique_grader_leaks = [value for value in GRADER_ONLY_VALUES[:-1] if value in bundle_text]
    if unique_grader_leaks:
        raise ValueError(f"Unique grader-only values leaked into r8 bundle: {unique_grader_leaks}")

    protected_list = protected_paths()
    protected = {
        "schema_version": 1,
        "cycle_id": "EX03-R8-G1",
        "base_commit": head,
        "files": [
            {"path": repo_path(path), "sha256": sha(path)} for path in protected_list
        ],
    }

    CYCLE.mkdir(parents=True, exist_ok=False)
    submitted_path = CYCLE / "submitted-body.txt"
    write_bytes(submitted_path, body)
    plan = {
        "schema_version": 1,
        "cycle_id": "EX03-R8-G1",
        "base_commit": head,
        "purpose": "One normal-M365 generation and at-most-two unmodified PAD runs for fixed EX03 after teaching/test separation",
        "candidate": {
            "version": manifest["version"],
            "instruction_path": repo_path(instruction_path),
            "instruction_sha256": sha(instruction_path),
            "bundle_path": repo_path(bundle_path),
            "bundle_sha256": sha(bundle_path),
            "manifest_path": repo_path(manifest_path),
            "manifest_sha256": sha(manifest_path),
            "robin_support_path": repo_path(robin_path),
            "robin_support_sha256": sha(robin_path),
            "script_support_path": repo_path(script_path),
            "script_support_sha256": sha(script_path),
            "inherits_live_acceptance": False,
        },
        "fixed_inputs": {
            "request": {"path": repo_path(request_path), "sha256": sha(request_path)},
            "spec": {"path": repo_path(spec_path), "sha256": sha(spec_path)},
            "grader_only_expected": {
                "path": repo_path(expected_path),
                "sha256": sha(expected_path),
                "send_to_copilot": False,
            },
            "input_a": {"path": repo_path(input_a_path), "sha256": sha(input_a_path)},
            "input_b": {"path": repo_path(input_b_path), "sha256": sha(input_b_path)},
            "template": {"path": repo_path(template_path), "sha256": sha(template_path)},
            "work": {
                "path": repo_path(work_path),
                "sha256": sha(work_path),
                "must_match_template_before_each_run": True,
            },
            "output": {
                "path": repo_path(output_path),
                "must_be_absent_before_each_run": True,
            },
        },
        "submission": {
            "body_path": repo_path(submitted_path),
            "body_sha256": sha(submitted_path),
            "body_contract": "unchanged full r8 instructions followed by unchanged fixed EX03 request",
            "attachment_path": repo_path(bundle_path),
            "attachment_sha256": sha(bundle_path),
            "normal_m365_new_chat": True,
            "model": "Think Deeper",
            "grader_only_expected_excluded": True,
            "fixed_completed_robin_excluded": True,
            "independent_teaching_robin_in_bundle": True,
            "action_time_confirmation_required_before_send": True,
        },
        "limits": {
            "max_generation_requests": 1,
            "max_pad_runs": 2,
            "no_regeneration_or_manual_robin_repair": True,
            "stop_on_refusal_safety_issue_mismatch_or_unknown_result": True,
            "run2_requires_run1_terminal_and_artifact_preserved": True,
        },
        "acceptance": {
            "scope": "fixed EX03 text/number case and r8 package only",
            "required": [
                "one normal-M365 send with exact full body and actual same-version bundle",
                "unmodified generated Robin in a new dedicated Power Fx OFF flow",
                "PAD save and re-copy before Run1",
                "Run1 terminal confirmation and full artifact preservation before Run2",
                "two runs with all twelve source/readback JSON type comparisons",
                "all fixed values, types, positions, outside cells, formulas and effective formats",
                "F6 exact System.String 100%, original format, empty prefix and no formula",
                "all protected input/template SHA values unchanged",
            ],
            "no_old_or_other_case_pass_inheritance": True,
            "no_unconfirmed_type_or_shape_generalization": True,
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path_still_required": True,
        },
        "github_write": False,
        "status": "READY_FOR_BROWSER_STAGING_ONLY",
    }
    preflight = {
        "schema_version": 1,
        "cycle_id": "EX03-R8-G1",
        "base_commit": head,
        "checks": {
            "base_commit_matches_frozen_r8": True,
            "fixed_fixture_spec_request_expected_hashes_match": True,
            "r8_instruction_bundle_manifest_support_hashes_match": True,
            "r8_all_evidence_input_hashes_match": True,
            "r8_teaching_test_independence_pass": True,
            "fixed_complete_answer_absent_from_r8_bundle": True,
            "grader_only_values_absent_from_submitted_body": True,
            "independent_example_data_absent_from_submitted_body": True,
            "work_exists_and_matches_template": True,
            "output_absent": True,
        },
        "hashes": {
            "submitted_body": sha(submitted_path),
            "instruction": sha(instruction_path),
            "bundle": sha(bundle_path),
            "manifest": sha(manifest_path),
            "robin_support": sha(robin_path),
            "script_support": sha(script_path),
            "work_and_template": sha(work_path),
            "input_a": sha(input_a_path),
            "input_b": sha(input_b_path),
        },
        "counts": {
            "protected_files": len(protected_list),
            "submitted_body_utf16_units": len(body_text.encode("utf-16-le")) // 2,
            "submitted_body_utf8_bytes": len(body),
        },
        "decision": {
            "browser_staging": "READY",
            "send": "REQUIRES_ACTION_TIME_CONFIRMATION",
            "copilot_generation": "NOT_STARTED",
            "pad_run1": "NOT_STARTED",
            "pad_run2": "NOT_STARTED",
        },
    }
    write_json(CYCLE / "plan.json", plan)
    write_json(CYCLE / "protected-files-before.json", protected)
    write_json(CYCLE / "preflight.json", preflight)
    return {
        "cycle": repo_path(CYCLE),
        "version": manifest["version"],
        "submitted_body_sha256": sha(submitted_path),
        "submitted_body_utf16_units": preflight["counts"]["submitted_body_utf16_units"],
        "bundle_sha256": sha(bundle_path),
        "manifest_sha256": sha(manifest_path),
        "protected_file_count": len(protected_list),
        "status": plan["status"],
    }


if __name__ == "__main__":
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))
