#!/usr/bin/env python3
"""Finalize fail-closed evidence for the single EX03-r11-G1 generation.

This finalizer never opens PAD, never executes the generated Robin or embedded
PowerShell, never changes the fixed request/fixtures/expected values, and never
writes to GitHub.  It records the one-send result, verifies protected files,
and makes the code-block delivery mismatch explicit.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r11-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260917-excel-r11"

BASE_COMMIT = "659ae9db649d33226d4bf9220965e263e34ee323"
VERSION_ID = "20260917-excel-r11"
FAILURE_CODE = "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD"
GENERATED_SHA256 = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"

EXPECTED = {
    "instruction": "bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1",
    "bundle": "2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69",
    "manifest": "295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e",
    "teaching": "148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b",
    "script": "068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae",
    "contract": "ffbe75f9803435c55341f2d7db73e85b5ce5ec961f637734da38b6ee332a1ec9",
    "submitted_body": "4bd51be17353634c8b38cabbee91a9235a1dd1af87243675f5d42500f40c5984",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip("\n") + "\n")


def assert_file_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Hash mismatch for {relative(path)}: {actual}")


def finalize() -> dict[str, object]:
    outputs = [
        CYCLE / "live-send.json",
        CYCLE / "generation-result.json",
        CYCLE / "acceptance-status.json",
        CYCLE / "protected-files-after.json",
        CYCLE / "review.md",
    ]
    existing = [relative(path) for path in outputs if path.exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite final evidence: {existing}")

    head = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != BASE_COMMIT:
        raise ValueError(f"Expected HEAD {BASE_COMMIT}, found {head}")

    paths = {
        "instruction": VERSION / "agent-instructions.txt",
        "bundle": VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "manifest": VERSION / "manifest.json",
        "teaching": VERSION / "support/EX03-R11-Independent-PAD-Recopy.robin",
        "script": VERSION / "support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt",
        "contract": VERSION / "support/EX03-R11-Minimal-Structural-Contract.txt",
        "submitted_body": CYCLE / "submitted-body.txt",
        "request": BASE / "requests/EX03.txt",
        "spec": BASE / "spec.json",
        "expected": BASE / "expected.json",
        "input_a": BASE / "fixtures/EX03/入力い.xlsx",
        "input_b": BASE / "fixtures/EX03/入力ろ.xlsx",
        "template": BASE / "fixtures/EX03/ひな形.xlsx",
    }
    for name, path in paths.items():
        assert_file_hash(path, EXPECTED[name])

    generated = CYCLE / "generated.robin"
    audit_path = CYCLE / "generation-safety-audit.json"
    response_path = CYCLE / "copilot-response.visible.txt"
    dom_path = CYCLE / "response-dom-inspection.json"
    assert_file_hash(generated, GENERATED_SHA256)
    audit = json.loads(audit_path.read_bytes())
    dom = json.loads(dom_path.read_bytes())
    if audit["decision"]["status"] != FAILURE_CODE:
        raise ValueError("Unexpected r11 audit decision")
    if audit["decision"]["downloaded_payload_static_safety"] != "PASS":
        raise ValueError("Downloaded r11 payload did not pass the static audit")
    if audit["decision"]["response_delivery_contract"] != "FAIL":
        raise ValueError("The required response delivery failure is not recorded")
    if audit["powershell_parser"]["generated_embedded_script_error_count"] != 0:
        raise ValueError("The generated embedded PowerShell did not parse cleanly")
    if audit["comparison"]["differing_content_line_count"] != 0:
        raise ValueError("The generated payload differs from the adapted teaching source")
    if dom["contract_observation"]["actual_text_code_block_count"] != 0:
        raise ValueError("The completed response unexpectedly contains a code block")

    before_path = CYCLE / "protected-files-before.json"
    before = json.loads(before_path.read_bytes())
    after_records = []
    mismatches = []
    for record in before["files"]:
        path = ROOT / record["path"]
        after_hash = sha256(path) if path.is_file() else None
        matches = after_hash == record["sha256"]
        after_record = {
            "path": record["path"],
            "before_sha256": record["sha256"],
            "after_sha256": after_hash,
            "matches": matches,
        }
        after_records.append(after_record)
        if not matches:
            mismatches.append(after_record)
    if mismatches:
        raise ValueError(f"Protected evidence changed: {mismatches[:3]}")

    work = RUN / "work.xlsx"
    output = RUN / "照合結果.xlsx"
    work_hash = sha256(work)
    if work_hash != EXPECTED["template"]:
        raise ValueError("work.xlsx no longer matches the frozen template")
    if output.exists():
        raise ValueError("An EX03 output exists despite the pre-PAD stop")

    now = datetime.now().astimezone().isoformat()
    conversation = dom["conversation"]
    generated_capture = audit["capture"]
    static_review = audit["target_workbook_and_side_effect_review"]

    live_send = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "recorded_at": now,
        "authorization": {
            "request": "one prepared r11 normal-M365 generation and at most two PAD runs",
            "explicit_action_time_authorization_received": True,
            "max_generation_requests": 1,
            "max_pad_runs": 2,
            "no_resend": True,
            "no_manual_generated_robin_repair": True,
            "no_additional_run": True,
            "no_fixed_condition_change": True,
            "no_automatic_successor_trial": True,
        },
        "checkpoint": {
            "base_commit": BASE_COMMIT,
            "action_time_starting_head": head,
            "preflight_verifier": "PASS_BEFORE_BROWSER_STAGING",
            "r9_r10_failure_and_stop_evidence_preserved": True,
            "protected_file_count": len(before["files"]),
            "protected_mismatch_count_before_send": 0,
            "work_matches_template_before_send": True,
            "output_absent_before_send": True,
        },
        "candidate": {
            "version": VERSION_ID,
            "instruction_sha256": EXPECTED["instruction"],
            "bundle_sha256": EXPECTED["bundle"],
            "manifest_sha256": EXPECTED["manifest"],
            "teaching_robin_sha256": EXPECTED["teaching"],
            "teaching_script_sha256": EXPECTED["script"],
            "structural_contract_sha256": EXPECTED["contract"],
        },
        "independence": {
            "frozen_preflight_check": "PASS",
            "teaching_and_test_independence_confirmed": True,
            "grader_only_expected_sent_to_copilot": False,
            "fixed_completed_robin_sent_to_copilot": False,
            "independent_teaching_robin_in_bundle": True,
            "no_old_or_probe_pass_inherited": True,
        },
        "destination": conversation,
        "attachment": {
            "path": relative(paths["bundle"]),
            "ui_label": "PAD-Robin-Knowledge-Bundle.txt",
            "sha256": EXPECTED["bundle"],
            "upload_count": 1,
            "ui_chip_visible_before_send": True,
            "same_version_as_body": True,
        },
        "body": {
            "path": relative(paths["submitted_body"]),
            "sha256": EXPECTED["submitted_body"],
            "utf16_units": 7937,
            "utf8_bytes": 18606,
            "line_count": 83,
            "exact_contract": "unchanged full r11 instructions followed by unchanged fixed EX03 request",
            "visible_editor_serialization_exact": True,
            "visible_editor_sha256": EXPECTED["submitted_body"],
            "raw_editor_copy_sha256": "bc57ef7f3f30f092de0834ae35769ae6ebed158aa156eaf6076a8b6fdcd87e75",
            "r11_marker_count": 1,
        },
        "editor_verification": {
            "send_clicked_while_stale_or_mismatched": False,
            "exact_body_inserted_as_plain_text": True,
            "raw_editor_copy_extra_codepoints": ["U+200B", "U+200C"],
            "extra_codepoint_count": 2,
            "extra_codepoints_aria_hidden": True,
            "visible_serialization_excluded_only_known_hidden_ui_marker": True,
            "visible_serialization_exact_r11_body": True,
        },
        "actions": {
            "browser_staging": 1,
            "bundle_upload": 1,
            "normal_m365_send": 1,
            "resend": 0,
            "generation_requests": 1,
            "response_dom_capture": 1,
            "generated_file_download": 1,
            "pad_import": 0,
            "pad_save": 0,
            "pad_recopy": 0,
            "pad_run": 0,
            "github_write": 0,
        },
        "result": {
            "send_clicked_once": True,
            "generation_completed": True,
            "reasoning_steps_reported": 8,
            "refusal": False,
            "required_text_code_block_count": 1,
            "actual_text_code_block_count": 0,
            "download_file_present": True,
            "stopped_before_pad": True,
            "stop_reason_code": FAILURE_CODE,
        },
    }

    generation_result = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "recorded_at": now,
        "checkpoint": {
            "base_commit": BASE_COMMIT,
            "action_time_starting_head": head,
        },
        "candidate": live_send["candidate"],
        "conversation": conversation,
        "rendered_response": {
            "completed": True,
            "reasoning_steps_reported": 8,
            "refusal": False,
            "required_text_code_block_count": 1,
            "actual_text_code_block_count": 0,
            "visible_response_path": relative(response_path),
            "visible_response_sha256": sha256(response_path),
            "response_dom_inspection_path": relative(dom_path),
            "response_dom_inspection_sha256": sha256(dom_path),
            "download_file_substituted_for_required_code_block": True,
            "response_claims_download_is_not_acceptance": True,
        },
        "generated_file_capture": {
            "repository_path": relative(generated),
            "repository_sha256": GENERATED_SHA256,
            "downloaded_file_name": "ex03.robin",
            "downloaded_utf8_bytes": generated_capture["utf8_bytes"],
            "utf16_units": generated_capture["utf16_units"],
            "line_count": generated_capture["line_count"],
            "line_ending": generated_capture["line_ending"],
            "final_newline": generated_capture["final_newline"],
            "first_line": generated_capture["first_line"],
            "last_line": generated_capture["last_line"],
            "download_to_repository_relation": "byte-identical SHA-256 match",
            "capture_method": "invoke the sole generated-file download link once and copy its bytes without editing",
            "generated_text_edited": False,
        },
        "static_audit": {
            "status": audit["decision"]["downloaded_payload_static_safety"],
            "expected_adapted_teaching_differing_lines": audit["comparison"][
                "differing_content_line_count"
            ],
            "embedded_powershell_parser_errors": audit["powershell_parser"][
                "generated_embedded_script_error_count"
            ],
            "runscript_count": static_review["run_powershell_script_count"],
            "numeric_write_count": static_review["write_action_count"],
            "source_json_count": static_review["source_json_actions"],
            "saved_json_count": static_review["saved_json_actions"],
            "value_type_match_count": static_review["value_type_match_variables"],
            "normalized_exact_workbook_match_count": static_review[
                "normalized_exact_fullname_match_count"
            ],
            "forbidden_runtime_fragments": static_review[
                "forbidden_runtime_fragments"
            ],
            "static_pass_not_used_as_pad_acceptance": True,
        },
        "generation_requests_used": 1,
        "generation_request_limit": 1,
        "regeneration_requested": False,
        "interpretation": (
            "The only generation completed without refusal. The downloaded file "
            "passes static fidelity and parser gates, but the completed response "
            "omitted the required single text code block and substituted a download. "
            "The fixed mismatch stop rule therefore prevents PAD import or execution."
        ),
    }

    protected_after = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "recorded_at": now,
        "source": relative(before_path),
        "protected_file_count": len(before["files"]),
        "protected_file_mismatch_count": 0,
        "work_sha256": work_hash,
        "template_sha256": EXPECTED["template"],
        "work_matches_template": True,
        "output_exists": False,
        "files": after_records,
    }

    acceptance_status = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "recorded_at": now,
        "candidate": {
            "version": VERSION_ID,
            "base_commit": BASE_COMMIT,
            "instruction_sha256": EXPECTED["instruction"],
            "bundle_sha256": EXPECTED["bundle"],
            "manifest_sha256": EXPECTED["manifest"],
            "submitted_body_sha256": EXPECTED["submitted_body"],
        },
        "predecessor_context": {
            "r10_stop_commit": "ac90b0943d2ff4e1172c23712ef49fe93787b7b2",
            "r10_result": "STOPPED_BEFORE_PAD_R10_GENERATION_SAFETY_FAILURE",
            "r11_change_reason": (
                "replace the r9/r10-fragile static method-call expressions with a "
                "shorter parser-clean -ieq and direct string/prefix checks"
            ),
            "r11_scope_change": (
                "new independent r11 teaching Robin and minimal embedded PowerShell; "
                "fixed EX03 request, fixtures and grader expectations unchanged"
            ),
            "old_or_synthetic_success_inherited": False,
        },
        "generation": {
            "normal_m365_send_count": 1,
            "resend_count": 0,
            "completed": True,
            "refusal": False,
            "required_text_code_block_count": 1,
            "actual_text_code_block_count": 0,
            "generated_file_sha256": GENERATED_SHA256,
            "generated_file_static_safety": "PASS",
            "embedded_powershell_parser_errors": 0,
            "delivery_contract": "FAIL",
            "failure_code": FAILURE_CODE,
        },
        "pad_import": {
            "dedicated_flow_opened": False,
            "unmodified_paste_count": 0,
            "saved": False,
            "recopy": "NOT_RUN_RESPONSE_DELIVERY_CONTRACT_MISMATCH",
            "recopy_match": "NOT_RUN",
            "manual_repair": False,
        },
        "runs": {
            "run1": "NOT_RUN_STOPPED_BEFORE_PAD_IMPORT",
            "run2": "NOT_RUN_RUN1_PREREQUISITES_NOT_REACHED",
            "pad_runs_used": 0,
            "pad_run_limit": 2,
        },
        "comparisons": {
            "run1_artifact": "NOT_CREATED",
            "run1_fixed_value_type_position_comparison": "NOT_RUN",
            "run1_original_outside_formula_format_comparison": "NOT_RUN",
            "run1_f6_string_100_percent_original_format_empty_prefix_no_formula": "NOT_RUN",
            "run2_artifact": "NOT_CREATED",
            "run2_fixed_value_type_position_comparison": "NOT_RUN",
            "run2_original_outside_formula_format_comparison": "NOT_RUN",
            "reason": (
                "No PAD paste, save, re-copy, execution or output was allowed after "
                "the completed response violated the fixed delivery contract."
            ),
        },
        "artifacts": {
            "runtime_output_exists": False,
            "work_sha256": work_hash,
            "template_sha256": EXPECTED["template"],
            "work_matches_template": True,
            "protected_file_count": len(before["files"]),
            "protected_file_mismatch_count": 0,
            "fixed_request_sha256": EXPECTED["request"],
            "grader_only_expected_sha256": EXPECTED["expected"],
            "fixed_expected_changed": False,
            "legacy_558_failure_preserved": True,
        },
        "scope": {
            "other_case_or_probe_pass_inherited": False,
            "unconfirmed_types_or_shapes_generalized": False,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
            "format_and_dimension_558_difference": "REMAINS_FAIL_NOT_HIDDEN",
            "next_version_created_or_tried": False,
        },
        "decision": {
            "accepted": False,
            "status": "STOPPED_BEFORE_PAD_R11_RESPONSE_DELIVERY_MISMATCH",
            "failure_code": FAILURE_CODE,
            "reason": (
                "The single generation completed and its downloaded Robin passed "
                "static safety, exact adapted-source comparison and PowerShell parsing, "
                "but the response contained zero required text code blocks and used a "
                "download link instead. The fixed stop condition therefore prohibited "
                "PAD import, re-copy, Run1 and Run2."
            ),
        },
        "github_write": False,
    }

    review = f"""# EX03-r11-G1 live-generation review

