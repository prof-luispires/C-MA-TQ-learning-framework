"""Zero-shot on independently mapped episode CSV. Requires verified ground truth.
Only load model pickle files produced locally by this framework; pickle is unsafe for untrusted files.
"""
import argparse, ast, pickle, pathlib, sys, json, time
import pandas as pd
import numpy as np
from core.evaluation import evaluate
ROOT=pathlib.Path(__file__).resolve().parent
FEATURES=['rssi','snr','delta_t_derived','c2','c8','c9','c15','counter_step_derived']
REQUIRED=set(FEATURES+['episode_id','t','scenario','onset'])
def load_policy_functions():
    # Use a separate module containing only the shared inference functions.
    import core.inference as m
    return m

def run(csv,model,out):
    with open(model,'rb') as f:artifact=pickle.load(f)
    if artifact.get('schema_version')!='E3-R66-v1':raise ValueError('Unsupported checkpoint')
    d=pd.read_csv(csv)
    missing=REQUIRED-set(d.columns)
    if missing:raise ValueError('Missing required fields: '+str(sorted(missing)))
    if d.duplicated(['episode_id','t']).any():raise ValueError('Duplicate episode and time')
    if d[FEATURES+['t','onset']].isna().any().any():raise ValueError('Missing features/labels; no silent imputation')
    if not np.isfinite(d[FEATURES+['t','onset']].to_numpy(dtype=float)).all():raise ValueError('Nonfinite values')
    if (d.groupby('episode_id')['scenario'].nunique()>1).any():raise ValueError('Mixed scenario in episode')
    if (d.groupby('episode_id')['onset'].nunique()>1).any():raise ValueError('Mixed onset in episode')
    if not all(g.t.is_monotonic_increasing for _,g in d.groupby('episode_id',sort=False)):raise ValueError('Nonmonotonic timestamps')
    if not all((g.t.to_numpy()==np.arange(len(g))).all() for _,g in d.groupby('episode_id',sort=False)):raise ValueError('t must be zero-based message index, contiguous')
    if not all((g.onset.iloc[0]>=0 and g.onset.iloc[0]<=len(g)) for _,g in d.groupby('episode_id')):raise ValueError('Invalid onset')
    # Onset for normal episodes must be episode length; for attack episodes must be < length.
    for _,g in d.groupby('episode_id'):
        is_normal=str(g.scenario.iloc[0]).lower()=='normal'
        if is_normal!=(int(g.onset.iloc[0])==len(g)):raise ValueError('Inconsistent scenario/onset')
    for f in FEATURES:
        d['b_'+f]=np.searchsorted(np.asarray(artifact['quantiles'][f]),d[f].to_numpy(),side='right').astype('int8')
    m=load_policy_functions();m.CAL.clear();m.CAL.update(artifact['calibration'])
    es=m.episodes(d); tic=time.perf_counter()
    result=m.evaluate(es,artifact['policy'],artifact['mode'],artifact['local_policies'],artifact['ablate'])
    duration=time.perf_counter()-tic
    result['seed']=artifact['seed'];result['variant']=artifact['variant'];result.to_csv(out,index=False)
    stats=evaluate(result)
    summary={'source':str(csv),'checkpoint':str(model),'confirmatory':False,'warning':'Dataset provenance, labels and non-overlap must be independently verified','seconds':duration,'metrics':stats}
    pathlib.Path(str(out)+'.json').write_text(json.dumps(summary,indent=2,default=lambda x:float(x) if hasattr(x,'item') else str(x)),encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--csv',required=True);p.add_argument('--model',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.csv,a.model,a.output)
