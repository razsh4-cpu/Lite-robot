"""Lite3-specific mapping into the generic Bipolix robot contract."""

from .state_mapping import (
    LITE3_CAPABILITIES,
    Lite3TelemetrySample,
    map_lite3_state,
    map_posture,
)

__all__ = [
    "LITE3_CAPABILITIES",
    "Lite3TelemetrySample",
    "map_lite3_state",
    "map_posture",
]
