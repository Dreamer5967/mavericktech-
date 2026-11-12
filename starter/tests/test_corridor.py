"""
Unit tests for AEGIS-EVC Emergency Green Corridor Service.
Tests V2X authentication, queue flushing progression, and MAPPO recovery.
"""
import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from starter.aegis_helpers.corridor_service import EmergencyCorridorService, CorridorStage


class EmergencyCorridorTests(unittest.TestCase):
    def setUp(self):
        self.service = EmergencyCorridorService()

    def test_unauthorized_dispatch_blocked(self):
        # Viewer token cannot dispatch emergency corridor
        success, msg, _ = self.service.dispatch_vehicle(
            token="unauthorized-token",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1,
        )
        self.assertFalse(success)
        self.assertIn("FIREWALL_DENIED", msg)

    def test_authorized_dispatch_success(self):
        success, msg, telem = self.service.dispatch_vehicle(
            token="local-demo-only",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1,
        )
        self.assertTrue(success)
        self.assertEqual(self.service.stage, CorridorStage.PRE_FLUSH)
        self.assertIsNotNone(telem)
        self.assertEqual(telem["active_vehicle"]["vehicle_id"], "AMB-101")

    def test_simulation_progression_and_flush(self):
        self.service.dispatch_vehicle(
            token="local-demo-only",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1,
        )
        # Advance 10 ticks
        for _ in range(10):
            telem = self.service.tick(delta_s=1.0)

        # Vehicle should have advanced 180m
        self.assertAlmostEqual(telem["active_vehicle"]["position_m"], 180.0, places=1)
        # J1 should have started flushing or reached green
        j1 = telem["junctions"]["J1"]
        self.assertIn(j1["phase"], ["PRE_FLUSH_YELLOW", "EVC_PRIORITY_GREEN"])

    def test_cancel_corridor(self):
        self.service.dispatch_vehicle(
            token="local-demo-only",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1,
        )
        cancelled, msg = self.service.cancel_corridor("local-demo-only")
        self.assertTrue(cancelled)
        self.assertEqual(self.service.stage, CorridorStage.STANDBY)
        self.assertIsNone(self.service.active_vehicle)


if __name__ == "__main__":
    unittest.main()
