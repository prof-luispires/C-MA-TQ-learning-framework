"""E3-R67: verifica reproducibilidade de inferência dos checkpoints E3-R66.
Não treina, não modifica checkpoints e não produz resultados confirmatórios.
"""
import argparse, hashlib, json, pickle, pathlib, sys, time
import numpy as np
import pandas as pd
from core import inference as inf
from core.evaluation import evaluate as frozen_evaluate
ROOT=pathlib.Path(__file__).resolve().parent
VARIANTS=('central','four_q','no_phy','no_protocol','permuted_q')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--data',default=str(ROOT/'data'/'test.csv.gz'));parser.add_argument('--output',default=str(ROOT/'results'/'checkpoint_verification.json'));args=parser.parse_args()
 data_path=pathlib.Path(args.data);d=pd.read_csv(data_path)
 if d.duplicated(['episode_id','t']).any():raise ValueError('Duplicate episode_id,t')
 if not {'episode_id','t','scenario','onset'}.issubset(d):raise ValueError('Missing episode fields')
 report={'status':'PASS','dataset':str(data_path),'dataset_sha256':sha(data_path),'episodes':int(d.episode_id.nunique()),'rows':len(d),'checkpoints':[], 'limitations':['Data are previously explored synthetic episodes; not an independent test.', 'Legacy E3-R66 permuted_q checkpoint cannot be verified; E3-R68 requires retraining it with persisted mapping.', 'The supplied Windows results.zip used 200 episodes, whereas the bundled test.csv.gz contains 175; no cross-dataset identity is claimed.']}
 for variant in VARIANTS:
  path=ROOT/'models'/f'{variant}_seed42.pkl'
  if not path.exists():raise FileNotFoundError(path)
  with open(path,'rb') as f:art=pickle.load(f) # local trusted checkpoints only
  if art.get('schema_version')!='E3-R66-v1':raise ValueError('Checkpoint schema mismatch')
  df=d.copy(); missing=[]
  for feature in art['features']:
   if feature not in df:missing.append(feature);continue
   values=pd.to_numeric(df[feature],errors='coerce')
   if np.isinf(values.to_numpy()).any():raise ValueError('Infinite values in '+feature)
   df['b_'+feature]=np.searchsorted(np.asarray(art['quantiles'][feature]),values.fillna(art['medians'][feature]).to_numpy(),side='right').astype('int8')
  if missing:raise ValueError('Missing features: '+str(missing))
  inf.CAL.clear();inf.CAL.update(art['calibration']);inf.PERM_MAP.clear()
  es=inf.episodes(df)
  if variant=='permuted_q':
   mapping=art.get('permutation_episode_map')
   if not mapping: raise ValueError('Legacy permuted_q checkpoint lacks permutation map; rerun development to regenerate it.')
   if art.get('permutation_dataset_sha256')!=sha(data_path): raise ValueError('Permuted checkpoint requires exact test dataset hash')
   by_id={str(e['id']):e for e in es}
   for e in es:
    target=mapping.get(str(e['id']))
    if target not in by_id: raise ValueError('Missing mapped episode '+str(target))
    inf.PERM_MAP[e['id']]=by_id[target]
    if e['n']!=by_id[target]['n']:raise ValueError('Permuted episodes have incompatible lengths')
  tic=time.perf_counter();p1=inf.evaluate(es,art['policy'],art['mode'],art['local_policies'],art['ablate']);elapsed=time.perf_counter()-tic
  # Force a fresh read of the checkpoint and repeat inference.
  with open(path,'rb') as f:art2=pickle.load(f)
  inf.CAL.clear();inf.CAL.update(art2['calibration']);inf.PERM_MAP.clear()
  if variant=='permuted_q':
   by_id={str(e['id']):e for e in es}
   inf.PERM_MAP.update({e['id']:by_id[art2['permutation_episode_map'][str(e['id'])]] for e in es})
  p2=inf.evaluate(es,art2['policy'],art2['mode'],art2['local_policies'],art2['ablate'])
  cols=['episode_id','pred','t','inspections','reward']
  equal=p1[cols].equals(p2[cols]); metrics=frozen_evaluate(p1)
  report['checkpoints'].append({'variant':variant,'checkpoint_sha256':sha(path),'identical_after_reload':bool(equal),'episodes':len(p1),'inference_seconds':round(elapsed,6),'metrics_diagnostic':metrics})
  print(variant,'PASS' if equal else 'FAIL','episodes',len(p1),'MCC',round(metrics['mcc'],4),flush=True)
  if not equal:report['status']='FAIL'
 out=pathlib.Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
 print('Report:',out)
 if report['status']!='PASS':sys.exit(1)
if __name__=='__main__':main()
