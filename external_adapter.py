"""Validate external episode data; no inference or label fabrication."""
import argparse,pandas as pd
REQUIRED={'episode_id','t','scenario','onset','rssi','snr','delta_t_derived','counter_step_derived','c2','c8','c9','c15'}
def main():
 p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--output',default='external_validated.csv');a=p.parse_args()
 d=pd.read_csv(a.csv);missing=REQUIRED-set(d.columns)
 if missing:raise ValueError(f'Missing fields: {sorted(missing)}. A documented source-to-feature mapping is required.')
 if d.duplicated(['episode_id','t']).any():raise ValueError('Duplicate episode/time pairs')
 if d[list(REQUIRED-{'episode_id','scenario'})].isna().any().any():raise ValueError('Missing numeric values; do not impute external data silently')
 for eid,g in d.groupby('episode_id'):
  if not g.t.is_monotonic_increasing:raise ValueError(f'Unordered episode {eid}')
  if g.scenario.nunique()!=1 or g.onset.nunique()!=1:raise ValueError(f'Inconsistent ground truth in {eid}')
 print('SCHEMA PASS; label provenance and source overlap still require manual verification')
 d.to_csv(a.output,index=False)
if __name__=='__main__':main()
