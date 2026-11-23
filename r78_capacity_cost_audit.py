"""E3-R78: observational capacity, cost and evaluation-protocol audit.
Does not retrain, alter reward, select models, or access test.csv.gz.
"""
import json,csv,hashlib,statistics,sys,time,tracemalloc,platform,ast,random
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parent;O=P/'results';O.mkdir(exist_ok=True)
J=P/'inputs/r76_multiseed_audit.json';T=P/'inputs/r76_multiseed_td_trace.csv'
D=json.loads(J.read_text(encoding='utf-8'));R=D['results']
assert D['status']=='PASS' and len(R)==75 and len(D['seed_list'])==5
variants=('central','four_q','no_phy','no_protocol','permuted_q');conds=('baseline','persist_inspection','persist_known_first')
assert {(r['seed'],r['variant'],r['condition']) for r in R}=={(s,v,c) for s in D['seed_list'] for v in variants for c in conds}
# empirical coordinator state occupancy from genuine training traces; not full state-space capacity
seen=defaultdict(set);sa=defaultdict(set);types=defaultdict(lambda:defaultdict(int));counts=defaultdict(int)
with T.open(encoding='utf-8-sig',newline='') as f:
 for r in csv.DictReader(f):
  k=(r['variant'],r['condition']);seen[k].add(r['state']);sa[k].add((r['state'],r['action']));counts[k]+=1;types[k][r['selection_type']]+=1
# Compare observed policy occupancy across seeds, no inference of equal capacity.
rows=[]
for c in conds:
 for v in variants:
  rr=[r for r in R if r['variant']==v and r['condition']==c]
  def vals(fn):return [fn(r) for r in rr]
  def mean(fn):return statistics.mean(vals(fn))
  rows.append({'condition':c,'variant':v,'n_seeds':5,'local_steps':D['local_steps'],'coordinator_steps':D['coordinator_steps'], 'policy_entries_mean':mean(lambda r:r['policy_entries']),'policy_entries_min':min(vals(lambda r:r['policy_entries'])),'policy_entries_max':max(vals(lambda r:r['policy_entries'])),'selected_step_mean':mean(lambda r:r['selected_step']),'unseen_rate_mean':mean(lambda r:r['stats']['unseen_selected']/r['stats']['decisions']),'observed_training_states':len(seen[(v,c)]),'observed_training_state_actions':len(sa[(v,c)]),'observed_trace_rows':counts[(v,c)],'mcc_mean':mean(lambda r:r['metrics']['mcc']),'fpr_mean':mean(lambda r:r['metrics']['fpr']),'recall_mean':mean(lambda r:r['metrics']['recall'])})
with (O/'r78_capacity_observed.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Microbenchmark only state encoding, using pre-existing calibration/training data. No inference-policy benchmark claims.
bench={};error=None
try:
 src=P/'core/r72_engine.py';tree=ast.parse(src.read_text(encoding='utf-8'))
 stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='Nlocal' for t in n.targets))
 ns={'__file__':str(src),'__name__':'r78_defs'}
 exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(src),'exec'),ns)
 localq={k:{} for k in ns['G']};ns['fit_calibration'](localq)
 episodes=ns['va'][:min(20,len(ns['va']))];assert episodes
 for name,mode,ablate in [('central','central',None),('four_q','multi',None),('no_phy','multi','phy'),('no_protocol','multi','protocol')]:
  for e in episodes:ns['coord_state'](e,0,False,mode,localq,ablate)
  n=4000;tracemalloc.start();start=time.perf_counter_ns()
  for i in range(n):
   e=episodes[i%len(episodes)];ns['coord_state'](e,min(5,e['n']-1),False,mode,localq,ablate)
  elapsed=time.perf_counter_ns()-start;current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  bench[name]={'calls':n,'ns_per_call':elapsed/n,'peak_tracemalloc_bytes':peak,'scope':'state encoding only; empty local Q; Python tracemalloc overhead; not end-to-end inference'}
except Exception as ex:error=repr(ex)
# design matrix identifies the fairness gaps, without claiming to solve them
fairness={'matched_seeds':True,'same_training_step_budget':True,'same_validation_episodes':True,'same_reward':True,'matched_parameter_capacity':False,'matched_state_space':False,'independent_checkpoint_selection_and_evaluation':False,'independent_external_attack_labels':False,'full_training_runtime_measured':False,'end_to_end_inference_runtime_measured':False,'memory_usage_model_measured':False}
report={'status':'PASS' if error is None else 'PARTIAL','scope':'development audit; NOT confirmatory','source_sha256':hashlib.sha256(J.read_bytes()).hexdigest(),'trace_sha256':hashlib.sha256(T.read_bytes()).hexdigest(),'data_train_sha256':D['train_sha256'],'seed_list':D['seed_list'],'configuration_count':len(R),'capacity_observed':rows,'state_encoding_microbenchmark':bench,'microbenchmark_error':error,'fairness_matrix':fairness,'environment':{'python':sys.version,'platform':platform.platform()},'limitations':['Empirical occupied Q entries are not theoretical model capacity','State-encoding microbenchmark excludes Q-learning, local agents, I/O and end-to-end inference','tracemalloc peak is allocation during microbenchmark, not model resident memory','No held-out confirmatory results; validation reused for checkpoint selection','No independent labeled external attacks; do not interpret this audit as external generalization','Capacity matching and true wall-clock training/inference benchmarks remain necessary'],'recommendation':'Do not freeze scientific claims; next create a matched-budget and held-out protocol before confirmatory testing.'}
(O/'r78_capacity_cost_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
lines=['# E3-R78 — Auditoria de capacidade e comparabilidade','','**Âmbito:** desenvolvimento, sem treino adicional nem acesso ao conjunto de teste.','','## Verificações','']
for k,v in fairness.items():lines.append(f'- {k}: {"SIM" if v else "NÃO"}')
lines+=['','## Interpretação','','A ocupação observada da tabela Q não equivale à capacidade teórica. O microbenchmark mede exclusivamente a codificação de estado, com Q locais vazias; não mede o tempo de inferência nem o custo de treino.','','## Decisão','','Não congelar conclusões científicas: faltam equivalência de capacidade, benchmark completo e avaliação independente.']
(O/'R78_RELATORIO_PT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('R78',report['status'],'configurations',len(R),'microbenchmarks',len(bench),'output',O)
