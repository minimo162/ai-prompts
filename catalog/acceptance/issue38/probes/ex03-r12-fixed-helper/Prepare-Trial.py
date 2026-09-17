#!/usr/bin/env python3
"""Prepare one path-isolated live PAD trial for the fixed-helper prototype."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
BASE = ROOT / "catalog/acceptance/issue38"
VERSION = ROOT / "copilot/versions/20260917-excel-r12"
BASELINE = "1f1e752eb82413b07437135a70eb7349dca313f0"
TRIAL_ID = "EX03-R12-FIXED-HELPER-P1-T1"
FLOW_NAME = "Issue38Ex03R12FixedHelperP1T1"
TRIAL = PROBE / "trials" / TRIAL_ID
RUNTIME = TRIAL / "runtime"

HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
BASE_INVOCATION = PROBE / "invocation.json"
BASE_LAUNCHER = PROBE / "launcher.ps1"
PROTOTYPE_MANIFEST = PROBE / "manifest.json"
PROTOTYPE_VERIFICATION = PROBE / "verification.json"
TEACHING = VERSION / "support/EX03-R12-Prepared-Normal.robin"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
INPUT_A = BASE / "fixtures/EX03/入力い.xlsx"
INPUT_B = BASE / "fixtures/EX03/入力ろ.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
WORK = RUNTIME / "work.xlsx"
INVOCATION = TRIAL / "invocation.json"
LAUNCHER = TRIAL / "launcher.ps1"
CANDIDATE = TRIAL / "candidate.robin"

ANALYZER_PATH = ROOT / "tools/Analyze-Issue38Ex03R12Generation.py"
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03CandidateR12.py"
PARSER_PATH = ROOT / "tools/Analyze-Issue38Ex03R10Generation.py"

EXPECTED_SHA256 = {
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "base_invocation": "9ff979598a0383099aec88ca3aace330f29ed519cc66d9cf6ca63e31d962227a",
    "base_launcher": "b509339998887977fc272613e9c6a479e444dfbed1e957d63588a89ac53bfbaf",
    "prototype_manifest": "911bb1e864fe1e183a839f094052ee895c0caad7968a8f038fd950f5ad0ffe01",
    "prototype_verification": "145027406d0a45ce7f2739d7ec7d0b6041a570f6d50a472cf9e240df7fb0d23d",
    "teaching": "7bde8bb20bb7f347c97722d77a4141bf8348bb40d97aaca435e01998e8b9d3a3",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}
SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


analyzer = load("issue38_r12_fixed_trial_analyzer", ANALYZER_PATH)
builder = load("issue38_r12_fixed_trial_builder", BUILDER_PATH)
parser = load("issue38_r12_fixed_trial_parser", PARSER_PATH)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_text(path: Path, value: str, final_newline: bool = True) -> None:
    path.write_text(
        value.rstrip("\r\n") + ("\n" if final_newline else ""),
        encoding="utf-8",
        newline="\n",
    )


def exact_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def replace_once(value: str, old: str, new: str, label: str) -> str:
    if value.count(old) != 1:
        raise ValueError(f"Expected one {label}, found {value.count(old)}")
    return value.replace(old, new, 1)


def protected_blob_map() -> dict[str, str]:
    paths = [
        "catalog/acceptance/issue38/requests/EX03.txt",
        "catalog/acceptance/issue38/spec.json",
        "catalog/acceptance/issue38/expected.json",
        "catalog/acceptance/issue38/cycles/EX03-r12-G1/generated.robin",
        "catalog/acceptance/issue38/cycles/EX03-r12-G1/generation-safety-audit.json",
        "copilot/versions/20260917-excel-r12/agent-instructions.txt",
        "copilot/versions/20260917-excel-r12/knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "copilot/versions/20260917-excel-r12/manifest.json",
    ]
    result: dict[str, str] = {}
    for item in paths:
        baseline_blob = subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE}:{item}"], cwd=ROOT, text=True
        ).strip()
        current_blob = subprocess.check_output(
            ["git", "hash-object", f"--path={item}", str(ROOT / item)],
            cwd=ROOT,
            text=True,
        ).strip()
        if current_blob != baseline_blob:
            raise ValueError(f"Protected evidence changed: {item}")
        result[item] = baseline_blob
    return result


def main() -> int:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"], cwd=ROOT
    ).returncode != 0:
        raise ValueError(f"HEAD does not retain baseline {BASELINE}")
    if TRIAL.exists():
        raise FileExistsError(f"Refusing to overwrite trial: {TRIAL}")

    fixed_paths = {
        "helper": HELPER,
        "base_invocation": BASE_INVOCATION,
        "base_launcher": BASE_LAUNCHER,
        "prototype_manifest": PROTOTYPE_MANIFEST,
        "prototype_verification": PROTOTYPE_VERIFICATION,
        "teaching": TEACHING,
        "template": TEMPLATE,
        "input_a": INPUT_A,
        "input_b": INPUT_B,
        "request": BASE / "requests/EX03.txt",
        "spec": BASE / "spec.json",
        "expected": BASE / "expected.json",
    }
    for name, path in fixed_paths.items():
        actual = sha256(path)
        if actual != EXPECTED_SHA256[name]:
            raise ValueError(f"Fixed SHA mismatch for {name}: {actual}")

    verification = json.loads(PROTOTYPE_VERIFICATION.read_text(encoding="utf-8"))
    normal_stub = verification["stub_matrix"]["normal"]
    if normal_stub != {
        "exit_code": 0,
        "stdout": SUCCESS,
        "helper_marker_created": True,
        "result": "PASS",
    }:
        raise ValueError("Existing normal stub evidence no longer proves one success JSON")

    TRIAL.mkdir(parents=True)
    RUNTIME.mkdir()
    shutil.copyfile(TEMPLATE, WORK)

    base_invocation = json.loads(BASE_INVOCATION.read_text(encoding="utf-8"))
    invocation = dict(base_invocation)
    invocation["prototype_id"] = TRIAL_ID
    invocation["target_workbook"] = str(WORK)
    invocation["json_root"] = str(RUNTIME)
    write_json(INVOCATION, invocation)
    invocation_sha = sha256(INVOCATION)

    launcher = exact_text(BASE_LAUNCHER).replace("\r\n", "\n")
    launcher = replace_once(
        launcher,
        str(BASE_INVOCATION),
        str(INVOCATION),
        "trial invocation path",
    )
    launcher = replace_once(
        launcher,
        EXPECTED_SHA256["base_invocation"],
        invocation_sha,
        "trial invocation SHA",
    )
    write_text(LAUNCHER, launcher)
    launcher_text = exact_text(LAUNCHER).replace("\r\n", "\n")

    teaching = analyzer.normalized(TEACHING.read_text(encoding="utf-8"))
    adapted, replacement_counts = analyzer.expected_adaptation(teaching)
    old_runtime = str(BASE / "runs/EX03-attempt1").replace("\\", "\\\\")
    new_runtime = str(RUNTIME).replace("\\", "\\\\")
    runtime_replacements = adapted.count(old_runtime)
    if runtime_replacements != 14:
        raise ValueError(f"Unexpected fixed runtime path count: {runtime_replacements}")
    path_bound = adapted.replace(old_runtime, new_runtime)

    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    start = path_bound.index(prefix)
    finish = path_bound.index(suffix, start) + len(suffix)
    candidate = (
        path_bound[:start]
        + builder.script_action(launcher_text)
        + path_bound[finish:]
    )
    write_text(CANDIDATE, candidate, final_newline=False)

    embedded = builder.embedded_script(CANDIDATE.read_text(encoding="utf-8"))
    if embedded != launcher_text.rstrip("\r\n"):
        raise ValueError("PAD-embedded launcher differs from the trial launcher")
    parser_errors = parser.parse_powershell(embedded)
    if parser_errors:
        raise ValueError(f"Trial launcher has PowerShell AST errors: {parser_errors}")

    forbidden = [
        "Invoke-Expression",
        "ScriptBlock]::Create",
        "Add-Type",
        "Start-Process",
        "Remove-Item",
        "Invoke-WebRequest",
        "Invoke-RestMethod",
        "System.RunDOSCommand",
        "System.RunApplication",
        "File.Delete",
        "Folder.Delete",
        "WebAutomation.",
        "HTTP.",
    ]
    forbidden_counts = {token: candidate.count(token) for token in forbidden}
    if any(forbidden_counts.values()):
        raise ValueError(f"Forbidden runtime token: {forbidden_counts}")

    structure = {
        "run_script_count": candidate.count("Scripting.RunPowershellScript.RunScript"),
        "source_json_write_count": sum(
            candidate.count(f"source-{index}.json") for index in range(1, 8)
        ),
        "mode_json_write_count": candidate.count("mode.json"),
        "numeric_write_count": candidate.count(
            "Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource"
        ),
        "save_as_count": candidate.count("Excel.SaveExcel.SaveAs"),
        "json_comparison_count": candidate.count(
            "_ValueTypeMatch TO SourceCellJson = SavedCellJson"
        ),
        "success_gate_count": candidate.count(
            "IF PowershellOutput = $'''{\\\"status\\\":\\\"OK\\\",\\\"mode\\\":\\\"NORMAL\\\",\\\"text_writes\\\":7,\\\"formats_restored\\\":true}''' THEN"
        ),
        "trial_runtime_count_after_helper_replacement": candidate.count(new_runtime),
    }
    expected_structure = {
        "run_script_count": 1,
        "source_json_write_count": 7,
        "mode_json_write_count": 1,
        "numeric_write_count": 5,
        "save_as_count": 1,
        "json_comparison_count": 12,
        "success_gate_count": 1,
        "trial_runtime_count_after_helper_replacement": 12,
    }
    if structure != expected_structure:
        raise ValueError(f"Trial Robin structure changed: {structure}")
    if OUTPUT.exists():
        raise FileExistsError(f"Output collision before live trial: {OUTPUT}")
    if sha256(WORK) != EXPECTED_SHA256["template"]:
        raise ValueError("Dedicated work copy does not match the fixed template")

    helper_invocation = json.loads(INVOCATION.read_text(encoding="utf-8"))
    if helper_invocation["target_workbook"] != str(WORK):
        raise ValueError("Invocation target does not identify the dedicated work copy")
    if helper_invocation["json_root"] != str(RUNTIME):
        raise ValueError("Invocation JSON root does not identify the dedicated runtime")

    protected_blobs = protected_blob_map()
    plan = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "flow_name": FLOW_NAME,
        "kind": "ISSUE38_EX03_R12_FIXED_HELPER_ONE_NORMAL_LIVE_TRIAL",
        "baseline_commit": BASELINE,
        "scope": "Dedicated fixed EX03 helper path only; not formal r12 acceptance.",
        "authorization": {
            "normal_pad_runs": 1,
            "reruns": 0,
            "copilot_sends": 0,
        },
        "success_output": SUCCESS,
        "stop_conditions": [
            "PAD save or re-copy is not exact",
            "PowerShell output, terminal state, or any comparison is not clearly PASS",
            "safety issue or result unknown",
        ],
        "out_of_scope": [
            "Copilot send",
            "formal EX03-r12 acceptance run",
            "candidate version creation",
            "full regression",
            "GitHub write",
            "generalization beyond fixed EX03 cells and values",
        ],
    }
    write_json(TRIAL / "plan.json", plan)

    preflight = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "result": "PASS_READY_FOR_ONE_NORMAL_PAD_RUN_ONLY",
        "baseline_commit": BASELINE,
        "return_behavior": {
            "real_helper_output_command": "Write-Output -NoEnumerate",
            "launcher_capture": "(& $helperPath -InvocationPath $invocationPath | Out-String).Trim()",
            "launcher_final_stdout": "[Console]::Out.Write($helperOutput)",
            "existing_stub_evidence_reused_without_rerun": True,
            "stub_stdout": normal_stub["stdout"],
            "final_output_is_one_success_json": True,
        },
        "files": {
            "helper": {"path": relative(HELPER), "sha256": sha256(HELPER)},
            "invocation": {"path": relative(INVOCATION), "sha256": invocation_sha},
            "launcher": {"path": relative(LAUNCHER), "sha256": sha256(LAUNCHER)},
            "candidate": {"path": relative(CANDIDATE), "sha256": sha256(CANDIDATE)},
            "input_a": {"path": relative(INPUT_A), "sha256": sha256(INPUT_A)},
            "input_b": {"path": relative(INPUT_B), "sha256": sha256(INPUT_B)},
            "template": {"path": relative(TEMPLATE), "sha256": sha256(TEMPLATE)},
            "work": {"path": relative(WORK), "sha256": sha256(WORK)},
            "output": {"path": relative(OUTPUT), "exists": False},
        },
        "fixed_sha256": EXPECTED_SHA256,
        "protected_baseline_blobs": protected_blobs,
        "adaptation": {
            "source": relative(TEACHING),
            "replacement_counts": replacement_counts,
            "fixed_runtime_path_replacements_before_helper_swap": runtime_replacements,
            "embedded_launcher_exact": True,
            "ast_error_count": 0,
            "forbidden_counts": forbidden_counts,
            "structure": structure,
        },
        "paths": {
            "helper": str(HELPER),
            "invocation": str(INVOCATION),
            "launcher": str(LAUNCHER),
            "target_workbook": str(WORK),
            "json_root": str(RUNTIME),
            "output": str(OUTPUT),
        },
        "pre_run": {
            "work_matches_template": True,
            "output_absent": True,
            "json_files_absent": all(
                not (RUNTIME / f"source-{index}.json").exists()
                for index in range(1, 8)
            )
            and not (RUNTIME / "mode.json").exists(),
            "real_helper_not_executed_by_preflight": True,
            "pad_save_count": 0,
            "pad_recopy_count": 0,
            "pad_run_count": 0,
        },
    }
    write_json(TRIAL / "preflight.json", preflight)
    print(json.dumps(preflight, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
