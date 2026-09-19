#!/usr/bin/env python3
"""Read-only verification of the frozen EX03 r10 pre-send checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r10-G1"
CHECKPOINT_COMMIT = "d510252b481a9ec4aa93b8db23961ab6da3e7771"

EXPECTED_CYCLE_HASHES = {
    "plan.json": "1a27ff5947e2509d5bb5fac41d02d99b9a202bf412950a459cfc69fe19065ab9",
    "preflight.json": "c2ec917fa2b0ab82cb88c5444bf882c4e81d5213b066223bb1ffbc96bb54edb1",
    "protected-files-before.json": "88f2d144af609c9ef79630daae524833ebd75b15878a8d1fc0fef6f43796d8d3",
    "submitted-body.txt": "751252c0ca263be62c01dce3dc83b10d733579bc395bc4bea01903d543be6247",
}

FORBIDDEN_PRE_SEND_FILES = [
    "browser-staging-stop.json",
    "browser-staging-body-mismatch.json",
    "m365-ready-to-send.json",
    "live-send.json",
    "generation-result.json",
    "generation-safety-audit.json",
    "copilot-response.clipboard.utf8.b64",
    "generated-robin.clipboard.utf8.b64",
    "generated.robin",
    "pad-flow-created.json",
    "pad-import-and-recopy.json",
    "acceptance-status.json",
    "protected-files-after.json",
    "review.md",
    "verification.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_bytes())


def verify(cycle: Path = CYCLE, verify_commit: bool = True) -> dict[str, object]:
    cycle = Path(cycle)
    if verify_commit:
        commit = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", CHECKPOINT_COMMIT + "^{commit}"],
            capture_output=True,
        )
        if commit.returncode != 0:
            raise ValueError("Frozen r10 checkpoint commit is missing")
        ancestor = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", CHECKPOINT_COMMIT, "HEAD"],
            capture_output=True,
        )
        if ancestor.returncode != 0:
            raise ValueError("Frozen r10 checkpoint commit is not an ancestor of HEAD")

    actual_cycle_hashes = {}
    for name, expected in EXPECTED_CYCLE_HASHES.items():
        path = cycle / name
        if not path.is_file():
            raise ValueError(f"Required checkpoint file is missing: {name}")
        actual = sha(path)
        actual_cycle_hashes[name] = actual
        if actual != expected:
            raise ValueError(f"Checkpoint hash mismatch for {name}: {actual}")

    unexpected = [name for name in FORBIDDEN_PRE_SEND_FILES if (cycle / name).exists()]
    if unexpected:
        raise ValueError(f"Checkpoint is no longer in sealed pre-send state: {unexpected}")

    plan = read_json(cycle / "plan.json")
    preflight = read_json(cycle / "preflight.json")
    protected = read_json(cycle / "protected-files-before.json")
    if plan["cycle_id"] != "EX03-R10-G1" or preflight["cycle_id"] != "EX03-R10-G1":
        raise ValueError("Unexpected r10 cycle identity")
    if plan["candidate"]["version"] != "20260917-excel-r10":
        raise ValueError("Unexpected r10 candidate version")
    if plan["candidate"]["inherits_live_acceptance"]:
        raise ValueError("The r10 checkpoint now inherits live acceptance")
    if plan["status"] != "READY_FOR_NEW_ACTION_TIME_CONFIRMATION_NOT_STAGED_NOT_SENT":
        raise ValueError("The r10 checkpoint status changed")
    if plan["authorization"] != {
        "r9_authorized_send_consumed": True,
        "r9_normal_m365_send_count": 1,
        "r9_resend_count": 0,
        "r9_stop_before_pad_preserved": True,
        "r10_normal_m365_send_count": 0,
        "r10_browser_staged": False,
        "r10_action_time_confirmation_required_before_staging_or_send": True,
    }:
        raise ValueError("The r10 authorization record changed")
    if any(plan["external_actions"].values()):
        raise ValueError("The local r10 checkpoint records an external action")
    if preflight["decision"] != {
        "local_checkpoint": "PASS",
        "browser_staging": "NOT_STARTED_REQUIRES_NEW_ACTION_TIME_CONFIRMATION",
        "send": "NOT_SENT_REQUIRES_NEW_ACTION_TIME_CONFIRMATION",
        "copilot_generation": "NOT_STARTED",
        "pad_run1": "NOT_STARTED",
        "pad_run2": "NOT_STARTED",
    }:
        raise ValueError("The r10 preflight decision changed")
    if not all(preflight["checks"].values()):
        raise ValueError("A frozen r10 preflight check is not passing")

    instruction_path = ROOT / plan["candidate"]["instruction_path"]
    bundle_path = ROOT / plan["candidate"]["bundle_path"]
    manifest_path = ROOT / plan["candidate"]["manifest_path"]
    request_path = ROOT / plan["fixed_inputs"]["request"]["path"]
    work_path = ROOT / plan["fixed_inputs"]["work"]["path"]
    output_path = ROOT / plan["fixed_inputs"]["output"]["path"]
    body_path = cycle / "submitted-body.txt"
    body_expected = instruction_path.read_bytes() + b"\n" + request_path.read_bytes() + b"\n"
    if body_path.read_bytes() != body_expected:
        raise ValueError("Submitted body is not exact r10 instructions plus fixed request")
    for label, path in [
        ("instruction", instruction_path),
        ("bundle", bundle_path),
        ("manifest", manifest_path),
    ]:
        expected = preflight["hashes"][label]
        if sha(path) != expected:
            raise ValueError(f"Current {label} hash mismatch: {sha(path)}")
    if sha(body_path) != plan["submission"]["body_sha256"]:
        raise ValueError("Current submitted body hash differs from plan")
    if sha(bundle_path) != plan["submission"]["attachment_sha256"]:
        raise ValueError("Current attachment hash differs from plan")
    if sha(work_path) != plan["fixed_inputs"]["work"]["sha256"]:
        raise ValueError("Current EX03 work copy no longer matches the checkpoint")
    if output_path.exists():
        raise ValueError("EX03 output exists before the authorized r10 run")

    files = protected["files"]
    expected_count = preflight["counts"]["protected_files"]
    if len(files) != expected_count or len(files) != 264:
        raise ValueError("Protected-file count changed")
    mismatches = []
    for record in files:
        path = ROOT / record["path"]
        if not path.is_file():
            mismatches.append({"path": record["path"], "status": "MISSING"})
            continue
        actual = sha(path)
        if actual != record["sha256"]:
            mismatches.append(
                {
                    "path": record["path"],
                    "status": "HASH_MISMATCH",
                    "expected": record["sha256"],
                    "actual": actual,
                }
            )
    if mismatches:
        raise ValueError(f"Protected checkpoint drift: {mismatches[:3]}")

    return {
        "schema_version": 1,
        "cycle_id": "EX03-R10-G1",
        "status": "READY_LOCAL_CHECKPOINT_AWAITING_EXPLICIT_AUTHORIZATION",
        "checkpoint_commit": CHECKPOINT_COMMIT,
        "head": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "cycle_hashes": actual_cycle_hashes,
        "submitted_body_sha256": sha(body_path),
        "bundle_sha256": sha(bundle_path),
        "protected_file_count": len(files),
        "protected_mismatch_count": 0,
        "work_matches_checkpoint": True,
        "output_absent": True,
        "recorded_external_actions": plan["external_actions"],
        "live_browser_or_pad_state_inspected": False,
        "send_authorized_by_this_verification": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