## 結論

EX03-r11-G1は**不受入**です。固定版`{VERSION_ID}`の本文と同版bundleを通常Microsoft 365 Copilotへ1回だけ送信し、拒否なしで応答と12,487-byteの`ex03.robin`を得ました。無修正ファイルは教材からの許可置換と167行すべて一致し、埋込みPowerShellのASTエラー0、固定token・対象ブック特定・副作用検査もPASSです。

一方、固定契約は全工程を1つの`text`コードブロックに出すことを要求していましたが、完成応答のコードブロックは0件で、Copilot自身が切り詰めを理由にblob-downloadへ置き換えました。失敗コードは`{FAILURE_CODE}`です。固定の不一致停止条件に従い、専用PADへの貼付け・保存・再コピー・Run1・Run2はすべて未実施です。再送、生成物修正、追加Run、次版試行は行っていません。

## 固定版と送信

- version: `{VERSION_ID}`
- base/action-time HEAD: `{BASE_COMMIT}`
- instruction SHA-256: `{EXPECTED['instruction']}`
- bundle SHA-256: `{EXPECTED['bundle']}`
- manifest SHA-256: `{EXPECTED['manifest']}`
- teaching Robin SHA-256: `{EXPECTED['teaching']}`
- embedded script SHA-256: `{EXPECTED['script']}`
- structural contract SHA-256: `{EXPECTED['contract']}`
- submitted body SHA-256: `{EXPECTED['submitted_body']}`
- conversation: <{conversation['url']}>
- normal M365 send: 1 / resend: 0 / model: Think Deeper

