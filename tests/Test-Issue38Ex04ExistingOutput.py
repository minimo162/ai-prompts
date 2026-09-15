"""Regression checks for the one-run EX04 existing-output live negative."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'catalog/acceptance/issue38'
G2 = BASE / 'cycles/EX02-r5-G2'
CYCLE = BASE / 'cycles/EX04-r5-G2-existing-output-neg1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(name):
    return json.loads((CYCLE / name).read_text(encoding='utf-8'))


class Ex04ExistingOutputTests(unittest.TestCase):
    def test_unmodified_g2_robin_has_the_guard_before_all_excel_actions(self):
        robin = G2 / 'generated.robin'
        self.assertEqual(
            sha(robin),
            '0829526420158a61146e5d3fde7c4a5cc035228e2ab98be96d9697aa64d457bd',
        )
        lines = robin.read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(lines), 87)
        self.assertEqual(lines[0], "SET TransferState TO $'''NOT_STARTED'''")
        self.assertIn('File.IfFile.Exists', lines[1])
        self.assertEqual(lines[2].strip(), "SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''")
        self.assertEqual(lines[3], 'ELSE')
        self.assertEqual(lines[-1], 'END')
        excel_indexes = [index for index, line in enumerate(lines) if 'Excel.' in line]
        self.assertTrue(excel_indexes)
        self.assertTrue(all(3 < index < len(lines) - 1 for index in excel_indexes))
        self.assertEqual(sum('Excel.SaveExcel.SaveAs' in line for line in lines), 1)

    def test_live_run_is_a_separate_single_negative_with_direct_observation(self):
        plan = read_json('plan.json')
        observation = read_json('pad-run-observation.json')
        self.assertEqual(plan['test_id'], 'EX04-R5-G2-EXISTING-OUTPUT-NEG1')
        self.assertTrue(plan['relationship']['separate_from_positive_run_ids'])
        self.assertFalse(plan['relationship']['positive_runs_reused_as_this_result'])
        self.assertFalse(plan['relationship']['format_558_reinvestigated'])
        self.assertEqual(plan['limits']['max_pad_runs'], 1)
        self.assertEqual(observation['runtime']['run_requests_used'], 1)
        self.assertEqual(observation['runtime']['run_request_limit'], 1)
        self.assertFalse(observation['runtime']['retry_issued'])
        self.assertEqual(observation['runtime']['action_count_visible'], 87)
        self.assertEqual(
            observation['direct_branch_observation']['full_value_in_pad_variable_dialog'],
            'OUTPUT_EXISTS_NO_WRITE',
        )
        self.assertTrue(observation['direct_branch_observation']['guard_branch_entered'])
        self.assertEqual(observation['direct_terminal_observation']['status_bar'], 'Ready')
        self.assertTrue(observation['direct_terminal_observation']['run_button_enabled'])
        self.assertTrue(observation['direct_terminal_observation']['stop_button_disabled'])
        self.assertFalse(observation['direct_terminal_observation']['design_or_runtime_error_observed'])
        self.assertFalse(observation['write_save_path']['entered'])

    def test_output_inputs_template_and_work_are_byte_unchanged(self):
        expected_output = '826d09ab3b5818326fa0dedac0af8a87f74057f4431e29e8a59c72ca7e08fda9'
        hashes = read_json('hashes-after-live-run.json')
        cleanup = read_json('cleanup.json')
        self.assertTrue(hashes['all_required_files_unchanged'])
        for record in hashes['files'].values():
            self.assertTrue(record['unchanged'])
            self.assertEqual(record['sha256_before'], record['sha256_after'])
        self.assertEqual(sha(CYCLE / 'existing-output-before.xlsx'), expected_output)
        self.assertEqual(sha(CYCLE / 'existing-output-after.xlsx'), expected_output)
        self.assertTrue(cleanup['archives_byte_identical'])
        self.assertFalse(cleanup['runtime_result_exists_after_cleanup'])
        self.assertFalse((BASE / 'runs/EX02-attempt1/result.xlsx').exists())
        self.assertEqual(
            sha(BASE / 'runs/EX02-attempt1/work.xlsx'),
            '0e3cf3b1c9e6e73e835c324b71602b50f708df689944a3760e4b411959f3b457',
        )
        self.assertEqual(
            sha(BASE / 'fixtures/EX02/input-a.xlsx'),
            'f655b62c82750fc07f4e54bcfd098e8e7c0b771c9422c4321cc413a4d6d07fa9',
        )
        self.assertEqual(
            sha(BASE / 'fixtures/EX02/input-b.xlsx'),
            '69627e161747fedad0f7c3b410c1d625b29a553786be0c145e83aaf43d1b105a',
        )
        self.assertEqual(
            sha(BASE / 'fixtures/EX02/template.xlsx'),
            '0e3cf3b1c9e6e73e835c324b71602b50f708df689944a3760e4b411959f3b457',
        )

    def test_direct_screenshots_and_protected_files_are_preserved(self):
        observation = read_json('pad-run-observation.json')
        for record in observation['screenshots'].values():
            path = ROOT / record['path']
            self.assertTrue(path.is_file())
            self.assertEqual(sha(path), record['sha256'])
        protected = {
            G2 / 'pad-import-and-recopy.json':
                '00656f74d81469be15add5fe6927e88fa0032f1d896d73bd70b02216b6bfa7ad',
            G2 / 'acceptance-status.json':
                '634298a3619039ff2e2fad0028e407e71b29ced8749bbbe6788176476b257292',
            G2 / 'run1/result.xlsx':
                'c678ae701725716d62aa945d73e341e0122db7e37a4ad35bc670108aeab68325',
            G2 / 'run2/result.xlsx':
                '826d09ab3b5818326fa0dedac0af8a87f74057f4431e29e8a59c72ca7e08fda9',
            ROOT / 'copilot/versions/20260915-excel-r5/agent-instructions.txt':
                'fe57e45c170fcdfe8f94d8e23f9cb58f00d5b54ae4abe35a43189767032b5aaa',
            ROOT / 'copilot/versions/20260915-excel-r5/knowledge/PAD-Robin-Knowledge-Bundle.txt':
                '2a0a420d9e9839f9ffe3923c43c85e37678d4f14af9b3e204fa3346cddcc57a3',
            ROOT / 'copilot/versions/20260915-excel-r5/manifest.json':
                '1ffacd9f478346fb38b146f135e19fd743d2b9a0ce1ab85d8b6b452899dcfd89',
        }
        for path, expected in protected.items():
            self.assertEqual(sha(path), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
