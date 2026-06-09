# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

import os
import sys
import time
import tracemalloc

try:
    import resource
except ImportError:  # pragma: no cover - platform without resource module
    resource = None


class MemoryMonitor(object):
    """Best-effort runtime memory monitor for terminal diagnostics only."""

    BYTES_IN_MB = 1024.0 * 1024.0

    def __init__(self, enabled=False, clock=None):
        """Initialize memory monitor.

        :param bool enabled: Whether memory sampling is enabled.
        :param callable|None clock: Monotonic clock provider for tests.
        """

        self.enabled = enabled is True
        self._clock = time.monotonic if clock is None else clock
        self._started = False
        self._owns_tracemalloc = False
        self._baseline = None
        self._latest = None
        self._tracemalloc_error = None

    def start(self):
        """Start memory sampling when enabled.

        :return: None
        """

        if self.enabled is not True:
            return

        if self._started is True:
            return

        try:
            if tracemalloc.is_tracing() is not True:
                tracemalloc.start()
                self._owns_tracemalloc = True
        except RuntimeError as error:
            self._tracemalloc_error = str(error)

        self._started = True
        self._baseline = self.sample()

    def stop(self):
        """Stop owned tracemalloc session and release monitor state.

        Memory diagnostics may be enabled for short CLI scans and also for
        repeated scans in long-running Python processes. When this monitor
        started tracemalloc itself, it must stop it during Browser cleanup so
        tracing overhead does not leak into the host process.

        :return: None
        """

        if self._started is not True:
            return

        try:
            if self._owns_tracemalloc is True and tracemalloc.is_tracing() is True:
                tracemalloc.stop()
        finally:
            self._started = False
            self._owns_tracemalloc = False
            self._baseline = None
            self._latest = None

    def close(self):
        """Alias for resource cleanup used by Browser.close().

        :return: None
        """

        self.stop()

    def sample(self):
        """Collect a best-effort memory sample.

        :return: memory sample
        :rtype: dict
        """

        if self.enabled is not True:
            return {}

        traced_current_mb = None
        traced_peak_mb = None

        if tracemalloc.is_tracing() is True:
            traced_current, traced_peak = tracemalloc.get_traced_memory()
            traced_current_mb = self._bytes_to_mb(traced_current)
            traced_peak_mb = self._bytes_to_mb(traced_peak)

        sample = {
            'timestamp': float(self._clock()),
            'rss_current_mb': self._current_rss_mb(),
            'rss_peak_mb': self._peak_rss_mb(),
            'tracemalloc_current_mb': traced_current_mb,
            'tracemalloc_peak_mb': traced_peak_mb,
        }
        self._latest = sample
        return dict(sample)

    def payload(self, processed=0, active_seconds=0.0):
        """Build CLI diagnostics payload for the latest memory state.

        :param int processed: Number of consumed scan items.
        :param float active_seconds: Active scan time in seconds.
        :return: memory diagnostics payload
        :rtype: dict
        """

        if self.enabled is not True:
            return {'enabled': False}

        if self._started is not True:
            self.start()

        current = self.sample()
        baseline = self._baseline if isinstance(self._baseline, dict) else current
        processed = self._safe_int(processed)
        active_seconds = self._safe_float(active_seconds)

        rss_delta_mb = self._delta(current.get('rss_current_mb'), baseline.get('rss_current_mb'))
        rss_peak_delta_mb = self._delta(current.get('rss_peak_mb'), baseline.get('rss_peak_mb'))
        traced_delta_mb = self._delta(
            current.get('tracemalloc_current_mb'),
            baseline.get('tracemalloc_current_mb'),
        )
        growth_per_1000 = self._first_meaningful_growth_per_1000(
            processed,
            traced_delta_mb,
            rss_delta_mb,
            rss_peak_delta_mb,
        )

        return {
            'enabled': True,
            'available': (
                current.get('rss_current_mb') is not None
                or current.get('rss_peak_mb') is not None
                or current.get('tracemalloc_current_mb') is not None
            ),
            'rss_start_mb': baseline.get('rss_current_mb'),
            'rss_current_mb': current.get('rss_current_mb'),
            'rss_delta_mb': rss_delta_mb,
            'rss_peak_start_mb': baseline.get('rss_peak_mb'),
            'rss_peak_mb': current.get('rss_peak_mb'),
            'rss_peak_delta_mb': rss_peak_delta_mb,
            'tracemalloc_start_mb': baseline.get('tracemalloc_current_mb'),
            'tracemalloc_current_mb': current.get('tracemalloc_current_mb'),
            'tracemalloc_peak_mb': current.get('tracemalloc_peak_mb'),
            'tracemalloc_delta_mb': traced_delta_mb,
            'growth_per_1000_items_mb': growth_per_1000,
            'processed': processed,
            'active_seconds': active_seconds,
            'error': self._tracemalloc_error,
        }

    @classmethod
    def format_payload(cls, payload):
        """Format memory diagnostics for a compact Runtime diagnostics row.

        :param dict payload: memory diagnostics payload.
        :return: formatted CLI value
        :rtype: str
        """

        if not isinstance(payload, dict) or payload.get('enabled') is not True:
            return 'disabled'

        if payload.get('available') is not True:
            return 'unavailable'

        parts = []
        rss_current = cls._format_mb(payload.get('rss_current_mb'))
        rss_delta = cls._format_delta(payload.get('rss_delta_mb'))
        if rss_current != 'n/a':
            parts.append('RSS {0} ({1})'.format(rss_current, rss_delta))
        else:
            rss_peak = cls._format_mb(payload.get('rss_peak_mb'))
            rss_peak_delta = cls._format_delta(payload.get('rss_peak_delta_mb'))
            if rss_peak != 'n/a':
                parts.append('RSS peak {0} ({1})'.format(rss_peak, rss_peak_delta))

        traced_current = cls._format_mb(payload.get('tracemalloc_current_mb'))
        traced_delta = cls._format_delta(payload.get('tracemalloc_delta_mb'))
        traced_peak = cls._format_mb(payload.get('tracemalloc_peak_mb'))
        if traced_current != 'n/a':
            parts.append('trace {0} ({1}), peak {2}'.format(traced_current, traced_delta, traced_peak))

        growth = payload.get('growth_per_1000_items_mb')
        if growth is not None:
            parts.append('{0}/1000 items'.format(cls._format_delta(growth)))

        return '; '.join(parts) if len(parts) > 0 else 'unavailable'

    @staticmethod
    def _safe_int(value):
        """Return a safe integer for diagnostics calculations."""

        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_float(value):
        """Return a safe float for diagnostics calculations."""

        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _bytes_to_mb(cls, value):
        """Convert bytes to megabytes."""

        try:
            return float(value) / cls.BYTES_IN_MB
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _delta(current, baseline):
        """Return numeric delta when both values are available."""

        if current is None or baseline is None:
            return None

        return float(current) - float(baseline)

    @staticmethod
    def _growth_per_1000(delta_mb, processed):
        """Normalize memory growth to 1000 consumed scan items."""

        if delta_mb is None or processed <= 0:
            return None

        return (float(delta_mb) / float(processed)) * 1000.0

    @classmethod
    def _first_meaningful_growth_per_1000(cls, processed, *delta_values):
        """Return normalized growth from the first useful memory source.

        ``tracemalloc`` can report ``0.0`` for long scans dominated by C-level
        buffers in ssl, sockets, urllib3 or zlib. In that case a process-level
        RSS source is more useful for terminal diagnostics. Keep zero growth
        only when every available source is zero or unavailable.
        """

        fallback_growth = None

        for delta_mb in delta_values:
            growth = cls._growth_per_1000(delta_mb, processed)
            if growth is None:
                continue

            if fallback_growth is None:
                fallback_growth = growth

            if abs(float(delta_mb)) >= 0.05:
                return growth

        return fallback_growth

    @classmethod
    def _format_mb(cls, value):
        """Format megabytes for terminal diagnostics."""

        if value is None:
            return 'n/a'

        return '{0:.1f} MB'.format(float(value))

    @classmethod
    def _format_delta(cls, value):
        """Format signed megabyte delta for terminal diagnostics."""

        if value is None:
            return 'n/a'

        value = float(value)
        sign = '+' if value >= 0 else ''
        return '{0}{1:.1f} MB'.format(sign, value)

    @classmethod
    def _current_rss_mb(cls):
        """Return current resident set size in megabytes when available.

        Linux exposes current RSS through /proc/self/statm. On platforms where
        current RSS is not available without optional dependencies, return None
        instead of guessing from peak-only process accounting.
        """

        if sys.platform.startswith('linux'):
            return cls._linux_current_rss_mb()

        return None

    @classmethod
    def _peak_rss_mb(cls):
        """Return peak resident set size in megabytes when available.

        The resource module is part of the Python standard library on Unix-like
        systems. macOS reports ru_maxrss in bytes, while Linux reports it in
        kibibytes. This provides useful long-scan process memory diagnostics on
        macOS where current RSS is otherwise unavailable without optional
        dependencies.
        """

        if resource is None:
            return None

        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            raw_peak = getattr(usage, 'ru_maxrss', None)
            if raw_peak is None or int(raw_peak) <= 0:
                return None

            if sys.platform == 'darwin':
                return cls._bytes_to_mb(int(raw_peak))

            return cls._bytes_to_mb(int(raw_peak) * 1024)
        except (OSError, TypeError, ValueError, AttributeError):
            return None

    @classmethod
    def _linux_current_rss_mb(cls):
        """Return current Linux RSS from /proc/self/statm."""

        try:
            with open('/proc/self/statm', 'r', encoding='utf-8') as handler:
                fields = handler.read().split()
            if len(fields) < 2:
                return None
            page_size = os.sysconf('SC_PAGE_SIZE')
            return cls._bytes_to_mb(int(fields[1]) * int(page_size))
        except (OSError, TypeError, ValueError, AttributeError):
            return None
