"""R80 development-only structural diagnostic. No hyperparameter selection or model edits."""
import ast,os,json,csv,random,hashlib,statistics,collections
from pathlib import Path
P=Path(__file__).resolve().parent; O=P/'results';O.mkdir(exist_ok=True)
src=P/'core/r72_engine.py'; tree=ast.parse(src.read_text());stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in n.targets))
ns={'__file__':str(src),'__name__':'r80_engine'};exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(src),'exec'),ns)
r76=P/'r76_stability.py';t2=ast.parse(r76.read_text());stop2=next(i for i,n in enumerate(t2.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='seed');exec(compile(ast.Module(body=[n for n in t2.body[:stop2] if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(r76),'exec'),ns);ns['ns']=ns
seeds=[42,123,2026,31415,27182] if os.getenv('R81_FULL','0')=='1' else [42,123]
local_steps=int(os.getenv('R81_LOCAL_STEPS','600' if len(seeds)==5 else '100'))
coord_steps=int(os.getenv('R81_COORD_STEPS','1000' if len(seeds)==5 else '180'))
condition=os.getenv('R81_CONDITION','persist_inspection');assert condition in ('baseline','persist_inspection','persist_known_first')
persist=condition!='baseline';known=condition=='persist_known_first'
variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('no_radio','multi','radio'),('no_temporal','multi','temporal')]
rows=[];ep_rows=[];state_rows=[];cf_rows=[];coverage=[];joint_rows=[]
for seed in seeds:
 rng=random.Random(seed);localq={}
 for name in ns['G']:
  q={}
  for i in range(1,local_steps+1):
   e=ns['balanced_choice'](ns['tr'],rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)));ns['local_roll'](e,name,q,rng,eps,True)
  localq[name]=q
 ns['fit_calibration'](localq)
 for label,mode,ablate in variants:
  rr=random.Random(seed+71);q={}
  for i in range(1,coord_steps+1):
   e=ns['balanced_choice'](ns['tr'],rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)));ns['roll'](e,q,mode,localq,rr,eps,True,ablate,persist,known)
  predictions=[];seen=collections.Counter();post=collections.Counter();signal_bins={n:collections.Counter() for n in ns['G']};pair=collections.Counter()
  for e in ns['va']:
   stat=collections.Counter();out=ns['roll'](e,q,mode,localq,random.Random(0),ablate=ablate,persist=persist,known_first=known,stats=stat);predictions.append(out)
   effective=int(out['pred']==1 and (out['y']==0 or out['t']>=out['onset']));category=('TP' if effective else 'FN') if out['y']==1 else ('FP' if effective else 'TN')
   ep_rows.append({'seed':seed,'variant':label,'condition':condition,'episode_id':str(e['id']),'scenario':e['scenario'],'class':category,'alert_t':out['t'],'onset':out['onset'],'inspections':out['inspections'],'reward':out['reward'],'decisions':stat['decisions'],'unseen_selected':stat['unseen_selected'],'post_total':stat['post_total'],'post_known':stat['post_known']})
   # Non-interventional coverage and bin co-occurrence on development episodes, across time.
   for t in range(e['n']):
    vals={n:ns['calibrated_bucket'](ns['advantage'](e,t,n,localq[n]),n) for n in ns['G']}
    for n,v in vals.items():signal_bins[n][v]+=1
    for a in ns['G']:
     for b in ns['G']:
      if a<b:pair[(a,b,vals[a],vals[b])]+=1
    for ins in (False,True):
     s=ns['coord_state'](e,t,ins,mode,localq,ablate)
     for a in ns['acts'](t,ins):seen[(ins,a)]+=1;post[(ins,a)]+=int((s,a) in q)
  import pandas as pd
  met=ns['metrics'](pd.DataFrame(predictions))
  counts=collections.Counter(r['class'] for r in ep_rows if r['seed']==seed and r['variant']==label and r['condition']==condition)
  expected={k:int(met[k.lower()]) for k in ('TP','TN','FP','FN')}
  assert all(counts[k]==v for k,v in expected.items()),f'FAIL confusion mismatch seed={seed} variant={label}: {counts} vs {expected}'
  rows.append({'seed':seed,'variant':label,'condition':condition,'mcc':met['mcc'],'recall':met['recall'],'fpr':met['fpr'],'tp':met['tp'],'tn':met['tn'],'fp':met['fp'],'fn':met['fn'],'coordinator_q_entries':len(q),'local_q_entries':sum(len(v) for v in localq.values())})
  for (ins,a),total in sorted(seen.items()):coverage.append({'seed':seed,'variant':label,'inspected':int(ins),'action':a,'possible_observations':total,'q_covered':post[(ins,a)],'coverage_fraction':post[(ins,a)]/total})
  # Joint calibrated-bucket contingency across development validation observations.
  # Association is descriptive, not a measure of causal contribution.
  for (a,b,va_bin,vb_bin),nobs in sorted(pair.items()):
   joint_rows.append({'seed':seed,'variant':label,'specialist_a':a,'specialist_b':b,'bucket_a':va_bin,'bucket_b':vb_bin,'observations':nobs})
  for n,c in signal_bins.items():
   for v,k in sorted(c.items()):state_rows.append({'seed':seed,'variant':label,'specialist':n,'bucket':v,'observations':k})
  # Post-hoc inference-only counterfactual: hold learned Q fixed, neutralize one signal.
  # Does NOT estimate retraining impact; do not interpret as causal contribution.
  if label=='four_q':
   for specialist in ns['G']:
    dd=pd.DataFrame([ns['roll'](e,q,'multi',localq,random.Random(0),ablate=specialist,persist=persist,known_first=known) for e in ns['va']]);m=ns['metrics'](dd)
    cf_rows.append({'seed':seed,'neutralized_specialist':specialist,'mcc':m['mcc'],'fpr':m['fpr'],'recall':m['recall'],'delta_mcc_vs_full':m['mcc']-met['mcc']})
  print(seed,label,'MCC',round(met['mcc'],3),'FP',met['fp'],'FN',met['fn'],flush=True)
