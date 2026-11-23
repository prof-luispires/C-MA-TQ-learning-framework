"""E3-R68: integrity and policy-collapse audit; no training or scientific claims."""
from pathlib import Path
import json, hashlib, pickle, collections
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parent
V=['central','four_q','no_phy','no_protocol','permuted_q']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report={'status':'PASS','purpose':'development diagnostic, NOT independent validation','datasets':{},'policies':{},'comparisons':{},'warnings':[]}
 for part in ['train','test']:
  p=ROOT/'data'/f'{part}.csv.gz'; d=pd.read_csv(p)
  required=['episode_id','t','scenario','onset','rssi','snr','delta_t_derived','counter_step_derived','c2','c8','c9','c15']
  missing=[c for c in required if c not in d]
  if missing:raise ValueError(f'{part}: missing {missing}')
  duplicate=int(d.duplicated(['episode_id','t']).sum())
  lengths=d.groupby('episode_id').size()
  inconsistent=int(sum(g.scenario.nunique()!=1 or g.onset.nunique()!=1 for _,g in d.groupby('episode_id')))
  report['datasets'][part]={'sha256':sha(p),'rows':len(d),'episodes':int(d.episode_id.nunique()),'scenario_counts':{str(k):int(v) for k,v in d.groupby('scenario').episode_id.nunique().items()},'duplicate_episode_t':duplicate,'inconsistent_episode_metadata':inconsistent,'min_episode_length':int(lengths.min()),'max_episode_length':int(lengths.max())}
  if duplicate or inconsistent:report['status']='FAIL'
 preds=ROOT/'results'/'predictions_by_episode.csv'
 if preds.exists():
  df=pd.read_csv(preds)
  for seed,ds in df.groupby('seed'):
   by={v:d.set_index('episode_id') for v,d in ds.groupby('variant')}
   for i,a in enumerate(V):
    for b in V[i+1:]:
     if a not in by or b not in by:continue
     shared=by[a].index.intersection(by[b].index)
     if len(shared)==0:continue
     x,y=by[a].loc[shared],by[b].loc[shared]
     agree=float((x.pred.to_numpy()==y.pred.to_numpy()).mean())
     exact=float(((x.pred.to_numpy()==y.pred.to_numpy()) & (x.t.to_numpy()==y.t.to_numpy()) & (x.inspections.to_numpy()==y.inspections.to_numpy())).mean())
     report['comparisons'][f'seed{seed}:{a}__{b}']={'shared_episodes':len(shared),'prediction_agreement':agree,'full_decision_agreement':exact}
     if a=='central' and b=='four_q' and exact==1:report['warnings'].append(f'Seed {seed}: central and four_q produce identical decisions; investigate learning and action distributions')
 for v in V:
  p=ROOT/'models'/f'{v}_seed42.pkl'
  if not p.exists():continue
  with p.open('rb') as f:art=pickle.load(f) # local trusted checkpoints only
  policy=art['policy'];actions=collections.Counter(k[1] for k in policy)
  report['policies'][v]={'checkpoint_sha256':sha(p),'q_state_action_entries':len(policy),'q_action_entry_counts':dict(actions),'local_policy_entries':{k:len(q) for k,q in art['local_policies'].items()},'permutation_map_persisted':bool(art.get('permutation_episode_map'))}
  if v=='permuted_q' and not art.get('permutation_episode_map'):report['warnings'].append('Legacy permuted_q checkpoint has no persisted map; retrain before verification')
 path=ROOT/'results'/'framework_audit.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8');print(json.dumps({'status':report['status'],'datasets':report['datasets'],'warnings':report['warnings']},indent=2));print('Saved',path)
 if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
