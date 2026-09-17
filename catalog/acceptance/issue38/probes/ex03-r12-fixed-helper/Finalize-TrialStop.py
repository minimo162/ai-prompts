#!/usr/bin/env python3
"""Finalize the fail-closed pre-run stop for the one normal fixed-helper trial."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
TRIAL = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
RUNTIME = TRIAL / "runtime"
PREFLIGHT = TRIAL / "preflight.json"
MISMATCH = TRIAL / "pad-recopy-mismatch.json"
ANALYSIS = TRIAL / "pad-recopy-diff-analysis.json"
RESULT = TRIAL / "result.json"
REPORT = TRIAL / "RESULT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> int:
    if RESULT.exists() or REPORT.exists():
        raise FileExistsError("Refusing to overwrite fixed-helper stop result")

    preflight = load(PREFLIGHT)
    mismatch = load(MISMATCH)
    analysis = load(ANALYSIS)
    if preflight["result"] != "PASS_READY_FOR_ONE_NORMAL_PAD_RUN_ONLY":
        raise ValueError("Preflight was not ready for the authorized single Run")
    if mismatch["decision"] != "STOP_PAD_RECOPY_NOT_BYTE_EXACT_NO_RUN":
        raise ValueError("PAD mismatch record does not require the pre-run stop")
    if analysis["decision"] != "STOP_REQUIRED_EXACT_RECOPY_CONTRACT_FAILED":
        raise ValueError("Re-copy analysis does not retain the exactness stop")
    if mismatch["observation"]["pad_run_count"] != 0:
        raise ValueError("Unexpected PAD Run after re-copy mismatch")
    if analysis["execution"]["helper_invocation_count"] != 0:
        raise ValueError("Unexpected helper invocation after re-copy mismatch")
    if mismatch["comparison"]["exact_text_and_utf8_bytes"] is not False:
        raise ValueError("Mismatch record no longer identifies the failed exact gate")
    if analysis["classification"]["decoded_embedded_launcher_exact"] is not True:
        raise ValueError("Decoded launcher changed during PAD save/re-copy")
    if analysis["content_diff_hunk_count"] != 1:
        raise ValueError("Unexpected number of content difference hunks")

    files = {
        "helper": PROBE / "EX03-R12-Fixed-StringTransfer.ps1",
        "invocation": TRIAL / "invocation.json",
        "launcher": TRIAL / "launcher.ps1",
        "candidate": TRIAL / "candidate.robin",
        "pad_recopy": TRIAL / "pad-recopy-mismatch.robin",
        "template": ROOT / preflight["files"]["template"]["path"],
        "work": RUNTIME / "work.xlsx",
    }
    hashes = {name: sha256(path) for name, path in files.items()}
    for name in ("helper", "invocation", "launcher", "candidate"):
        if hashes[name] != preflight["files"][name]["sha256"]:
            raise ValueError(f"Fixed preflight file changed: {name}")
    if hashes["pad_recopy"] != mismatch["comparison"]["recopy_sha256"]:
        raise ValueError("Preserved PAD re-copy SHA mismatch")
    if hashes["template"] != hashes["work"]:
        raise ValueError("Dedicated work copy changed without a PAD Run")
    if hashes["template"] != preflight["fixed_sha256"]["template"]:
        raise ValueError("Template SHA changed after preflight")

    output = Path(preflight["paths"]["output"])
    json_files = [RUNTIME / f"source-{index}.json" for index in range(1, 8)]
    json_files.append(RUNTIME / "mode.json")
    if output.exists():
        raise ValueError("Output unexpectedly exists after the pre-run stop")
    if any(path.exists() for path in json_files):
        raise ValueError("JSON handoff unexpectedly exists after the pre-run stop")

    result = {
        "schema_version": 1,
        "trial_id": "EX03-R12-FIXED-HELPER-P1-T1",
        "baseline_commit": preflight["baseline_commit"],
        "decision": "STOPPED_PRE_RUN_PAD_RECOPY_NOT_EXACT",
        "scope": "Dedicated fixed-helper alternate path only; not formal EX03-r12 acceptance.",
        "return_behavior": {
            **preflight["return_behavior"],
            "live_observation": "NOT_RUN_BECAUSE_PAD_RECOPY_GATE_FAILED",
        },
        "sha256": hashes,
        "pad": {
            "version": "2.71.115.26224",
            "flow_name": mismatch["flow"]["name"],
            "flow_window_id": mismatch["flow"]["window_id"],
            "subflow": "Main",
            "power_fx": "OFF",
            "paste_count": 1,
            "save_count": 1,
            "recopy_count": 1,
            "run_count": 0,
            "status_after_save": "READY",
        },
        "recopy": {
            "exact": False,
            "candidate_sha256": hashes["candidate"],
            "recopy_sha256": hashes["pad_recopy"],
            "content_difference_hunks": analysis[
                "content_diff_hunks_ignoring_line_endings_and_final_newline"
            ],
            "decoded_launcher_exact": True,
            "candidate_serialization": analysis["classification"][
                "line_ending_serialization"
            ] | {},
            "classification": (
                "PAD escaped the eight JSON double quotes in launcher expectedSuccess, "
                "changed newline serialization, and added a final newline."
            ),
            "semantic_equivalence_not_used_as_acceptance": True,
        },
        "execution": {
            "launcher_invocation_count": 0,
            "helper_invocation_count": 0,
            "excel_execution_count": 0,
            "success_json": "NOT_OBSERVED_LIVE",
            "stderr": "NOT_OBSERVED_LIVE",
            "normal_termination": "NOT_OBSERVED_LIVE",
            "numeric_write": "NOT_ENTERED",
            "save_as": "NOT_ENTERED",
            "output": "ABSENT",
        },
        "comparison": {
            "twelve_target_cells": "NOT_RUN",
            "outside_cells": "NOT_RUN",
            "formulas": "NOT_RUN",
            "effective_format": "NOT_RUN",
            "F6_100_percent_string_original_format_empty_prefix_no_formula": "NOT_RUN",
            "reason": "The mandatory pre-run exact PAD save/re-copy gate failed.",
        },
        "preservation": {
            "work_still_exact_template": True,
            "template_and_work_sha256": hashes["template"],
            "output_absent": True,
            "json_handoff_files_absent": True,
            "formal_r12_and_fixed_inputs_unchanged": True,
            "existing_prototype_evidence_unchanged": True,
            "github_write": False,
        },
        "remaining": [
            "A separately authorized successor trial would need a PAD-canonical candidate serialization before any Run.",
            "The real helper success JSON, stderr, normal termination, saved workbook, 12 target cells, outside cells, formulas, effective formatting, and F6 contract remain unobserved in this trial.",
            "Formal EX03-r12 acceptance remains unchanged and was not rerun.",
        ],
    }
    RESULT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    hunk = result["recopy"]["content_difference_hunks"][0]
    report = f"""# Issue #38 EX03 r12 fixed-helper one-run trial

