"""E3-R71: read-only counterfactual and Q coverage audit; synthetic development only."""
import ast, copy, hashlib, json, pickle, random
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
source=(P/'core'/'r70_engine.py').read_text(encoding='utf-8')
tree=ast.parse(source)
# Import only definitions and data preparation. Never execute the training loop.
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in node.targets))
module=ast.Module(body=tree.body[:stop],type_ignores=[])
ns={'__file__':str(P/'core'/'r70_engine.py'),'__name__':'r71_readonly'}
exec(compile(module,str(P/'core'/'r70_engine.py'),'exec'),ns)
variants=['central','four_q','no_phy','no_protocol','permuted_q']
report={'status':'PASS','purpose':'exploratory synthetic diagnostic; NOT independent validation','dataset_sha256':hashlib.sha256((P/'data'/'test.csv.gz').read_bytes()).hexdigest(),'episodes':len(ns['te']),'models':{},'comparisons':{},'warnings':[]}
for label in variants:
 path=P/'models'/f'{label}_seed42.pkl'
 if not path.exists():report['status']='INCOMPLETE';report['warnings'].append(f'Missing checkpoint {path.name}');continue
 with path.open('rb') as f:artifact=pickle.load(f) # trusted bundled checkpoint only
 mode=artifact['mode'];ablate=artifact.get('ablate');q=artifact['policy'];lq=artifact['local_policies']
 ns['CAL'].clear();ns['CAL'].update(artifact['calibration']);ns['PERM_MAP'].clear()
 if mode=='permuted':
  ids=artifact.get('permutation_episode_map')
  if not ids:
   report['warnings'].append('permuted_q has no persisted map: skip replay/counterfactual')
   report['models'][label]={'checkpoint_present':True,'permutation_map_persisted':False,'evaluation_skipped':True};continue
  index={str(e['id']):e for e in ns['te']}
  missing=[k for k,v in ids.items() if k in index and v not in index]
  if missing:report['status']='INCOMPLETE';report['warnings'].append('permutation map refers to unavailable test episodes');continue
  ns['PERM_MAP'].update({e['id']:index[ids[str(e['id'])]] for e in ns['te'] if str(e['id']) in ids})
 original=ns['coord_state']
 counts={'decision_steps':0,'post_inspection_steps':0,'post_inspection_any_learned':0,'post_inspection_all_actions_learned':0,'post_inspection_unseen_all':0,'action_counts':{'0':0,'1':0,'2':0},'unique_post_states':set()}
 def instrument(e,t,ins,m,l,ablate=None):
  s=original(e,t,ins,m,l,ablate)
  counts['decision_steps']+=1
  if ins:
   counts['post_inspection_steps']+=1;counts['unique_post_states'].add(str(s))
   actions=ns['acts'](t,ins)
   learned=[(s,a) in q for a in actions]
   counts['post_inspection_any_learned']+=int(any(learned))
   counts['post_inspection_all_actions_learned']+=int(all(learned))
   counts['post_inspection_unseen_all']+=int(not any(learned))
  return s
 ns['coord_state']=instrument
 base=ns['evaluate'](ns['te'],q,mode,lq,ablate)
 ns['coord_state']=original
 for action,n in base['pred'].value_counts().items():pass
 base_key=list(zip(base['pred'].astype(int),base['t'].astype(int),base['inspections'].astype(int)))
 item={k:v for k,v in counts.items() if k!='unique_post_states'}
 item.update({'checkpoint_present':True,'permutation_map_persisted':bool(artifact.get('permutation_episode_map')),'unique_post_states':len(counts['unique_post_states']),'base_metrics':ns['metrics'](base),'counterfactuals':{}})
 if mode=='central':
  report['models'][label]=item;continue
 # Counterfactual state perturbations: after inspection only. No training or label access.
 specialists=[n for n in ns['G'] if n!=ablate]
 for specialist in specialists:
  idx=specialists.index(specialist)
  for replacement in [0,3]:
   def perturb(e,t,ins,m,l,ablate=None):
    s=original(e,t,ins,m,l,ablate)
    if not ins:return s
    v=list(s);v[4+idx]=replacement;return tuple(v)
   ns['coord_state']=perturb
   altered=ns['evaluate'](ns['te'],q,mode,lq,ablate)
   alt_key=list(zip(altered['pred'].astype(int),altered['t'].astype(int),altered['inspections'].astype(int)))
   item['counterfactuals'][f'{specialist}_to_{replacement}']={'episodes_changed':sum(a!=b for a,b in zip(base_key,alt_key)),'predictions_changed':sum(a[0]!=b[0] for a,b in zip(base_key,alt_key)),'mcc':ns['metrics'](altered)['mcc'],'fpr':ns['metrics'](altered)['fpr']}
   ns['coord_state']=original
 report['models'][label]=item
# Compare actual episode decisions rather than only aggregate metrics; no claims of significance.
for label,item in report['models'].items():
 if item.get('post_inspection_steps',0) and not item['post_inspection_any_learned']:
  report['warnings'].append(f'{label}: no visited post-inspection state/action has learned Q')
 if item.get('counterfactuals') and all(x['episodes_changed']==0 for x in item['counterfactuals'].values()):
  report['warnings'].append(f'{label}: tested post-inspection signal interventions did not alter decisions')
(P/'results').mkdir(exist_ok=True)
output=P/'results'/'r71_counterfactual_audit.json'
output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'status':report['status'],'episodes':report['episodes'],'models':{k:{'post_inspection_steps':v.get('post_inspection_steps'),'post_inspection_any_learned':v.get('post_inspection_any_learned'),'changed_interventions':sum(x['episodes_changed']>0 for x in v.get('counterfactuals',{}).values())} for k,v in report['models'].items()},'warnings':report['warnings']},indent=2))
print('Saved:',output)
