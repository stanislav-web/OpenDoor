# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import helper
from src.lib.browser.browser import Browser


class TestBrowserExtra(unittest.TestCase):
    """Extra coverage for Browser branches."""

    def make_browser(self, **config_overrides):
        """Create Browser via __new__ with minimal runtime state."""

        br = Browser.__new__(Browser)

        config = {
            'is_waf_safe_mode': True,
            'is_waf_detect': True,
            'is_session_enabled': False,
            'is_response_filtering': False,
            'is_recursive': True,
            'recursive_depth': 2,
            'recursive_status': ['200', '403'],
            'recursive_exclude': [],
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'host': 'example.com',
            'scheme': 'http://',
            'is_ssl': False,
            'port': 80,
            'prefix': '',
            'reports': ['std'],
            'proxy': '',
            'headers': [],
            'cookies': [],
            'raw_request': None,
            'request_body': None,
            'accept_cookies': False,
            'keep_alive': False,
            'is_fingerprint': False,
            'wordlist': None,
            'reports_dir': None,
            'is_random_user_agent': False,
            'is_random_list': False,
            'extensions': [],
            'ignore_extensions': [],
            'sniffers': [],
            'include_status': [],
            'exclude_status': [],
            'exclude_size': [],
            'exclude_size_range': [],
            'match_text': [],
            'exclude_text': [],
            'match_regex': [],
            'exclude_regex': [],
            'min_response_length': None,
            'max_response_length': None,
            'threads': 1,
            'delay': 0,
            'timeout': 30,
            'retries': 1,
            'debug': 0,
            'is_internal_torlist': False,
            'is_external_torlist': False,
            'torlist': '',
            'requested_method': 'HEAD',
            'session_save': None,
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        }
        config.update(config_overrides)

        setattr(br, '_Browser__config', SimpleNamespace(**config))
        setattr(br, '_Browser__client', MagicMock())
        setattr(br, '_Browser__reader', SimpleNamespace(
            total_lines=3,
            get_ignored_list=MagicMock(return_value=[]),
            get_lines=MagicMock(),
        ))
        setattr(br, '_Browser__response', SimpleNamespace(
            handle=MagicMock(),
            waf_detection=None,
        ))
        setattr(br, '_Browser__pool', SimpleNamespace(
            items_size=1,
            total_items_size=1,
            size=0,
            workers_size=1,
            add=MagicMock(),
            join=MagicMock(),
            extend_total_items=MagicMock(),
            is_started=True,
        ))
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })
        setattr(br, '_Browser__session_lock', __import__('threading').RLock())
        setattr(br, '_Browser__session', None)
        setattr(br, '_Browser__session_dirty', False)
        setattr(br, '_Browser__completed_requests', set())
        setattr(br, '_Browser__pending_requests', {})
        setattr(br, '_Browser__processed_offset', 0)
        setattr(br, '_Browser__session_snapshot', None)
        setattr(br, '_Browser__waf_safe_lock', __import__('threading').RLock())
        setattr(br, '_Browser__waf_safe_active', False)
        setattr(br, '_Browser__waf_safe_next_at', 0.0)
        setattr(br, '_Browser__waf_safe_delay', 0.75)
        setattr(br, '_Browser__waf_safe_vendor', None)
        setattr(br, '_Browser__waf_safe_confidence', None)

        return br

    def test_request_with_waf_safe_mode_active_without_sleep(self):
        """Browser should serialize through safe mode without sleeping when slot is already available."""

        br = self.make_browser()
        br._Browser__client.request.return_value = 'ok'
        br._Browser__waf_safe_active = True
        br._Browser__waf_safe_next_at = 10.0

        with patch('src.lib.browser.browser.time.monotonic', side_effect=[10.5, 10.6]), \
                patch('src.lib.browser.browser.time.sleep') as sleep_mock:
            actual = br._Browser__request_with_waf_safe_mode('http://example.com')

        self.assertEqual(actual, 'ok')
        sleep_mock.assert_not_called()
        self.assertEqual(br._Browser__waf_safe_next_at, 11.35)

    def test_activate_waf_safe_mode_returns_when_safe_mode_disabled(self):
        """Browser should not activate safe mode when the feature is disabled."""

        br = self.make_browser(is_waf_safe_mode=False)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92})

        self.assertFalse(br._Browser__waf_safe_active)
        warning_mock.assert_not_called()

    def test_activate_waf_safe_mode_returns_for_invalid_detection(self):
        """Browser should ignore non-dict WAF detections."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode('bad')

        self.assertFalse(br._Browser__waf_safe_active)
        warning_mock.assert_not_called()

    def test_activate_waf_safe_mode_does_not_warn_twice(self):
        """Browser should not re-activate or re-warn when safe mode is already active."""

        br = self.make_browser()
        br._Browser__waf_safe_active = True

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92})

        warning_mock.assert_not_called()

    def test_http_request_records_ignored_when_response_is_filtered_out(self):
        """Browser should classify filtered responses as ignored."""

        br = self.make_browser(is_response_filtering=True)
        br._Browser__client.request.return_value = SimpleNamespace(data=b'body', headers={})
        br._Browser__response.handle.return_value = ('success', 'http://example.com/admin', '10B', '200')

        with patch.object(Browser, '_Browser__is_response_allowed', return_value=False):
            br._Browser__http_request('http://example.com/admin', depth=0)

        self.assertEqual(br._Browser__result['items']['ignored'], ['http://example.com/admin'])

    def test_is_response_allowed_rejects_excluded_status(self):
        """Browser should reject statuses from exclude-status filters."""

        br = self.make_browser(
            is_response_filtering=True,
            include_status=[],
            exclude_status=['403'],
        )

        response = SimpleNamespace(data=b'', headers={'Content-Length': '0'})
        allowed = br._Browser__is_response_allowed(response, ('forbidden', 'http://example.com', '0B', '403'))

        self.assertFalse(allowed)

    def test_should_expand_recursively_allows_non_excluded_extension(self):
        """Browser recursive expansion should allow files with extensions outside the exclude list."""

        br = self.make_browser(recursive_exclude=['jpg', 'png'])

        actual = br._Browser__should_expand_recursively('200', 'http://example.com/admin.php', 0)

        self.assertTrue(actual)

    def test_enqueue_recursive_children_skips_when_loader_produces_no_urls(self):
        """Browser should not expand totals or enqueue work when recursive loader yields no child URLs."""

        br = self.make_browser()
        br._Browser__reader.get_lines.side_effect = lambda params, loader: loader([])

        with patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            br._Browser__enqueue_recursive_children('http://example.com/panel', 0)

        br._Browser__pool.extend_total_items.assert_not_called()
        br._Browser__pool.add.assert_not_called()
        debug_mock.assert_not_called()

    def test_enqueue_recursive_children_does_not_add_when_request_already_registered(self):
        """Browser should skip pool.add when child request is already registered."""

        br = self.make_browser()
        br._Browser__reader.get_lines.side_effect = lambda params, loader: loader(['http://example.com/admin'])
        with patch.object(Browser, '_Browser__register_pending_request', return_value=False):
            br._Browser__enqueue_recursive_children('http://example.com/panel', 0)

        br._Browser__pool.add.assert_not_called()

    def test_add_urls_skips_pool_add_when_request_registration_returns_false(self):
        """Browser _add_urls should tolerate duplicate or already tracked items."""

        br = self.make_browser()
        with patch.object(Browser, '_Browser__is_ignored', return_value=False), \
                patch.object(Browser, '_Browser__register_pending_request', return_value=False):
            br._add_urls(['http://example.com/admin'])

        br._Browser__pool.add.assert_not_called()
        br._Browser__pool.join.assert_called_once()

    def test_catch_report_data_supports_partial_waf_metadata(self):
        """Browser should persist partial WAF metadata without requiring all fields."""

        br = self.make_browser()
        br._Browser__catch_report_data(
            'blocked',
            'http://example.com/login',
            '10B',
            '403',
            metadata={'confidence': 92}
        )

        self.assertEqual(
            br._Browser__result['report_items']['blocked'],
            [{'url': 'http://example.com/login', 'size': '10B', 'code': '403', 'waf_confidence': 92}]
        )

    def test_export_targets_omits_port_when_missing(self):
        """Browser should export target without port when port is None."""

        br = self.make_browser(port=None)

        actual = br._Browser__export_targets()

        self.assertEqual(actual, [{'host': 'example.com', 'scheme': 'http://', 'ssl': False}])

    def test_save_session_returns_when_manager_is_missing(self):
        """Browser should quietly skip session save when session manager is absent."""

        br = self.make_browser(is_session_enabled=True)
        br._Browser__session = None

        br._Browser__save_session(reason='items', force=False)

        self.assertFalse(br._Browser__session_dirty)

    def test_resume_pending_requests_bumps_total_items_size(self):
        """Browser should grow total-items size when restored pending requests exceed current total."""

        br = self.make_browser()
        br._Browser__processed_offset = 5
        br._Browser__pending_requests = {
            '0::http://example.com/a': {'url': 'http://example.com/a', 'depth': 0},
            '0::http://example.com/b': {'url': 'http://example.com/b', 'depth': 0},
        }
        br._Browser__pool.total_items_size = 1

        br._Browser__resume_pending_requests()

        self.assertEqual(br._Browser__pool.total_items_size, 7)
        self.assertEqual(br._Browser__pool.add.call_count, 2)


    def test_activate_waf_safe_mode_uses_tpl_warning_key(self):
        """Browser should announce safe mode activation through tpl key-based warning."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92})

        warning_mock.assert_called_once_with(
            key='waf_safe_mode_activated',
            vendor='Cloudflare',
            confidence=92,
            delay=0.75
        )

