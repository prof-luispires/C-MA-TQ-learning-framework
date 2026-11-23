"""Frozen event-level evaluator, version 1.0. No fitted model or tuning."""
import numpy as np
import pandas as pd
from sklearn.metrics import matthews_corrcoef, balanced_accuracy_score, f1_score, confusion_matrix

def evaluate(d):
    required={'episode_id','y','pred','t','onset'}
    if not required.issubset(d): raise ValueError('Missing '+str(required-set(d)))
    if d.episode_id.duplicated().any(): raise ValueError('Duplicate episodes within evaluation group')
    if not set(d.y.unique()).issubset({0,1}) or not set(d.pred.unique()).issubset({0,1}):raise ValueError('Invalid binary labels')
    if d[['t','onset']].isna().any().any():raise ValueError('Missing time/onset')
    premature=(d.y.eq(1)&d.pred.eq(1)&d.t.lt(d.onset))
    valid=(d.y.eq(1)&d.pred.eq(1)&d.t.ge(d.onset))
    # Premature alerts are FN for event detection, plus a separate premature alarm.
    predicted=(valid | (d.y.eq(0)&d.pred.eq(1))).astype(int)
    tn,fp,fn,tp=confusion_matrix(d.y,predicted,labels=[0,1]).ravel()
    positives=tp+fn;negatives=tn+fp
    delays=(d.loc[valid,'t']-d.loc[valid,'onset']).astype(float)
    return {'n':len(d),'tp':int(tp),'tn':int(tn),'fp':int(fp),'fn':int(fn),
      'premature':int(premature.sum()),'mcc':float(matthews_corrcoef(d.y,predicted)),
      'balanced_accuracy':float(balanced_accuracy_score(d.y,predicted)),
      'f1':float(f1_score(d.y,predicted,zero_division=0)),
      'recall':float(tp/positives) if positives else np.nan,
      'fpr':float(fp/negatives) if negatives else np.nan,
      'delay_messages':float(delays.mean()) if len(delays) else np.nan,
      'inspections_per_episode':float(d.inspections.mean()) if 'inspections' in d else np.nan}
