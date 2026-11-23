"""E3-R65 integrated development runner; NOT confirmatory."""
import argparse, subprocess, sys, os, json, hashlib, platform, time, pathlib
P=pathlib.Path(__file__).resolve().parent

def fingerprint(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def main():
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['check','smoke','development','results','r70_smoke','r70_development']);a.add_argument('--seeds',type=int,default=5);a.add_argument('--steps',type=int,default=3500);args=a.parse_args()
 if args.mode=='check':
  import numpy,pandas,sklearn
  print('Python',sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'sklearn',sklearn.__version__)
  import unittest
  suite=unittest.defaultTestLoader.discover(str(P/'core'),pattern='test_*.py')
  r=unittest.TextTestRunner(verbosity=2).run(suite)
  if not r.wasSuccessful():sys.exit(1)
  print('Data SHA256:',json.dumps({f.name:fingerprint(f) for f in sorted((P/'data').glob('*.gz'))},indent=2));return
 if args.mode=='results':
  import pandas as pd
  p=P/'results'/'metrics_by_seed.csv'
  if not p.exists():sys.exit('No experiment outputs. Run smoke/development first.')
  df=pd.read_csv(p);print(df.groupby('variant')[['mcc','bal_acc','recall','fpr','inspections']].agg(['mean','std']).to_string());return
 env=os.environ.copy();env['NUM_SEEDS']=str(1 if args.mode in ('smoke','r70_smoke') else args.seeds);env['LOCAL_STEPS']=str(80 if args.mode=='r70_smoke' else 30 if args.mode=='smoke' else args.steps);env['COORD_STEPS']=str(80 if args.mode=='r70_smoke' else 30 if args.mode=='smoke' else args.steps)
 if args.mode in ('development','r70_development'):
  print('WARNING: existing test campaigns have already been explored; results are exploratory, NOT confirmatory.',flush=True)
 else:print('SMOKE TEST ONLY: metrics have no scientific interpretation.',flush=True)
 start=time.perf_counter();proc=subprocess.run([sys.executable,str(P/'core'/('r70_engine.py' if args.mode.startswith('r70_') else 'legacy_engine.py'))],env=env,cwd=P)
 if proc.returncode:sys.exit(proc.returncode)
 import pandas as pd
 from core.evaluation import evaluate
 preds=pd.read_csv(P/'results'/'predictions_by_episode.csv')
 rows=[]
 for (seed,variant),d in preds.groupby(['seed','variant']):
  rows.append({'seed':seed,'variant':variant,**evaluate(d)})
 pd.DataFrame(rows).to_csv(P/'results'/'metrics_FROZEN_corrected.csv',index=False)
 meta={'mode':args.mode,'engine':'r70_engine.py' if args.mode.startswith('r70_') else 'legacy_engine.py','confirmatory':False,'seeds':int(env['NUM_SEEDS']),'steps':int(env['LOCAL_STEPS']),'elapsed_seconds':time.perf_counter()-start,'python':platform.python_version(),'files_sha256':{f.name:fingerprint(f) for f in sorted((P/'data').glob('*.gz'))}}
 (P/'results'/'run_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 print('Frozen evaluator metrics:',(P/'results'/'metrics_FROZEN_corrected.csv').as_posix())
if __name__=='__main__':main()