## 判定

`{result['trial_id']}` は、専用PADフロー `Power Automate | {result['pad']['flow_name']}` へ1回貼付けて保存し、実行前再コピーを1回取得した。再コピーは候補とバイト完全一致しなかったため、既定の停止条件どおりRun前に停止した。PAD Run、launcher/helper実行、Excel操作、数値書込み、SaveAs、成果物照合は0回である。

## 固定SHA-256

| 対象 | SHA-256 |
|---|---|
| helper | `{hashes['helper']}` |
| invocation | `{hashes['invocation']}` |
| launcher | `{hashes['launcher']}` |
| PAD貼付け候補 | `{hashes['candidate']}` |
| PAD保存後再コピー | `{hashes['pad_recopy']}` |
| 原本 / 専用work | `{hashes['template']}` |

## 返却経路の事前照合

既存stub証拠を再実行せず、実helperの `Write-Output -NoEnumerate`、launcherの `(& $helperPath ... | Out-String).Trim()`、最終 `[Console]::Out.Write($helperOutput)` を照合した。既存正常stubは単一の成功JSONを返す。ただし今回の実経路はRun前停止のため、実helperでの成功JSON・stderr・正常終了は未観測である。

## PAD保存・再コピー

- PAD: `2.71.115.26224`、Power Fx OFF、Main、保存後ステータス READY
- 貼付け1回、保存1回、再コピー1回、Run 0回
- 候補: LF-only 194、最終改行なし
- 再コピー: CRLF 136 + LF-only 59、最終改行あり
- 内容差分: 1 hunk。候補line {hunk['candidate_lines'][0]}のlauncher `$expectedSuccess` 内のJSON二重引用符8個へ、PADがRobinエスケープ `\\\"` を付加
- Robinを復号したlauncher本文は一致するが、意味同値をバイト完全一致PASSへ読み替えていない

## 停止時保全

- 専用workは原本と同一SHAのまま
- JSON handoff 8ファイルは不在
- 出力xlsxは不在
- launcher/helper、数値書込み、SaveAsは未進入
- 正式r12、固定依頼・spec・期待値、既存prototype証跡は不変
- GitHub書込みなし

## 未実施・残件

12対象セル、対象外セル、数式、Excel実効書式、F6の `100%` 文字列・元書式・空prefix・数式なしは、成果物がないためすべてNOT_RUN。別途承認された後継試行では、実行前にPAD正規化後とバイト一致する候補表現を固定する必要がある。
"""
    REPORT.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
