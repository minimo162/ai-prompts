#!/usr/bin/env python3
"""Prepare fail-closed PAD source-capture inputs for the EX03 r7 successor.

This does not run EX03 or modify a sealed candidate.  It extracts the r6
integrated example and its one novel PowerShell action, then proves their
relationship to the actually sent bundle, measured probe action, and embedded
script before a dedicated PAD paste/save/re-copy observation.
"""

from __future__ import annotations

import hashlib
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R6 = ROOT / "copilot/versions/20260916-excel-r6"
R6_BUILDER = ROOT / "tools/Build-Issue38Ex03CandidateR6.py"
PROBE = ROOT / "catalog/acceptance/issue38/probes/percent-text-write"
R5_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r5-G1"
OUTPUT = ROOT / "catalog/acceptance/issue38/probes/ex03-r7-robin-source"

EXPECTED = {
    "bundle": "9c566e7f85a431f1869302c6a40985e2f81237f17ac4fbbdc9a73e62a646b580",
    "support": "d0a5df36516fcf4e27f6d789300ee5a03789aba8176571b1ab86fe84f15fba1a",
    "captured_flow": "0b86dd150dac532e2c73f5a407a7c396b4153bbc3052e03a65a8c84c6dab6f46",
    "captured_action": "aae8f3d12b458e7bba0bf7759ad0f2c15720bbc803f032e5c86e3621edc16538",
    "captured_script": "748c7e512353cc487d572fe81fc6487ece910f8538a2bd55b1f8d535b0c799ee",
    "r5_generated": "4ab085c52ba6f40fc52a55d910459eb917cb7ea3f4174737879d8bb4e5361f7e",
    "r5_recopy": "66a77eb39a8695bd8acd02538775705b06b520eadd968fd86fd1096cf45c2393",
}

ACTION_PREFIX = "Scripting.RunPowershellScript.RunScript Script: $'''"
ACTION_SUFFIX = "''' ScriptOutput=> PowershellOutput"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalized_robin(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def decode_robin_string(value: str) -> str:
    """Decode the escapes observed in PAD-recopied $'''...''' actions."""
    decoded: list[str] = []
    index = 0
    while index < len(value):
        if (
            value[index] == "\\"
            and index + 1 < len(value)
            and value[index + 1] in {"\\", "'", '"'}
        ):
            decoded.append(value[index + 1])
            index += 2
        else:
            decoded.append(value[index])
            index += 1
    return "".join(decoded)


def action_payload(action: str) -> str:
    candidate = action.rstrip("\r\n")
    if not candidate.startswith(ACTION_PREFIX) or not candidate.endswith(ACTION_SUFFIX):
        raise ValueError("PowerShell action wrapper does not match the measured PAD wrapper")
    return candidate[len(ACTION_PREFIX) : -len(ACTION_SUFFIX)]


def write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite capture input: {path}")
    path.write_bytes(data)


def main() -> None:
    paths = {
        "bundle": R6 / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "support": R6 / "support/EX03-TextWrite-FormatSandwich.ps1.txt",
        "captured_flow": PROBE / "captured-final.robin",
        "captured_action": PROBE / "captured-powershell-format-action-v2.robin",
        "captured_script": PROBE / "active-excel-format-sandwich.ps1.txt",
        "r5_generated": R5_CYCLE / "generated.robin",
        "r5_recopy": R5_CYCLE / "pad-recopy-before-run1.robin",
    }
    actual = {name: sha256(path) for name, path in paths.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected source hash mismatch: {actual}")
    if OUTPUT.exists():
        raise FileExistsError(f"Capture directory already exists: {OUTPUT}")

    module = runpy.run_path(str(R6_BUILDER))
    flow = module["full_robin_example"]()
    action = module["robin_script_action"](module["TEXT_WRITE_SCRIPT"]) + "\n"
    support = text(paths["support"])
    bundle = text(paths["bundle"])
    captured_action = text(paths["captured_action"])
    captured_script = text(paths["captured_script"])

    decoded_r6 = decode_robin_string(action_payload(action))
    decoded_probe = decode_robin_string(action_payload(captured_action))
    checks = {
        "r6_flow_in_actual_sent_bundle_exact": flow.rstrip("\n") in bundle,
        "r6_action_in_flow_exact_with_else_indent": all(
            line in flow.splitlines() for line in [
                "    " + action.splitlines()[0],
                "    " + action.splitlines()[-1],
            ]
        ),
        "r6_action_decodes_to_support_exact_ignoring_final_lf": (
            normalized_robin(decoded_r6) == normalized_robin(support)
        ),
        "measured_probe_action_decodes_to_recorded_script_exact_ignoring_final_lf": (
            normalized_robin(decoded_probe) == normalized_robin(captured_script)
        ),
        "r5_generated_equals_pad_recopy_lf_normalized": (
            normalized_robin(text(paths["r5_generated"]))
            == normalized_robin(text(paths["r5_recopy"]))
        ),
        "actual_bundle_has_no_backslash_markdown_escape_before_arrow": "=\\>" not in bundle,
        "actual_bundle_has_no_backslash_markdown_escape_before_underscore": "\\_" not in bundle,
        "actual_bundle_has_no_backslash_markdown_escape_before_left_bracket": "\\[" not in bundle,
        "actual_bundle_contains_raw_arrow": "=>" in bundle,
        "actual_bundle_contains_raw_value_type_variable": "_ValueTypeMatch" in bundle,
        "actual_bundle_contains_raw_datatable_index": "Data1[0][0]" in bundle,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"Source audit failed: {failed}")

    OUTPUT.mkdir(parents=True)
    full_path = OUTPUT / "candidate-full.robin"
    action_path = OUTPUT / "candidate-action.robin"
    write_new(full_path, flow.encode("utf-8"))
    write_new(action_path, action.encode("utf-8"))

    preflight = {
        "schema_version": 1,
        "capture_id": "EX03-R7-ROBIN-SOURCE",
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Dedicated PAD paste/save/re-copy only; no Copilot send and no EX03 execution",
        "source_version": "20260916-excel-r6",
        "source_bundle": {
            "path": rel(paths["bundle"]),
            "sha256": actual["bundle"],
        },
        "candidate_full": {
            "path": rel(full_path),
            "sha256": sha256(full_path),
            "utf8_bytes": len(full_path.read_bytes()),
            "lines": len(flow.splitlines()),
        },
        "candidate_action": {
            "path": rel(action_path),
            "sha256": sha256(action_path),
            "utf8_bytes": len(action_path.read_bytes()),
            "lines": len(action.splitlines()),
        },
        "mechanical_checks": checks,
        "diagnosis_before_pad": {
            "copilot_reported_escape_sequences_present_in_actual_bundle": False,
            "r6_embedded_script_mismatch": False,
            "missing_evidence": "The exact r6 integrated Robin has not yet been accepted and re-copied by PAD Designer.",
        },
        "live_limits": {
            "dedicated_flow_name": "RobinIssue38EX03R7Source20260916A",
            "paste_save_recopy_only": True,
            "execute": False,
            "copilot_send": False,
            "integrated_ex03_run": False,
            "github_write": False,
        },
    }
    write_new(
        OUTPUT / "preflight.json",
        (json.dumps(preflight, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps(preflight, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
