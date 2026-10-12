import ast
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from transformers import AutoTokenizer  # Load native extensions once before module isolation.

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'data/evaluation/granite-dependency-20261012'
OLD=ROOT/'data/evaluation/dependency-generalization-20261012'


def load(folder):
    with patch.dict(sys.modules),patch.object(sys,'path',[str(folder),*sys.path]):
        for name in ('prompts','base_prompts','dependency_prompt','legacy_prompts','configs','evidence','selection'):
            sys.modules.pop(name,None)
        spec=importlib.util.spec_from_file_location('test_native_runner',folder/'run_batch.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module


class GraniteDependencyTests(unittest.TestCase):
    def test_inputs_prompt_and_schema_are_byte_identical_to_control(self):
        for name in ('pairs.jsonl','context-snapshots.json','prompts.py','base_prompts.py','dependency_prompt.py','legacy_prompts.py','configs.py','evidence.py','selection.py','summarize.py'):
            self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes(),name)

    def test_payload_only_changes_model_and_native_template_eos(self):
        old,new=load(OLD),load(HERE)
        snapshots=json.loads((HERE/'context-snapshots.json').read_text())
        for pair in map(json.loads,(HERE/'pairs.jsonl').read_text().splitlines()):
            for arm in ('NO-SOURCE','WITH-SOURCE'):
                control=old.payload_for('control',arm,pair,snapshots[pair['id']])
                candidate=new.payload_for('granite',arm,pair,snapshots[pair['id']])
                self.assertEqual(candidate.pop('chat_template_kwargs'),{'thinking':False})
                self.assertEqual(candidate.pop('stop_token_ids'),[0])
                candidate['model']='control'
                self.assertEqual(control,candidate)

    def test_parser_logic_is_unchanged(self):
        functions=[]
        for folder in (OLD,HERE):
            tree=ast.parse((folder/'run_batch.py').read_text())
            functions.append(ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse')))
        self.assertEqual(*functions)


if __name__=='__main__':
    unittest.main()
