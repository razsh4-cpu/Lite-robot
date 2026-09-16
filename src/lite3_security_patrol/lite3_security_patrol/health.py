"""Unified, transport-neutral health snapshot for future monitoring."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class SensorEvent:
    """Transport-neutral environmental/sensor event; never a motion command."""
    event_type: str
    value: float
    unit: str
    threshold: Optional[float]
    timestamp: float
    severity: str
    source_id: str
    location_frame: Optional[str] = None
    is_fresh: bool = True
    evidence_reference: Optional[str] = None


@dataclass
class RobotHealth:
    control_connected: bool = False
    localization_ok: bool = False
    sensors: Dict[str, bool] = field(default_factory=dict)
    network_ok: bool = False
    battery_percent: Optional[float] = None
    mission_state: str = 'IDLE'
    errors: list[str] = field(default_factory=list)

    def add_error_once(self, error: str) -> None:
        if error not in self.errors:
            self.errors.append(error)
