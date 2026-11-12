"""Compatibility forwarding for services.evc.corridor_service."""
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from starter.aegis_helpers.corridor_service import (
    EmergencyCorridorService,
    EmergencyVehicle,
    CorridorStage,
    CorridorJunctionState,
)

__all__ = [
    "EmergencyCorridorService",
    "EmergencyVehicle",
    "CorridorStage",
    "CorridorJunctionState",
]
