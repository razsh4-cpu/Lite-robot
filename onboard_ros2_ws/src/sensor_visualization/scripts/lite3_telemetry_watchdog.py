#!/usr/bin/env python3
"""Passive, low-overhead health watchdog for the DeepRobotics Lite3.

This node only binds a UDP socket and calls ``recvfrom()`` to consume Motion
Host telemetry.  It deliberately has no command socket and no ``send`` or
``sendto`` call, so it cannot issue robot commands.
"""

import importlib.util
import json
import math
import os
from pathlib import Path
import queue
import socket
import sys
import threading
import time
import types
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import rclpy
from rclpy.node import Node


def load_motion_host_codecs(plugin_root: Path):
    """Load the vendor-compatible telemetry decoder without plugin runtime."""
    package_dir = plugin_root / 'lite3_plugin'
    protocol_path = package_dir / 'protocol.py'
    codecs_path = package_dir / 'codecs.py'
    if not protocol_path.is_file() or not codecs_path.is_file():
        raise FileNotFoundError(f'Expected protocol.py and codecs.py under {package_dir}')

    package_name = '_lite3_watchdog_decoder'
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_dir)]
    sys.modules[package_name] = package

    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f'Cannot load {path}')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    protocol = load(f'{package_name}.protocol', protocol_path)
    codecs = load(f'{package_name}.codecs', codecs_path)
    return protocol, codecs


def load_telegram_settings(config_path):
    """Read credentials from environment or a mode-600 user configuration file."""
    settings = {
        'LITE3_TELEGRAM_BOT_TOKEN': os.environ.get('LITE3_TELEGRAM_BOT_TOKEN', ''),
        'LITE3_TELEGRAM_CHAT_ID': os.environ.get('LITE3_TELEGRAM_CHAT_ID', ''),
    }
    path = Path(config_path).expanduser()
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            key, separator, value = line.partition('=')
            if separator and key in settings and not settings[key]:
                settings[key] = value
    token = settings['LITE3_TELEGRAM_BOT_TOKEN']
    chat_id = settings['LITE3_TELEGRAM_CHAT_ID']
    return (token, chat_id) if token and chat_id else (None, None)


