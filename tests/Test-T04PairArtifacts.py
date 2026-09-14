import importlib.util, json, pathlib, shutil, sys, uuid
sys.dont_write_bytecode = True

root = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('pair_artifacts', root / 'tools/Verify-T04PairArtifacts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = root / 'catalog/evidence/t04-independent-pair-20260914w'
assert module.verify(root, source, 1)['status'] == 'PASS'
assert module.verify(root, source, 2)['status'] == 'PASS'
work = root / '.work' / ('test-t04-artifacts-' + uuid.uuid4().hex)
work.mkdir()
for case in ['missing_xlsx', 'wrong_run', 'changed_sha', 'wrong_expectation', 'not_completed']:
    target = work / case
    target.mkdir()
    shutil.copy2(source / 'plan.json', target / 'plan.json')
    shutil.copy2(source / 'run1-observation.json', target / 'run1-observation.json')
    shutil.copytree(source / 'run1', target / 'run1')
    file = target / 'run1/normal-chat-t04-output-independent-20260914e.xlsx.gate.json'
    if case == 'missing_xlsx':
        p = target / 'run1/normal-chat-t04-output-independent-20260914e.xlsx'
        assert p.resolve().is_relative_to(work.resolve())
        p.rename(p.with_suffix('.withheld'))
    else:
        if case == 'wrong_expectation': file = target / 'plan.json'
        if case == 'not_completed': file = target / 'run1-observation.json'
        data = json.loads(file.read_text(encoding='utf-8-sig'))
        if case == 'wrong_run': data['run_number'] = 2
        if case == 'changed_sha': data['snapshot_sha256'] = '0' * 64
        if case == 'wrong_expectation': data['expected_cells'][0][2] = 99
        if case == 'not_completed': data['completion_observed'] = False
        file.write_text(json.dumps(data), encoding='utf-8')
    try:
        module.verify(root, target, 1)
    except (AssertionError, FileNotFoundError):
        pass
    else:
        raise AssertionError('Accepted negative control: ' + case)
print('PASS: 2 live-snapshot reads and 5 artifact rejection controls; no workbook edits or native calls')