def save(name,data):
 with (O/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
for name,data in [('r80_metrics.csv',rows),('r80_episode_errors.csv',ep_rows),('r80_q_coverage.csv',coverage),('r80_specialist_buckets.csv',state_rows),('r80_inference_counterfactual.csv',cf_rows),('r81_joint_buckets.csv',joint_rows)]:save(name,data)
assert len(rows)==len(seeds)*len(variants) and len(ep_rows)==len(seeds)*len(variants)*len(ns['va'])
assert all(r['tp']+r['tn']+r['fp']+r['fn']==len(ns['va']) for r in rows)
report={'status':'PASS','purpose':'E3-R81 six architectures retrained and joint specialist bucket distributions; development only','seeds':seeds,'condition':condition,'local_steps':local_steps,'coordinator_steps':coord_steps,'architectures':[x[0] for x in variants],'validation_episodes':len(ns['va']),'confusion_consistency':'PASS','counts':{'configurations':len(rows),'episode_predictions':len(ep_rows),'coverage_rows':len(coverage),'counterfactuals':len(cf_rows)},'train_sha256':hashlib.sha256((P/'data/train.csv.gz').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'limitations':['Calibration uses development validation observations (unlabeled), hence validation is not independent of calibration; must be moved to training-only before confirmatory protocol','Engine imports and preprocesses historical test.csv.gz at initialization, although R80 evaluates only va: remove test ingestion for a future clean confirmatory pipeline','The validation split has been used repeatedly for development and is not independent','Counterfactual neutralization uses unchanged trained Q and is not equivalent to retraining an ablated specialist','Specialist bin counts are descriptive, not mutual information or causal attribution','No capacity/CPU matching','No externally labeled independent attacks','Fixed final checkpoints; not directly comparable to R76 validation-selected checkpoints']}
(O/'r81_structural_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
(O/'R81_RELATORIO_PT.md').write_text('# E3-R80 — Diagnóstico estrutural (desenvolvimento)\n\nEstado: PASS; configurações: '+str(len(rows))+'; episódios: '+str(len(ep_rows))+'\n\n## Ficheiros\n- r80_metrics.csv: MCC, FPR, recall e matriz de confusão por semente\n- r80_episode_errors.csv: classificação TP/TN/FP/FN por episódio e cobertura de Q nas decisões\n- r80_q_coverage.csv: cobertura observada dos pares estado-ação\n- r80_specialist_buckets.csv: distribuição marginal de sinais dos especialistas\n- r80_inference_counterfactual.csv: neutralização **apenas na inferência**, sem retreino\n\n## Avisos\n- Dados de validação de desenvolvimento já explorados. Sem inferência confirmatória.\n- Neutralização pós-treino não prova importância causal; comparar com ablação retreinada.\n- O motor carrega historicamente test.csv.gz no arranque; a R80 não o avalia, mas esta dependência deve ser removida antes do protocolo independente.\n- O estudo de redundância entre sinais e a equivalência de capacidade ainda exigem uma fase adicional.\n',encoding='utf-8')
print('R81 PASS',len(rows),'configurations',flush=True)

# Empirical pairwise mutual information from joint bucket counts (bits).
import math
mi_rows=[]
for seed in seeds:
 for label,_,_ in variants:
  sub=[r for r in joint_rows if r['seed']==seed and r['variant']==label]
  pairs=sorted(set((r['specialist_a'],r['specialist_b']) for r in sub))
  for a,b in pairs:
   obs=[r for r in sub if r['specialist_a']==a and r['specialist_b']==b]
   total=sum(r['observations'] for r in obs)
   ma=collections.Counter();mb=collections.Counter()
   for r in obs:ma[r['bucket_a']]+=r['observations'];mb[r['bucket_b']]+=r['observations']
   mi=sum((r['observations']/total)*math.log2((r['observations']*total)/(ma[r['bucket_a']]*mb[r['bucket_b']])) for r in obs if r['observations']>0) if total else 0
   mi_rows.append({'seed':seed,'variant':label,'specialist_a':a,'specialist_b':b,'mutual_information_bits':mi,'observations':total})
save('r81_pairwise_mutual_information.csv',mi_rows)
assert len(mi_rows)==len(seeds)*len(variants)*6
assert all(r['mutual_information_bits']>=-1e-10 for r in mi_rows)
print('R81 pairwise MI PASS',len(mi_rows),flush=True)
