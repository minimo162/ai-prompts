"""EX02 diagnostics and reproducible package regression; synthetic fault injection only."""
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old_tests = load('old_tests', 'tests/Test-Issue38Excel.py')
new = load('diagnostic', 'tools/Compare-Issue38Ex02.py')
builder = load('builder', 'tools/Build-Issue38Ex02Candidate.py')
r5_builder = load('r5_builder', 'tools/Build-Issue38Ex02CandidateR5.py')
typed_transfer = load('typed_transfer', 'tools/Verify-Issue38Ex02TypedTransfer.py')
negative_builder = load('negative_builder', 'tools/Build-Issue38Ex02TypeNegative.py')
format_classifier = load(
    'format_classifier', 'tools/Classify-Issue38Ex02FormatDifferences.py'
)


class Ex02Tests(unittest.TestCase):
    def simulate(self, mutate=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'simulated.xlsx'
            old_tests.simulated_output('EX02', output, mutate)
            return new.compare(output)

    def test_positive_independent_output_is_not_runtime_pass(self):
        result = self.simulate()
        self.assertEqual(result['status'], 'PASS_LOGICAL_OUTPUT_ONLY')
        self.assertEqual(result['checks']['target_values_types_positions']['checked'], 12)
        self.assertEqual(result['checks']['outside_values_types_formulas']['checked'], 468)
        self.assertEqual(result['flow_internal_type_check'], 'NOT_PROVEN')
        self.assertEqual(result['pad_execution'], 'NOT_ASSERTED')

    def test_number_one_and_text_one_remain_different(self):
        self.assertNotEqual(new.legacy.typed(1), new.legacy.typed('1'))
        self.assertNotEqual(new.legacy.typed(True), new.legacy.typed(1))
        def mutate(tree):
            cell = old_tests.cell(tree, 'D4')
            cell.remove(cell.find(old_tests.q('v')))
            cell.set('t', 'inlineStr')
            ET.SubElement(ET.SubElement(cell, old_tests.q('is')), old_tests.q('t')).text = '12.5'
        result = self.simulate(mutate)
        mismatch = result['checks']['target_values_types_positions']['mismatches'][0]
        self.assertEqual(mismatch['expected'], ['number', 12.5])
        self.assertEqual(mismatch['actual'], ['text', '12.5'])
        self.assertEqual(result['status'], 'FAIL')

    def test_wrong_value_detected(self):
        result = self.simulate(lambda t: setattr(old_tests.cell(t, 'D4').find(old_tests.q('v')), 'text', '999'))
        self.assertEqual(result['failure_counts']['values_types_positions'], 1)

    def test_wrong_position_detected(self):
        def move(tree):
            row = next(r for r in tree.iter(old_tests.q('row')) if r.attrib['r'] == '4')
            # Remove the existing empty J4 so the injection is a valid moved cell,
            # not duplicate XML addresses where openpyxl can keep the later cell.
            row.remove(old_tests.cell(tree, 'J4'))
            old_tests.cell(tree, 'D4').set('r', 'J4')
        result = self.simulate(move)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['checks']['outside_values_types_formulas']['mismatches']), 1)

    def test_outside_formula_detected(self):
        result = self.simulate(lambda t: setattr(old_tests.cell(t, 'B15').find(old_tests.q('f')), 'text', '2+4'))
        self.assertEqual(result['checks']['outside_values_types_formulas']['mismatches'][0]['actual'], ['formula', '=2+4'])

    def test_style_and_dimension_negatives_remain_fail(self):
        def row_height(t):
            next(t.iter(old_tests.q('row'))).set('ht', '99')
        for mutate, category in [(lambda t: old_tests.cell(t, 'B15').set('s', '0'), 'styles'),
                                 (row_height, 'row_dimensions')]:
            with self.subTest(category=category):
                result = self.simulate(mutate)
                self.assertEqual(result['status'], 'FAIL')
                self.assertGreater(result['failure_counts'][category], 0)

    def test_legacy_558_failures_are_preserved(self):
        result = new.compare(new.legacy.BASE / 'probes/matrix-write/run2/result.xlsx')
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['legacy']['failures']), 558)
        self.assertEqual(result['checks']['target_values_types_positions']['mismatches'], [])
        self.assertEqual(result['checks']['outside_values_types_formulas']['mismatches'], [])
        self.assertEqual(result['native_styles'], 'NOT_RUN_BY_THIS_COMPARATOR')

    def test_rebuild_is_byte_identical_and_existing_version_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / 'r4'
            builder.build(dest)
            frozen = ROOT / 'copilot/versions' / builder.VERSION
            for p in frozen.rglob('*'):
                if p.is_file():
                    self.assertEqual(p.read_bytes(), (dest / p.relative_to(frozen)).read_bytes(), str(p))
            with self.assertRaisesRegex(ValueError, 'sealed'):
                builder.build(dest)

    def test_example_does_not_write_outside_missing_output_branch(self):
        lines = builder.assembled_example().splitlines()
        self.assertEqual(lines[3], 'ELSE')
        self.assertEqual(lines[-1], 'END')
        self.assertTrue(all(l.startswith('    ') for l in lines if l.lstrip().startswith('Excel.')))
        self.assertFalse(any(l.strip() == 'EXIT' for l in lines))
        self.assertIn("    SET TypeState TO $'''NOT_PROVEN'''", lines)
        self.assertEqual(sum(l.strip() == 'IF SourceCell = SavedCell THEN' for l in lines), 12)

    def test_r5_rebuild_is_byte_identical_and_existing_version_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / 'r5'
            r5_builder.build(dest)
            frozen = ROOT / 'copilot/versions' / r5_builder.VERSION
            for p in frozen.rglob('*'):
                if p.is_file():
                    self.assertEqual(p.read_bytes(), (dest / p.relative_to(frozen)).read_bytes(), str(p))
            with self.assertRaisesRegex(ValueError, 'sealed'):
                r5_builder.build(dest)

    def test_r5_example_guards_writes_and_has_twelve_scoped_json_comparisons(self):
        lines = r5_builder.assembled_example().splitlines()
        self.assertEqual(lines[3], 'ELSE')
        self.assertEqual(lines[-1], 'END')
        self.assertTrue(all(line.startswith('    ') for line in lines if line.lstrip().startswith('Excel.')))
        self.assertFalse(any(line.strip() == 'EXIT' for line in lines))
        self.assertFalse(any('GetType' in line for line in lines))
        self.assertEqual(sum('_ValueTypeMatch TO SourceCellJson = SavedCellJson' in line for line in lines), 12)
        self.assertEqual(sum("ConvertCustomObjectToJson CustomObject: { 'probe': SourceCell }" in line for line in lines), 12)
        self.assertEqual(sum("ConvertCustomObjectToJson CustomObject: { 'probe': SavedCell }" in line for line in lines), 12)
        self.assertFalse(any('runs\\\\probe-matrix-A' in line for line in lines))
        self.assertEqual(sum('runs\\\\EX02-attempt1' in line for line in lines), 4)

    def test_r5_live_generation_failure_is_preserved_without_repair(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5'
        generated_bytes = (cycle / 'generated.robin').read_bytes()
        self.assertEqual(
            hashlib.sha256(generated_bytes).hexdigest(),
            'c26b5c6cf42b66fecb1272222b64c2ab7aaa38921802945d9a58d7636c6a7dec',
        )
        generated = generated_bytes.decode('utf-8').replace('\r\n', '\n')
        self.assertEqual(generated, r5_builder.assembled_example() + '`')
        audit = json.loads((cycle / 'generation-safety-audit.json').read_bytes())
        paste = json.loads((cycle / 'pad-paste-attempt.json').read_bytes())
        acceptance = json.loads((cycle / 'acceptance-status.json').read_bytes())
        recheck = json.loads((cycle / 'continuation-recheck.json').read_bytes())
        self.assertEqual(audit['decision']['status'], 'FAIL_UNMODIFIED_CODE_COPY_EXTRA_BACKTICK')
        self.assertFalse(audit['comparison']['repair_applied'])
        self.assertEqual(paste['operation']['final_action_count'], 0)
        self.assertEqual(paste['result']['run1'], 'NOT_RUN')
        self.assertEqual(paste['result']['run2'], 'NOT_RUN')
        self.assertFalse(acceptance['overall']['accepted'])
        self.assertEqual(acceptance['legacy_558']['count'], 558)
        self.assertEqual(recheck['normal_m365_existing_response']['code_editor_count'], 1)
        self.assertEqual(
            recheck['normal_m365_existing_response']['code_editor']['last_numbered_entries'],
            [{'line': 87, 'text': 'END'}, {'line': 88, 'text': '`'}],
        )
        self.assertEqual(recheck['existing_pad_flow']['visible_action_count'], 0)
        self.assertFalse(recheck['controls']['regeneration_requested'])
        self.assertFalse(recheck['controls']['generated_robin_edited'])
        self.assertFalse(recheck['controls']['pad_run_started'])
        self.assertTrue(recheck['decision']['previous_failure_affirmed'])
        self.assertEqual(acceptance['continuation_evidence']['additional_generation_requests'], 0)

    def test_r5_protected_files_and_unrun_workbook_state_are_preserved(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5'
        before = json.loads((cycle / 'protected-files-before.json').read_bytes())
        after = json.loads((cycle / 'protected-files-after.json').read_bytes())
        before_hashes = {item['path']: item['sha256'] for item in before['files']}
        after_hashes = {item['path']: item['sha256'] for item in after['files']}
        self.assertEqual(after_hashes, before_hashes)
        for path, expected_sha in after_hashes.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected_sha, path)
        runtime = after['runtime_preconditions_after_failed_paste']
        work = ROOT / 'catalog/acceptance/issue38/runs/EX02-attempt1/work.xlsx'
        result = ROOT / 'catalog/acceptance/issue38/runs/EX02-attempt1/result.xlsx'
        self.assertEqual(hashlib.sha256(work.read_bytes()).hexdigest(), runtime['work_sha256'])
        self.assertTrue(runtime['work_matches_template'])
        self.assertFalse(result.exists())

    def test_r5_g2_is_separate_cycle_with_identical_fixed_inputs(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5-G2'
        plan = json.loads((cycle / 'plan.json').read_bytes())
        preflight = json.loads((cycle / 'preflight.json').read_bytes())
        self.assertEqual(plan['cycle_id'], 'EX02-R5-G2')
        self.assertEqual(plan['predecessor']['cycle_id'], 'EX02-R5-G1')
        self.assertEqual(plan['predecessor']['max_generation_requests'], 1)
        self.assertEqual(plan['predecessor']['generation_requests_used'], 1)
        self.assertEqual(plan['limits']['max_generation_requests'], 1)
        self.assertTrue(plan['limits']['no_retry_or_regeneration_after_failure'])
        self.assertFalse(plan['fixed_inputs']['grader_only_expected']['send_to_copilot'])
        self.assertTrue(plan['submission']['completed_robin_excluded'])
        self.assertEqual(plan['submission']['model'], 'Think Deeper')
        for item in [plan['candidate']['instruction_path'], plan['candidate']['bundle_path'],
                     plan['candidate']['manifest_path'], plan['submission']['body_path']]:
            self.assertTrue((ROOT / item).is_file(), item)
        hash_records = [
            plan['fixed_inputs']['request'], plan['fixed_inputs']['spec'],
            plan['fixed_inputs']['grader_only_expected'], plan['fixed_inputs']['input_a'],
            plan['fixed_inputs']['input_b'], plan['fixed_inputs']['template'],
            plan['fixed_inputs']['work'],
        ]
        for record in hash_records:
            self.assertEqual(hashlib.sha256((ROOT / record['path']).read_bytes()).hexdigest(), record['sha256'])
        self.assertEqual(
            hashlib.sha256((ROOT / plan['candidate']['instruction_path']).read_bytes()).hexdigest(),
            plan['candidate']['instruction_sha256'],
        )
        self.assertEqual(
            hashlib.sha256((ROOT / plan['candidate']['bundle_path']).read_bytes()).hexdigest(),
            plan['candidate']['bundle_sha256'],
        )
        self.assertEqual(
            hashlib.sha256((ROOT / plan['submission']['body_path']).read_bytes()).hexdigest(),
            plan['submission']['body_sha256'],
        )
        self.assertFalse((ROOT / plan['fixed_inputs']['result']['path']).exists())
        self.assertTrue(preflight['fixed_input_checks']['all_plan_hashes_match_current_files'])
        self.assertFalse(preflight['fixed_input_checks']['fixed_input_problem_requiring_stop'])
        self.assertTrue(preflight['decision']['safe_to_consume_one_new_generation_request'])

    def test_r5_g2_live_generation_and_unmodified_pad_evidence(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5-G2'
        generation = json.loads((cycle / 'generation-result.json').read_bytes())
        pad = json.loads((cycle / 'pad-import-and-recopy.json').read_bytes())
        acceptance = json.loads((cycle / 'acceptance-status.json').read_bytes())
        raw = (cycle / 'code-copy-raw.robin').read_bytes()
        generated = (cycle / 'generated.robin').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), generation['code_copy']['sha256'])
        self.assertFalse(raw.endswith(b'\n'))
        self.assertEqual(raw + b'\n', generated)
        self.assertEqual(generated, r5_builder.assembled_example().encode('utf-8'))
        self.assertEqual(pad['import']['final_action_count'], 87)
        self.assertFalse(pad['import']['manual_edit'])
        self.assertTrue(pad['recopy_after_save']['lf_normalized_exact_generated_robin'])
        self.assertEqual(acceptance['overall']['generation_requests_used'], 1)
        self.assertEqual(acceptance['overall']['pad_runs_used'], 2)
        self.assertEqual(acceptance['overall']['functional_generated_pad_path'],
                         'PASS_FIXED_EX02_TEXT_NUMBER_SCOPE')
        self.assertFalse(acceptance['overall']['accepted'])
        self.assertEqual(acceptance['legacy_558']['count'], 558)
        self.assertFalse(acceptance['scope']['generalized_to_unconfirmed_types'])
        self.assertFalse(acceptance['scope']['probe_success_used_as_generated_flow_success'])
        self.assertFalse(acceptance['overall']['github_write'])

    def test_r5_g2_two_positive_runs_match_fixed_typed_contract(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5-G2'
        results = []
        for run in ['run1', 'run2']:
            with self.subTest(run=run):
                result = typed_transfer.verify_output(cycle / run / 'result.xlsx', run)
                self.assertEqual(result['status'], 'MATCH_FIXED_EX02_TEXT_NUMBER_SCOPE')
                self.assertEqual(len(result['mappings']), 12)
                self.assertEqual(result['mismatches'], [])
                self.assertTrue(result['output']['unchanged_by_verifier'])
                self.assertTrue(result['originals_unchanged_by_verifier'])
                self.assertTrue(all(item['source_matches_target'] for item in result['mappings']))
                self.assertTrue(all(item['target_actual'][0] in {'text', 'number'}
                                    for item in result['mappings']))
                results.append(result)
        two_run = typed_transfer.compare_runs(
            cycle / 'run1/result.xlsx', cycle / 'run2/result.xlsx'
        )
        self.assertEqual(two_run['status'], 'MATCH')
        self.assertTrue(two_run['semantic_equal'])
        self.assertFalse(two_run['binary_sha_equal'])
        self.assertEqual(two_run['checked_cells'], 480)

    def test_r5_g2_one_cell_type_negative_is_detected_without_hiding_558(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5-G2'
        negative = cycle / 'negative/result-one-type-changed.xlsx'
        build = json.loads((cycle / 'negative/build-evidence.json').read_bytes())
        comparison = new.compare(negative)
        typed = typed_transfer.verify_output(negative, 'negative')
        native = json.loads((cycle / 'negative/native-styles-vs-positive.json').read_bytes())
        render = json.loads((cycle / 'negative/render-equivalence.json').read_bytes())
        self.assertEqual(build['semantic_delta_count'], 1)
        self.assertEqual(build['fixed_change']['sheet'], 'Target A')
        self.assertEqual(build['fixed_change']['cell'], 'D4')
        self.assertEqual(build['fixed_change']['before'], ['number', 12.5])
        self.assertEqual(build['fixed_change']['after'], ['text', '12.5'])
        self.assertTrue(build['fixed_change']['same_display_text'])
        self.assertTrue(build['fixed_change']['style_unchanged'])
        self.assertEqual(build['package_payload']['changed_members'], ['xl/worksheets/sheet2.xml'])
        self.assertEqual(comparison['failure_counts']['values_types_positions'], 1)
        self.assertEqual(comparison['failure_counts']['styles'], 480)
        self.assertEqual(comparison['failure_counts']['row_dimensions'], 48)
        self.assertEqual(comparison['failure_counts']['column_dimensions'], 30)
        self.assertEqual(len(comparison['legacy']['failures']), 559)
        self.assertEqual(comparison['checks']['outside_values_types_formulas']['mismatches'], [])
        self.assertEqual(len(typed['mismatches']), 1)
        self.assertEqual(typed['mismatches'][0]['target_cell'], 'D4')
        self.assertEqual(native['status'], 'MATCH_WITHIN_RECORDED_SCOPE')
        self.assertTrue(render['render_bytes_equal'])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'negative.xlsx'
            rebuilt = negative_builder.build(cycle / 'run2/result.xlsx', destination)
            self.assertEqual(rebuilt['semantic_delta_count'], 1)
            self.assertEqual(rebuilt['fixed_change']['after'], ['text', '12.5'])

    def test_r5_g2_legacy_558_are_classified_without_rewriting_old_fail(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX02-r5-G2'
        reconciliation = cycle / 'format-reconciliation'
        result = json.loads((reconciliation / 'classification.json').read_bytes())
        old_acceptance = json.loads((cycle / 'acceptance-status.json').read_bytes())
        self.assertFalse(old_acceptance['overall']['accepted'])
        self.assertEqual(old_acceptance['legacy_558']['status'], 'UNRESOLVED_AND_VISIBLE')
        self.assertEqual(result['old_fail_preserved']['sha256'],
                         hashlib.sha256((cycle / 'acceptance-status.json').read_bytes()).hexdigest())
        self.assertEqual(result['legacy_failure_counts'], {
            'cell_style': 480,
            'column_dimension': 30,
            'row_dimension': 48,
        })
        self.assertEqual(result['classification_counts'], {
            'SERIALIZATION_OR_COMPARISON_METHOD_ONLY': 558,
        })
        self.assertEqual(len(result['entries']), 558)
        self.assertTrue(all(item['raw_change_reproduced_by_noop_and_run2']
                            for item in result['entries']))
        self.assertTrue(all(item['effective_before_sha256'] == item['effective_after_sha256']
                            for item in result['entries']))
        self.assertTrue(all(item['effective_changed_attributes'] == []
                            for item in result['entries']))
        self.assertEqual(result['decision']['actual_effective_changes_in_positive_outputs'], 0)
        self.assertEqual(result['decision']['unresolved_legacy_failures'], 0)
        self.assertEqual(result['decision']['functional_g2_status_preserved'],
                         'PASS_FIXED_EX02_TEXT_NUMBER_SCOPE')
        self.assertEqual(result['decision']['existing_output_guard_live_check'],
                         'NOT_RUN_REMAINS_OPEN')
        self.assertEqual(result['negative_detection']['status'],
                         'PASS_EXACT_THREE_EFFECTIVE_CHANGES')
        negative_differences = result['negative_detection']['effective_differences']
        self.assertEqual(
            {(item['category'], item['sheet'], str(item['location']), item['attribute'])
             for item in negative_differences},
            {
                ('cell_style', 'Target A', 'C4', 'fill'),
                ('row_dimension', 'Target A', '2', 'height'),
                ('column_dimension', 'Target A', '2', 'width'),
            },
        )
        self.assertEqual(
            typed_transfer.verify_output(
                reconciliation / 'negative-format-dimensions.xlsx', 'format-negative'
            )['status'],
            'MATCH_FIXED_EX02_TEXT_NUMBER_SCOPE',
        )
        positive_snapshot_hashes = set()
        for name in ['noop-effective.json', 'run1-effective.json', 'run2-effective.json']:
            native = json.loads((reconciliation / name).read_bytes())
            self.assertEqual(native['status'], 'MATCH_EFFECTIVE_FORMAT')
            self.assertEqual(native['differences'], [])
            self.assertEqual(native['snapshot_sha256']['reference'],
                             native['snapshot_sha256']['output'])
            positive_snapshot_hashes.add(native['snapshot_sha256']['reference'])
        self.assertEqual(positive_snapshot_hashes,
                         {result['positive_effective_snapshot_sha256']})
        with tempfile.TemporaryDirectory() as directory:
            rerun = format_classifier.classify(Path(directory) / 'classification.json')
            self.assertEqual(rerun['decision']['status'],
                             'PASS_558_CLASSIFIED_AS_NON_EFFECTIVE_NORMALIZATION')


if __name__ == '__main__':
    unittest.main(verbosity=2)
