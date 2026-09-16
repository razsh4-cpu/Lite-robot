import json
import tempfile
import unittest
from pathlib import Path

from lite3_security_patrol.alerts import LocalEventSink
from lite3_security_patrol.health import RobotHealth, SensorEvent
from lite3_security_patrol.mission_core import SecurityEvent


class AlertsAndHealthTest(unittest.TestCase):
    def test_local_event_sink_writes_structured_event(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            event = SecurityEvent('person-000001', 1.0, 'PERSON_DETECTED', 0.9,
                                  'image.jpg', None, 'healthy')
            LocalEventSink(path).record(event)
            self.assertEqual(json.loads(path.read_text()), {
                'confidence': 0.9, 'event_id': 'person-000001',
                'event_type': 'PERSON_DETECTED', 'image_reference': 'image.jpg',
                'robot_pose': None, 'robot_status': 'healthy', 'timestamp': 1.0})

    def test_health_errors_are_deduplicated(self):
        health = RobotHealth()
        health.add_error_once('telemetry stale')
        health.add_error_once('telemetry stale')
        self.assertEqual(health.errors, ['telemetry stale'])

    def test_sensor_event_contains_no_motion_interface(self):
        event = SensorEvent('SMOKE', 2.0, 'ppm', 1.0, 1.0, 'HIGH', 'smoke-1')
        self.assertEqual(event.event_type, 'SMOKE')
        self.assertFalse(hasattr(event, 'velocity'))


if __name__ == '__main__':
    unittest.main()
