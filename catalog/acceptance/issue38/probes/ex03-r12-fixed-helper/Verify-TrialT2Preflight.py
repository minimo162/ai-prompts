#!/usr/bin/env python3
"""Fail-closed preflight for the saved-flow T2 fixed-helper auxiliary run."""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
BASELINE = "6a48efc009efe10cedbeab015eb0d3cfce751b94"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUNTIME = T1 / "runtime"
HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = T1 / "invocation.json"
LAUNCHER = T1 / "launcher.ps1"
T1_CANDIDATE = T1 / "candidate.robin"
T1_RECOPY = T1 / "pad-recopy-mismatch.robin"
T2_RECOPY = T2 / "pad-recopy-before-run.robin"
IDENTITY = T2 / "pad-recopy.json"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
TEMPLATE = ROOT / "catalog/acceptance/issue38/fixtures/EX03/ひな形.xlsx"
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03CandidateR12.py"

EXPECTED = {
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "candidate": "0a84679b0b9875780aa70c975602a7404af0dd82fcf9b13978fe9c1e036f5b94",
    "recopy": "da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("issue38_t2_builder", BUILDER_PATH)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def exact_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> int:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"], cwd=ROOT
    ).returncode != 0:
        raise ValueError("HEAD does not retain the authorized T2 baseline")
    for path in (T2 / "plan.json", T2 / "preflight.json", T2 / "work-before.xlsx"):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite T2 preflight: {path}")

    fixed = {
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "candidate": T1_CANDIDATE,
        "recopy": T1_RECOPY,
        "template": TEMPLATE,
        "input_a": ROOT / "catalog/acceptance/issue38/fixtures/EX03/入力い.xlsx",
        "input_b": ROOT / "catalog/acceptance/issue38/fixtures/EX03/入力ろ.xlsx",
    }
    for name, path in fixed.items():
        actual = sha256(path)
        if actual != EXPECTED[name]:
            raise ValueError(f"Fixed SHA mismatch for {name}: {actual}")
    if sha256(T2_RECOPY) != EXPECTED["recopy"]:
        raise ValueError("Current saved-flow capture is not the T1 execution baseline")
    if T1_RECOPY.read_bytes() != T2_RECOPY.read_bytes():
        raise ValueError("Current saved-flow capture is not byte exact to T1 re-copy")
    if sha256(WORK) != EXPECTED["template"] or sha256(TEMPLATE) != EXPECTED["template"]:
        raise ValueError("Pre-run work/template identity failed")
    if OUTPUT.exists():
        raise ValueError("Output exists before the authorized T2 Run")
    handoff = [RUNTIME / f"source-{index}.json" for index in range(1, 8)]
    handoff.append(RUNTIME / "mode.json")
    if any(path.exists() for path in handoff):
        raise ValueError("JSON handoff exists before the authorized T2 Run")
    tasklist = subprocess.check_output(
        ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE"],
        text=True,
        encoding="mbcs",
        errors="replace",
    )
    if "EXCEL.EXE" in tasklist.upper():
        raise ValueError("Excel is already running before the authorized T2 Run")

    identity = load(IDENTITY)
    if identity["result"] != "PASS_CURRENT_SAVED_FLOW_EXACT_T1_RECOPY_BASELINE":
        raise ValueError("Saved-flow identity record did not pass")
    if identity["comparison"]["byte_exact_to_t1_baseline"] is not True:
        raise ValueError("Saved-flow identity record is not exact")

    candidate = exact_text(T1_CANDIDATE)
    recopy = exact_text(T2_RECOPY)
    candidate_lines = candidate.replace("\r\n", "\n").rstrip("\r\n").split("\n")
    recopy_lines = recopy.replace("\r\n", "\n").rstrip("\r\n").split("\n")
    hunks = []
    for tag, a1, a2, b1, b2 in difflib.SequenceMatcher(
        None, candidate_lines, recopy_lines
    ).get_opcodes():
        if tag != "equal":
            hunks.append(
                {
                    "operation": tag,
                    "candidate_lines": [a1 + 1, a2],
                    "recopy_lines": [b1 + 1, b2],
                    "candidate": candidate_lines[a1:a2],
                    "recopy": recopy_lines[b1:b2],
                }
            )
    expected_candidate = (
        "$expectedSuccess = \\'{\"status\":\"OK\",\"mode\":\"NORMAL\"," 
        "\"text_writes\":7,\"formats_restored\":true}\\'"
    )
    expected_recopy = expected_candidate.replace('"', '\\"')
    expected_hunks = [
        {
            "operation": "replace",
            "candidate_lines": [48, 48],
            "recopy_lines": [48, 48],
            "candidate": [expected_candidate],
            "recopy": [expected_recopy],
        }
    ]
    if hunks != expected_hunks:
        raise ValueError(f"Unknown saved-flow content difference: {hunks!r}")

    launcher = exact_text(LAUNCHER).rstrip("\r\n")
    candidate_launcher = builder.embedded_script(candidate)
    recopy_launcher = builder.embedded_script(recopy)
    if candidate_launcher != launcher or recopy_launcher != launcher:
        raise ValueError("Decoded launcher differs from the fixed launcher")

    analysis = load(T1 / "pad-recopy-diff-analysis.json")
    if not (
        analysis["candidate_sha256"] == EXPECTED["candidate"]
        and analysis["recopy_sha256"] == EXPECTED["recopy"]
        and analysis["content_diff_hunk_count"] == 1
        and analysis["classification"]["decoded_embedded_launcher_exact"] is True
        and analysis["content_diff_hunks_ignoring_line_endings_and_final_newline"]
        == expected_hunks
    ):
        raise ValueError("Existing T1 difference analysis no longer proves the fixed boundary")

    invocation = load(INVOCATION)
    if Path(invocation["target_workbook"]) != WORK:
        raise ValueError("Invocation target path changed")
    if Path(invocation["json_root"]) != RUNTIME:
        raise ValueError("Invocation JSON root changed")
    if len(invocation["text_writes"]) != 7:
        raise ValueError("Invocation mapping count changed")
    if str(HELPER) not in launcher or str(INVOCATION) not in launcher:
        raise ValueError("Launcher fixed path changed")
    if EXPECTED["helper"] not in launcher or EXPECTED["invocation"] not in launcher:
        raise ValueError("Launcher fixed SHA changed")

    protected_paths = [
        relative(HELPER),
        relative(INVOCATION),
        relative(LAUNCHER),
        relative(T1_CANDIDATE),
        relative(T1_RECOPY),
        relative(T1 / "pad-recopy-mismatch.json"),
        relative(T1 / "pad-recopy-diff-analysis.json"),
        relative(T1 / "result.json"),
        relative(T1 / "RESULT.md"),
        "catalog/acceptance/issue38/requests/EX03.txt",
        "catalog/acceptance/issue38/spec.json",
        "catalog/acceptance/issue38/expected.json",
        "catalog/acceptance/issue38/cycles/EX03-r12-G1/generated.robin",
        "catalog/acceptance/issue38/cycles/EX03-r12-G1/generation-safety-audit.json",
        "copilot/versions/20260917-excel-r12/agent-instructions.txt",
        "copilot/versions/20260917-excel-r12/knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "copilot/versions/20260917-excel-r12/manifest.json",
    ]
    protected = []
    for item in protected_paths:
        baseline_blob = subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE}:{item}"], cwd=ROOT, text=True
        ).strip()
        current_blob = subprocess.check_output(
            ["git", "hash-object", f"--path={item}", str(ROOT / item)],
            cwd=ROOT,
            text=True,
        ).strip()
        if current_blob != baseline_blob:
            raise ValueError(f"Protected tracked file changed: {item}")
        protected.append({"path": item, "git_blob": baseline_blob})

    shutil.copy2(WORK, T2 / "work-before.xlsx")
    if sha256(T2 / "work-before.xlsx") != EXPECTED["template"]:
        raise ValueError("Preserved pre-run work copy mismatch")

    plan = {
        "schema_version": 1,
        "trial_id": "EX03-R12-FIXED-HELPER-P1-T2",
        "baseline_commit": BASELINE,
        "classification": "FIXED_HELPER_AUXILIARY_ONLY_NOT_FORMAL_EX03_R12_ACCEPTANCE",
        "execution_baseline": {
            "source_trial": "EX03-R12-FIXED-HELPER-P1-T1",
            "pad_recopy_sha256": EXPECTED["recopy"],
            "unknown_content_differences": 0,
            "known_content_difference_hunks": 1,
            "known_differences": [
                "Robin escaping of eight JSON double quotes in launcher expectedSuccess",
                "line-ending serialization and final newline",
            ],
            "decoded_launcher_exact": True,
        },
        "authorization": {
            "normal_pad_runs": 1,
            "additional_runs": 0,
            "repaste": 0,
            "resave": 0,
            "copilot_sends": 0,
            "formal_ex03_r12_runs": 0,
            "github_writes": 0,
        },
        "stop_conditions": [
            "saved flow differs from the fixed T1 re-copy baseline",
            "unknown difference or code change",
            "PAD refusal, error, mismatch, or unknown result",
        ],
    }
    write_json(T2 / "plan.json", plan)

    preflight = {
        "schema_version": 1,
        "trial_id": "EX03-R12-FIXED-HELPER-P1-T2",
        "result": "PASS_READY_FOR_ONE_SAVED_FLOW_NORMAL_PAD_RUN",
        "baseline_commit": BASELINE,
        "flow": identity["flow"],
        "fixed_sha256": {
            "helper": sha256(HELPER),
            "invocation": sha256(INVOCATION),
            "launcher": sha256(LAUNCHER),
            "execution_recopy": sha256(T2_RECOPY),
            "template": sha256(TEMPLATE),
            "work": sha256(WORK),
        },
        "fixed_paths": {
            "helper": str(HELPER),
            "invocation": str(INVOCATION),
            "launcher": str(LAUNCHER),
            "target_workbook": str(WORK),
            "json_root": str(RUNTIME),
            "output": str(OUTPUT),
        },
        "identity": {
            "current_saved_flow_byte_exact_to_t1_recopy": True,
            "known_content_difference_hunks": hunks,
            "unknown_content_difference_count": 0,
            "decoded_candidate_launcher_exact": True,
            "decoded_saved_flow_launcher_exact": True,
            "other_robin_processing_exact_after_known_difference": True,
        },
        "pre_run": {
            "work_matches_template": True,
            "work_before_path": relative(T2 / "work-before.xlsx"),
            "output_absent": True,
            "json_handoff_absent": True,
            "excel_not_running": True,
        },
        "protected_tracked_files": protected,
    }
    write_json(T2 / "preflight.json", preflight)
    print(json.dumps(preflight, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
