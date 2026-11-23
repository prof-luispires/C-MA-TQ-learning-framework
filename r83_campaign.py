"""R83: large-scale development benchmark using only original synthetic train.csv.gz.
No historical test access, no checkpoint selection, no tuning, no claims of independent validation.
"""
import csv,json,os,sys,time,random,hashlib,platform,statistics,pickle,tracemalloc
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent; O=P/'results';O.mkdir(exist_ok=True)
source=P/'core/r82_clean_engine.py'
assert 'test.csv.gz' not in source.read_text(encoding='utf8')
ns={'__file__':str(source),'__name__':'r83_clean'}
exec(compile(source.read_text(encoding='utf8'),str(source),'exec'),ns)
assert 'te' not in ns and 'test' not in ns
variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol'),('no_radio','multi','radio'),('no_temporal','multi','temporal')]
mode=os.getenv('R83_MODE','SMOKE').upper(); assert mode in ('SMOKE','PILOT','FULL')
seeds=([42,123] if mode=='SMOKE' else [42,123,2026,31415,27182] if mode=='PILOT' else [42,123,2026,31415,27182,17,29,73,101,211,307,401,503,601,701,809,907,1009,1103,1201])
local_steps=int(os.getenv('R83_LOCAL_STEPS','80' if mode=='SMOKE' else '600'))
coord_steps=int(os.getenv('R83_COORD_STEPS','150' if mode=='SMOKE' else '1000'))
assert local_steps>0 and coord_steps>0
rows=[];episodes=[]; costs=[]
for seed in seeds:
 rng=random.Random(seed); localq={};t0=time.perf_counter()
 for name in ns['G']:
  q={}
  for i in range(1,local_steps+1):
   e=ns['balanced_choice'](ns['tr'],rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)))
   ns['local_roll'](e,name,q,rng,eps,True)
  localq[name]=q
 local_elapsed=time.perf_counter()-t0
 ns['fit_calibration'](localq)
 for label,architecture,ablate in variants:
  rr=random.Random(seed+71);q={}; t1=time.perf_counter()
  for i in range(1,coord_steps+1):
   e=ns['balanced_choice'](ns['tr'],rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)))
   ns['coord_roll'](e,q,architecture,localq,rr,eps,True,ablate)
  train_elapsed=time.perf_counter()-t1
  t2=time.perf_counter(); pred=ns['evaluate'](ns['va'],q,architecture,localq,ablate)
  infer_elapsed=time.perf_counter()-t2
  met=ns['metrics'](pred)
  record={'seed':seed,'variant':label,'mode':mode,'local_steps_per_specialist':local_steps,'coordinator_steps':coord_steps,**met,'local_q_entries':sum(map(len,localq.values())),'coordinator_q_entries':len(q),'local_train_seconds_shared':local_elapsed,'coordinator_train_seconds':train_elapsed,'validation_inference_seconds':infer_elapsed,'inference_ms_per_episode':1000*infer_elapsed/len(ns['va']),'serialized_coord_bytes':len(pickle.dumps(q,protocol=4)),'serialized_local_bytes_shared':len(pickle.dumps(localq,protocol=4))}
  rows.append(record)
  for r in pred.to_dict('records'):
   positive=int(r['pred']==1 and (r['y']==0 or r['t']>=r['onset']))
   category=('TP' if positive else 'FN') if r['y']==1 else ('FP' if positive else 'TN')
   episodes.append({'seed':seed,'variant':label,'episode_id':r['episode_id'],'scenario':r['scenario'],'class':category,'alert_t':r['t'],'onset':r['onset'],'inspections':r['inspections']})
  c=Counter(x['class'] for x in episodes if x['seed']==seed and x['variant']==label)
  assert all(c[k]==met[k.lower()] for k in ('TP','TN','FP','FN')),(seed,label,c,met)
  print(mode,seed,label,'MCC',round(met['mcc'],3),'FPR',round(met['fpr'],3),flush=True)
def save_csv(path,records):
 with (O/path).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
save_csv('r83_metrics.csv',rows);save_csv('r83_episode_predictions.csv',episodes)
summary=[]
for label,_,_ in variants:
 group=[r for r in rows if r['variant']==label]
 item={'variant':label,'seeds':len(group)}
 for key in ('mcc','f1','recall','fpr','bal_acc','coordinator_train_seconds','inference_ms_per_episode','coordinator_q_entries'):
  v=[r[key] for r in group];item[key+'_mean']=statistics.mean(v);item[key+'_sd']=statistics.stdev(v) if len(v)>1 else 0
 summary.append(item)
save_csv('r83_summary.csv',summary)
manifest={'status':'PASS','scope':'development_only_nonconfirmatory','mode':mode,'dataset':'original synthetic LoRaWAN train.csv.gz only','historical_test_loaded':False,'train_sha256':hashlib.sha256((P/'data/train.csv.gz').read_bytes()).hexdigest(),'clean_engine_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seeds':seeds,'architectures':[x[0] for x in variants],'train_unique_episode_ids':len({str(e['id']).removeprefix('hard_') for e in ns['tr']}),'validation_unique_episode_ids':len({str(e['id']).removeprefix('hard_') for e in ns['va']}),'train_validation_overlap':len({str(e['id']).removeprefix('hard_') for e in ns['tr']}&{str(e['id']).removeprefix('hard_') for e in ns['va']}),'local_steps_per_specialist':local_steps,'coordinator_steps':coord_steps,'configuration_count':len(rows),'episode_count':len(episodes),'confusion_consistency':'PASS','calibration':'training_only','checkpoint':'final_fixed','python':sys.version,'platform':platform.platform(),'limitations':['Validation episodes have been repeatedly explored in previous iterations; NOT an independent test','No real traffic dataset; only original synthetic LoRaWAN data','Same transition count but not equal wall-clock, state-space capacity or total effective computation','Local specialist training cost shared across variants; coordinator timing excludes local training','Ablation holds removed signal in neutral bucket, retrains coordinator, retains local specialist training','No external generalization claims']}
assert manifest['train_validation_overlap']==0
(O/'r83_campaign_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
(O/'R83_RELATORIO_PT.md').write_text('# E3-R83 — Campanha de desenvolvimento ('+mode+')\n\nPASS: '+str(len(rows))+' configurações, '+str(len(episodes))+' previsões; sem teste histórico.\n\n**Não é avaliação confirmatória.** Dataset original sintético e validação previamente explorada.\n',encoding='utf8')
print('R83 PASS',len(rows),'configurations',len(episodes),'episodes')
