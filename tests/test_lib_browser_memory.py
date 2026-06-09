# -*- coding: utf-8 -*-

import unittest
from unittest.mock import mock_open, patch

from src.lib.browser.memory import MemoryMonitor


class MemoryMonitorTestCase(unittest.TestCase):
    """Runtime memory diagnostics tests."""

    def test_disabled_monitor_is_noop(self):
        """Disabled monitor should not start tracing or expose memory data."""

        monitor = MemoryMonitor(enabled=False)

        with patch('src.lib.browser.memory.tracemalloc.start') as start_mock:
            monitor.start()

        start_mock.assert_not_called()
        self.assertEqual(monitor.sample(), {})
        self.assertEqual(monitor.payload(processed=10), {'enabled': False})
        self.assertEqual(MemoryMonitor.format_payload({'enabled': False}), 'disabled')

    def test_start_should_start_tracemalloc_once_and_capture_baseline(self):
        """Enabled monitor should start tracemalloc and keep a baseline sample."""

        monitor = MemoryMonitor(enabled=True, clock=lambda: 10.0)

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', side_effect=[False, True]), \
                patch('src.lib.browser.memory.tracemalloc.start') as start_mock, \
                patch('src.lib.browser.memory.tracemalloc.get_traced_memory', return_value=(2 * 1024 * 1024, 4 * 1024 * 1024)), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=64.0):
            monitor.start()
            monitor.start()

        start_mock.assert_called_once_with()
        self.assertTrue(monitor._started)
        self.assertTrue(monitor._owns_tracemalloc)
        self.assertEqual(monitor._baseline['rss_current_mb'], 64.0)
        self.assertEqual(monitor._baseline['tracemalloc_current_mb'], 2.0)
        self.assertEqual(monitor._baseline['tracemalloc_peak_mb'], 4.0)

    def test_payload_should_calculate_memory_deltas_and_growth(self):
        """Memory payload should include deltas and growth per 1000 consumed items."""

        monitor = MemoryMonitor(enabled=True, clock=lambda: 20.0)
        monitor._started = True
        monitor._baseline = {
            'timestamp': 1.0,
            'rss_current_mb': 100.0,
            'tracemalloc_current_mb': 10.0,
            'tracemalloc_peak_mb': 12.0,
        }

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=True), \
                patch('src.lib.browser.memory.tracemalloc.get_traced_memory', return_value=(30 * 1024 * 1024, 35 * 1024 * 1024)), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=130.0):
            payload = monitor.payload(processed=500, active_seconds=25.0)

        self.assertTrue(payload['enabled'])
        self.assertTrue(payload['available'])
        self.assertEqual(payload['rss_start_mb'], 100.0)
        self.assertEqual(payload['rss_current_mb'], 130.0)
        self.assertEqual(payload['rss_delta_mb'], 30.0)
        self.assertEqual(payload['tracemalloc_start_mb'], 10.0)
        self.assertEqual(payload['tracemalloc_current_mb'], 30.0)
        self.assertEqual(payload['tracemalloc_peak_mb'], 35.0)
        self.assertEqual(payload['tracemalloc_delta_mb'], 20.0)
        self.assertEqual(payload['growth_per_1000_items_mb'], 40.0)
        self.assertEqual(payload['processed'], 500)
        self.assertEqual(payload['active_seconds'], 25.0)

    def test_payload_should_fall_back_to_rss_growth_when_trace_delta_is_unavailable(self):
        """Memory payload should still report growth when only RSS is available."""

        monitor = MemoryMonitor(enabled=True)
        monitor._started = True
        monitor._baseline = {
            'timestamp': 1.0,
            'rss_current_mb': 100.0,
            'tracemalloc_current_mb': None,
            'tracemalloc_peak_mb': None,
        }

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=False), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=125.0):
            payload = monitor.payload(processed='250', active_seconds='bad')

        self.assertEqual(payload['rss_delta_mb'], 25.0)
        self.assertIsNone(payload['tracemalloc_delta_mb'])
        self.assertEqual(payload['growth_per_1000_items_mb'], 100.0)
        self.assertEqual(payload['processed'], 250)
        self.assertEqual(payload['active_seconds'], 0.0)

    def test_payload_should_fall_back_to_peak_rss_when_trace_delta_is_zero(self):
        """Peak RSS should drive growth when tracemalloc stays effectively flat."""

        monitor = MemoryMonitor(enabled=True)
        monitor._started = True
        monitor._baseline = {
            'timestamp': 1.0,
            'rss_current_mb': None,
            'rss_peak_mb': 100.0,
            'tracemalloc_current_mb': 0.0,
            'tracemalloc_peak_mb': 0.0,
        }

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=True), \
                patch('src.lib.browser.memory.tracemalloc.get_traced_memory', return_value=(0, 0)), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=None), \
                patch.object(MemoryMonitor, '_peak_rss_mb', return_value=140.0):
            payload = monitor.payload(processed=500, active_seconds=10)

        self.assertTrue(payload['available'])
        self.assertIsNone(payload['rss_current_mb'])
        self.assertEqual(payload['rss_peak_mb'], 140.0)
        self.assertEqual(payload['rss_peak_delta_mb'], 40.0)
        self.assertEqual(payload['tracemalloc_delta_mb'], 0.0)
        self.assertEqual(payload['growth_per_1000_items_mb'], 80.0)
        self.assertIn('RSS peak 140.0 MB (+40.0 MB)', MemoryMonitor.format_payload(payload))

    def test_payload_should_handle_unavailable_memory_sources(self):
        """Memory payload should degrade gracefully when no memory source is available."""

        monitor = MemoryMonitor(enabled=True)
        monitor._started = True
        monitor._baseline = {
            'timestamp': 1.0,
            'rss_current_mb': None,
            'tracemalloc_current_mb': None,
            'tracemalloc_peak_mb': None,
        }

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=False), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=None), \
                patch.object(MemoryMonitor, '_peak_rss_mb', return_value=None):
            payload = monitor.payload(processed=0, active_seconds=0)

        self.assertFalse(payload['available'])
        self.assertIsNone(payload['rss_delta_mb'])
        self.assertIsNone(payload['tracemalloc_delta_mb'])
        self.assertIsNone(payload['growth_per_1000_items_mb'])
        self.assertEqual(MemoryMonitor.format_payload(payload), 'unavailable')

    def test_format_payload_should_render_compact_cli_value(self):
        """Formatted memory payload should be compact enough for Runtime diagnostics."""

        payload = {
            'enabled': True,
            'available': True,
            'rss_current_mb': 130.0,
            'rss_delta_mb': 30.0,
            'tracemalloc_current_mb': 30.0,
            'tracemalloc_delta_mb': 20.0,
            'tracemalloc_peak_mb': 35.0,
            'growth_per_1000_items_mb': -5.25,
        }

        rendered = MemoryMonitor.format_payload(payload)

        self.assertIn('RSS 130.0 MB (+30.0 MB)', rendered)
        self.assertIn('trace 30.0 MB (+20.0 MB), peak 35.0 MB', rendered)
        self.assertIn('-5.2 MB/1000 items', rendered)

    def test_format_payload_should_render_trace_only_payload(self):
        """Formatted memory payload should support platforms without current RSS."""

        payload = {
            'enabled': True,
            'available': True,
            'rss_current_mb': None,
            'rss_delta_mb': None,
            'tracemalloc_current_mb': 9.5,
            'tracemalloc_delta_mb': 1.5,
            'tracemalloc_peak_mb': 10.0,
            'growth_per_1000_items_mb': None,
        }

        self.assertEqual(
            MemoryMonitor.format_payload(payload),
            'trace 9.5 MB (+1.5 MB), peak 10.0 MB',
        )

    def test_linux_current_rss_should_read_proc_statm(self):
        """Linux RSS helper should read /proc/self/statm using system page size."""

        with patch('src.lib.browser.memory.sys.platform', 'linux'), \
                patch('src.lib.browser.memory.os.sysconf', return_value=4096), \
                patch('builtins.open', mock_open(read_data='100 256 0 0 0 0 0')):
            self.assertEqual(MemoryMonitor._current_rss_mb(), 1.0)

    def test_current_rss_should_return_none_when_unavailable(self):
        """RSS helper should avoid guessing on unsupported platforms or invalid proc data."""

        with patch('src.lib.browser.memory.sys.platform', 'darwin'):
            self.assertIsNone(MemoryMonitor._current_rss_mb())

        with patch('src.lib.browser.memory.sys.platform', 'linux'), \
                patch('builtins.open', side_effect=OSError('missing')):
            self.assertIsNone(MemoryMonitor._current_rss_mb())

        with patch('src.lib.browser.memory.sys.platform', 'linux'), \
                patch('builtins.open', mock_open(read_data='bad')):
            self.assertIsNone(MemoryMonitor._current_rss_mb())

    def test_peak_rss_should_read_resource_units_on_unix_platforms(self):
        """Peak RSS helper should normalize Linux KiB and macOS bytes."""

        linux_usage = type('Usage', (), {'ru_maxrss': 2048})()
        darwin_usage = type('Usage', (), {'ru_maxrss': 2 * 1024 * 1024})()

        with patch('src.lib.browser.memory.resource') as resource_mock, \
                patch('src.lib.browser.memory.sys.platform', 'linux'):
            resource_mock.RUSAGE_SELF = object()
            resource_mock.getrusage.return_value = linux_usage
            self.assertEqual(MemoryMonitor._peak_rss_mb(), 2.0)

        with patch('src.lib.browser.memory.resource') as resource_mock, \
                patch('src.lib.browser.memory.sys.platform', 'darwin'):
            resource_mock.RUSAGE_SELF = object()
            resource_mock.getrusage.return_value = darwin_usage
            self.assertEqual(MemoryMonitor._peak_rss_mb(), 2.0)

    def test_peak_rss_should_ignore_empty_or_zero_resource_values(self):
        """Peak RSS helper should ignore missing or non-positive ru_maxrss values."""

        for raw_peak in (None, 0):
            with self.subTest(raw_peak=raw_peak):
                usage = type('Usage', (), {'ru_maxrss': raw_peak})()
                with patch('src.lib.browser.memory.resource') as resource_mock:
                    resource_mock.RUSAGE_SELF = object()
                    resource_mock.getrusage.return_value = usage
                    self.assertIsNone(MemoryMonitor._peak_rss_mb())

    def test_peak_rss_should_return_none_when_resource_is_unavailable(self):
        """Peak RSS helper should degrade safely on unsupported platforms."""

        with patch('src.lib.browser.memory.resource', None):
            self.assertIsNone(MemoryMonitor._peak_rss_mb())

        with patch('src.lib.browser.memory.resource') as resource_mock:
            resource_mock.RUSAGE_SELF = object()
            resource_mock.getrusage.side_effect = OSError('not available')
            self.assertIsNone(MemoryMonitor._peak_rss_mb())

    def test_start_should_preserve_tracemalloc_errors(self):
        """Monitor should keep running when tracemalloc cannot be started."""

        monitor = MemoryMonitor(enabled=True)

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=False), \
                patch('src.lib.browser.memory.tracemalloc.start', side_effect=RuntimeError('trace failed')), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=None):
            monitor.start()

        self.assertEqual(monitor._tracemalloc_error, 'trace failed')
        self.assertTrue(monitor._started)


    def test_stop_should_stop_owned_tracemalloc_and_release_state(self):
        """Owned tracemalloc sessions should not leak after monitor cleanup."""

        monitor = MemoryMonitor(enabled=True)
        monitor._started = True
        monitor._owns_tracemalloc = True
        monitor._baseline = {'rss_current_mb': 1.0}
        monitor._latest = {'rss_current_mb': 2.0}

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=True), \
                patch('src.lib.browser.memory.tracemalloc.stop') as stop_mock:
            monitor.stop()
            monitor.stop()

        stop_mock.assert_called_once_with()
        self.assertFalse(monitor._started)
        self.assertFalse(monitor._owns_tracemalloc)
        self.assertIsNone(monitor._baseline)
        self.assertIsNone(monitor._latest)

    def test_stop_should_not_stop_external_tracemalloc_session(self):
        """Monitor cleanup must preserve tracemalloc sessions it did not start."""

        monitor = MemoryMonitor(enabled=True)
        monitor._started = True
        monitor._owns_tracemalloc = False
        monitor._baseline = {'rss_current_mb': 1.0}

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=True), \
                patch('src.lib.browser.memory.tracemalloc.stop') as stop_mock:
            monitor.close()

        stop_mock.assert_not_called()
        self.assertFalse(monitor._started)
        self.assertFalse(monitor._owns_tracemalloc)
        self.assertIsNone(monitor._baseline)



