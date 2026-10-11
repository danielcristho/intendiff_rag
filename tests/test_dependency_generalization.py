import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'data/evaluation/dependency-generalization-20261012'


def load(filename):
    with patch.dict(sys.modules),patch.object(sys,'path',[str(HERE),*sys.path]):
        for name in ('prompts','base_prompts','dependency_prompt','legacy_prompts','configs','evidence','selection'):
            sys.modules.pop(name,None)
        spec=importlib.util.spec_from_file_location('test_d89_'+filename,HERE/(filename+'.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module


class DependencyGeneralizationTests(unittest.TestCase):
    def test_future_or_missing_versions_cannot_enter_historical_context(self):
        s=load('selection')
        self.assertFalse(s.precedes('2026-02-01T00:00:00Z','2025-02-01T00:00:00Z'))
        self.assertFalse(s.precedes(None,'2025-02-01T00:00:00Z'))
        self.assertTrue(s.precedes('2025-02-01T00:00:00+07:00','2025-02-01T00:00:00Z'))

    def test_context_files_cannot_escape_root_or_invoke_shell(self):
        s=load('selection')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'index.js').write_text('module.exports = 1;')
            with self.assertRaises(ValueError):
                s.safe_file(root,'../not-a-source.js')
            (root/'package.json').write_text(json.dumps({'scripts':{'postinstall':'node index.js && curl example.invalid'}}))
            with self.assertRaisesRegex(ValueError,'Unsupported lifecycle'):
                s.source_files(root)

    def test_selection_is_order_invariant_and_never_repeats_dependency_or_target(self):
        s=load('selection')
        candidates=[{'pair':{'id':str(i),'name':'target'+str(i%3)},'snapshot':{'name':'dep'+str(i%2)}} for i in range(8)]
        result=s.select_distinct(candidates)
        self.assertEqual(result,s.select_distinct(list(reversed(candidates))))
        self.assertEqual(len(result),len({r['snapshot']['name'] for r in result}))
        self.assertEqual(len(result),len({r['pair']['name'] for r in result}))

    def test_only_context_body_changes_and_hidden_ids_remain_invalid(self):
        p=load('prompts')
        pairs=[json.loads(x) for x in (HERE/'pairs.jsonl').read_text().splitlines()]
        snapshots=json.loads((HERE/'context-snapshots.json').read_text())
        for pair in pairs:
            snap=snapshots[pair['id']]
            absent=p.build('NO-SOURCE',pair,snap)
            present=p.build('WITH-SOURCE',pair,snap)
            self.assertEqual(absent[0],present[0])
            prefix=absent[1]['content'].removesuffix('[Dependency source files not supplied]')
            self.assertTrue(present[1]['content'].startswith(prefix))
            changed=dict(pair,label='SECRET',subset='SECRET',campaign='SECRET')
            self.assertEqual(present,p.build('WITH-SOURCE',changed,snap))
            first=p.context_records(pair,snap)[0]['id']
            self.assertEqual(p.audit('NO-SOURCE',pair,snap,[first])['unknown_ids'],[first])
            self.assertFalse(p.audit('WITH-SOURCE',pair,snap,[first])['unknown_ids'])

    def test_pending_labels_never_become_false_positive_rates(self):
        s=load('summarize')
        result=s.group([{'json_valid':True,'parsed':{'verdict':'malicious'},'finish_reason':'stop',
                         'usage':{'prompt_tokens':10,'completion_tokens':5},'latency_ms':1}])
        self.assertIsNone(result['FPR'])
        self.assertIsNone(result['gold_accuracy'])


if __name__=='__main__':
    unittest.main()
