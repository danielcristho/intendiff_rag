"""Audit every frozen D89 input against Granite's pinned native tokenizer."""
import json
from pathlib import Path
from transformers import AutoTokenizer
from prompts import ARMS,build

HERE=Path(__file__).resolve().parent
model=json.loads((HERE/'model.json').read_text())
tokenizer=AutoTokenizer.from_pretrained(model['path'],local_files_only=True,trust_remote_code=False)
snapshots=json.loads((HERE/'context-snapshots.json').read_text())
rows=[]
for pair in map(json.loads,(HERE/'pairs.jsonl').read_text().splitlines()):
 for arm in ARMS:
  tokens=tokenizer.apply_chat_template(build(arm,pair,snapshots[pair['id']]),tokenize=True,add_generation_prompt=True,thinking=False)['input_ids']
  rows.append({'pair_id':pair['id'],'arm':arm,'prompt_tokens':len(tokens)})
maximum=max(r['prompt_tokens'] for r in rows)
context=32768 if maximum+2048<=32768 else 49152
assert maximum+2048<=context<=json.loads((Path(model['path'])/'config.json').read_text())['max_position_embeddings']
result={'pairs':15,'generations':30,'max_prompt_tokens':maximum,'max_model_len':context,
 'kv_cache_memory_bytes':6442450944 if context==32768 else 8589934592,
 'chat_template_kwargs':{'thinking':False},'stop_token_ids':[0],
 'input_truncation_added':False,'rows':rows}
(HERE/'preflight.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
