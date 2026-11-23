"""E3-R70 exploratory redesign (NOT confirmatory). Previously E3-R58: four independently trained tabular Q policies + learned coordinator.
No supervised encoders. Exploratory synthetic episodes; prior test exploration.
"""
from pathlib import Path
import os, random, json, time, copy, pickle, tracemalloc, hashlib
import numpy as np, pandas as pd
from sklearn.metrics import matthews_corrcoef, balanced_accuracy_score, confusion_matrix, f1_score
P=Path(__file__).resolve().parent.parent; O=P/'results'; O.mkdir(exist_ok=True)
G={'radio':['rssi','snr'],'temporal':['delta_t_derived'],'phy':['c2','c8','c9','c15'],'protocol':['counter_step_derived']}
F=sum(G.values(),[]); GAMMA=.94; ALPHA=.13
raw=pd.read_csv(P/'data/train.csv.gz'); test=pd.read_csv(P/'data/test.csv.gz')
ids=np.array(sorted(raw.episode_id.unique()));np.random.default_rng(20261119).shuffle(ids)
va_ids=set(ids[:35]);train=raw[~raw.episode_id.isin(va_ids)].copy();val=raw[raw.episode_id.isin(va_ids)].copy()
# All transforms are learned on training episodes only; no label-dependent encoders.
med=train[F].median().fillna(0); qs={f:np.unique(train[f].dropna().quantile([.2,.5,.8]).to_numpy()) for f in F}
# A single, bounded per-feature ordinal bin; no full-precision or target leakage.
def discretize(d):
 d=d.copy()
 for f in F:d['b_'+f]=np.searchsorted(qs[f],d[f].fillna(med[f]).to_numpy(),side='right').astype('int8')
 return d
train,val,test=map(discretize,(train,val,test))
def episodes(d):
 out=[]
 for eid,g in d.groupby('episode_id',sort=True):
  g=g.sort_values('t');out.append({'id':eid,'scenario':g.scenario.iloc[0],'onset':int(g.onset.iloc[0]),'n':len(g),'b':{f:g['b_'+f].to_numpy() for f in F}})
 return out
tr,va,te=map(episodes,(train,val,test))
# Hard-normal controls: bounded, time-coherent non-attack fluctuations.
# All are derived independently within each partition, never from attack examples.
def hard_normals(es):
 out=[]
 for e in es:
  if e['scenario']!='normal':continue
  v={'id':'hard_'+str(e['id']),'scenario':'normal','onset':e['n'],'n':e['n'],
     'b':{f:a.copy() for f,a in e['b'].items()}}
  # Sustained but modest RSSI/SNR fluctuation, no protocol counter replay.
  for f in ('rssi','snr'):
   a=v['b'][f];a[9:15]=np.clip(a[9:15]+1,0,3)
  # Natural interval variation is not itself a security attack.
  a=v['b']['delta_t_derived'];a[15:19]=np.clip(a[15:19]-1,0,3)
  out.append(v)
 return out
tr+=hard_normals(tr);va+=hard_normals(va);te+=hard_normals(te)
# Calibrate specialist advantages from unlabeled validation episodes only.
CAL={}
def fit_calibration(localq):
 for n in G:
  x=np.array([advantage(e,t,n,localq[n]) for e in va for t in range(5,e['n'])],dtype=float)
  # Robust scale: differences in absolute Q magnitude cannot dominate the fusion.
  center=float(np.median(x));scale=float(max(1.,np.quantile(x,.75)-np.quantile(x,.25)))
  CAL[n]=(center,scale)
def calibrated_bucket(v,n):
 c,s=CAL[n];return int(np.digitize(np.clip((v-c)/s,-8,8),[-.75,0,.75]))
