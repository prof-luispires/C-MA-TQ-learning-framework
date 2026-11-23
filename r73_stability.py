"""E3-R73 development-only stability and reward audit; no test-set optimization."""
import ast, json, os, random, hashlib, statistics
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
source=P/'core'/'r72_engine.py'
tree=ast.parse(source.read_text())
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in node.targets))
ns={'__file__':str(source),'__name__':'r73_definitions'}
exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(source),'exec'),ns)
G=ns['G'];tr=ns['tr'];va=ns['va']; variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('permuted_q','permuted',None)]
smoke=len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='smoke'
seeds=[42] if smoke else [42,123,2026]
local_steps=100 if smoke else int(os.getenv('R73_LOCAL_STEPS','400'))
coord_steps=180 if smoke else int(os.getenv('R73_COORD_STEPS','700'))
report={'status':'PASS','purpose':'development-only stability and reward audit; synthetic previously explored; NOT confirmatory','dataset_sha256':hashlib.sha256((P/'data'/'train.csv.gz').read_bytes()).hexdigest(),'seeds':seeds,'local_steps':local_steps,'coordinator_steps':coord_steps,'reward_definition':{'true_alert_after_onset':'18 - 0.35 * delay','false_or_premature_alert':-32,'correct_no_alert_terminal':9,'missed_attack_terminal':-24,'wait_per_step':-0.08,'inspection':-0.8},'variants':[],'warnings':[]}
for seed in seeds:
 rng=random.Random(seed);localq={}
 for name in G:
  q={}
  for i in range(1,local_steps+1):
   e=ns['balanced_choice'](tr,rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)))
   ns['local_roll'](e,name,q,rng,eps,True)
  localq[name]=q
 ns['fit_calibration'](localq)
 for label,mode,ablate in variants:
  ns['PERM_MAP'].clear()
  if mode=='permuted':
   for partition in (tr,va):
    order=list(partition);random.Random(seed+10007+len(partition)).shuffle(order)
    ns['PERM_MAP'].update({e['id']:other for e,other in zip(partition,order)})
  rr=random.Random(seed+71);q={};bestq={};bestscore=-1e10;beststep=0;curve=[]
  for i in range(1,coord_steps+1):
   e=ns['balanced_choice'](tr,rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)))
   ns['coord_roll'](e,q,mode,localq,rr,eps,True,ablate)
   if i%max(1,min(100,coord_steps))==0 or i==coord_steps:
    m=ns['metrics'](ns['evaluate'](va,q,mode,localq,ablate));score=m['mcc']-.1*m['fpr'];curve.append({'step':i,'score':score,'mcc':m['mcc'],'fpr':m['fpr']})
    if score>bestscore:bestscore=score;bestq=q.copy();beststep=i
  counts={'wait':0,'inspect':0,'alert':0,'pre_known':0,'pre_total':0,'post_known':0,'post_total':0,'post_both_known':0,'post_alert_chosen':0,'post_wait_chosen':0,'terminal_no_alert':0}
  for e in va:
   t=0;ins=False;inscount=0
   for _ in range(e['n']*2+1):
    s=ns['coord_state'](e,t,ins,mode,localq,ablate)
    available=tuple(a for a in ns['acts'](t,ins) if a!=1 or inscount==0)
    a=max(available,key=lambda z:(bestq.get((s,z),0),-z))
    counts[{0:'wait',1:'inspect',2:'alert'}[a]]+=1
    counts['post_total' if ins else 'pre_total']+=1
    counts['post_known' if ins else 'pre_known']+=int(any((s,z) in bestq for z in available))
    if ins:
     counts['post_both_known']+=int(all((s,z) in bestq for z in (0,2) if z in available))
     counts['post_alert_chosen' if a==2 else 'post_wait_chosen']+=int(a in (0,2))
    if a==1:ins=True;inscount+=1
    elif a==2:break
    elif t==e['n']-1:counts['terminal_no_alert']+=1;break
    else:t+=1;ins=False
  d=ns['evaluate'](va,bestq,mode,localq,ablate);m=ns['metrics'](d)
  item={'seed':seed,'variant':label,'selected_step':beststep,'policy_entries':len(bestq),'validation_metrics':m,'action_counts':counts,'validation_curve':curve,'permutation_map_present':bool(ns['PERM_MAP']) if mode=='permuted' else None}
  report['variants'].append(item)
  if counts['post_total'] and counts['post_known']/counts['post_total']<.5:report['warnings'].append(f'{seed}/{label}: post-inspection Q coverage below 50%')
  if m['fpr']>.5:report['warnings'].append(f'{seed}/{label}: validation FPR above 50%')
  print(seed,label,'MCC',round(m['mcc'],3),'FPR',round(m['fpr'],3),'post known',counts['post_known'],'/',counts['post_total'],flush=True)
# Do not use test partition for this analysis; no checkpoints or selection on test.
for label,_,_ in variants:
 vals=[x['validation_metrics']['mcc'] for x in report['variants'] if x['variant']==label]
 report.setdefault('summary',{})[label]={'mcc_mean':float(np.mean(vals)),'mcc_std':float(np.std(vals,ddof=1)) if len(vals)>1 else None}
out=P/'results'/'r73_stability_audit.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print('Saved',out)
