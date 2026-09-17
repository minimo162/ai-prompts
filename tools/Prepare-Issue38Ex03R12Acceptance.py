#!/usr/bin/env python3
"""Create the local-only EX03-r12-G1 live acceptance checkpoint.

This script performs no browser, Copilot, PAD, or Excel UI action.  It freezes
the exact submission body and attachment plus the one-send/two-run stop rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r12-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260917-excel-r12"
BASE_COMMIT = "0f6e47197ecb5f4316e00aa319efa6c4213f696f"

PATHS = {
    "instruction": VERSION / "agent-instructions.txt",
    "bundle": VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "manifest": VERSION / "manifest.json",
    "normal_robin": VERSION / "support/EX03-R12-Prepared-Normal.robin",
    "negative_robin": VERSION / "support/EX03-R12-Prepared-Exception-Negative.robin",
    "script": VERSION / "support/EX03-R12-JSON-File-Handoff.ps1.txt",
    "contract": VERSION / "support/EX03-R12-JSON-Handoff-Contract.txt",
    "request": BASE / "requests/EX03.txt",
    "spec": BASE / "spec.json",
    "expected": BASE / "expected.json",
    "input_a": BASE / "fixtures/EX03/入力い.xlsx",
    "input_b": BASE / "fixtures/EX03/入力ろ.xlsx",
    "template": BASE / "fixtures/EX03/ひな形.xlsx",
    "work": RUN / "work.xlsx",
    "output": RUN / "照合結果.xlsx",
}

EXPECTED_SHA256 = {
    "instruction": "11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06",
    "bundle": "ddee43a1eddc966f62095b63a23b135df184f3cbe0ded635cbf72520e6744b97",
    "manifest": "a6f65db93d56c1e0a212a8059f034240489b29ee4cfd4abc6b998e73ea2cefb1",
    "normal_robin": "7bde8bb20bb7f347c97722d77a4141bf8348bb40d97aaca435e01998e8b9d3a3",
    "negative_robin": "2c826e2d478075991db8a264c7396adcc5cd6ce454232f8d332b558f61b0c054",
    "script": "314b687ce8d1848558d80340b414d32c8d3baca2c5e699541db0eb062f96ba1c",
    "contract": "b44d5901e4cd8c01b6ca1012e5e376f90a4bfeae5045fd269738103c93181b03",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "work": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

GRADER_ONLY_VALUES = ["春", "夏", "秋", "項目甲", "項目乙", "-4.5", "6.25", "100%"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def write_json(path: Path, content: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def verify_fixed_state() -> dict[str, object]:
    head = git("rev-parse", "HEAD")
    if head != BASE_COMMIT:
        raise ValueError(f"Expected HEAD {BASE_COMMIT}, found {head}")
    status = {line for line in git("status", "--porcelain=v1").splitlines() if line}
    allowed = {"?? tools/Prepare-Issue38Ex03R12Acceptance.py"}
    if status != allowed:
        raise ValueError(f"Unexpected pre-cycle changes: {sorted(status)}")
    if CYCLE.exists():
        raise ValueError(f"Cycle already exists; refusing overwrite: {CYCLE}")

    for name, expected in EXPECTED_SHA256.items():
        actual = sha256(PATHS[name])
        if actual != expected:
            raise ValueError(f"{name} SHA mismatch: {actual}")
    if PATHS["output"].exists():
        raise ValueError("Fixed output already exists before r12 send")

    manifest = json.loads(PATHS["manifest"].read_bytes())
    if manifest["version"] != "20260917-excel-r12":
        raise ValueError("Unexpected candidate version")
    if manifest["inherits_live_acceptance"] is not False:
        raise ValueError("r12 must not inherit live acceptance")
    evidence = manifest["evidence"]
    required = {
        "copilot_send_count": 0,
        "integrated_ex03_run_count": 0,
        "r12_pad_save_recopy_count": 0,
        "teaching_test_independence": "PASS_R12_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_INSTRUCTION_AND_NEW_SOURCE",
        "formal_text_code_block_required_count": 1,
    }
    for key, value in required.items():
        if evidence.get(key) != value:
            raise ValueError(f"Unexpected manifest evidence {key}: {evidence.get(key)!r}")
    for record in manifest["source_files"] + manifest["support_files"]:
        path = VERSION / record["path"]
        if sha256(path) != record["sha256"]:
            raise ValueError(f"Manifest member changed: {record['path']}")

    instruction = PATHS["instruction"].read_bytes()
    request = PATHS["request"].read_bytes()
    body = instruction + b"\n" + request + b"\n"
    body_text = body.decode("utf-8")
    leaks = [value for value in GRADER_ONLY_VALUES if value in body_text]
    if leaks:
        raise ValueError(f"Grader-only values leaked into submission body: {leaks}")
    return {"head": head, "manifest": manifest, "body": body}


def tracked_snapshot() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for name in git("ls-files").splitlines():
        path = ROOT / name
        if path.is_file():
            records.append({"path": name.replace("\\", "/"), "sha256": sha256(path)})
    records.append({"path": rel(Path(__file__)), "sha256": sha256(Path(__file__))})
    return sorted(records, key=lambda item: item["path"].lower())


def prepare(ui_query: str, ui_result: str) -> None:
    state = verify_fixed_state()
    CYCLE.mkdir(parents=True, exist_ok=False)
    body_path = CYCLE / "submitted-body.txt"
    write_bytes(body_path, state["body"])

    plan = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "base_commit": state["head"],
        "candidate": {
            "version": state["manifest"]["version"],
            **{name + "_path": rel(PATHS[name]) for name in ("instruction", "bundle", "manifest")},
            **{name + "_sha256": sha256(PATHS[name]) for name in ("instruction", "bundle", "manifest")},
            "inherits_live_acceptance": False,
            "teaching_test_independence": state["manifest"]["evidence"]["teaching_test_independence"],
        },
        "submission": {
            "destination": "normal Microsoft 365 Copilot chat",
            "body_path": rel(body_path),
            "body_sha256": sha256(body_path),
            "body_contract": "unchanged full r12 instruction followed by unchanged fixed EX03 request",
            "attachment_path": rel(PATHS["bundle"]),
            "attachment_sha256": sha256(PATHS["bundle"]),
            "required_text_code_blocks": 1,
            "generated_robin_must_be_unmodified": True,
        },
        "limits": {
            "total_copilot_sends": 1,
            "total_pad_runs": 2,
            "run2_requires_run1_normal_exit_all_comparisons_pass_and_artifact_preserved": True,
            "stop_on_refusal_mismatch_safety_issue_or_unknown": True,
            "no_resend_manual_repair_extra_run_successor_or_github_write": True,
        },
        "fixed_inputs": {
            name: {"path": rel(PATHS[name]), "sha256": sha256(PATHS[name])}
            for name in ("request", "spec", "expected", "input_a", "input_b", "template", "work")
        },
        "output": {"path": rel(PATHS["output"]), "exists_before_send": False},
        "status": "READY_ONE_SEND_AFTER_SEND_HISTORY_CONFIRMED_EMPTY",
    }
    preflight = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "head_and_worktree_match_checkpoint": True,
            "candidate_and_fixed_sha_match": True,
            "manifest_member_sha_match": True,
            "teaching_test_independence_pass": True,
            "candidate_reports_zero_send_save_recopy_and_integrated_runs": True,
            "work_matches_frozen_template": True,
            "output_absent": True,
            "local_r12_cycle_absent_before_preparation": True,
            "copilot_history_query": ui_query,
            "copilot_history_result": ui_result,
            "send_history_conclusion": "UNSENT_CONFIRMED",
        },
        "external_actions_before_checkpoint": {
            "copilot_send": 0,
            "pad_save_recopy": 0,
            "pad_run": 0,
            "github_write": 0,
        },
    }
    protected = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "base_commit": state["head"],
        "files": tracked_snapshot(),
    }
    write_json(CYCLE / "plan.json", plan)
    write_json(CYCLE / "preflight.json", preflight)
    write_json(CYCLE / "protected-files-before.json", protected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ui-query", required=True)
    parser.add_argument("--ui-result", choices=["NO_RESULTS"], required=True)
    args = parser.parse_args()
    prepare(args.ui_query, args.ui_result)
