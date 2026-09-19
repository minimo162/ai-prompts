#!/usr/bin/env python3
"""Prepare a path-isolated live trial for the already-fixed R2/R3 probe."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
BASELINE = "1f929d6c4e1ba5bc4d963374e3e322c7a52649c1"
TRIAL_ID = "EX03-R2R3-POSTFIX-20260917-T1"
TRIAL = PROBE / "trials" / TRIAL_ID
OLD_RUNTIME = PROBE / "runtime"
SOURCE = PROBE / "source.xlsx"
TEMPLATE = PROBE / "template.xlsx"
FIXED_SCRIPT = PROBE / "embedded-safe.ps1.txt"
FIXED_CANDIDATES = {
    "normal": PROBE / "candidate-normal-postfix.robin",
    "negative": PROBE / "candidate-negative-postfix.robin",
}
EXPECTED_FIXED_SHA256 = {
    "source.xlsx": "74d2f493e8e687859badcb9c0b13ddff54d466c7394c3212e512a050113a2dc4",
    "template.xlsx": "108d25e5cfb86cd34422e738f7590d6050933c4f5429c672df65907fb2f31a36",
    "embedded-safe.ps1.txt": "aa2091327607b9ed1496f5ebb4a8bca2968e95e56ae3337f541651141e55f571",
    "candidate-normal-postfix.robin": "aaac1b7c04156f8038d26f6671c692faede55c91097cbf3f5d4c575348ae3851",
    "candidate-negative-postfix.robin": "a1ff8f503d485402ffdbb98248a52e62eedf98ac27f95d566dbaca1800dfcd1f",
    "candidate-normal.robin": "a9ba6694b40840a7583c5c61cf2f46a5cc7a279a337b69bfcfa23523430d2e9d",
    "runtime/work.xlsx": "108d25e5cfb86cd34422e738f7590d6050933c4f5429c672df65907fb2f31a36",
    "runtime/source-1.json": "7273709aa70b86cbdb175bc8b6bdf8ab3daccff23b0cf785064adf8a3e3917d7",
    "runtime/source-2.json": "d1c5eba5c453454900b950e2377fcf321eafd50678a4a79c91f1a8adfaf6f93b",
    "runtime/source-3.json": "ea52d7bfd0a3d8fa32fc37a96b68726ae91ae277a5d2862d44303148f7a61580",
    "runtime/source-4.json": "0300d9078e3fc280b8b7f946191afaebf0d3c7f70c9005dbb645e83bb708724a",
    "runtime/mode.json": "fae5483dc7d97912790a3571f752fb76e03056557928b8c94654e4822e8ba62d",
}
SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":3,"formats_restored":true}'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def decode_robin_string(value: bytes) -> bytes:
    decoded = bytearray()
    index = 0
    while index < len(value):
        if value[index] == 0x5C and index + 1 < len(value) and value[index + 1] in {
            0x5C,
            0x27,
            0x22,
        }:
            decoded.append(value[index + 1])
            index += 2
        else:
            decoded.append(value[index])
            index += 1
    return bytes(decoded)


def embedded_script(flow: bytes) -> bytes:
    prefix = b"Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = b"''' ScriptOutput=> PowershellOutput"
    start = flow.index(prefix) + len(prefix)
    end = flow.index(suffix, start)
    return decode_robin_string(flow[start:end])


def ast_errors(path: Path) -> list[str]:
    literal = str(path).replace("'", "''")
    command = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        f"$path='{literal}';$tokens=$null;$errors=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        "$path,[ref]$tokens,[ref]$errors);"
        "@($errors|ForEach-Object Message)|ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if not completed.stdout.strip():
        return []
    value = json.loads(completed.stdout)
    return value if isinstance(value, list) else [value]


def windows_powershell_type_probe() -> dict[str, object]:
    json_path = str(OLD_RUNTIME / "source-4.json").replace("'", "''")
    command = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        f"$p='{json_path}';"
        "$numberPayload=(Get-Content -LiteralPath $p -Raw -Encoding UTF8|ConvertFrom-Json).probe;"
        "[ordered]@{"
        "ps_version=$PSVersionTable.PSVersion.ToString();"
        "ps_edition=[string]$PSVersionTable.PSEdition;"
        "number_type=$numberPayload.GetType().FullName;"
        "accepted=(($numberPayload -is [double]) -or ($numberPayload -is [decimal]));"
        "is_double=($numberPayload -is [double]);"
        "is_decimal=($numberPayload -is [decimal]);"
        "value=[string]$numberPayload"
        "}|ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def baseline_blob_map() -> dict[str, str]:
    prefix = PROBE.relative_to(ROOT).as_posix()
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE, "--", prefix],
        cwd=ROOT,
        text=True,
    ).splitlines()
    result: dict[str, str] = {}
    for name in names:
        result[name] = subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE}:{name}"], cwd=ROOT, text=True
        ).strip()
        current = ROOT / name
        if not current.is_file():
            raise FileNotFoundError(current)
        current_blob = subprocess.check_output(
            ["git", "hash-object", f"--path={name}", str(current)], cwd=ROOT, text=True
        ).strip()
        if current_blob != result[name]:
            raise ValueError(f"Baseline evidence changed before trial: {name}")
    return result


def main() -> int:
    if TRIAL.exists():
        existing = {
            path.relative_to(TRIAL).as_posix()
            for path in TRIAL.rglob("*")
            if path.is_file()
        }
        if existing != {"normal/runtime/work.xlsx"} or sha256(
            TRIAL / "normal/runtime/work.xlsx"
        ) != sha256(TEMPLATE):
            raise FileExistsError(f"Refusing to overwrite existing trial: {TRIAL}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"], cwd=ROOT
    )
    if ancestor.returncode != 0:
        raise ValueError(f"HEAD does not retain baseline {BASELINE}")

    for relative, expected in EXPECTED_FIXED_SHA256.items():
        path = PROBE / relative
        if sha256(path) != expected:
            raise ValueError(f"Fixed input SHA mismatch: {relative}")
    blobs = baseline_blob_map()
    if (OLD_RUNTIME / "result.xlsx").exists():
        raise FileExistsError("Preserved failed runtime unexpectedly contains result.xlsx")

    records: dict[str, object] = {}
    old_runtime_escaped = str(OLD_RUNTIME).replace("\\", "\\\\").encode("utf-8")
    for label, fixed_candidate in FIXED_CANDIDATES.items():
        phase = TRIAL / label
        runtime = phase / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATE, runtime / "work.xlsx")

        fixed_bytes = fixed_candidate.read_bytes()
        new_runtime_escaped = str(runtime).replace("\\", "\\\\").encode("utf-8")
        replacements = fixed_bytes.count(old_runtime_escaped)
        if replacements != 11:
            raise ValueError(f"Unexpected runtime path occurrence count for {label}: {replacements}")
        bound_bytes = fixed_bytes.replace(old_runtime_escaped, new_runtime_escaped)
        candidate = phase / "candidate.robin"
        candidate.write_bytes(bound_bytes)
        if bound_bytes.replace(new_runtime_escaped, old_runtime_escaped) != fixed_bytes:
            raise ValueError(f"Path normalization failed for {label}")

        script_bytes = embedded_script(bound_bytes)
        script = phase / "embedded-safe-pathbound.ps1.txt"
        script.write_bytes(script_bytes)
        old_runtime_raw = str(OLD_RUNTIME).encode("utf-8")
        new_runtime_raw = str(runtime).encode("utf-8")
        if script_bytes.replace(new_runtime_raw, old_runtime_raw) != FIXED_SCRIPT.read_bytes().rstrip(b"\r\n"):
            raise ValueError(f"Embedded script differs beyond path binding for {label}")
        errors = ast_errors(script)
        if errors:
            raise ValueError(f"Bound {label} script has AST errors: {errors}")
        text = script_bytes.decode("utf-8")
        for forbidden in (
            "Invoke-Expression",
            "ScriptBlock]::Create",
            "Add-Type",
            "Start-Process",
            "Remove-Item",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "%Source",
            "%RunMode",
        ):
            if forbidden in text:
                raise ValueError(f"Forbidden token in {label} script: {forbidden}")
        if text.count("GetActiveObject('Excel.Application')") != 1:
            raise ValueError(f"Unexpected Excel attachment count in {label}")
        if bound_bytes.count(b"Excel.SaveExcel.SaveAs") != 1:
            raise ValueError(f"Unexpected SaveAs count in {label}")
        if bound_bytes.count(b"Excel.WriteToExcel.WriteCell Instance: Work") != 1:
            raise ValueError(f"Unexpected numeric write count in {label}")
        success_gate = bound_bytes.index(
            b"IF PowershellOutput = $'''{\\\"status\\\":\\\"OK\\\",\\\"mode\\\":\\\"NORMAL\\\",\\\"text_writes\\\":3,\\\"formats_restored\\\":true}''' THEN"
        )
        mode_gate = bound_bytes.index(b"IF RunMode = $'''NORMAL''' THEN", success_gate)
        numeric_write = bound_bytes.index(b"Excel.WriteToExcel.WriteCell Instance: Work")
        save_as = bound_bytes.index(b"Excel.SaveExcel.SaveAs")
        if not success_gate < mode_gate < numeric_write < save_as:
            raise ValueError(f"Write/Save gate ordering changed for {label}")

        records[label] = {
            "mode": "NORMAL" if label == "normal" else "INJECT_AFTER_FORMAT_CHANGE",
            "runtime": runtime.relative_to(ROOT).as_posix(),
            "fixed_candidate": fixed_candidate.relative_to(ROOT).as_posix(),
            "fixed_candidate_sha256": sha256(fixed_candidate),
            "candidate": candidate.relative_to(ROOT).as_posix(),
            "candidate_sha256": sha256(candidate),
            "embedded_script": script.relative_to(ROOT).as_posix(),
            "embedded_script_sha256": sha256(script),
            "runtime_path_replacements": replacements,
            "normalized_exact_fixed_candidate": True,
            "normalized_exact_fixed_script": True,
            "ast_error_count": 0,
            "work_sha256": sha256(runtime / "work.xlsx"),
            "result_exists": False,
            "json_files_exist": False,
            "maximum_pad_runs": 1,
        }

    type_probe = windows_powershell_type_probe()
    if not (
        str(type_probe.get("ps_version", "")).startswith("5.1.")
        and type_probe.get("ps_edition") == "Desktop"
        and type_probe.get("number_type") == "System.Decimal"
        and type_probe.get("accepted") is True
        and type_probe.get("is_double") is False
        and type_probe.get("is_decimal") is True
        and type_probe.get("value") == "42.5"
    ):
        raise ValueError(f"Unexpected Windows PowerShell type probe: {type_probe!r}")

    plan = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "kind": "ISSUE38_EX03_R2_R3_POSTFIX_LIVE_TRIAL",
        "baseline_commit": BASELINE,
        "scope": "Dedicated postfix probe only; path-bound execution copies, no candidate version.",
        "authorization": {
            "normal_runs": 1,
            "negative_runs_after_normal_full_pass": 1,
            "reruns": 0,
        },
        "fixed_values": {
            "Source!A2": "O'Brien",
            "Source!B2": "He said \"Go\"\nSecond line 'quoted'",
            "Source!C2": "100%",
            "Source!D2": 42.5,
        },
        "target_before": {
            "Target!A2": ["BEFORE_A", "System.String", "General", "", False],
            "Target!B2": ["BEFORE_B", "System.String", "0.00", "", False],
            "Target!C2": ["BEFORE_C", "System.String", "General", "", False],
            "Target!D2": [7, "System.Double", "0.00", "", False],
        },
        "target_after_normal": {
            "Target!A2": ["O'Brien", "System.String", "General", "", False],
            "Target!B2": ["He said \"Go\"\nSecond line 'quoted'", "System.String", "0.00", "", False],
            "Target!C2": ["100%", "System.String", "General", "", False],
            "Target!D2": [42.5, "System.Double", "0.00", "", False],
        },
        "normal_success_output": SUCCESS,
        "negative_expected_output": '{"status":"EXPECTED_ERROR","mode":"INJECT_AFTER_FORMAT_CHANGE","format_restored":true,"value_unchanged":true}',
        "negative_injection": "Target!A2 immediately after NumberFormat='@' and before Value2 assignment",
        "stop_conditions": [
            "normal PAD terminal or any comparison is not clearly PASS",
            "saved re-copy differs",
            "safety issue",
            "result is unclear",
        ],
        "out_of_scope": [
            "Copilot submission",
            "EX03 integrated rerun",
            "candidate version",
            "full regression",
            "GitHub write",
            "type generalization beyond the fixed values",
        ],
    }
    write_json(TRIAL / "plan.json", plan)
    preflight = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "result": "PASS_READY_FOR_NORMAL_ONE_RUN_ONLY",
        "baseline_commit": BASELINE,
        "baseline_probe_tree_blob_count": len(blobs),
        "baseline_probe_blobs": blobs,
        "fixed_sha256": EXPECTED_FIXED_SHA256,
        "windows_powershell_non_live_type_probe": type_probe,
        "actual_json_source": {
            "path": (OLD_RUNTIME / "source-4.json").relative_to(ROOT).as_posix(),
            "sha256": sha256(OLD_RUNTIME / "source-4.json"),
        },
        "phases": records,
        "old_runtime_result_exists": False,
        "old_evidence_unchanged": True,
    }
    write_json(TRIAL / "preflight.json", preflight)
    print(json.dumps(preflight, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
