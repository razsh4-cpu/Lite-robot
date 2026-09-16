import unittest

from lite3_security_patrol.mission_core import (
    MissionManager, MissionState, PatrolManager, PersonDetected, Waypoint)


class MissionCoreTest(unittest.TestCase):
    def test_patrol_order_pause_repeat(self):
        patrol = PatrolManager([Waypoint('a', 0, 0, 0), Waypoint('b', 1, 0, 0)], repeat=False)
        patrol.start()
        self.assertEqual(patrol.current_waypoint().name, 'a')
        patrol.pause()
        self.assertIsNone(patrol.current_waypoint())
        patrol.resume()
        self.assertTrue(patrol.goal_succeeded())
        self.assertEqual(patrol.current_waypoint().name, 'b')
        self.assertFalse(patrol.goal_succeeded())
        self.assertFalse(patrol.active)

    def test_person_event_never_commands_navigation(self):
        mission = MissionManager()
        mission.start_patrol()
        event = mission.person_detected(PersonDetected(1.0, 0.9, 'image.jpg'), 'healthy')
        self.assertEqual(mission.state, MissionState.OBSERVING)
        self.assertEqual(event.event_type, 'PERSON_DETECTED')
        mission.capture_complete()
        self.assertEqual(mission.state, MissionState.WAITING)

    def test_person_metadata_is_optional_and_transport_neutral(self):
        detection = PersonDetected(
            2.0, 0.8, bounding_box_xyxy=(10, 20, 30, 40),
            source_frame='camera_color_optical_frame', pose_is_fresh=True)
        self.assertEqual(detection.bounding_box_xyxy, (10, 20, 30, 40))
        self.assertTrue(detection.pose_is_fresh)


if __name__ == '__main__':
    unittest.main()