def local_state(e,t,name):
 # Include causal trend (current vs previous) in each specialist's state.
 cols=G[name];cur=tuple(int(e['b'][f][t]) for f in cols)
 prev=tuple(int(np.sign(int(e['b'][f][t])-int(e['b'][f][max(0,t-3)]))) for f in cols)
 return (min(3,t//6),)+cur+prev
# Terminal alert / sequential wait: explicit TD bootstrap on future observations.
def reward(e,t,a):
 attack=e['scenario']!='normal';on=e['onset']
 if a==1:return (18-.35*max(0,t-on)) if attack and t>=on else -32
 if t==e['n']-1:return 9 if not attack else -24
 return -.08

def local_roll(e,name,q,rng,epsilon=0,learn=False):
 t=0;total=0;tds=[]
 while True:
  s=local_state(e,t,name);acts=(0,1) if t>=5 else (0,)
  a=rng.choice(acts) if rng.random()<epsilon else max(acts,key=lambda a:(q.get((s,a),0),-a))
  r=reward(e,t,a);total+=r;done=(a==1 or t==e['n']-1)
  if learn:
   ns=local_state(e,t+1,name) if not done else None
   future=0 if done else max(q.get((ns,z),0) for z in ((0,1) if t+1>=5 else (0,)))
   td=r+GAMMA*future-q.get((s,a),0);q[(s,a)]=q.get((s,a),0)+ALPHA*td;tds.append(abs(td))
  if done:return total,int(a==1),t,float(np.mean(tds)) if tds else 0
  t+=1

def advantage(e,t,name,q):
 s=local_state(e,t,name)
 return q.get((s,1),0)-q.get((s,0),0)

def bucket(v):return int(np.digitize(v,[-5,0,5]))
PERM_MAP={}
def coord_state(e,t,ins,mode,localq,ablate=None):
 base=(min(3,t//6),int(ins),int(e['b']['rssi'][t]),int(e['b']['delta_t_derived'][t]))
 if not ins:return base
 # Compact, shared state cardinality: every policy uses 4 grouped signals after inspection.
 # This is an exploratory design change, not a post-hoc confirmatory adjustment.
 if mode=='central':
  return base+tuple(int(np.median([e['b'][f][t] for f in G[n]])) for n in G)
 return base+tuple(calibrated_bucket(advantage(PERM_MAP.get(e['id'],e) if mode=='permuted' else e,t,n,localq[n]),n) for n in G if n!=ablate)
def acts(t,ins):return (0,1,2) if t>=5 and not ins else ((0,2) if t>=5 else ((0,1) if not ins else (0,)))
def coord_roll(e,q,mode,localq,rng,epsilon=0,learn=False,ablate=None):
 t=0;ins=False;total=0;count=0;tds=[]
 for _ in range(e['n']*2+1):
  s=coord_state(e,t,ins,mode,localq,ablate);available=tuple(a for a in acts(t,ins) if a!=1 or count==0)
  # Stratified training exploration: ensure the inspection transition is visited.
  if learn and not ins and count==0 and t>=5 and rng.random()<min(0.35,epsilon):
   a=1
  else:
   a=rng.choice(available) if rng.random()<epsilon else max(available,key=lambda a:(q.get((s,a),0),-a))
  if a==1:nt=t;ni=True;r=-.8;done=False;count+=1
  elif a==2:nt=t;ni=ins;r=reward(e,t,1);done=True
  elif t==e['n']-1:nt=t;ni=ins;r=reward(e,t,0);done=True
  else:nt=t+1;ni=False;r=-.08;done=False
  total+=r
  if learn:
   ns=coord_state(e,nt,ni,mode,localq,ablate) if not done else None
   future=0 if done else max(q.get((ns,z),0) for z in acts(nt,ni) if z!=1 or count==0)
   td=r+GAMMA*future-q.get((s,a),0);q[(s,a)]=q.get((s,a),0)+ALPHA*td;tds.append(abs(td))
  if done:return {'episode_id':e['id'],'scenario':e['scenario'],'y':int(e['scenario']!='normal'),'pred':int(a==2),'t':t,'onset':e['onset'],'inspections':count,'reward':total},float(np.mean(tds)) if tds else 0
  t,ins=nt,ni
 raise RuntimeError('Episode exceeded finite horizon')
def evaluate(es,q,mode,localq,ablate=None):
 rng=random.Random(0)
 return pd.DataFrame([coord_roll(e,q,mode,localq,rng,ablate=ablate)[0] for e in es])
def metrics(d):
 correct=(d.pred.eq(1)&d.y.eq(1)&d.t.ge(d.onset)); premature=(d.pred.eq(1)&d.y.eq(1)&d.t.lt(d.onset)); effective=(correct | (d.pred.eq(1)&d.y.eq(0))).astype(int); tn,fp,fn,tp=confusion_matrix(d.y,effective,labels=[0,1]).ravel()
 det=d[correct];delay=(det.t-det.onset).mean()
 return {'mcc':float(matthews_corrcoef(d.y,effective)),'bal_acc':float(balanced_accuracy_score(d.y,effective)),'f1':float(f1_score(d.y,effective,zero_division=0)),'recall':float(tp/(tp+fn)),'fpr':float(fp/(fp+tn)),'premature_rate':float(premature.sum()/max(1,(d.y==1).sum())),'tp':int(tp),'tn':int(tn),'fp':int(fp),'fn':int(fn),'delay_messages':float(delay) if len(det) else None,'inspections':float(d.inspections.mean()),'mean_reward':float(d.reward.mean())}
def balanced_choice(es,rng,i):
 normal=[e for e in es if e['scenario']=='normal'];anomaly=[e for e in es if e['scenario']!='normal']
 return rng.choice(normal if i%2 else anomaly)
Nlocal=int(os.getenv('LOCAL_STEPS','1200'));Ncoord=int(os.getenv('COORD_STEPS','1200'));num=int(os.getenv('NUM_SEEDS','2'))
seeds=[42,123,2026,7,99][:num]; variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('permuted_q','permuted',None)]
results=[];predictions=[];curves=[];localscores=[];started=time.time()
MODELS=P/'models';MODELS.mkdir(exist_ok=True)
benchmarks=[]
for seed in seeds:
 rng=random.Random(seed);localq={}
 for name in G:
  q={};td=0
  for i in range(1,Nlocal+1):
   e=balanced_choice(tr,rng,i);eps=max(.05,.8*(1-i/(Nlocal*.85)))
   _,_,_,td=local_roll(e,name,q,rng,eps,True)
  localq[name]=q
  # Each specialist is genuinely learned by TD, not a supervised classifier.
  for part,es in [('validation',va),('test',te)]:
   for e in es:
    _,alarm,t,_=local_roll(e,name,q,random.Random(0))
    localscores.append({'seed':seed,'specialist':name,'partition':part,'episode_id':e['id'],'y':int(e['scenario']!='normal'),'pred':alarm,'decision_t':t})
 fit_calibration(localq)
 for label,mode,ablate in variants:
  PERM_MAP.clear()
  if mode=='permuted':
   for partition in (tr,va,te):
    order=list(partition);random.Random(seed+10007+len(partition)).shuffle(order)
    PERM_MAP.update({e['id']:other for e,other in zip(partition,order)})
  rng=random.Random(seed+71);q={};bestscore=-1e10;bestq={};beststep=0
  for i in range(1,Ncoord+1):
   e=balanced_choice(tr,rng,i);eps=max(.05,.8*(1-i/(Ncoord*.85)))
   _,td=coord_roll(e,q,mode,localq,rng,eps,True,ablate)
   if i%max(1,min(500,Ncoord))==0 or i==Ncoord:
    mv=metrics(evaluate(va,q,mode,localq,ablate));score=mv['mcc']-.1*mv['fpr']
    curves.append({'seed':seed,'variant':label,'step':i,'last_td_abs':td,'val_score':score,**mv})
    if score>bestscore:bestscore=score;bestq=q.copy();beststep=i
  # Store exact policy and all preprocessing parameters needed for zero-shot evaluation.
  artifact={'schema_version':'E3-R70-exploratory-v1','seed':seed,'variant':label,'mode':mode,'ablate':ablate,
    'policy':bestq,'local_policies':copy.deepcopy(localq),'calibration':dict(CAL),
    'medians':med.to_dict(),'quantiles':{f:qs[f].tolist() for f in F},
    'feature_groups':G,'features':F,'inspection_budget':1,'state_design':'compressed_group_median_central_vs_calibrated_q_multi_post_inspection','exploration':'forced_inspection_probability_min_0.35_epsilon',
    'source':'exploratory synthetic training','confirmatory':False,
    'permutation_episode_map':{str(k):str(v['id']) for k,v in PERM_MAP.items()} if mode=='permuted' else None,
    'permutation_dataset_sha256':hashlib.sha256((P/'data'/'test.csv.gz').read_bytes()).hexdigest() if mode=='permuted' else None}
  with open(MODELS/f'{label}_seed{seed}.pkl','wb') as pf:pickle.dump(artifact,pf,protocol=pickle.HIGHEST_PROTOCOL)
  tracemalloc.start();tic=time.perf_counter()
  d=evaluate(te,bestq,mode,localq,ablate)
  infer_sec=time.perf_counter()-tic;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  d['seed']=seed;d['variant']=label;predictions.append(d)
  benchmarks.append({'seed':seed,'variant':label,'episodes':len(te),'inference_seconds':infer_sec,
    'inference_ms_per_episode':1000*infer_sec/max(1,len(te)),'peak_python_alloc_bytes':peak,
    'serialized_policy_bytes':(MODELS/f'{label}_seed{seed}.pkl').stat().st_size,
    'inspection_mean':float(d.inspections.mean())})
  result={'seed':seed,'variant':label,'selected_step':beststep,'states':len(bestq),'val_score':bestscore,**metrics(d)}
  # Report whether any learned Q entries cover inspected states.
  result['learned_post_inspection_entries']=sum(1 for (st,act) in bestq if len(st)>1 and st[1]==1)
  result['post_inspection_coverage_flag']=bool(result['learned_post_inspection_entries'])
  results.append(result);print(seed,label,'MCC',round(result['mcc'],4),'FPR',round(result['fpr'],3),'states',len(bestq),flush=True)
r=pd.DataFrame(results);r.to_csv(O/'metrics_by_seed.csv',index=False)
pd.concat(predictions).to_csv(O/'predictions_by_episode.csv',index=False)
pd.DataFrame(curves).to_csv(O/'learning_curves.csv',index=False)
pd.DataFrame(benchmarks).to_csv(O/'benchmarks.csv',index=False)
ld=pd.DataFrame(localscores);ld.to_csv(O/'local_agents_predictions.csv',index=False)
local_metrics=[]
for (seed,name,part),d in ld.groupby(['seed','specialist','partition']):local_metrics.append({'seed':seed,'specialist':name,'partition':part,**metrics(d.assign(inspections=0,reward=0,onset=0,t=d.decision_t))})
pd.DataFrame(local_metrics).to_csv(O/'local_agents_metrics.csv',index=False)
r.groupby('variant')[['mcc','bal_acc','recall','fpr','inspections','states']].agg(['mean','std']).to_csv(O/'summary.csv')
(O/'metadata.json').write_text(json.dumps({'seeds':seeds,'local_steps_per_agent':Nlocal,'coordinator_steps':Ncoord,'gamma':GAMMA,'alpha':ALPHA,'train_episodes':len(tr),'validation_episodes':len(va),'test_episodes':len(te),'feature_groups':G,'local_agent_learning':'independent tabular Q-learning TD(0) with sequential wait/alert actions','coordinator_learning':'tabular Q-learning TD(0) observe/inspect/alert','supervised_models':False,'training_labels_used_in_reward':True,'data':'synthetic anomalies, previously explored test campaign','confirmatory':False,'temporal_metrics':'alert before onset is not TP; premature rate separately reported','permutation':'episode-wise shuffle within train validation test separately, all four Q advantages shuffled together, temporal profile preserved; coordinator retrained','equal_information':'same raw feature set available after paid inspection, but not matched capacity/state size','calibration':'unlabeled validation robust median/IQR for each specialist','inspection_budget':1,'hard_normal_controls':'bounded non-attack perturbations on normal sequences; synthetic' ,'elapsed_seconds':round(time.time()-started,2)},indent=2))
print('\n',r.groupby('variant')[['mcc','bal_acc','recall','fpr','inspections']].mean().round(4).to_string());print('elapsed',round(time.time()-started,2))
