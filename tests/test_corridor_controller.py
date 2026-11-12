"""
Comprehensive Integration Tests for AEGIS Emergency Green Corridor
===================================================================
Tests CorridorController, SafetyPhaseManager preemption,
SecurityFirewall authorization, and post-corridor MAPPO compensation.
"""

import unittest
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.control.phase_manager import SafetyPhaseManager
from services.control.corridor_controller import CorridorController, CorridorMode
from services.security.firewall import SecurityFirewall


class TestEmergencyCorridorIntegration(unittest.TestCase):

    def setUp(self):
        self.allowed = {
            "J1": {"NS_GREEN", "EW_GREEN"},
            "J2": {"NS_GREEN", "EW_GREEN"},
            "J3": {"NS_GREEN", "EW_GREEN"},
            "J4": {"NS_GREEN", "EW_GREEN"},
        }
        self.phase_mgr = SafetyPhaseManager(
            allowed_phases=self.allowed,
            min_green_s=10.0,
            yellow_s=3.0,
            all_red_s=2.0,
            max_green_s=60.0
        )
        self.firewall = SecurityFirewall(operator_secret="test-operator-secret")
        self.controller = CorridorController(
            phase_manager=self.phase_mgr,
            firewall=self.firewall,
            junction_distances_m={
                "J1": 100.0,
                "J2": 250.0,
                "J3": 400.0,
                "J4": 550.0,
            }
        )

    def test_unauthorized_dispatch_blocked_by_firewall(self):
        ok, msg = self.controller.dispatch_corridor(
            token="invalid-or-viewer-token",
            vehicle_id="AMB-99",
            vehicle_type="ambulance",
            priority_level=1
        )
        self.assertFalse(ok)
        self.assertIn("SECURITY_FIREWALL_REJECTED", msg)
        self.assertEqual(self.controller.mode, CorridorMode.STANDBY)

    def test_authorized_dispatch_succeeds(self):
        ok, msg = self.controller.dispatch_corridor(
            token="test-operator-secret",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "CORRIDOR_ACTIVE")
        self.assertEqual(self.controller.mode, CorridorMode.FLUSHING)
        self.assertIsNotNone(self.controller.active_vehicle)

    def test_flush_time_calculation(self):
        # 4 vehicles, s = 0.5 veh/s, startup = 2.5s
        # t_flush = 2.5 + (4 / 0.5) = 10.5 seconds
        t_flush = self.controller.calculate_flush_time_s(4.0)
        self.assertAlmostEqual(t_flush, 10.5)

        # 0 vehicles -> 0s
        self.assertEqual(self.controller.calculate_flush_time_s(0.0), 0.0)

    def test_preemption_enforces_mandatory_clearance_stages(self):
        # Place J1 in EW_GREEN (cross street)
        self.phase_mgr.states["J1"].current_phase = "EW_GREEN"
        self.phase_mgr.states["J1"].elapsed_s = 6.0  # >= 5.0 emergency minimum

        # Request emergency preemption for NS_GREEN
        ok, code, seq = self.phase_mgr.request_emergency_preemption("J1", "NS_GREEN", priority_level=1)
        self.assertTrue(ok)
        self.assertEqual(code, "emergency_clearance_initiated")
        self.assertEqual(seq, ["EW_GREEN_YELLOW", "ALL_RED", "NS_GREEN"])

        # In transition: tick 1s -> must be YELLOW
        sig = self.phase_mgr.tick(1.0)
        self.assertEqual(sig["J1"], "YELLOW")

        # Tick 2s -> must enter ALL_RED
        sig = self.phase_mgr.tick(2.5)
        self.assertEqual(sig["J1"], "ALL_RED")

        # Tick 2s -> clearance completes, NS_GREEN is active
        sig = self.phase_mgr.tick(2.0)
        self.assertEqual(sig["J1"], "NS_GREEN")

    def test_multi_junction_corridor_progression(self):
        self.controller.dispatch_corridor(
            token="test-operator-secret",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1
        )

        # Step 5 seconds (ambulance travels 5 * 16.67 = ~83m, approaching J1 at 100m)
        status = self.controller.step(dt=5.0)
        self.assertEqual(self.controller.mode, CorridorMode.FLUSHING)
        self.assertTrue(status["junctions"]["J1"]["is_preempted"])

        # Step another 20 seconds (ambulance passes J1 and approaches J2 at 250m)
        status = self.controller.step(dt=20.0)
        # J1 should have recovered and assigned compensation
        self.assertGreater(status["junctions"]["J1"]["compensation_s"], 0.0)

    def test_priority_conflict_arbitration(self):
        self.controller.dispatch_corridor(
            token="test-operator-secret",
            vehicle_id="AMB-CODE1",
            vehicle_type="ambulance",
            priority_level=1
        )
        # Attempt to dispatch lower priority (Code 2) while Code 1 is active
        ok, msg = self.controller.dispatch_corridor(
            token="test-operator-secret",
            vehicle_id="FIRE-CODE2",
            vehicle_type="fire_truck",
            priority_level=2
        )
        self.assertFalse(ok)
        self.assertIn("CORRIDOR_CONFLICT", msg)

    def test_corridor_cancel(self):
        self.controller.dispatch_corridor(
            token="test-operator-secret",
            vehicle_id="AMB-101",
            vehicle_type="ambulance",
            priority_level=1
        )
        ok, msg = self.controller.cancel("test-operator-secret")
        self.assertTrue(ok)
        self.assertEqual(self.controller.mode, CorridorMode.STANDBY)
        self.assertIsNone(self.controller.active_vehicle)


if __name__ == '__main__':
    unittest.main()
