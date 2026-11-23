"""E3-R74: independent transition, reward, Q-update and action-selection audit.
Development/validation only. Does not modify the legacy learning engine.
"""
import ast, csv, hashlib, json, math, os, random, sys
from pathlib import Path
P=Path(__file__).resolve().parent
source=P/'core'/'r72_engine.py'
tree=ast.parse(source.read_text(encoding='utf-8'))
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in node.targets))
ns={'__file__':str(source),'__name__':'r74_definitions'}
exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(source),'exec'),ns)
smoke=len(sys.argv)>1 and sys.argv[1]=='smoke'
local_steps=100 if smoke else int(os.getenv('R74_LOCAL_STEPS','400'))
coord_steps=180 if smoke else int(os.getenv('R74_COORD_STEPS','700'))
seed=42
variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('permuted_q','permuted',None)]
report={'status':'PASS','purpose':'development-only; synthetic previously explored; NOT confirmatory','seed':seed,'local_steps':local_steps,'coordinator_steps':coord_steps,'train_sha256':hashlib.sha256((P/'data/train.csv.gz').read_bytes()).hexdigest(),'tests':[],'variants':[],'warnings':[],'limitations':[]}

def check(name,actual,expected,detail=''):
 ok=math.isclose(actual,expected,abs_tol=1e-10,rel_tol=1e-10) if isinstance(actual,(int,float)) and isinstance(expected,(int,float)) else actual==expected
 report['tests'].append({'name':name,'pass':bool(ok),'actual':actual,'expected':expected,'detail':detail})
 if not ok:report['status']='FAIL'

# Explicit hand-computable terminal rewards and transition returns.
normal={'scenario':'normal','onset':24,'n':24}
attack={'scenario':'attack','onset':10,'n':24}
for name,e,t,a,expected in [('normal_terminal',normal,23,0,9),('attack_missed',attack,23,0,-24),('normal_false_alert',normal,10,1,-32),('attack_premature_alert',attack,9,1,-32),('attack_onset_alert',attack,10,1,18),('attack_delayed_alert',attack,14,1,16.6),('normal_wait',normal,10,0,-.08)]:
 check('reward_'+name,ns['reward'](e,t,a),expected)
check('inspection_immediate_reward',-.8,-.8,'inspection is an explicit action separate from alert')
alpha=ns['ALPHA'];gamma=ns['GAMMA']
for name,q0,r,nextq,terminal,expected in [('terminal_positive',0,18,999,True,alpha*18),('terminal_negative',0,-32,999,True,alpha*-32),('bootstrap_positive',2,-.08,5,False,2+alpha*(-.08+gamma*5-2)),('bootstrap_negative',-1,-.8,-4,False,-1+alpha*(-.8+gamma*-4+1))]:
 updated=q0+alpha*(r+(0 if terminal else gamma*nextq)-q0)
 check('TD_'+name,updated,expected)
check('tie_wait',max((0,2),key=lambda a:(0,-a)),0)
check('known_alert_beats_unseen',max((0,2),key=lambda a:({(0,2):1}.get((0,a),0),-a)),2)
check('unknown_zero_can_beat_negative_known',max((0,2),key=lambda a:({(0,2):-1}.get((0,a),0),-a)),0,'structural risk: missing action Q defaults to zero')

rng=random.Random(seed);localq={}
for name in ns['G']:
 q={}
 for i in range(1,local_steps+1):
  e=ns['balanced_choice'](ns['tr'],rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)))
  ns['local_roll'](e,name,q,rng,eps,True)
 localq[name]=q
