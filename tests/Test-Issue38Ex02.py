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


if __name__ == '__main__':
    unittest.main(verbosity=2)