class TelegramNotifier:
    """Bounded, asynchronous Telegram delivery for watchdog alert transitions."""

    TIMEOUT_S = 4.0
    ERROR_LOG_PERIOD_S = 60.0

    def __init__(self, token, chat_id, logger):
        self._token = token
        self._chat_id = str(chat_id)
        self._logger = logger
        self._queue = queue.Queue(maxsize=32)
        self._last_error_log = 0.0
        self._stopping = False
        self._worker = threading.Thread(target=self._run, daemon=True,
                                        name='lite3-telegram-notifier')
        self._worker.start()

    @staticmethod
    def should_notify(event):
        return event.startswith((
            '⚠ LOW BATTERY',
            '⚠ BATTERY GETTING CRITICAL',
            '🔴 CRITICAL BATTERY',
            '⚠ UNKNOWN ROBOT STATE',
            '🔴 PROTECTION STATE',
            '⚠ TELEMETRY LOST',
            '✓ TELEMETRY RESTORED',
            '⚠ BATTERY DATA STALE',
            '✓ Lite3 battery/state telemetry restored',
        ))

    def notify(self, event):
        """Queue an alert without ever blocking the telemetry callback."""
        if not self.should_notify(event):
            return
        if event.startswith('⚠ BATTERY DATA STALE — last known: '):
            event = ('⚠️ Lite3 battery/state data is stale — last known battery: ' +
                     event.removeprefix('⚠ BATTERY DATA STALE — last known: '))
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            self._rate_limited_error('Telegram queue full; dropped watchdog alert')

    def _rate_limited_error(self, message):
        now = time.monotonic()
        if now - self._last_error_log >= self.ERROR_LOG_PERIOD_S:
            self._last_error_log = now
            self._logger.warn(message)

    def _post(self, text):
        body = urlencode({'chat_id': self._chat_id, 'text': text}).encode('utf-8')
        request = Request(
            f'https://api.telegram.org/bot{self._token}/sendMessage',
            data=body,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST')
        with urlopen(request, timeout=self.TIMEOUT_S) as response:
            payload = json.load(response)
        if not payload.get('ok'):
            raise RuntimeError('Telegram API rejected sendMessage')

    def _run(self):
        while not self._stopping:
            try:
                event = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._post(event)
            except Exception as exc:
                self._rate_limited_error(
                    f'Telegram notification failed ({type(exc).__name__}); monitoring continues')
            finally:
                self._queue.task_done()

    def close(self):
        self._stopping = True
        self._worker.join(timeout=self.TIMEOUT_S + 0.5)


class WatchdogCore:
    """Stateful alert logic independent of ROS and network I/O."""

    LOW_BATTERY = 35.0
    CRITICAL_BATTERY = 25.0
    MOVEMENT_LOCK_BATTERY = 20.0

    def __init__(self, codecs, raw_udp_timeout_s, robot_state_timeout_s):
        self.codecs = codecs
        self.raw_udp_timeout_s = float(raw_udp_timeout_s)
        self.robot_state_timeout_s = float(robot_state_timeout_s)
        self.first_raw_packet_time = None
        self.last_raw_packet_time = None
        self.last_robot_state_time = None
        self.last_known_battery = None
        self.have_seen_robot_state = False
        self.raw_telemetry_lost = False
        self.robot_state_stale = False
        self.last_state = None
        self.battery_latched = {
            'low': False,
            'critical': False,
            'movement_lock': False,
        }

    def observe_raw_packet(self, now):
        """Record any packet arrival; raw UDP health is independent of frame type."""
        events = []
        if self.first_raw_packet_time is None:
            self.first_raw_packet_time = now
        if self.raw_telemetry_lost:
            self.raw_telemetry_lost = False
            events.append('✓ TELEMETRY RESTORED')
        self.last_raw_packet_time = now
        return events

    @staticmethod
    def _format_battery(level):
        return f'{level:.0f}%'

    def _battery_is_current(self, now):
        return (self.last_known_battery is not None and
                self.last_robot_state_time is not None and
                not self.robot_state_stale and
                now - self.last_robot_state_time <= self.robot_state_timeout_s)

    def battery_presentation(self, now):
        """Return a freshness-labelled battery string; never imply stale is current."""
        if self.last_known_battery is None:
            return 'Battery: unavailable (no fresh RobotState received)'
        if self._battery_is_current(now):
            return f'Battery: {self._format_battery(self.last_known_battery)}'
        return ('⚠ BATTERY DATA STALE — last known: ' +
                self._format_battery(self.last_known_battery))

    def _reset_battery_latches(self):
        for key in self.battery_latched:
            self.battery_latched[key] = False

    def _battery_events(self, battery):
        if not math.isfinite(battery):
            return []
        events = []
        thresholds = (
            ('low', self.LOW_BATTERY, True, '⚠ LOW BATTERY — {}'),
            ('critical', self.CRITICAL_BATTERY, True,
             '⚠ BATTERY GETTING CRITICAL — {}'),
            ('movement_lock', self.MOVEMENT_LOCK_BATTERY, False,
             '🔴 CRITICAL BATTERY — {} — ROBOT NOT READY FOR MOVEMENT'),
        )
        for key, threshold, inclusive, message in thresholds:
            active = battery <= threshold if inclusive else battery < threshold
            if active and not self.battery_latched[key]:
                events.append(message.format(self._format_battery(battery)))
                self.battery_latched[key] = True
            elif not active:
                # Charging above this threshold re-arms its next downward crossing.
                self.battery_latched[key] = False
        return events

    def observe(self, state, now):
        """Consume one decoded RobotState and return only newly relevant alerts."""
        events = []
        status = self.codecs.describe_robot_status(state)
        basic_state = int(state.robot_basic_state)
        battery = float(state.battery_level)
        self.last_known_battery = battery

        if not self.have_seen_robot_state:
            self.have_seen_robot_state = True
            events.append(
                f'LITE3 WATCHDOG ACTIVE — Battery: {self._format_battery(battery)} '
                f'| State: {basic_state}/{status} | Telemetry: OK')
        elif self.robot_state_stale:
            self.robot_state_stale = False
            events.append('✓ ROBOT STATE TELEMETRY RESTORED')
            events.append(
                '✓ Lite3 battery/state telemetry restored — Battery: ' +
                self._format_battery(battery))

        state_changed = basic_state != self.last_state
        if self.last_state is not None and state_changed:
            old_status = self.codecs.BASIC_STATE_NAMES.get(
                self.last_state, f'unknown_{self.last_state}')
            events.append(
                f'ROBOT STATE: {self.last_state}/{old_status} -> {basic_state}/{status}')

        known_basic_states = self.codecs.BASIC_STATE_NAMES
        if state_changed and basic_state not in known_basic_states:
            events.append(
                f'⚠ UNKNOWN ROBOT STATE — {basic_state}/{status}; '
                'no meaning is inferred for this vendor-undocumented value')
        elif state_changed and basic_state in self.codecs.FALLEN_BASIC_STATES:
            # These are the only protection/fall states named by the existing decoder.
            events.append(f'🔴 PROTECTION STATE — {basic_state}/{status}')

        self.last_state = basic_state
        events.extend(self._battery_events(battery))
        self.last_robot_state_time = now
        return events

    def check_freshness(self, now):
        """Report raw UDP loss separately from the RobotState health stream."""
        if (self.last_raw_packet_time is not None and not self.raw_telemetry_lost and
                now - self.last_raw_packet_time > self.raw_udp_timeout_s):
            self.raw_telemetry_lost = True
            return ['⚠ TELEMETRY LOST']
        if self.raw_telemetry_lost or self.first_raw_packet_time is None:
            return []
        reference_time = self.last_robot_state_time or self.first_raw_packet_time
        if (not self.robot_state_stale and
                now - reference_time > self.robot_state_timeout_s):
            self.robot_state_stale = True
            # A retained number is historical from this point onward. Reset
            # latches so the first fresh value is evaluated as current even
            # when it is unchanged and already below a threshold.
            self._reset_battery_latches()
            return [
                '⚠ ROBOT STATE TELEMETRY STALE',
                self.battery_presentation(now),
            ]
        return []


class Lite3TelemetryWatchdog(Node):
    """ROS 2 wrapper around the passive Motion Host telemetry watchdog."""

    def __init__(self):
        super().__init__('lite3_telemetry_watchdog')
        self.declare_parameter('telemetry_port', 43897)
        self.declare_parameter('raw_udp_timeout_s', 1.0)
        self.declare_parameter('robot_state_timeout_s', 4.0)
        self.declare_parameter('plugin_root', '/home/abx/emos-plugin-lite3')
        self.declare_parameter(
            'telegram_config_path', '/home/abx/.config/lite3-watchdog/telegram.env')

        telemetry_port = int(self.get_parameter('telemetry_port').value)
        raw_udp_timeout_s = float(self.get_parameter('raw_udp_timeout_s').value)
        robot_state_timeout_s = float(self.get_parameter('robot_state_timeout_s').value)
        plugin_root = Path(str(self.get_parameter('plugin_root').value)).expanduser()
        telegram_config_path = str(self.get_parameter('telegram_config_path').value)
        self.protocol, codecs = load_motion_host_codecs(plugin_root)
        self.core = WatchdogCore(codecs, raw_udp_timeout_s, robot_state_timeout_s)
        token, chat_id = load_telegram_settings(telegram_config_path)
        self._telegram = TelegramNotifier(token, chat_id, self.get_logger()) if token else None

        # Receive-only socket: this node has no command endpoint by design.
        self._telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._telemetry_socket.bind(('0.0.0.0', telemetry_port))
        self._telemetry_socket.setblocking(False)
        self.create_timer(0.05, self._receive_telemetry)
        self.create_timer(0.10, self._check_freshness)
        self.get_logger().info(
            f'Lite3 watchdog started: passive UDP receive on :{telemetry_port}; '
            f'raw UDP stale after {raw_udp_timeout_s:.1f}s; RobotState stale after '
            f'{robot_state_timeout_s:.1f}s. No command socket exists.')
        if self._telegram:
            self.get_logger().info('Telegram watchdog alerts enabled.')
        else:
            self.get_logger().warn('Telegram alerts disabled: protected token/chat configuration unavailable.')

    def _log_events(self, events):
        for event in events:
            self.get_logger().warn(event) if event.startswith(('⚠', '🔴')) else self.get_logger().info(event)
            if self._telegram:
                self._telegram.notify(event)

    def _receive_telemetry(self):
        while True:
            try:
                raw, _peer = self._telemetry_socket.recvfrom(4096)
            except BlockingIOError:
                return
            now = time.monotonic()
            self._log_events(self.core.observe_raw_packet(now))
            state = self.core.codecs.parse_robot_state(raw)
            if state is not None:
                self._log_events(self.core.observe(state, now))

    def _check_freshness(self):
        self._log_events(self.core.check_freshness(time.monotonic()))

    def destroy_node(self):
        if self._telegram:
            self._telegram.close()
        self._telemetry_socket.close()
        return super().destroy_node()


def run_offline_tests():
    """Exercise alert transitions using synthetic vendor RobotState instances only."""
    plugin_root = Path('/home/abx/emos-plugin-lite3')
    protocol, codecs = load_motion_host_codecs(plugin_root)

    def state(battery, basic=6):
        sample = protocol.RobotState()
        sample.battery_level = battery
        sample.robot_basic_state = basic
        sample.robot_gait_state = 0
        sample.robot_motion_state = 0
        return sample

    core = WatchdogCore(codecs, raw_udp_timeout_s=1.0, robot_state_timeout_s=4.0)
    # A: a valid RobotState makes the battery current.
    assert core.observe_raw_packet(0.0) == []
    startup = core.observe(state(50.0), 0.0)
    assert any('WATCHDOG ACTIVE' in text for text in startup)
    assert not any('BATTERY' in text for text in startup)
    assert core.battery_presentation(0.1) == 'Battery: 50%'

    low = core.observe(state(35.0), 0.1)
    assert low == ['⚠ LOW BATTERY — 35%']
    assert core.observe(state(35.0), 0.2) == []  # anti-spam
    critical = core.observe(state(25.0), 0.3)
    assert critical == ['⚠ BATTERY GETTING CRITICAL — 25%']
    locked = core.observe(state(19.0), 0.4)
    assert locked == ['🔴 CRITICAL BATTERY — 19% — ROBOT NOT READY FOR MOVEMENT']
    core.observe(state(40.0), 0.5)  # charging resets all threshold latches
    assert core.observe(state(35.0), 0.6) == ['⚠ LOW BATTERY — 35%']

    state_change = core.observe(state(50.0, basic=98), 0.7)
    assert any('ROBOT STATE: 6/standing -> 98/unknown_98' == text for text in state_change)
    assert any('UNKNOWN ROBOT STATE' in text for text in state_change)
    assert not any('UNKNOWN ROBOT STATE' in text for text in core.observe(state(50.0, basic=98), 0.8))

    # B/G: non-RobotState packets keep raw UDP healthy but make the retained
    # number stale, explicitly labelled as last known and never current.
    assert core.observe_raw_packet(4.6) == []
    assert core.check_freshness(4.6) == []
    stale = core.check_freshness(4.81)
    assert stale == [
        '⚠ ROBOT STATE TELEMETRY STALE',
        '⚠ BATTERY DATA STALE — last known: 50%',
    ]
    assert core.battery_presentation(4.81) == '⚠ BATTERY DATA STALE — last known: 50%'
    assert core.check_freshness(5.0) == []  # state-stale anti-spam

    # D: restore at 33% must announce both restoration and current low battery.
    assert core.observe_raw_packet(5.1) == []
    restored = core.observe(state(33.0, basic=6), 5.1)
    assert '✓ ROBOT STATE TELEMETRY RESTORED' in restored
    assert '✓ Lite3 battery/state telemetry restored — Battery: 33%' in restored
    assert '⚠ LOW BATTERY — 33%' in restored
    assert core.battery_presentation(5.1) == 'Battery: 33%'

    # C: raw loss remains a distinct, one-shot event.
    assert core.check_freshness(6.11) == ['⚠ TELEMETRY LOST']
    assert core.check_freshness(6.2) == []  # raw-loss anti-spam
    assert core.observe_raw_packet(6.3) == ['✓ TELEMETRY RESTORED']

    # E: a critically low first fresh value after stale generates all current
    # threshold alerts without requiring a downward threshold crossing.
    critical_core = WatchdogCore(codecs, raw_udp_timeout_s=1.0, robot_state_timeout_s=4.0)
    critical_core.observe_raw_packet(0.0)
    critical_core.observe(state(50.0), 0.0)
    critical_core.observe_raw_packet(4.1)
    assert any('BATTERY DATA STALE' in text for text in critical_core.check_freshness(4.1))
    critical_core.observe_raw_packet(4.2)
    critical_restore = critical_core.observe(state(19.0), 4.2)
    assert '✓ Lite3 battery/state telemetry restored — Battery: 19%' in critical_restore
    assert '⚠ LOW BATTERY — 19%' in critical_restore
    assert '⚠ BATTERY GETTING CRITICAL — 19%' in critical_restore
    assert '🔴 CRITICAL BATTERY — 19% — ROBOT NOT READY FOR MOVEMENT' in critical_restore

    assert TelegramNotifier.should_notify('⚠ LOW BATTERY — 35%')
    assert TelegramNotifier.should_notify('⚠ TELEMETRY LOST')
    assert TelegramNotifier.should_notify('✓ TELEMETRY RESTORED')
    assert TelegramNotifier.should_notify('⚠ BATTERY DATA STALE — last known: 50%')
    assert TelegramNotifier.should_notify('✓ Lite3 battery/state telemetry restored — Battery: 33%')
    assert not TelegramNotifier.should_notify('LITE3 WATCHDOG ACTIVE — Battery: 50%')
    print('Offline watchdog tests: PASS')


def send_telegram_test_message():
    """Send the one explicit setup test message without starting a ROS node."""
    token, chat_id = load_telegram_settings('/home/abx/.config/lite3-watchdog/telegram.env')
    if not token:
        raise RuntimeError('Telegram token/chat ID configuration is unavailable')
    body = urlencode({
        'chat_id': str(chat_id),
        'text': '✅ Lite3 watchdog Telegram notifications are working.',
    }).encode('utf-8')
    request = Request(
        f'https://api.telegram.org/bot{token}/sendMessage', data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    with urlopen(request, timeout=TelegramNotifier.TIMEOUT_S) as response:
        payload = json.load(response)
    if not payload.get('ok'):
        raise RuntimeError('Telegram API rejected the watchdog test message')
    print('Telegram test message accepted.')


def main():
    if '--self-test' in sys.argv:
        run_offline_tests()
        return
    if '--telegram-test' in sys.argv:
        send_telegram_test_message()
        return
    rclpy.init()
    node = Lite3TelemetryWatchdog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
