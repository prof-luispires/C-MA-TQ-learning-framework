"""E3-R77: descriptive matched-seed development analysis. No test evaluation."""
import json,csv,statistics,math,hashlib,sys
from pathlib import Path
from collections import defaultdict,Counter
P=Path(__file__).resolve().parent
J=P/'inputs/r76_multiseed_audit.json'; C=P/'inputs/r76_multiseed_td_trace.csv';O=P/'results';O.mkdir(exist_ok=True)
d=json.loads(J.read_text(encoding='utf-8'))
assert d['status']=='PASS' and len(d['seed_list'])==5
assert len(d['results'])==75
seeds=d['seed_list']; variants=['central','four_q','no_phy','no_protocol','permuted_q'];conds=['baseline','persist_inspection','persist_known_first']
by={(r['seed'],r['variant'],r['condition']):r for r in d['results']}
assert len(by)==75 and all((s,v,c) in by for s in seeds for v in variants for c in conds)
assert len({r['train_sha256'] for r in [d]})==1
metrics=['mcc','bal_acc','f1','recall','fpr','premature_rate','delay_messages','inspections','mean_reward']
def avg(a):return statistics.mean(a)
def sd(a):return statistics.stdev(a) if len(a)>1 else 0
summary=[]
for c in conds:
 for v in variants:
  rs=[by[(s,v,c)] for s in seeds]
  rec={'condition':c,'variant':v,'n_seeds':len(seeds),'selected_step_mean':avg([r['selected_step'] for r in rs]),'policy_entries_mean':avg([r['policy_entries'] for r in rs]),'unseen_rate_mean':avg([r['stats']['unseen_selected']/r['stats']['decisions'] for r in rs]),'reset_count_total':sum(r['stats']['reset_after_inspection_wait'] for r in rs)}
  for m in metrics:
   vals=[r['metrics'][m] for r in rs];rec[m+'_mean']=avg(vals);rec[m+'_sd']=sd(vals);rec[m+'_min']=min(vals);rec[m+'_max']=max(vals)
  summary.append(rec)
pairs=[]
for c in conds:
 for v in ['central','no_phy','no_protocol','permuted_q']:
  x=[by[(s,'four_q',c)]['metrics']['mcc']-by[(s,v,c)]['metrics']['mcc'] for s in seeds]
  f=[by[(s,'four_q',c)]['metrics']['fpr']-by[(s,v,c)]['metrics']['fpr'] for s in seeds]
  pairs.append({'condition':c,'comparison':'four_q minus '+v,'n':5,'mcc_delta_mean':avg(x),'mcc_delta_sd':sd(x),'mcc_positive_seeds':sum(z>0 for z in x),'fpr_delta_mean':avg(f),'mcc_by_seed':dict(zip(map(str,seeds),x))})
checks=[];counts=Counter();trace_rows=0;failures=[]
with C.open(newline='',encoding='utf-8-sig') as fh:
 for r in csv.DictReader(fh):
  trace_rows+=1;counts[r['selection_type']]+=1
  try:
   old=float(r['q_old']);rew=float(r['reward']);future=float(r['future']);target=float(r['td_target']);err=float(r['td_error']);new=float(r['q_new']);done=int(r['done']);updated=int(r['update_applied'])
   ok=(math.isclose(target,rew+.94*(0 if done else future),abs_tol=1e-8) and math.isclose(err,target-old,abs_tol=1e-8) and math.isclose(new,old+(.13*err if updated else 0),abs_tol=1e-8) and r['known_before'] in ('0','1'))
   if not ok and len(failures)<10:failures.append({'line':trace_rows+1,'reason':'TD identity or known_before invalid'})
  except (ValueError,KeyError) as ex:
   if len(failures)<10:failures.append({'line':trace_rows+1,'reason':str(ex)})
assert not failures,failures
checks.append('TD numeric identity and known_before valid for all trace rows')
checks.append('75 complete matched configurations and five seeds')
# Capacity fairness: policy_entries is an observed occupancy proxy, not parameter capacity.
report={'status':'PASS','scope':'development only, not confirmatory','source_sha256':hashlib.sha256(J.read_bytes()).hexdigest(),'trace_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'seeds':seeds,'configuration_count':75,'trace_rows':trace_rows,'selection_types':dict(counts),'checks':checks,'limitations':['Validation set is reused for checkpoint selection; descriptive results only','40 validation episodes per seed (30 attacks, 10 normal); seeds share evaluation episodes','No independently labeled external attack dataset','No capacity-matched centralized baseline; policy_entries is not model capacity','No measured runtime or memory cost; do not interpret decision counts as wall-clock costs','Five seeds are insufficient for robust inferential claims','Reward and training logic unchanged from R76'],'summary':summary,'paired_comparisons':pairs}
(O/'r77_consolidated_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
def writecsv(name,rows):
 with (O/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
writecsv('r77_summary.csv',summary)
writecsv('r77_paired_differences.csv',[{k:v for k,v in r.items() if k!='mcc_by_seed'} for r in pairs])
lines=['# E3-R77 — Análise consolidada (desenvolvimento)','',f'Execuções: {len(by)}; sementes: {seeds}; linhas TD verificadas: {trace_rows}.','', '## MCC médio ± desvio-padrão por condição','']
for c in conds:
 lines.append('### '+c)
 for r in summary:
  if r['condition']==c:lines.append(f"- {r['variant']}: MCC {r['mcc_mean']:.3f} ± {r['mcc_sd']:.3f}; FPR {r['fpr_mean']:.1%}; recall {r['recall_mean']:.1%}; unseen {r['unseen_rate_mean']:.1%}")
lines+=['','## Comparações emparelhadas: four_q − alternativa','']
for r in pairs:lines.append(f"- {r['condition']} / {r['comparison']}: ΔMCC={r['mcc_delta_mean']:+.3f}; four_q superior em {r['mcc_positive_seeds']}/5 sementes; ΔFPR={r['fpr_delta_mean']:+.1%}")
lines+=['','## Limitações','']+['- '+x for x in report['limitations']]
(O/'R77_RELATORIO_PT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('PASS: 75 configurations; ',trace_rows,'TD rows; 5 matched seeds')
