import unittest

from lite3_security_patrol.velocity_mapping import (
    CommandWatchdog, VelocityCommand, VelocityMapper, VelocityMappingConfig)


class VelocityMappingTest(unittest.TestCase):
    def test_uncalibrated_limits_are_safe_zero(self):
        mapper = VelocityMapper(VelocityMappingConfig())
        self.assertEqual(mapper.map_physical(1.0, 1.0, 1.0), VelocityCommand())

    def test_mapping_and_limits(self):
        mapper = VelocityMapper(VelocityMappingConfig(0.5, 0.25, 1.0, 0.5, 0.3))
        self.assertEqual(mapper.map_physical(1.0, -1.0, 2.0), VelocityCommand(0.5, -0.5, 0.5))
        self.assertEqual(mapper.map_physical(0.25, 0.125, -0.5), VelocityCommand(0.5, 0.5, -0.5))

    def test_timeout_returns_zero(self):
        watchdog = CommandWatchdog(0.3)
        watchdog.update(VelocityCommand(0.2, 0.0, 0.0), 10.0)
        self.assertEqual(watchdog.current(10.29), VelocityCommand(0.2, 0.0, 0.0))
        self.assertEqual(watchdog.current(10.31), VelocityCommand())


if __name__ == '__main__':
    unittest.main()