if __name__ == '__main__':
    unittest.main()


class MemoryMonitorCoverageGapsTestCase(unittest.TestCase):
    """Additional edge coverage for memory monitor diagnostics."""

    def test_start_should_reuse_existing_tracemalloc_session(self):
        """Enabled monitor should not claim ownership when tracing already runs."""

        monitor = MemoryMonitor(enabled=True, clock=lambda: 1.0)

        with patch('src.lib.browser.memory.tracemalloc.is_tracing', return_value=True), \
                patch('src.lib.browser.memory.tracemalloc.start') as start_mock, \
                patch('src.lib.browser.memory.tracemalloc.get_traced_memory', return_value=(0, 0)), \
                patch.object(MemoryMonitor, '_current_rss_mb', return_value=1.0):
            monitor.start()

        start_mock.assert_not_called()
        self.assertFalse(monitor._owns_tracemalloc)
        self.assertTrue(monitor._started)
        self.assertEqual(monitor._baseline['rss_current_mb'], 1.0)

    def test_payload_should_lazy_start_monitor(self):
        """payload() should start the monitor lazily when it was not started yet."""

        monitor = MemoryMonitor(enabled=True)

        with patch.object(monitor, 'start', side_effect=lambda: setattr(monitor, '_started', True)) as start_mock, \
                patch.object(monitor, 'sample', return_value={
                    'timestamp': 3.0,
                    'rss_current_mb': 10.0,
                    'tracemalloc_current_mb': None,
                    'tracemalloc_peak_mb': None,
                }):
            payload = monitor.payload(processed='bad', active_seconds='bad')

        start_mock.assert_called_once_with()
        self.assertEqual(payload['processed'], 0)
        self.assertEqual(payload['active_seconds'], 0.0)
        self.assertTrue(payload['available'])

    def test_format_payload_should_render_rss_only_and_unavailable_fallback(self):
        """format_payload() should cover RSS-only and empty available payloads."""

        self.assertEqual(
            MemoryMonitor.format_payload({
                'enabled': True,
                'available': True,
                'rss_current_mb': 12.25,
                'rss_delta_mb': -1.5,
                'tracemalloc_current_mb': None,
                'growth_per_1000_items_mb': None,
            }),
            'RSS 12.2 MB (-1.5 MB)',
        )

        self.assertEqual(
            MemoryMonitor.format_payload({
                'enabled': True,
                'available': True,
                'rss_current_mb': None,
                'tracemalloc_current_mb': None,
                'growth_per_1000_items_mb': None,
            }),
            'unavailable',
        )

    def test_growth_helper_should_skip_flat_trace_delta_for_rss_growth(self):
        """Growth helper should prefer a non-zero later source over flat trace data."""

        self.assertEqual(
            MemoryMonitor._first_meaningful_growth_per_1000(500, 0.0, None, 25.0),
            50.0,
        )
        self.assertEqual(
            MemoryMonitor._first_meaningful_growth_per_1000(500, 0.0, None, 0.0),
            0.0,
        )

    def test_numeric_helpers_should_reject_invalid_values(self):
        """Numeric helpers should stay deterministic on invalid inputs."""

        self.assertEqual(MemoryMonitor._safe_int(object()), 0)
        self.assertEqual(MemoryMonitor._safe_float(object()), 0.0)
        self.assertIsNone(MemoryMonitor._bytes_to_mb(object()))