送信直前には通常M365、Think Deeper、同版bundleの添付chip、固定本文を確認しました。生のエディタシリアライズにだけ現れた末尾U+200B/U+200Cを除く可視本文は固定本文とSHA一致しています。送信クリックは1回です。

## r11生成物の静的検査

- generated Robin SHA-256: `{GENERATED_SHA256}`
- 12,487 UTF-8 bytes / 167行 / LF / 最終改行なし
- 独立教材からの許可置換との差: 0行
- PowerShell ASTエラー: 0
- `[string]` 12 / `[bool]` 2 / `[void]` 6
- `[Runtime.InteropServices.Marshal]` 7 / `[IO.Path]` 2 / `::GetFullPath(` 2
- `-ieq` 1 / `$matches[0]` 1 / `$beforeNumberFormat` 3
- 禁止旧表現・破損断片: すべて0
- RunScript 1 / numeric WriteCell 5 / source JSON 7 / saved JSON 12 / ValueTypeMatch 12
- normalized FullNameによる一冊選択: 1
- delete/network/external-process断片: 0

このPASSは**ダウンロードされた生成ファイルの静的検査だけ**です。コードブロック契約違反を相殺せず、PAD保存・再コピー・実行成功・EX03受入へ読み替えていません。

## 工程判定

- 送信先・固定本文・同版bundle・SHA・独立性: PASS
- 通常M365送信: PASS（1回、拒否なし、再送0）
- 無修正ダウンロード原文の構文・構造・対象ブック・副作用検査: PASS
- 応答の固定delivery契約: FAIL（要求1 code block / 実際0）
- PAD貼付け・保存: NOT_RUN
- PAD再コピー一致: NOT_RUN
- Run1: NOT_RUN
- Run1の12セル・F6・対象外・数式・実効書式・原本SHA照合: NOT_RUN
- Run2: NOT_RUN（Run1前提未達）
- 出力`照合結果.xlsx`: 未作成
- `work.xlsx`とテンプレート: SHA一致
- 保護対象{len(before['files'])}ファイル: 不一致0
- 固定依頼・fixture・期待値: 変更なし
- 旧558差分FAIL: 保持
- 既存output guard実機経路: 未確認のまま
- GitHub書込み: 0

詳細は`generation-safety-audit.json`、`generation-result.json`、`live-send.json`、`acceptance-status.json`、`protected-files-after.json`に記録しています。Copilot可視応答は`copilot-response.visible.txt`、無修正生成ファイルは`generated.robin`です。
"""

    write_json(CYCLE / "live-send.json", live_send)
    write_json(CYCLE / "generation-result.json", generation_result)
    write_json(CYCLE / "protected-files-after.json", protected_after)
    write_json(CYCLE / "acceptance-status.json", acceptance_status)
    write_text(CYCLE / "review.md", review)
    return {
        "status": FAILURE_CODE,
        "generated_sha256": GENERATED_SHA256,
        "static_payload_safety": "PASS",
        "delivery_contract": "FAIL",
        "pad_runs_used": 0,
        "protected_file_count": len(before["files"]),
        "protected_mismatch_count": 0,
        "output_exists": False,
    }


if __name__ == "__main__":
    print(json.dumps(finalize(), ensure_ascii=False))
