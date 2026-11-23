"""E3-R72 exploratory structural test; not confirmatory. Train new checkpoints, do not reuse R70/R71."""
import ast, copy, hashlib, json, os, pickle, random, sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
source=P/'core'/'r72_engine.py';tree=ast.parse(source.read_text())
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in node.targets))
ns={'__file__':str(source),'__name__':'r72_definitions'}
exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(source),'exec'),ns)
G=ns['G'];tr=ns['tr'];va=ns['va'];te=ns['te']; variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('permuted_q','permuted',None)]
local_steps=int(os.getenv('R72_LOCAL_STEPS','300'));coord_steps=int(os.getenv('R72_COORD_STEPS','600'))
if len(sys.argv)>1 and sys.argv[1]=='smoke':local_steps=100;coord_steps=180
seed=int(os.getenv('R72_SEED','42'));rng=random.Random(seed)
localq={}
for name in G:
 q={}
 for i in range(1,local_steps+1):
  e=ns['balanced_choice'](tr,rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)))
  ns['local_roll'](e,name,q,rng,eps,True)
 localq[name]=q
ns['fit_calibration'](localq)
report={'status':'PASS','purpose':'exploratory structural and counterfactual diagnostic; NOT confirmatory','seed':seed,'local_steps_per_agent':local_steps,'coordinator_steps':coord_steps,'dataset_sha256':hashlib.sha256((P/'data'/'test.csv.gz').read_bytes()).hexdigest(),'episodes':len(te),'models':{},'warnings':[]}
modeldir=P/'models_r72';modeldir.mkdir(exist_ok=True)
for label,mode,ablate in variants:
 ns['PERM_MAP'].clear()
 if mode=='permuted':
  for partition in (tr,va,te):
   order=list(partition);random.Random(seed+10007+len(partition)).shuffle(order)
   ns['PERM_MAP'].update({e['id']:other for e,other in zip(partition,order)})
 rr=random.Random(seed+71);q={};bestq={};bestscore=-1e10;beststep=0
 for i in range(1,coord_steps+1):
  e=ns['balanced_choice'](tr,rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)))
  ns['coord_roll'](e,q,mode,localq,rr,eps,True,ablate)
  if i%max(1,min(100,coord_steps))==0 or i==coord_steps:
   m=ns['metrics'](ns['evaluate'](va,q,mode,localq,ablate));score=m['mcc']-.1*m['fpr']
   if score>bestscore:bestscore=score;bestq=q.copy();beststep=i
 artifact={'schema_version':'E3-R72-development-v1','seed':seed,'variant':label,'mode':mode,'ablate':ablate,'policy':bestq,'local_policies':copy.deepcopy(localq),'calibration':dict(ns['CAL']),'medians':ns['med'].to_dict(),'quantiles':{f:ns['qs'][f].tolist() for f in ns['F']},'state_design':'early_two_signals_then_four_after_inspection','permutation_episode_map':{str(k):str(v['id']) for k,v in ns['PERM_MAP'].items()} if mode=='permuted' else None,'confirmatory':False}
 path=modeldir/f'{label}_seed{seed}.pkl'
 with path.open('wb') as f:pickle.dump(artifact,f)
 # Trusted local checkpoint roundtrip, full policy and mapping.
 with path.open('rb') as f:loaded=pickle.load(f)
 assert loaded['policy']==bestq and loaded['permutation_episode_map']==artifact['permutation_episode_map']
 original=ns['coord_state'];stats={'decision_steps':0,'post_inspection_steps':0,'post_inspection_any_learned':0,'post_inspection_unseen_all':0,'pre_inspection_any_learned':0,'action_counts':{'0':0,'1':0,'2':0}}
 # Instrument action selection via a transparent rollout; check equality to engine rollout.
 def trace(e,statefn=original):
  t=0;ins=False;count=0;total=0;acts=[]
  for _ in range(e['n']*2+1):
   s=statefn(e,t,ins,mode,localq,ablate)
   available=tuple(a for a in ns['acts'](t,ins) if a!=1 or count==0)
   a=max(available,key=lambda z:(bestq.get((s,z),0),-z));acts.append(a)
   if statefn is original:
    stats['decision_steps']+=1;stats['action_counts'][str(a)]+=1
    known=any((s,z) in bestq for z in available)
    if ins:stats['post_inspection_steps']+=1;stats['post_inspection_any_learned']+=int(known);stats['post_inspection_unseen_all']+=int(not known)
    else:stats['pre_inspection_any_learned']+=int(known)
   if a==1:nt=t;ni=True;r=-.8;done=False;count+=1
   elif a==2:nt=t;ni=ins;r=ns['reward'](e,t,1);done=True
   elif t==e['n']-1:nt=t;ni=ins;r=ns['reward'](e,t,0);done=True
   else:nt=t+1;ni=False;r=-.08;done=False
   total+=r
   if done:return {'episode_id':e['id'],'scenario':e['scenario'],'y':int(e['scenario']!='normal'),'pred':int(a==2),'t':t,'onset':e['onset'],'inspections':count,'reward':total},acts
   t,ins=nt,ni
  raise RuntimeError('horizon exceeded')
 base=[];action_sequences=[]
 for e in te:
  result,seq=trace(e);base.append(result);action_sequences.append(seq)
  reference,_=ns['coord_roll'](e,bestq,mode,localq,random.Random(0),ablate=ablate)
  assert result==reference,(label,e['id'],result,reference)
 import pandas as pd
 d=pd.DataFrame(base);basekeys=[(x['pred'],x['t'],x['inspections']) for x in base]
 item={'selected_step':beststep,'policy_entries':len(bestq),'coverage':stats,'metrics':ns['metrics'](d),'counterfactuals':{},'checkpoint_roundtrip':True,'permutation_map_persisted':bool(artifact['permutation_episode_map'])}
 if mode!='central':
  for name in G:
   if name==ablate:continue
   idx=list(G).index(name)
   for replacement in [0,3]:
    def perturb(e,t,ins,m,l,ablate=None):
     s=list(original(e,t,ins,m,l,ablate));position=2+idx
     if (ins or idx<2) and position<len(s):s[position]=replacement
     return tuple(s)
    alt=[trace(e,perturb)[0] for e in te]
    changed=sum((x['pred'],x['t'],x['inspections'])!=y for x,y in zip(alt,basekeys))
    item['counterfactuals'][f'{name}_to_{replacement}']={'episodes_changed':changed,'predictions_changed':sum(x['pred']!=y[0] for x,y in zip(alt,basekeys))}
  if not any(v['episodes_changed'] for v in item['counterfactuals'].values()):report['warnings'].append(f'{label}: no final-decision sensitivity to tested interventions')
 report['models'][label]=item
 print(label,'MCC',round(item['metrics']['mcc'],4),'post coverage',stats['post_inspection_any_learned'],'/',stats['post_inspection_steps'],'counterfactual changes',sum(v['episodes_changed'] for v in item['counterfactuals'].values()),flush=True)
 # Restore base mapping for next variant; training creates next map independently.
output=P/'results'/'r72_structural_audit.json';output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('Saved',output)
