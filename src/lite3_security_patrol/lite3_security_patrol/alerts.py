"""Local/mock alert backend. It records events but never contacts a cloud API."""
import json
from dataclasses import asdict
from pathlib import Path

from .mission_core import SecurityEvent


class LocalEventSink:
    def __init__(self, path: Path):
        self.path = Path(path)

    def record(self, event: SecurityEvent) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a', encoding='utf-8') as output:
            output.write(json.dumps(asdict(event), sort_keys=True) + '\n')
        return self.path
