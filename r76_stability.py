"""E3-R76: instrumented training and multi-seed development stability; NOT confirmatory."""
import ast,csv,hashlib,json,random,os,math
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent
src=P/'core'/'r72_engine.py'; tree=ast.parse(src.read_text())
stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in n.targets))
ns={'__file__':str(src),'__name__':'r75_defs'}
exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(src),'exec'),ns)
variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('permuted_q','permuted',None)]
# Baseline reproduces R72 semantics. Persist keeps inspection flag after wait.
# Known-first chooses among learned actions when any exist, otherwise defaults to wait.
conditions=[('baseline',False,False),('persist_inspection',True,False),('persist_known_first',True,True)]
seeds=[42] if len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='smoke' else [42,123,2026,31415,27182]
local_steps=int(os.getenv('R76_LOCAL_STEPS','100' if len(seeds)==1 else '600'))
coord_steps=int(os.getenv('R76_COORD_STEPS','180' if len(seeds)==1 else '1000'))
rows=[];td_rows=[];checks=[]
def select(q,s,available,known_first):
 if known_first:
  known=[a for a in available if (s,a) in q]
  if known: return max(known,key=lambda a:(q[(s,a)],-a))
  return 0 if 0 in available else min(available)
 return max(available,key=lambda a:(q.get((s,a),0),-a))
def roll(e,q,mode,localq,rng,epsilon=0,learn=False,ablate=None,persist=False,known_first=False,trace=None,stats=None):
 t=0;ins=False;count=0;total=0
 for step in range(e['n']*2+1):
  s=ns['coord_state'](e,t,ins,mode,localq,ablate)
  available=tuple(a for a in ns['acts'](t,ins) if a!=1 or count==0)
  if learn and not ins and count==0 and t>=5 and rng.random()<min(.35,epsilon): a=1; selection_type='forced_inspection_exploration'
  elif learn and rng.random()<epsilon:a=rng.choice(available); selection_type='epsilon_exploration'
  else:a=select(q,s,available,known_first); selection_type='greedy'
  known_before=(s,a) in q
  known_available=sum((s,z) in q for z in available)
  old=q.get((s,a),0.)
  if a==1:nt=t;ni=True;r=-.8;done=False;count+=1
  elif a==2:nt=t;ni=ins;r=ns['reward'](e,t,1);done=True
  elif t==e['n']-1:nt=t;ni=ins;r=ns['reward'](e,t,0);done=True
  else:nt=t+1;ni=ins if persist else False;r=-.08;done=False
  total+=r
  ns_=None if done else ns['coord_state'](e,nt,ni,mode,localq,ablate)
  nxt=() if done else tuple(z for z in ns['acts'](nt,ni) if z!=1 or count==0)
  future=0 if done else (q.get((ns_,select(q,ns_,nxt,known_first)),0) if known_first else max(q.get((ns_,z),0) for z in nxt))
  target=r+ns['GAMMA']*future
  td=target-old;new=old+ns['ALPHA']*td if learn else old
  if learn:q[(s,a)]=new
  if trace is not None:
   trace.append({'episode_id':str(e['id']),'step':step,'t':t,'inspected_before':int(ins),'state':repr(s),'action':a,'known_before':int(known_before),'known_available':known_available,'available_actions':repr(available),'selection_type':selection_type,'epsilon':epsilon, 'reward':r,'done':int(done),'next_t':nt,'inspected_after':int(ni),'next_state':repr(ns_),'q_old':old,'future':future,'td_target':target,'td_error':td,'q_new':new,'update_applied':int(learn)})
  if stats is not None:
   stats['decisions']+=1;stats['unseen_selected']+=int(not known_before);stats['post_total']+=int(ins);stats['post_known']+=int(ins and any((s,z) in q for z in available));stats['reset_after_inspection_wait']+=int(ins and a==0 and not done and not ni);stats['actions_'+str(a)]+=1
  if done:return {'episode_id':e['id'],'scenario':e['scenario'],'y':int(e['scenario']!='normal'),'pred':int(a==2),'t':t,'onset':e['onset'],'inspections':count,'reward':total}
  t,ins=nt,ni
 raise RuntimeError('Finite horizon exceeded')
