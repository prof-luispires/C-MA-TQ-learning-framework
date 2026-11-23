"""E3-R79 development-only end-to-end benchmark. No test data access.
Measures full training rollouts and full validation rollouts, not only encoding.
Fixed last checkpoint, no validation-driven checkpoint selection.
"""
import ast,os,json,csv,random,time,tracemalloc,statistics,hashlib,platform,sys,gc
from pathlib import Path
P=Path(__file__).resolve().parent;O=P/'results';O.mkdir(exist_ok=True)
source=P/'core/r72_engine.py';tree=ast.parse(source.read_text())
stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in n.targets))
ns={'__file__':str(source),'__name__':'r79_engine'}
exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(source),'exec'),ns)
r76=P/'r76_stability.py';tree2=ast.parse(r76.read_text());stop2=next(i for i,n in enumerate(tree2.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='seed')
# Only load function definitions and constants; do not execute the R76 campaign.
selected=[n for n in tree2.body[:stop2] if isinstance(n,(ast.FunctionDef,))]
exec(compile(ast.Module(body=selected,type_ignores=[]),str(r76),'exec'),ns)
assert 'roll' in ns and 'select' in ns
ns['ns']=ns
local_steps=int(os.getenv('R79_LOCAL_STEPS','100'));coord_steps=int(os.getenv('R79_COORD_STEPS','180'));repeat=int(os.getenv('R79_INFER_REPEATS','5'))
seeds=[42,123] if os.getenv('R79_FULL','0')!='1' else [42,123,2026,31415,27182]
variants=[('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol')]
condition=os.getenv('R79_CONDITION','persist_inspection');assert condition in ('baseline','persist_inspection','persist_known_first')
persist=condition!='baseline';known=condition=='persist_known_first'
assert local_steps>0 and coord_steps>0 and repeat>0
records=[];errors=[]
for seed in seeds:
 rng=random.Random(seed);localq={};gc.collect();tracemalloc.start();t0=time.perf_counter_ns()
 for name in ns['G']:
  q={}
  for i in range(1,local_steps+1):
   e=ns['balanced_choice'](ns['tr'],rng,i);eps=max(.05,.8*(1-i/max(1,local_steps*.85)))
   ns['local_roll'](e,name,q,rng,eps,True)
  localq[name]=q
 ns['fit_calibration'](localq)
 local_ms=(time.perf_counter_ns()-t0)/1e6;_,local_peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 for label,mode,ablate in variants:
  rr=random.Random(seed+71);q={};gc.collect();tracemalloc.start();t0=time.perf_counter_ns()
  for i in range(1,coord_steps+1):
   e=ns['balanced_choice'](ns['tr'],rr,i);eps=max(.05,.8*(1-i/max(1,coord_steps*.85)))
   ns['roll'](e,q,mode,localq,rr,eps,True,ablate,persist,known)
  coord_ms=(time.perf_counter_ns()-t0)/1e6;_,train_peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  # Fixed final checkpoint, development validation for runtime measurement only.
  validation=ns['va'];results=[];timings=[]
  for j in range(repeat):
   for e in validation:
    t0=time.perf_counter_ns();out=ns['roll'](e,q,mode,localq,random.Random(0),ablate=ablate,persist=persist,known_first=known)
    timings.append((time.perf_counter_ns()-t0)/1e6)
    if j==0:results.append(out)
  import pandas as pd
  metrics=ns['metrics'](pd.DataFrame(results))
  records.append({'seed':seed,'variant':label,'condition':condition,'local_steps':local_steps,'coordinator_steps':coord_steps,'validation_episodes':len(validation),'training_local_ms_shared':round(local_ms,4),'training_coordinator_ms':round(coord_ms,4),'training_total_ms':round(local_ms+coord_ms,4),'local_peak_tracemalloc_bytes':local_peak,'coordinator_peak_tracemalloc_bytes':train_peak,'coordinator_q_entries':len(q),'local_q_entries':sum(len(z) for z in localq.values()),'inference_episode_mean_ms':round(statistics.mean(timings),6),'inference_episode_median_ms':round(statistics.median(timings),6),'inference_episode_p95_ms':round(sorted(timings)[int(.95*(len(timings)-1))],6),'mcc_development':metrics['mcc'],'fpr_development':metrics['fpr'],'recall_development':metrics['recall']})
  print(seed,label,'train ms',round(coord_ms,1),'inference mean ms',round(statistics.mean(timings),3),flush=True)
assert len(records)==len(seeds)*len(variants)
fields=list(records[0]);withfile=O/'r79_end_to_end.csv'
with withfile.open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
# No claim of capacity matching: same episode counts do not imply equal computational budgets.
checks={'same_seeds':True,'same_local_training_steps':True,'same_coordinator_training_steps':True,'same_validation_episodes':True,'fixed_checkpoint_no_validation_selection':True,'full_rollout_training_timed':True,'full_rollout_inference_timed':True,'equal_capacity':False,'equal_compute':False,'independent_confirmatory_test':False,'external_attack_labels':False,'resident_set_memory_measured':False}
report={'status':'PASS','purpose':'DEVELOPMENT benchmark only, NOT confirmatory','checks':checks,'seeds':seeds,'local_steps':local_steps,'coordinator_steps':coord_steps,'inference_repeats':repeat,'condition':condition,'results':records,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'train_sha256':hashlib.sha256((P/'data/train.csv.gz').read_bytes()).hexdigest(),'environment':{'python':sys.version,'platform':platform.platform()},'limitations':['Development validation reused historically; metrics not confirmatory','Training times are Python wall-clock with tracemalloc enabled; infer times without tracemalloc','Local training shared across architectures: training_total_ms includes shared local training even for central architecture, therefore not a deployable central cost','tracemalloc measures Python allocated peak, not process RSS','No matching of capacity, state-space size, or CPU budget','Inference episode includes full sequence of state encoding, action selection, Q lookup and reward accounting; excludes file IO and real hardware/network','Runtime comparison is within this machine only; use repetitions and controlled environment','No independent externally labeled attacks','Only fixed last checkpoint; not directly comparable to R76 validation-selected performance']}
(O/'r79_benchmark_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
lines=['# E3-R79 — Benchmark end-to-end (desenvolvimento)','','Executa treino local e do coordenador, com tempos medidos, e inferência de episódios completos. Não utiliza test.csv.gz.','','## Limites metodológicos','','- Os custos de treino local são partilhados e **não** devem ser atribuídos ao modelo centralizado como custo intrínseco.','- Não existe equivalência de capacidade nem de orçamento de CPU entre arquiteturas.','- Os MCC são apenas diagnósticos no conjunto de desenvolvimento, com checkpoint final fixo.','- A memória tracemalloc não é a memória residente do processo.','- A avaliação confirmatória exige dados independentes nunca explorados e rótulos externos.','','## Resultados','']
for r in records:lines.append(f"- Semente {r['seed']} / {r['variant']}: treino coordenador {r['training_coordinator_ms']:.1f} ms; inferência {r['inference_episode_mean_ms']:.3f} ms/episódio; Q={r['coordinator_q_entries']}; MCC desenvolvimento={r['mcc_development']:.3f}")
(O/'R79_RELATORIO_PT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('R79 PASS',len(records),'rows',flush=True)
