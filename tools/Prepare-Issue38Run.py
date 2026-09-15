"""Create only a new synthetic work copy and answer-free request. Never runs PAD."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil

module=importlib.util.spec_from_file_location('oracle',Path(__file__).with_name('Verify-Issue38Excel.py'))
oracle=importlib.util.module_from_spec(module); module.loader.exec_module(oracle)


def prepare(case_id, directory):
    spec=oracle.case_spec(case_id)
    directory=Path(directory).resolve()
    allowed=(oracle.BASE/'runs').resolve()
    if not directory.is_relative_to(allowed) or directory==allowed:
        raise ValueError('Run directory must be a new child of catalog/acceptance/issue38/runs')
    work=directory/'work.xlsx'; output=directory/spec['output']
    originals=oracle.preflight(spec,output,work)
    directory.mkdir(parents=True,exist_ok=False)
    # All later creations use exclusive mode; never overwrite a result from a previous attempt.
    with work.open('xb') as dst, (oracle.BASE/spec['template']).open('rb') as src:
        shutil.copyfileobj(src,dst)
    prep={'case':case_id,'originals':{str(p.relative_to(oracle.BASE)):oracle.sha(p) for p in originals},
          'work':str(work),'work_sha256':oracle.sha(work),'output':str(output),'pad_requested':False}
    with (directory/'preparation.json').open('x',encoding='utf-8') as f:
        json.dump(prep,f,ensure_ascii=False,indent=2)
    print(json.dumps(prep,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True,choices=['EX02','EX03'])
    parser.add_argument('--directory',required=True,type=Path)
    args=parser.parse_args(); prepare(args.case,args.directory)