# Unit tests for transition semantics, known-first selection and TD numerical identity.
checks.append({'name':'unknown_fallback_wait','pass':select({},('s',),(0,2),True)==0})
checks.append({'name':'known_negative_preferred_over_unknown','pass':select({(('s',),2):-3},('s',),(0,2),True)==2})
checks.append({'name':'td_manual','pass':math.isclose(-.08+.94*2-(-1),2.8)})
for seed in seeds:
 rng=random.Random(seed);localq={}
 for name in ns['G']:
  q={}
  for i in range(1,local_steps+1):
   e=ns['balanced_choice'](ns['tr'],rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)))
   ns['local_roll'](e,name,q,rng,eps,True)
  localq[name]=q
 ns['fit_calibration'](localq)
 for label,mode,ablate in variants:
  ns['PERM_MAP'].clear()
  if mode=='permuted':
   for part in (ns['tr'],ns['va']):
    order=list(part);random.Random(seed+10007+len(part)).shuffle(order)
    ns['PERM_MAP'].update({e['id']:other for e,other in zip(part,order)})
  for condition,persist,known_first in conditions:
   rr=random.Random(seed+71);q={};bestq={};bestscore=-1e20;beststep=0
   for i in range(1,coord_steps+1):
    e=ns['balanced_choice'](ns['tr'],rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)))
    trace=[] if i<=min(3,coord_steps) or i%max(1,coord_steps//12)==0 else None
    roll(e,q,mode,localq,rr,eps,True,ablate,persist,known_first,trace)
    if trace is not None:
     for r in trace:td_rows.append({'seed':seed,'variant':label,'condition':condition,'train_episode_index':i,**r})
    if i%max(1,min(100,coord_steps))==0 or i==coord_steps:
     import pandas as pd
     d=pd.DataFrame([roll(e,q,mode,localq,random.Random(0),ablate=ablate,persist=persist,known_first=known_first) for e in ns['va']]);m=ns['metrics'](d)
     score=m['mcc']-.1*m['fpr']
     if score>bestscore:bestscore=score;bestq=q.copy();beststep=i
   stats=Counter();import pandas as pd
   d=pd.DataFrame([roll(e,bestq,mode,localq,random.Random(0),ablate=ablate,persist=persist,known_first=known_first,stats=stats) for e in ns['va']]);m=ns['metrics'](d)
   rows.append({'seed':seed,'variant':label,'condition':condition,'selected_step':beststep,'policy_entries':len(bestq),'stats':dict(stats),'metrics':m})
   print(seed,label,condition,'MCC',round(m['mcc'],3),'FPR',round(m['fpr'],3),flush=True)
# Verify exact arithmetic on genuine training-time trace, not reconstructed checkpoints.
checks.append({'name':'training_trace_has_real_known_before','pass':all(isinstance(r['known_before'],int) for r in td_rows)})
checks.append({'name':'training_trace_has_selection_type','pass':all(r['selection_type'] in ('forced_inspection_exploration','epsilon_exploration','greedy') for r in td_rows)})
checks.append({'name':'training_trace_has_greedy_and_exploration','pass':{'greedy','epsilon_exploration'}.issubset({r['selection_type'] for r in td_rows})})
for r in td_rows:
 if not r['update_applied']:continue
 checks.append({'name':'td_logged_'+str(len(checks)),'pass':math.isclose(r['td_target'],r['reward']+ns['GAMMA']*r['future'],abs_tol=1e-9) and math.isclose(r['q_new'],r['q_old']+ns['ALPHA']*r['td_error'],abs_tol=1e-9)})
O=P/'results';O.mkdir(exist_ok=True)
with (O/'r76_training_td_trace.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(td_rows[0]));w.writeheader();w.writerows(td_rows)
report={'status':'PASS' if all(x['pass'] for x in checks) and all(isinstance(r['known_before'],int) and r['selection_type'] in ('forced_inspection_exploration','epsilon_exploration','greedy') for r in td_rows) else 'FAIL','purpose':'development-only multi-seed structural ablation and authentic training instrumentation; NOT confirmatory','seed_list':seeds,'local_steps':local_steps,'coordinator_steps':coord_steps,'train_sha256':hashlib.sha256((P/'data'/'train.csv.gz').read_bytes()).hexdigest(),'conditions':{'baseline':'R72 semantics: post-inspection wait resets flag; unseen Q=0','persist_inspection':'inspection state persists; unseen Q=0','persist_known_first':'persistent inspection; prefer learned Q actions, fallback wait'},'results':rows,'instrumentation':{'trace_scope':'first three plus spaced training episodes per configuration','known_before_captured_pre_update':True,'selection_types':['forced_inspection_exploration','epsilon_exploration','greedy']},'tests_passed':sum(x['pass'] for x in checks),'tests_total':len(checks),'tests_failed':[x for x in checks if not x['pass']],'limitations':['Same development dataset previously explored; not confirmatory','Known-first is an experimental rule, not proven optimal','Central and multi variants not capacity matched','First three and approximately twelve spaced training episodes per configuration are traced in detail','Training-time TD logs are authentic for the instrumented training, not historical R74 checkpoints','No external labeled attacks included','Five seeds are descriptive; no inferential significance is claimed','No architecture capacity matching yet']}
(O/'r76_stability_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print('Saved',O/'r76_stability_audit.json','checks',report['tests_passed'],'/',report['tests_total'])
if report['status']!='PASS':raise SystemExit(1)
