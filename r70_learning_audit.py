from pathlib import Path
import json,pandas as pd
P=Path(__file__).resolve().parent
m=P/'results'/'metrics_by_seed.csv'
if not m.exists():raise SystemExit('Execute 11_R70_SMOKE_TEST.bat primeiro')
d=pd.read_csv(m)
cols=['seed','variant','states','learned_post_inspection_entries','post_inspection_coverage_flag','mcc','fpr','recall']
if any(c not in d.columns for c in cols):raise SystemExit('Resultados nao sao E3-R70. Execute 11_R70_SMOKE_TEST.bat')
rows=d[cols].to_dict(orient='records')
report={'status':'PASS' if all(x['learned_post_inspection_entries']>0 for x in rows) else 'FAIL_COVERAGE','purpose':'development-only; synthetic data previously explored; NOT confirmatory','rows':rows,'limitations':['State design and exploration modified; previous metrics are not directly comparable','Independent labeled attack dataset not yet integrated','Matched capacity and compute benchmark pending']}
p=P/'results'/'r70_learning_audit.json';p.write_text(json.dumps(report,indent=2,default=str));print(json.dumps(report,indent=2,default=str))