class TestBrowserInitExtra(unittest.TestCase):
    """Extra init-branch coverage for Browser."""

    def make_config(self, **overrides):
        data = {
            'scan': 'directories',
            'DEFAULT_SCAN': 'directories',
            '_method': 'HEAD',
            'method': 'GET',
            'method_override_items': [],
            'torlist': '',
            'is_random_list': False,
            'is_extension_filter': False,
            'is_ignore_extension_filter': False,
            'is_external_wordlist': False,
            'wordlist': None,
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
            'is_external_reports_dir': False,
            'reports_dir': None,
            'extensions': [],
            'ignore_extensions': [],
            'threads': 1,
            'delay': 0,
            'is_session_enabled': False,
            'session_save': None,
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        }
        data.update(overrides)
        return SimpleNamespace(**data)

    def test_init_head_get_without_override_items_does_not_warn(self):
        """Browser init should not warn when HEAD->GET override has no items to report."""

        reader = MagicMock()
        reader.total_lines = 3

        with patch('src.lib.browser.browser.Config', return_value=self.make_config()), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            Browser({'host': 'test.local'})

        warning_mock.assert_not_called()

    def test_init_applies_extension_filter_on_default_scan(self):
        """Browser init should build extensionlist when extension-filter mode is enabled."""

        reader = MagicMock()
        reader.total_lines = 3

        with patch('src.lib.browser.browser.Config', return_value=self.make_config(is_extension_filter=True, extensions=['php'])), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()):
            Browser({'host': 'test.local'})

        reader.filter_by_extension.assert_called_once()

    def test_init_creates_session_manager_when_enabled(self):
        """Browser init should create SessionManager when persistent sessions are enabled."""

        reader = MagicMock()
        reader.total_lines = 3
        session_manager = MagicMock()

        with patch('src.lib.browser.browser.Config', return_value=self.make_config(
            is_session_enabled=True,
            session_save='/tmp/session.json',
            session_autosave_sec=20,
            session_autosave_items=200
        )), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch('src.lib.browser.browser.SessionManager', return_value=session_manager) as manager_mock:
            br = Browser({'host': 'test.local'})

        manager_mock.assert_called_once()
        self.assertIs(getattr(br, '_Browser__session'), session_manager)

    def test_init_restores_snapshot_when_present(self):
        """Browser init should restore state from a provided session snapshot."""

        reader = MagicMock()
        reader.total_lines = 3
        snapshot = {'pending': [], 'seen': [], 'stats': {'processed': 0, 'total_items': 1}}

        with patch('src.lib.browser.browser.Config', return_value=self.make_config()), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch.object(Browser, '_Browser__restore_session_state') as restore_mock:
            Browser({'host': 'test.local', 'session_snapshot': snapshot})

        restore_mock.assert_called_once_with(snapshot)