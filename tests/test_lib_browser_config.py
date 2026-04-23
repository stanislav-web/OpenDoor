# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.config import Config


class TestBrowserConfig(unittest.TestCase):
    """TestBrowserConfig class."""

    def test_defaults_are_normalized(self):
        """Config should expose normalized defaults when params are missing."""

        cfg = Config({'reports': 'std'})

        self.assertEqual(cfg.scan, Config.DEFAULT_SCAN)
        self.assertEqual(cfg.scheme, Config.DEFAULT_SCHEME)
        self.assertFalse(cfg.is_ssl)
        self.assertEqual(cfg.prefix, '')
        self.assertEqual(cfg.proxy, '')
        self.assertFalse(cfg.is_proxy)
        self.assertFalse(cfg.is_random_list)
        self.assertFalse(cfg.is_extension_filter)
        self.assertFalse(cfg.is_ignore_extension_filter)
        self.assertFalse(cfg.is_external_wordlist)
        self.assertFalse(cfg.is_external_reports_dir)
        self.assertEqual(cfg.torlist, '')
        self.assertEqual(cfg.user_agent, Config.DEFAULT_USER_AGENT)
        self.assertEqual(cfg.threads, Config.DEFAULT_MIN_THREADS)
        self.assertFalse(cfg.accept_cookies)
        self.assertFalse(cfg.keep_alive)
        self.assertEqual(cfg.timeout, Config.DEFAULT_SOCKET_TIMEOUT)

    def test_port_switches_to_ssl_default_for_https(self):
        """Config.port should switch from 80 to 443 when SSL is enabled."""

        cfg = Config({'reports': 'std', 'ssl': True, 'port': 80})
        self.assertEqual(cfg.port, 443)

    def test_method_uses_get_for_non_file_sniffers(self):
        """Config.method should use GET when multiple sniffers are enabled."""

        cfg = Config({'reports': 'std', 'sniff': 'file,indexof'})
        self.assertEqual(cfg.method, 'GET')

    def test_method_uses_head_for_single_file_sniffer(self):
        """Config.method should use HEAD for a single file sniffer."""

        cfg = Config({'reports': 'std', 'sniff': 'file'})
        self.assertEqual(cfg.method, 'HEAD')

    def test_method_override_warning_lists_body_required_sniffers(self):
        """Config should describe why HEAD is overridden when body sniffers are selected."""

        cfg = Config({'reports': 'std', 'method': 'HEAD', 'sniff': 'file,indexof,collation,skipempty'})

        self.assertEqual(
            cfg.method_override_warning,
            'HEAD overridden to GET because selected sniffers/filters require response body: indexof, collation'
        )

    def test_method_override_warning_is_empty_without_body_required_sniffers(self):
        """Config should not warn when selected sniffers can still work with HEAD."""

        cfg = Config({'reports': 'std', 'method': 'HEAD', 'sniff': 'file,skipempty'})

        self.assertEqual(cfg.method_override_warning, '')

    def test_reports_extensions_and_ignore_extensions_are_normalized(self):
        """Config should normalize CSV values into clean lists."""

        cfg = Config({
            'reports': 'json, html',
            'extensions': 'php, html ',
            'ignore_extensions': 'jpg, png ',
        })

        self.assertEqual(cfg.reports, ['json', 'html', 'std'])
        self.assertEqual(cfg.extensions, ['php', 'html'])
        self.assertEqual(cfg.ignore_extensions, ['jpg', 'png'])

    def test_proxy_related_flags_are_derived_from_input(self):
        """Config should resolve standalone and tor proxy modes correctly."""

        standalone = Config({'reports': 'std', 'proxy': 'http://127.0.0.1:8080'})
        self.assertTrue(standalone.is_proxy)
        self.assertTrue(standalone.is_standalone_proxy)
        self.assertFalse(standalone.is_external_torlist)

        external = Config({'reports': 'std', 'torlist': 'torlist.txt'})
        self.assertTrue(external.is_proxy)
        self.assertTrue(external.is_external_torlist)

        internal = Config({'reports': 'std', 'tor': True})
        self.assertTrue(internal.is_proxy)
        self.assertTrue(internal.is_internal_torlist)

    def test_timeout_setter_converts_to_float(self):
        """Config.timeout setter should coerce the value to float."""

        cfg = Config({'reports': 'std'})
        cfg.timeout = '4.5'
        self.assertEqual(cfg.timeout, 4.5)

    def test_threads_and_prefix_mutators_work(self):
        """Config should expose configurable threads and normalized prefixes."""

        cfg = Config({'reports': 'std', 'prefix': '/admin/', 'threads': 5, 'reports_dir': '/tmp/reports', 'wordlist': '/tmp/list'})
        self.assertEqual(cfg.prefix, 'admin/')
        self.assertEqual(cfg.threads, 5)
        cfg.set_threads(9)
        self.assertEqual(cfg.threads, 9)
        self.assertEqual(cfg.reports_dir, '/tmp/reports')
        self.assertEqual(cfg.wordlist, '/tmp/list')
        self.assertTrue(cfg.is_external_reports_dir)
        self.assertTrue(cfg.is_external_wordlist)

    def test_recursive_settings_are_normalized(self):
        """Config should normalize recursive scan settings."""

        cfg = Config({
            'reports': 'std',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200, 403 , 301',
            'recursive_exclude': '.jpg, png , css ',
        })

        self.assertTrue(cfg.is_recursive)
        self.assertEqual(cfg.recursive_depth, 2)
        self.assertEqual(cfg.recursive_status, ['200', '403', '301'])
        self.assertEqual(cfg.recursive_exclude, ['jpg', 'png', 'css'])

    def test_recursive_settings_defaults_are_safe(self):
        """Config should expose safe recursive defaults when the feature is disabled."""

        cfg = Config({'reports': 'std'})

        self.assertFalse(cfg.is_recursive)
        self.assertEqual(cfg.recursive_depth, 1)
        self.assertEqual(cfg.recursive_status, [])
        self.assertEqual(cfg.recursive_exclude, [])

    def test_headers_are_normalized(self):
        """Config should normalize custom request headers."""

        cfg = Config({
            'reports': 'std',
            'header': [' Authorization: Bearer test ', 'X-Test: 1', '   '],
        })

        self.assertEqual(
            cfg.headers,
            ['Authorization: Bearer test', 'X-Test: 1']
        )

    def test_headers_default_to_empty_list(self):
        """Config should expose an empty header list by default."""

        cfg = Config({'reports': 'std'})

        self.assertEqual(cfg.headers, [])

    def test_cookies_are_normalized(self):
        """Config should normalize custom request cookies."""

        cfg = Config({
            'reports': 'std',
            'cookie': [' sid=abc123 ', 'locale=en', '   '],
        })

        self.assertEqual(cfg.cookies, ['sid=abc123', 'locale=en'])

    def test_cookies_default_to_empty_list(self):
        """Config should expose an empty cookie list by default."""

        cfg = Config({'reports': 'std'})

        self.assertEqual(cfg.cookies, [])

    def test_response_filter_properties_are_normalized(self):
        """Config should normalize all response-filter properties."""

        cfg = Config({
            'reports': 'std',
            'include_status': ['200-201', '403'],
            'exclude_status': ['404'],
            'exclude_size': ['0', '12'],
            'exclude_size_range': ['1-8', '10-20'],
            'match_text': ['login'],
            'exclude_text': ['forbidden'],
            'match_regex': ['(?i)admin'],
            'exclude_regex': ['(?i)denied'],
            'min_response_length': 5,
            'max_response_length': 50,
        })

        self.assertEqual(cfg.include_status, ['200', '201', '403'])
        self.assertEqual(cfg.exclude_status, ['404'])
        self.assertEqual(cfg.exclude_size, [0, 12])
        self.assertEqual(cfg.exclude_size_range, [(1, 8), (10, 20)])
        self.assertEqual(cfg.match_text, ['login'])
        self.assertEqual(cfg.exclude_text, ['forbidden'])
        self.assertEqual(cfg.match_regex, ['(?i)admin'])
        self.assertEqual(cfg.exclude_regex, ['(?i)denied'])
        self.assertEqual(cfg.min_response_length, 5)
        self.assertEqual(cfg.max_response_length, 50)
        self.assertTrue(cfg.is_response_filtering)
        self.assertTrue(cfg.is_body_required_response_filtering)

    def test_method_override_items_merge_filters_and_sniffers_without_duplicates(self):
        """Config should merge body-required sniffers and filters into one override list."""

        cfg = Config({
            'reports': 'std',
            'method': 'HEAD',
            'sniff': 'indexof,file',
            'match_text': ['login'],
            'exclude_regex': ['(?i)forbidden'],
        })

        self.assertEqual(cfg.method_override_items, ['indexof', '--match-text', '--exclude-regex'])
        self.assertIn('--match-text', cfg.method_override_warning)
        self.assertIn('indexof', cfg.method_override_warning)
        self.assertEqual(cfg.method, 'GET')

    def test_method_preserves_requested_method_without_sniffers_or_filters(self):
        """Config.method should preserve the explicit method when no body-dependent features are active."""

        cfg = Config({'reports': 'std', 'method': 'post'})
        self.assertEqual(cfg.method, 'POST')
        self.assertFalse(cfg.is_response_filtering)

    def test_delay_reports_and_recursive_exclude_cover_edge_paths(self):
        """Config should normalize delay rounding, report defaults and empty recursive excludes."""

        cfg = Config({'delay': 1.7, 'reports': None, 'recursive_exclude': None})
        self.assertEqual(cfg.delay, 1)
        self.assertEqual(cfg.reports, ['std'])
        self.assertEqual(cfg.recursive_exclude, [])

    def test_normalize_csv_passthrough_for_lists(self):
        """Config._normalize_csv() should keep list values unchanged."""

        self.assertEqual(Config._normalize_csv(['200', '403']), ['200', '403'])

    def test_expand_numeric_tokens_should_ignore_blank_entries(self):
        """Config._expand_numeric_tokens() should skip blank tokens while expanding ranges."""

        self.assertEqual(
            Config._expand_numeric_tokens(['200', ' ', '201-202']),
            ['200', '201', '202']
        )

    def test_scan_setter_request_body_and_raw_request_flags_should_work(self):
        """Config should expose scan setter, raw-request flag and request-body accessors."""

        cfg = Config({
            'reports': 'std',
            'raw_request': 'request.txt',
            'request_body': 'username=admin',
        })

        cfg.scan = 'subdomains'

        self.assertEqual(cfg.scan, 'subdomains')
        self.assertTrue(cfg.is_raw_request)
        self.assertEqual(cfg.request_body, 'username=admin')

    def test_method_override_warning_should_be_empty_for_non_head_requests(self):
        """Config should not warn about HEAD override when explicit method is not HEAD."""

        cfg = Config({
            'reports': 'std',
            'method': 'POST',
            'match_text': ['login'],
        })

        self.assertEqual(cfg.method_override_warning, '')
        self.assertEqual(cfg.method, 'POST')

    def test_is_standalone_proxy_should_clear_torlist(self):
        """Config.is_standalone_proxy should clear torlist when standalone proxy mode wins."""

        cfg = Config({
            'reports': 'std',
            'proxy': 'http://127.0.0.1:8080',
            'torlist': 'custom-torlist.txt',
        })

        self.assertTrue(cfg.is_standalone_proxy)
        self.assertEqual(cfg.torlist, '')

    def test_recursive_exclude_should_return_empty_list_when_not_configured(self):
        """Config.recursive_exclude should safely return an empty list when unset."""

        cfg = Config({
            'reports': 'std',
            'recursive_exclude': None,
        })

        self.assertEqual(cfg.recursive_exclude, [])

    def test_session_mode_is_disabled_by_default(self):
        """Config should keep session mode disabled when session_save is not provided."""

        cfg = Config({
            'reports': 'std',
            'host': 'example.com',
        })

        self.assertFalse(cfg.is_session_enabled)

    def test_session_mode_is_enabled_only_when_session_save_is_present(self):
        """Config should enable persistent sessions only when session_save is configured."""

        cfg = Config({
            'reports': 'std',
            'host': 'example.com',
            'session_save': '/tmp/session.json',
        })

        self.assertTrue(cfg.is_session_enabled)
        self.assertEqual(cfg.session_save, '/tmp/session.json')

    def test_session_config_accessors_cover_load_and_thresholds(self):
        """Config should expose session load/save and autosave threshold accessors."""

        cfg = Config({
            'reports': 'std',
            'session_save': '/tmp/session.json',
            'session_load': '/tmp/session.json',
            'session_autosave_sec': 7,
            'session_autosave_items': 13,
        })

        self.assertEqual(cfg.session_save, '/tmp/session.json')
        self.assertEqual(cfg.session_load, '/tmp/session.json')
        self.assertEqual(cfg.session_autosave_sec, 7)
        self.assertEqual(cfg.session_autosave_items, 13)
        self.assertTrue(cfg.is_session_enabled)

if __name__ == '__main__':
    unittest.main()