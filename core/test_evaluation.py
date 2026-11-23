import unittest
import pandas as pd
from evaluation import evaluate

def row(id,y,pred,t,onset=8):return dict(episode_id=id,y=y,pred=pred,t=t,onset=onset,inspections=0)
class TestFrozenEvaluation(unittest.TestCase):
 def test_all_four_outcomes(self):
  d=pd.DataFrame([row('tp',1,1,10),row('tn',0,0,23),row('fp',0,1,12),row('fn',1,0,23)])
  m=evaluate(d);self.assertEqual(tuple(m[k] for k in ('tp','tn','fp','fn')),(1,1,1,1));self.assertEqual(m['fpr'],.5)
 def test_premature_is_not_tp(self):
  m=evaluate(pd.DataFrame([row('early',1,1,5),row('normal',0,0,23)]))
  self.assertEqual((m['tp'],m['fn'],m['premature']),(0,1,1))
 def test_normal_alert_is_fp(self):
  m=evaluate(pd.DataFrame([row('normal',0,1,9),row('anomaly',1,1,9)]))
  self.assertEqual((m['fp'],m['tp'],m['fpr']),(1,1,1.0))
 def test_duplicates_rejected(self):
  with self.assertRaises(ValueError):evaluate(pd.DataFrame([row('same',1,1,9),row('same',0,0,9)]))
 def test_future_onset_not_detected(self):
  m=evaluate(pd.DataFrame([row('a',1,1,7,8),row('b',1,1,8,8)]))
  self.assertEqual((m['tp'],m['fn'],m['premature']),(1,1,1))
if __name__=='__main__':unittest.main()