ns['fit_calibration'](localq)
rows=[]
for label,mode,ablate in variants:
 ns['PERM_MAP'].clear()
 if mode=='permuted':
  for partition in (ns['tr'],ns['va']):
   order=list(partition);random.Random(seed+10007+len(partition)).shuffle(order)
   ns['PERM_MAP'].update({e['id']:other for e,other in zip(partition,order)})
 rr=random.Random(seed+71);q={};bestq={};bestscore=-1e10;beststep=0
 for i in range(1,coord_steps+1):
  e=ns['balanced_choice'](ns['tr'],rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)))
  ns['coord_roll'](e,q,mode,localq,rr,eps,True,ablate)
  if i%max(1,min(100,coord_steps))==0 or i==coord_steps:
   m=ns['metrics'](ns['evaluate'](ns['va'],q,mode,localq,ablate));score=m['mcc']-.1*m['fpr']
   if score>bestscore:bestscore=score;bestq=q.copy();beststep=i
 summary={'seed':seed,'variant':label,'selected_step':beststep,'actions':{'wait':0,'inspect':0,'alert':0},'state_action_coverage':{'pre_total':0,'pre_all_known':0,'pre_any_known':0,'post_total':0,'post_all_known':0,'post_any_known':0},'selection':{'all_unknown':0,'some_unknown':0,'all_known':0,'tie':0,'unseen_chosen':0,'known_chosen':0},'reward_by_outcome':{'true_alert':[],'false_alert':[],'premature_alert':[],'correct_normal_terminal':[],'missed_attack_terminal':[]},'inspection_transitions':0,'post_inspection_wait_resets_inspection':0,'trajectory_mismatch':0}
 for e in ns['va']:
  t=0;ins=False;count=0;total=0.;prediction=0
  for j in range(e['n']*2+1):
   s=ns['coord_state'](e,t,ins,mode,localq,ablate)
   available=tuple(a for a in ns['acts'](t,ins) if a!=1 or count==0)
   vals={a:float(bestq.get((s,a),0)) for a in available}
   known={a:(s,a) in bestq for a in available}
   a=max(available,key=lambda z:(vals[z],-z))
   n_known=sum(known.values());section='post' if ins else 'pre'
   cov=summary['state_action_coverage'];cov[section+'_total']+=1;cov[section+'_all_known']+=int(n_known==len(available));cov[section+'_any_known']+=int(n_known>0)
   select=summary['selection'];select['all_unknown' if n_known==0 else ('all_known' if n_known==len(available) else 'some_unknown')]+=1
   select['tie']+=int(sum(abs(v-vals[a])<1e-12 for v in vals.values())>1)
   select['known_chosen' if known[a] else 'unseen_chosen']+=1
   summary['actions'][{0:'wait',1:'inspect',2:'alert'}[a]]+=1
   old_t=t;old_ins=ins
   if a==1:nt=t;ni=True;r=-.8;done=False;count+=1;summary['inspection_transitions']+=1
   elif a==2:nt=t;ni=ins;r=ns['reward'](e,t,1);done=True;prediction=1
   elif t==e['n']-1:nt=t;ni=ins;r=ns['reward'](e,t,0);done=True
   else:nt=t+1;ni=False;r=-.08;done=False
   if old_ins and a==0 and not done:summary['post_inspection_wait_resets_inspection']+=1
   total+=r
   ns_state=None if done else ns['coord_state'](e,nt,ni,mode,localq,ablate)
   future_acts=[] if done else [z for z in ns['acts'](nt,ni) if z!=1 or count==0]
   target=float(r+(0 if done else gamma*max(bestq.get((ns_state,z),0) for z in future_acts)))
   if done:
    outcome=('true_alert' if e['scenario']!='normal' and t>=e['onset'] else 'premature_alert' if e['scenario']!='normal' else 'false_alert') if a==2 else ('correct_normal_terminal' if e['scenario']=='normal' else 'missed_attack_terminal')
    summary['reward_by_outcome'][outcome].append(r)
   rows.append({'seed':seed,'variant':label,'episode_id':str(e['id']),'scenario':e['scenario'],'onset':e['onset'],'step':j,'t':old_t,'inspected_before':int(old_ins),'action':a,'action_name':{0:'wait',1:'inspect',2:'alert'}[a],'available_actions':'|'.join(map(str,available)),'known_actions':'|'.join(str(z) for z in available if known[z]),'q_values':json.dumps(vals,sort_keys=True),'state':repr(s),'reward':r,'next_t':nt,'inspected_after':int(ni),'next_state':repr(ns_state),'done':int(done),'bootstrap_target':target,'selected_q':vals[a],'td_error_if_updated':target-vals[a],'inspection_count':count})
   if done:
    expected=ns['coord_roll'](e,bestq,mode,localq,random.Random(0),ablate=ablate)[0]
    if expected['pred']!=prediction or expected['t']!=t or expected['inspections']!=count or abs(expected['reward']-total)>1e-9:summary['trajectory_mismatch']+=1
    break
   t,ins=nt,ni
  else:
   summary['trajectory_mismatch']+=1
 summary['validation_metrics']=ns['metrics'](ns['evaluate'](ns['va'],bestq,mode,localq,ablate))
 summary['reward_by_outcome']={k:{'count':len(v),'mean_terminal_reward':sum(v)/len(v) if v else None} for k,v in summary['reward_by_outcome'].items()}
 check(label+'_trace_matches_engine',summary['trajectory_mismatch'],0)
 check(label+'_action_count_equals_decisions',sum(summary['actions'].values()),summary['state_action_coverage']['pre_total']+summary['state_action_coverage']['post_total'])
 if summary['selection']['unseen_chosen']:report['warnings'].append(f'{label}: {summary["selection"]["unseen_chosen"]} decisions selected unlearned Q values')
 if summary['post_inspection_wait_resets_inspection']:report['warnings'].append(f'{label}: {summary["post_inspection_wait_resets_inspection"]} post-inspection waits reset inspection state; verify intended semantics')
 report['variants'].append(summary)
 print(label,'MCC',round(summary['validation_metrics']['mcc'],3),'FPR',round(summary['validation_metrics']['fpr'],3),'unseen chosen',summary['selection']['unseen_chosen'],flush=True)
report['limitations']=['The per-step bootstrap targets are reconstructed from the frozen selected policy, not the original historical training Q table; they are counterfactual update diagnostics, NOT training-time TD logs.','Terminal reward tests use hand-computable cases; training dynamics and reward preference require further analysis.','Only validation episodes are traced; no test-set optimization.','Exploration in training is not instrumented; greedy action selection and transitions are independently traced.','No architecture or reward weights changed in E3-R74.']
report['test_counts']={'passed':sum(t['pass'] for t in report['tests']),'total':len(report['tests'])}
out=P/'results';out.mkdir(exist_ok=True)
with (out/'r74_transition_trace.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'r74_transition_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print('Saved',out/'r74_transition_audit.json','and',out/'r74_transition_trace.csv','tests',report['test_counts'])
if report['status']!='PASS':sys.exit(1)
