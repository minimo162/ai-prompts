"""Freeze one EX03/r5 generation cycle without sending or running anything."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'catalog/acceptance/issue38'
CYCLE = BASE / 'cycles/EX03-r5-G1'
RUN = BASE / 'runs/EX03-attempt1'
VERSION = ROOT / 'copilot/versions/20260915-excel-r5'


def load_oracle():
    spec = importlib.util.spec_from_file_location(
        'issue38_excel_oracle', ROOT / 'tools/Verify-Issue38Excel.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load_oracle()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(path):
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def write_bytes(path, value):
    with Path(path).open('xb') as handle:
        handle.write(value)


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def protected_paths():
    return [
        'catalog/acceptance/issue38/expected.json',
        'catalog/acceptance/issue38/spec.json',
        'catalog/acceptance/issue38/freeze.json',
        'catalog/acceptance/issue38/requests/EX03.txt',
        'catalog/acceptance/issue38/fixtures/EX03/入力い.xlsx',
        'catalog/acceptance/issue38/fixtures/EX03/入力ろ.xlsx',
        'catalog/acceptance/issue38/fixtures/EX03/ひな形.xlsx',
        'catalog/acceptance/issue38/copilot/EX03/plan.json',
        'catalog/acceptance/issue38/copilot/EX03/send-attempt.json',
        'catalog/acceptance/issue38/copilot/EX03/result.json',
        'catalog/acceptance/issue38/copilot/EX03/response-full.txt',
        'catalog/acceptance/issue38/copilot/EX03/code-copy.robin',
        'catalog/acceptance/issue38/cycles/EX02-r5-G2/generated.robin',
        'catalog/acceptance/issue38/cycles/EX02-r5-G2/acceptance-status.json',
        'catalog/acceptance/issue38/cycles/EX02-r5-G2/run1/result.xlsx',
        'catalog/acceptance/issue38/cycles/EX02-r5-G2/run2/result.xlsx',
        'catalog/acceptance/issue38/cycles/EX04-r5-G2-existing-output-neg1/verification.json',
        'copilot/versions/20260915-excel-r5/agent-instructions.txt',
        'copilot/versions/20260915-excel-r5/knowledge/PAD-Robin-Knowledge-Bundle.txt',
        'copilot/versions/20260915-excel-r5/manifest.json',
    ]


def prepare():
    if CYCLE.exists():
        raise ValueError(f'Cycle already exists; refusing overwrite: {CYCLE}')
    oracle.check_frozen()
    manifest_path = VERSION / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    instruction_path = VERSION / manifest['instruction_path']
    bundle_path = VERSION / manifest['bundle_path']
    request_path = BASE / 'requests/EX03.txt'
    expected_path = BASE / 'expected.json'
    spec_path = BASE / 'spec.json'
    template_path = BASE / 'fixtures/EX03/ひな形.xlsx'
    input_a_path = BASE / 'fixtures/EX03/入力い.xlsx'
    input_b_path = BASE / 'fixtures/EX03/入力ろ.xlsx'
    work_path = RUN / 'work.xlsx'
    output_path = RUN / '照合結果.xlsx'
    preparation_path = RUN / 'preparation.json'

    if sha(instruction_path) != manifest['instruction_sha256']:
        raise ValueError('r5 instruction hash mismatch')
    if sha(bundle_path) != manifest['bundle_sha256']:
        raise ValueError('r5 bundle hash mismatch')
    if not work_path.is_file() or sha(work_path) != sha(template_path):
        raise ValueError('EX03 work copy must exist and match the frozen template')
    if output_path.exists():
        raise ValueError('EX03 output collision before generation')
    if not preparation_path.is_file():
        raise ValueError('Existing EX03 preparation evidence is required')

    body = instruction_path.read_bytes() + b'\n' + request_path.read_bytes() + b'\n'
    body_text = body.decode('utf-8')
    # "日本語" also appears as an ordinary request qualifier, so it cannot
    # distinguish grader leakage from the fixed user request.
    forbidden_expected_values = ['春', '夏', '秋', '項目甲', '項目乙', '-4.5', '6.25']
    leaked = [value for value in forbidden_expected_values if value in body_text]
    if leaked:
        raise ValueError(f'Grader-only expected values leaked into submission: {leaked}')

    head = subprocess.check_output(
        ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True
    ).strip()
    CYCLE.mkdir(parents=True, exist_ok=False)
    submitted_path = CYCLE / 'submitted-body.txt'
    write_bytes(submitted_path, body)

    plan = {
        'schema_version': 1,
        'cycle_id': 'EX03-R5-G1',
        'base_commit': head,
        'purpose': 'Fixed EX03 parameter-change acceptance on the frozen r5 candidate',
        'candidate': {
            'version': '20260915-excel-r5',
            'instruction_path': repo_path(instruction_path),
            'instruction_sha256': sha(instruction_path),
            'bundle_path': repo_path(bundle_path),
            'bundle_sha256': sha(bundle_path),
            'manifest_path': repo_path(manifest_path),
            'manifest_sha256': sha(manifest_path),
            'candidate_changed': False,
        },
        'fixed_inputs': {
            'request': {'path': repo_path(request_path), 'sha256': sha(request_path)},
            'spec': {'path': repo_path(spec_path), 'sha256': sha(spec_path)},
            'grader_only_expected': {
                'path': repo_path(expected_path),
                'sha256': sha(expected_path),
                'send_to_copilot': False,
            },
            'input_a': {'path': repo_path(input_a_path), 'sha256': sha(input_a_path)},
            'input_b': {'path': repo_path(input_b_path), 'sha256': sha(input_b_path)},
            'template': {'path': repo_path(template_path), 'sha256': sha(template_path)},
            'existing_preparation': {
                'path': repo_path(preparation_path),
                'sha256': sha(preparation_path),
            },
            'work': {
                'path': repo_path(work_path),
                'sha256': sha(work_path),
                'must_match_template_before_each_run': True,
            },
            'output': {
                'path': repo_path(output_path),
                'must_be_absent_before_each_run': True,
            },
        },
        'parameters': {
            'input_a': '入力い.xlsx / 受取明細 / D4:E6 -> 集計先 / F7:G9',
            'input_b': '入力ろ.xlsx / 追加項目 / B2:D3 -> 追記先 / D5:F6',
            'template': 'ひな形.xlsx',
            'output': '照合結果.xlsx',
            'target_cells_derived_from_ex03_spec': 12,
        },
        'submission': {
            'body_path': repo_path(submitted_path),
            'body_sha256': sha(submitted_path),
            'body_contract': 'unchanged full r5 instructions followed by unchanged EX03 request',
            'attachment_path': repo_path(bundle_path),
            'attachment_sha256': sha(bundle_path),
            'normal_m365_new_chat': True,
            'model': 'Think Deeper',
            'grader_only_expected_excluded': True,
            'completed_robin_excluded': True,
        },
        'limits': {
            'max_generation_requests': 1,
            'max_pad_runs': 2,
            'no_regeneration_or_manual_robin_repair': True,
            'stop_on_refusal_uncaptured_command_or_unknown_result': True,
        },
        'pad': {
            'new_dedicated_flow': True,
            'power_fx': 'OFF',
            'unmodified_code_copy_only': True,
            'save_and_recopy_before_run1': True,
            'preserve_run1_before_run2': True,
            'restore_work_from_frozen_template_before_run2': True,
            'output_absent_before_run2': True,
        },
        'acceptance': {
            'scope': 'fixed EX03 text/number parameter-change case only',
            'required': [
                'Japanese filenames and sheet names',
                'EX03 source rectangles, target starts, and output name',
                'unmodified PAD import/save/recopy',
                'Run1 preserved before Run2 and collision-safe preparation',
                'two PAD runs with source/readback JSON type identity',
                'all EX03 target values, types, and positions against grader-only expectations',
                'outside cells, formulas, representative styles, and original hashes',
            ],
            'no_other_case_or_issue_wide_generalization': True,
        },
        'github_write': False,
        'status': 'READY_AFTER_PREFLIGHT',
    }

    protected = {
        'schema_version': 1,
        'cycle_id': 'EX03-R5-G1',
        'base_commit': head,
        'files': [
            {'path': path, 'sha256': sha(ROOT / path)} for path in protected_paths()
        ],
    }
    preflight = {
        'schema_version': 1,
        'cycle_id': 'EX03-R5-G1',
        'base_commit': head,
        'checks': {
            'frozen_fixture_spec_request_expected_hashes_match': True,
            'r5_instruction_bundle_manifest_hashes_match': True,
            'work_exists_and_matches_template': True,
            'output_absent': True,
            'grader_only_expected_values_absent_from_submission': True,
            'completed_robin_absent_from_submission': True,
            'excel_process_count_checked_separately_before_pad': True,
        },
        'hashes': {
            'submitted_body': sha(submitted_path),
            'work_and_template': sha(work_path),
            'input_a': sha(input_a_path),
            'input_b': sha(input_b_path),
        },
        'decision': {
            'safe_to_consume_single_generation_request': True,
            'copilot_generation': 'NOT_STARTED',
            'pad_run1': 'NOT_STARTED',
            'pad_run2': 'NOT_STARTED',
        },
    }
    write_json(CYCLE / 'plan.json', plan)
    write_json(CYCLE / 'protected-files-before.json', protected)
    write_json(CYCLE / 'preflight.json', preflight)
    return {
        'cycle': repo_path(CYCLE),
        'submitted_body_sha256': sha(submitted_path),
        'protected_file_count': len(protected['files']),
        'status': 'READY_AFTER_PREFLIGHT',
    }


if __name__ == '__main__':
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))
