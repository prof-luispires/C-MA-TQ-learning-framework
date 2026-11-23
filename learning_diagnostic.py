"""E3-R69: checkpoint-only causal diagnostic, no retraining or test tuning."""
import json,pickle,hashlib,collections,random,sys
from pathlib import Path
import numpy as np,pandas as pd
from core import inference as I
P=Path(__file__).resolve().parent
MODELS=P/'models'; OUT=P/'results';OUT.mkdir(exist_ok=True)
VARIANTS=['central','four_q','no_phy','no_protocol','permuted_q']

def read_checkpoint(path):
    # Only load trusted, locally generated checkpoints. Pickle is executable.
    with path.open('rb') as f:return pickle.load(f)

def prepare(ck,df):
    I.med=pd.Series(ck['medians']);I.qs={k:np.asarray(v) for k,v in ck['quantiles'].items()}
    I.CAL=ck['calibration'];I.PERM_MAP={}
    return I.episodes(I.discretize(df))

def trace(e,ck,mutate=None):
    q=ck['policy'];localq=ck['local_policies'];mode=ck['mode'];ablate=ck['ablate']
    t=0;ins=False;count=0;records=[]
    for _ in range(2*e['n']+1):
        s=I.coord_state(e,t,ins,mode,localq,ablate)
        if mutate and ins and mode!='central':
            # Direct counterfactual on specialist Q signals, keeping base and others fixed.
            base=s[:4];signals=list(s[4:]);names=[n for n in I.G if n!=ablate]
            if mutate in names:signals[names.index(mutate)]=0
            s=base+tuple(signals)
        allowed=tuple(a for a in I.acts(t,ins) if a!=1 or count==0)
        seen={a:(s,a) in q for a in allowed}
        vals={a:float(q.get((s,a),0)) for a in allowed}
        a=max(allowed,key=lambda a:(vals[a],-a))
        records.append({'t':t,'ins':int(ins),'action':a,'state':str(s),'seen_actions':sum(seen.values()),'n_actions':len(allowed),'all_unseen':int(not any(seen.values())),'tie':int(sum(abs(vals[a]-vals[z])<1e-12 for z in allowed)==len(allowed)),'q_margin':max(vals.values())-sorted(vals.values())[-2] if len(vals)>1 else 0})
        if a==1:ins=True;count+=1
        elif a==2 or t==e['n']-1:break
        else:t+=1;ins=False
    return records

def main():
    df=pd.read_csv(P/'data/test.csv.gz')
    report={'status':'PASS','purpose':'diagnostic only, NOT confirmatory','test_sha256':hashlib.sha256((P/'data/test.csv.gz').read_bytes()).hexdigest(),'models':{},'comparisons':{},'warnings':[]}
    alltraces={};allfinal={}
    for name in VARIANTS:
        file=MODELS/f'{name}_seed42.pkl'
        if not file.exists():report['warnings'].append('Missing '+str(file));continue
        ck=read_checkpoint(file);es=prepare(ck,df)
        if ck['mode']=='permuted':
            report['warnings'].append('permuted_q legacy map missing: skip full evaluation, report structural checkpoint statistics only')
            report['models'][name]={'checkpoint_entries':len(ck['policy']),'permutation_map_persisted':bool(ck.get('permutation_episode_map'))}
            continue
        traces=[trace(e,ck) for e in es];alltraces[name]=traces
        d=I.evaluate(es,ck['policy'],ck['mode'],ck['local_policies'],ck['ablate']);allfinal[name]=d
        flat=[z for tr in traces for z in tr];post=[z for z in flat if z['ins']]
        byaction=collections.Counter(z['action'] for z in flat)
        result={'episodes':len(es),'decision_steps':len(flat),'action_counts':{str(k):v for k,v in sorted(byaction.items())},'inspection_fraction':float((d.inspections>0).mean()),'all_unseen_fraction':float(np.mean([z['all_unseen'] for z in flat])),'all_unseen_after_inspection_fraction':float(np.mean([z['all_unseen'] for z in post])) if post else None,'post_inspection_steps':len(post),'ties_fraction':float(np.mean([z['tie'] for z in flat])),'median_q_margin':float(np.median([z['q_margin'] for z in flat])),'unique_visited_states':len(set(z['state'] for z in flat)),'policy_entries':len(ck['policy'])}
        if ck['mode']!='central':
            cf={}
            for agent in I.G:
                if agent==ck['ablate']:continue
                changed=0
                for e,orig in zip(es,traces):
                    alt=trace(e,ck,mutate=agent)
                    if [(z['t'],z['action']) for z in alt]!=[(z['t'],z['action']) for z in orig]:changed+=1
                cf[agent]={'episodes_changed':changed,'fraction_changed':changed/len(es)}
            result['post_inspection_zero_signal_counterfactual']=cf
        report['models'][name]=result
    if 'central' in allfinal:
        ref=allfinal['central'].sort_values('episode_id').reset_index(drop=True)
        for name,d in allfinal.items():
            d=d.sort_values('episode_id').reset_index(drop=True)
            report['comparisons']['central__'+name]={'identical_final_decisions':bool(d[['episode_id','pred','t','inspections']].equals(ref[['episode_id','pred','t','inspections']])),'different_predictions':int((d.pred!=ref.pred).sum()),'different_timing':int((d.t!=ref.t).sum())}
    # Warn if policies share an invariant pre-inspection state, by design.
    report['warnings'].append('All variants use the same pre-inspection state; specialist Q signals enter only after an inspection. This can mask cooperative differences.')
    report['warnings'].append('Unknown Q(state,action) entries default to 0 and ties prefer wait (action 0); quantify this before interpreting equivalence.')
    (OUT/'learning_diagnostic.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'status':report['status'],'models':{k:{x:v for x,v in m.items() if x in ('all_unseen_fraction','all_unseen_after_inspection_fraction','post_inspection_steps','action_counts')} for k,m in report['models'].items()},'warnings':report['warnings']},indent=2))
    print('Saved:',OUT/'learning_diagnostic.json')
if __name__=='__main__':main()
