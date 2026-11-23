"""R82: isolated leakage-free engine audit and development-only pilot. Not confirmatory."""
import ast,hashlib,json,random,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;O=P/'results';O.mkdir(exist_ok=True)
src=P/'core/r82_clean_engine.py'
code=src.read_text(encoding='utf-8')
assert 'test.csv.gz' not in code and 'read_csv' in code
assert 'for e in tr for t in range(5' in code
ns={'__file__':str(src),'__name__':'r82_clean'}
exec(compile(code,str(src),'exec'),ns)
assert len(ns['tr'])>0 and len(ns['va'])>0 and 'te' not in ns and 'test' not in ns
train_ids={str(e['id']).removeprefix('hard_') for e in ns['tr']};val_ids={str(e['id']).removeprefix('hard_') for e in ns['va']}
assert train_ids.isdisjoint(val_ids), 'TRAIN-VALIDATION LEAKAGE'
assert len(train_ids)>0 and len(val_ids)>0
# Train a small pilot to verify calibration is computed from train only.
rng=random.Random(42);localq={};steps=int(os.getenv('R82_PILOT_STEPS','20'))
for name in ns['G']:
 q={}
 for i in range(1,steps+1):
  e=ns['balanced_choice'](ns['tr'],rng,i)
  ns['local_roll'](e,name,q,rng,.3,True)
 localq[name]=q
ns['fit_calibration'](localq)
assert len(ns['CAL'])==len(ns['G'])
report={'status':'PASS','scope':'R82 clean engine isolated pilot; not a frozen confirmatory experiment',
 'train_file_sha256':hashlib.sha256((P/'data/train.csv.gz').read_bytes()).hexdigest(),
 'clean_engine_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'train_unique_episode_ids':len(train_ids),'validation_unique_episode_ids':len(val_ids),
 'train_validation_id_overlap':len(train_ids&val_ids),'historical_test_loaded':False,
 'calibration_partition':'training_only','local_pilot_steps_per_specialist':steps,
 'calibration':{k:list(v) for k,v in ns['CAL'].items()},
 'limitations':['Existing R81 and earlier scripts retain legacy behavior and are not confirmatory',
 'Training/validation partitions from historically explored data; validation not independent',
 'No external labeled independent evaluation data provided',
 'Capacity and wall-clock budgets not yet matched',
 'No R83 large-scale campaign performed']}
(O/'r82_freeze_readiness.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('R82 CLEAN ENGINE PILOT PASS',len(train_ids),len(val_ids),'episode IDs')
