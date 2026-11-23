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
raw=pd.read_csv(P/'data/train.csv.gz')
ids=np.array(sorted(raw.episode_id.unique()));np.random.default_rng(20261119).shuffle(ids)
va_ids=set(ids[:35]);train=raw[~raw.episode_id.isin(va_ids)].copy();val=raw[raw.episode_id.isin(va_ids)].copy()
# All transforms are learned on training episodes only; no label-dependent encoders.
med=train[F].median().fillna(0); qs={f:np.unique(train[f].dropna().quantile([.2,.5,.8]).to_numpy()) for f in F}
# A single, bounded per-feature ordinal bin; no full-precision or target leakage.
def discretize(d):
 d=d.copy()
 for f in F:d['b_'+f]=np.searchsorted(qs[f],d[f].fillna(med[f]).to_numpy(),side='right').astype('int8')
 return d
train,val=map(discretize,(train,val))
def episodes(d):
 out=[]
 for eid,g in d.groupby('episode_id',sort=True):
  g=g.sort_values('t');out.append({'id':eid,'scenario':g.scenario.iloc[0],'onset':int(g.onset.iloc[0]),'n':len(g),'b':{f:g['b_'+f].to_numpy() for f in F}})
 return out
tr,va=map(episodes,(train,val))
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
tr+=hard_normals(tr);va+=hard_normals(va)
# R82: calibrate specialist advantages on training episodes only.
CAL={}
def fit_calibration(localq):
 for n in G:
  x=np.array([advantage(e,t,n,localq[n]) for e in tr for t in range(5,e['n'])],dtype=float)
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
 # R72: same time/inspection indicators; signals available before decisions.
 # Two coarse signals pre-inspection; all specialist signals after inspection.
 # Both architectures have matched signal count (2 before, 4 after).
 base=(min(3,t//6),int(ins))
 names=list(G)
 if mode=='central':
  signals=[int(np.median([e['b'][f][t] for f in G[n]])) for n in names]
 else:
  src=PERM_MAP.get(e['id'],e) if mode=='permuted' else e
  signals=[calibrated_bucket(advantage(src,t,n,localq[n]),n) for n in names]
 # Ablated channels are held at a fixed neutral bin, not removed (capacity matched).
 if ablate in names:signals[names.index(ablate)]=1
 if not ins:
  return base+(signals[0],signals[1])
 return base+tuple(signals)

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
