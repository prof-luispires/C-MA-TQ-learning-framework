import unittest,ast,pathlib,types,random
import numpy as np
P=pathlib.Path(__file__).resolve().parent
class R70Tests(unittest.TestCase):
 def test_structure(self):
  source=(P/'r70_engine.py').read_text(); tree=ast.parse(source)
  self.assertIn('forced_inspection_probability_min_0.35_epsilon',source)
  self.assertIn('learned_post_inspection_entries',source)
  self.assertIn('compressed_group_median',source)
 def test_post_inspection_state_sensitive(self):
  source=(P/'r70_engine.py').read_text();tree=ast.parse(source)
  functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  m=ast.Module(body=[functions[x] for x in ('local_state','advantage','calibrated_bucket','coord_state')],type_ignores=[])
  ns={'np':np,'G':{'radio':['rssi','snr'],'temporal':['delta_t_derived'],'phy':['c2','c8','c9','c15'],'protocol':['counter_step_derived']},'F':['rssi','snr','delta_t_derived','c2','c8','c9','c15','counter_step_derived'],'CAL':{n:(0.,1.) for n in ('radio','temporal','phy','protocol')},'PERM_MAP':{}}
  exec(compile(m,'<r70-test>','exec'),ns)
  e={'id':'test','n':24,'b':{f:np.array([1]*24) for f in ns['F']}}
  localq={n:{} for n in ns['G']}
  s0=ns['coord_state'](e,8,False,'multi',localq)
  s1=ns['coord_state'](e,8,True,'multi',localq)
  self.assertNotEqual(s0,s1)
  radio=ns['local_state'](e,8,'radio');localq['radio'][(radio,1)]=4.
  s2=ns['coord_state'](e,8,True,'multi',localq)
  self.assertNotEqual(s1,s2,'Specialist Q change must reach coordinator state')
  self.assertEqual(s0,ns['coord_state'](e,8,False,'central',localq))
if __name__=='__main__':unittest.main()
