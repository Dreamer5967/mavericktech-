import unittest
from services.control.corridor_controller import CorridorController
from services.control.phase_manager import SafetyPhaseManager
from services.security.firewall import SecurityFirewall

class CorridorRegressions(unittest.TestCase):
 def setUp(self):
  self.manager=SafetyPhaseManager({'J1':{'NS_GREEN','EW_GREEN'}})
  self.controller=CorridorController(self.manager,SecurityFirewall(operator_secret='fixture-only'),{'J1':100})
 def test_invalid_route_and_time(self):
  self.assertFalse(self.controller.dispatch_corridor('fixture-only','test',route=['unknown'])[0])
  for dt in [float('nan'),float('inf'),-1,0]:
   with self.assertRaises(ValueError):self.controller.step(dt)
 def test_clearance_does_not_flush_queue(self):
  state=self.manager.states['J1'];state.current_phase='EW_GREEN';state.elapsed_s=6
  self.controller.dispatch_corridor('fixture-only','test');self.controller.step(5)
  self.assertEqual(self.controller.junction_states['J1'].estimated_queue,4)
  self.assertFalse(self.controller.get_status()['actuation_permitted'])
 def test_rejection_logs_no_token(self):
  self.controller.dispatch_corridor('invalid-fixture','test')
  self.assertNotIn('token_prefix',self.controller.event_log[-1]['details'])
