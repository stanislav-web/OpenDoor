# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch

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
        self.assertEqual(cfg.proxy_list, '')
        self.assertEqual(cfg.user_agent, Config.DEFAULT_USER_AGENT)
        self.assertEqual(cfg.threads, Config.DEFAULT_MIN_THREADS)
        self.assertFalse(cfg.accept_cookies)
        self.assertFalse(cfg.keep_alive)
        self.assertFalse(cfg.is_follow_redirects)

    def test_follow_redirects_config_flag(self):
        """Config should expose explicit same-host redirect following without method override."""

        cfg = Config({'reports': 'std', 'follow_redirects': True})

        self.assertTrue(cfg.is_follow_redirects)
        self.assertNotIn('--follow-redirects', cfg.method_override_items)
        self.assertEqual(cfg.method, 'HEAD')

    def test_keep_alive_respects_explicit_false_and_true(self):
        """Config should not treat an explicit False keep_alive value as enabled."""

        self.assertFalse(Config({'reports': 'std', 'keep_alive': False}).keep_alive)
        self.assertTrue(Config({'reports': 'std', 'keep_alive': True}).keep_alive)

    def test_memory_monitor_follows_debug_level(self):
        """Config should expose memory diagnostics only when debug is enabled."""

        self.assertFalse(Config({'reports': 'std', 'debug': 0}).is_memory_monitor)
        self.assertTrue(Config({'reports': 'std', 'debug': 1}).is_memory_monitor)
        self.assertTrue(Config({'reports': 'std', 'debug': '2'}).is_memory_monitor)
        self.assertFalse(Config({'reports': 'std', 'debug': 'bad'}).is_memory_monitor)
        self.assertFalse(Config({'reports': 'std', 'debug': 0, 'memory_monitor': True}).is_memory_monitor)

    def test_port_switches_to_ssl_default_for_https(self):
        """Config.port should switch from 80 to 443 when SSL is enabled."""

        cfg = Config({'reports': 'std', 'ssl': True, 'port': 80})
        self.assertEqual(cfg.port, 443)

    def test_scheme_is_source_of_truth_for_ssl_mode(self):
        """Config should derive SSL mode from HTTPS scheme."""

        cfg = Config({'reports': 'std', 'scheme': 'https://', 'ssl': False, 'port': 80})

        self.assertEqual(cfg.scheme, 'https://')
        self.assertTrue(cfg.is_ssl)
        self.assertEqual(cfg.port, 443)

    def test_legacy_ssl_true_promotes_default_http_scheme(self):
        """Config should keep old wizard configs with ssl=True compatible."""

        cfg = Config({'reports': 'std', 'scheme': 'http://', 'ssl': True, 'port': 80})

        self.assertEqual(cfg.scheme, 'https://')
        self.assertTrue(cfg.is_ssl)
        self.assertEqual(cfg.port, 443)

    def test_port_defaults_by_scheme_when_missing(self):
        """Config.port should default to the scheme default when no port is configured."""

        self.assertEqual(Config({'reports': 'std', 'scheme': 'http://'}).port, 80)
        self.assertEqual(Config({'reports': 'std', 'scheme': 'https://'}).port, 443)

    def test_port_normalizes_string_values(self):
        """Config.port should normalize wizard/session string port values."""

        self.assertEqual(Config({'reports': 'std', 'scheme': 'http://', 'port': '8080'}).port, 8080)

    def test_port_rejects_invalid_values(self):
        """Config.port should reject invalid port values before runtime requests."""

        for value in ['abc', '0', '-1', '65536']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Config({'reports': 'std', 'scheme': 'http://', 'port': value})

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

        cfg = Config({'reports': 'std', 'method': 'HEAD', 'sniff': 'file,indexof,collation,stacktrace,endpoint,skipempty'})

        self.assertEqual(
            cfg.method_override_warning,
            'HEAD overridden to GET because selected sniffers/filters require response body: indexof, collation, stacktrace, endpoint'
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

    def test_reports_default_to_std_when_missing(self):
        """Config.reports should default to std when reports are missing or disabled."""

        self.assertEqual(Config({}).reports, ['std'])
        self.assertEqual(Config({'reports': 'None'}).reports, ['std'])

    def test_reports_are_normalized_and_deduped(self):
        """Config.reports should normalize report names and avoid duplicates."""

        self.assertEqual(Config({'reports': 'HTML,csv,csv,std'}).reports, ['html', 'csv', 'std'])
        self.assertEqual(Config({'reports': ['json', 'csv', 'json']}).reports, ['json', 'csv', 'std'])

    def test_reports_reject_unknown_values(self):
        """Config.reports should reject unsupported wizard/session report plugins."""

        for value in ['xml', 'std,xml', ['json', 'bad']]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Config({'reports': value})

    def test_reports_dir_normalizes_none_and_paths(self):
        """Config.reports_dir should normalize None-like values and filesystem paths."""

        self.assertIsNone(Config({'reports_dir': None}).reports_dir)
        self.assertIsNone(Config({'reports_dir': 'None'}).reports_dir)
        self.assertEqual(Config({'reports_dir': ['./reports']}).reports_dir, os.path.abspath('./reports'))
        self.assertEqual(Config({'reports_dir': './reports'}).reports_dir, os.path.abspath('./reports'))

    def test_random_list_flag_requires_true_value(self):
        """Config should not enable random list mode from explicit False or missing values."""

        self.assertFalse(Config({'reports': 'std', 'random_list': False}).is_random_list)
        self.assertTrue(Config({'reports': 'std', 'random_list': True}).is_random_list)

    def test_empty_extension_filters_are_disabled(self):
        """Config should not enable extension filters from empty CSV values."""

        cfg = Config({'reports': 'std', 'extensions': ' , ', 'ignore_extensions': ',,'})

        self.assertEqual(cfg.extensions, [])
        self.assertEqual(cfg.ignore_extensions, [])
        self.assertFalse(cfg.is_extension_filter)
        self.assertFalse(cfg.is_ignore_extension_filter)

    def test_proxy_related_flags_are_derived_from_input(self):
        """Config should resolve standalone and proxy routing modes correctly."""

        standalone = Config({'reports': 'std', 'proxy': 'http://127.0.0.1:8080'})
        self.assertTrue(standalone.is_proxy)
        self.assertTrue(standalone.is_standalone_proxy)
        self.assertFalse(standalone.is_external_proxy_list)

        external = Config({'reports': 'std', 'proxy_list': 'proxy-list.txt'})
        self.assertTrue(external.is_proxy)
        self.assertTrue(external.is_external_proxy_list)
        self.assertEqual(external.proxy_rotation, 'random')

        sequential = Config({'reports': 'std', 'proxy_list': 'proxy-list.txt', 'proxy_rotation': 'sequential'})
        self.assertEqual(sequential.proxy_rotation, 'sequential')

        internal = Config({'reports': 'std', 'proxy_pool': True})
        self.assertTrue(internal.is_proxy)
        self.assertTrue(internal.is_builtin_proxy_pool)

    def test_timeout_setter_converts_to_float(self):
        """Config.timeout setter should coerce the value to float."""

        cfg = Config({'reports': 'std'})
        cfg.timeout = '4.5'
        self.assertEqual(cfg.timeout, 4.5)

    def test_retries_are_normalized_for_runtime_transport(self):
        """Config should expose retries as a non-negative integer for urllib3."""

        self.assertEqual(Config({'reports': 'std', 'retries': '0'}).retries, 0)
        self.assertEqual(Config({'reports': 'std', 'retries': '3'}).retries, 3)
        self.assertFalse(Config({'reports': 'std', 'retries': None}).retries)

        with self.assertRaises(ValueError):
            Config({'reports': 'std', 'retries': '-1'})

    def test_retries_fail_streak_defaults_and_validates_positive_integer(self):
        """Config should expose the consecutive max-retry path abort threshold."""

        self.assertEqual(Config({'reports': 'std'}).retries_fail_streak, 10)
        self.assertEqual(Config({'reports': 'std', 'retries_fail_streak': '25'}).retries_fail_streak, 25)

        with self.assertRaises(ValueError):
            Config({'reports': 'std', 'retries_fail_streak': '0'})

        with self.assertRaises(ValueError):
            Config({'reports': 'std', 'retries_fail_streak': '-1'})

    def test_threads_default_to_min_when_missing(self):
        """Config should default worker threads to the minimum safe value."""

        self.assertEqual(Config({'reports': 'std'}).threads, Config.DEFAULT_MIN_THREADS)

    def test_threads_normalizes_string_values(self):
        """Config should normalize thread counts from wizard/session strings."""

        self.assertEqual(Config({'reports': 'std', 'threads': '8'}).threads, 8)

    def test_threads_rejects_invalid_values(self):
        """Config should reject thread counts that cannot create workers."""

        for value in ['0', 0, '-1', -1, 'bad']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Config({'reports': 'std', 'threads': value})

    def test_set_threads_validates_values(self):
        """Config.set_threads() should keep runtime thread assignments safe."""

        cfg = Config({'reports': 'std'})
        cfg.set_threads('3')

        self.assertEqual(cfg.threads, 3)

        with self.assertRaises(ValueError):
            cfg.set_threads(0)

    def test_default_max_threads_is_configured_to_fifty(self):
        """Config should allow a higher I/O-bound thread clamp for scan workers."""

        self.assertEqual(Config.DEFAULT_MAX_THREADS, 50)

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

    def test_recursive_defaults_apply_when_enabled(self):
        """Config should apply recursive defaults when recursion is enabled."""

        cfg = Config({'reports': 'std', 'recursive': True})

        self.assertTrue(cfg.is_recursive)
        self.assertEqual(cfg.recursive_depth, 1)
        self.assertEqual(cfg.recursive_status, ['200', '301', '302', '307', '308', '403'])
        self.assertEqual(
            cfg.recursive_exclude,
            ['jpg', 'jpeg', 'png', 'gif', 'svg', 'css', 'js', 'ico', 'woff', 'woff2', 'ttf', 'map', 'pdf', 'zip', 'gz', 'tar']
        )

    def test_recursive_settings_reject_invalid_values(self):
        """Config should reject invalid recursive settings from wizard/session snapshots."""

        for params in [
            {'recursive_depth': '0'},
            {'recursive_status': '200-299'},
            {'recursive_status': '600'},
            {'recursive_exclude': '../env'},
            {'recursive_exclude': 'jpg/png'},
        ]:
            with self.subTest(params=params):
                config = {'reports': 'std'}
                config.update(params)
                with self.assertRaises(ValueError):
                    Config(config)


    def test_tls_legacy_defaults_to_disabled_and_can_be_enabled(self):
        """Config should expose the opt-in legacy TLS mode."""

        self.assertFalse(Config({'reports': 'std'}).is_tls_legacy)
        self.assertTrue(Config({'reports': 'std', 'tls_legacy': True}).is_tls_legacy)

    def test_client_cert_config_is_normalized_and_privacy_safe(self):
        """Config should store mTLS paths and env names, never env password values."""

        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, 'client.crt')
            key_path = os.path.join(tmpdir, 'client.key')
            with open(cert_path, 'w', encoding='utf-8') as handle:
                handle.write('cert')
            with open(key_path, 'w', encoding='utf-8') as handle:
                handle.write('key')

            with patch.dict(os.environ, {'OPENDOOR_CLIENT_KEY_PASSWORD': 'secret-value'}):
                cfg = Config({
                    'reports': 'std',
                    'client_cert': cert_path,
                    'client_key': key_path,
                    'client_key_password_env': 'OPENDOOR_CLIENT_KEY_PASSWORD',
                })

        self.assertTrue(cfg.is_client_cert_enabled)
        self.assertEqual(cfg.client_cert, os.path.abspath(cert_path))
        self.assertEqual(cfg.client_key, os.path.abspath(key_path))
        self.assertEqual(cfg.client_key_password_env, 'OPENDOOR_CLIENT_KEY_PASSWORD')
        self.assertNotEqual(cfg.client_key_password_env, 'secret-value')

    def test_client_cert_config_rejects_invalid_combinations(self):
        """Config should revalidate session/wizard mTLS values."""

        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, 'client.key')
            with open(key_path, 'w', encoding='utf-8') as handle:
                handle.write('key')

            with self.assertRaises(ValueError):
                Config({'reports': 'std', 'client_key': key_path})

            with self.assertRaises(ValueError):
                Config({'reports': 'std', 'client_key_password_env': 'OPENDOOR_MISSING_PASSWORD'})

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


    def test_wizard_regex_filter_should_preserve_commas_and_precompile(self):
        """Config should treat wizard regex values as one pattern even when they contain commas."""

        cfg = Config({
            'reports': 'std',
            'method': 'HEAD',
            'match_regex': '[a-z]{1,3}',
            'exclude_regex': 'error,{critical}',
        })

        self.assertEqual(cfg.match_regex, ['[a-z]{1,3}'])
        self.assertEqual(cfg.exclude_regex, ['error,{critical}'])
        self.assertEqual(len(cfg.match_regex_compiled), 1)
        self.assertEqual(len(cfg.exclude_regex_compiled), 1)
        self.assertEqual(cfg.method, 'GET')

    def test_config_rejects_invalid_wizard_response_filters_early(self):
        """Config should reject invalid response filters from wizard/session params."""

        invalid_cases = [
            {'include_status': '99'},
            {'exclude_status': '600'},
            {'exclude_size': 'abc'},
            {'exclude_size_range': '200-100'},
            {'match_regex': '['},
            {'min_response_length': -1},
            {'min_response_length': 10, 'max_response_length': 1},
        ]

        for params in invalid_cases:
            with self.subTest(params=params):
                payload = {'reports': 'std'}
                payload.update(params)
                with self.assertRaises(ValueError):
                    Config(payload)

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
        self.assertEqual(cfg.delay, 1.7)
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

    def test_is_standalone_proxy_should_clear_proxy_list(self):
        """Config.is_standalone_proxy should clear proxy_list when standalone proxy mode wins."""

        cfg = Config({
            'reports': 'std',
            'proxy': 'http://127.0.0.1:8080',
            'proxy_list': 'custom-proxy-list.txt',
        })

        self.assertTrue(cfg.is_standalone_proxy)
        self.assertEqual(cfg.proxy_list, '')

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

    def test_waf_detect_flag_is_disabled_by_default_and_enabled_explicitly(self):
        """Config should expose passive WAF detection as an opt-in flag."""

        cfg = Config({'reports': 'std'})
        self.assertFalse(cfg.is_waf_detect)

        cfg = Config({'reports': 'std', 'waf_detect': True})
        self.assertTrue(cfg.is_waf_detect)


    def test_fingerprint_defaults_to_false_when_missing(self):
        """Config should keep fingerprinting disabled by default."""

        cfg = Config({'reports': 'std'})

        self.assertFalse(cfg.is_fingerprint)

    def test_fingerprint_normalizes_bool_like_values(self):
        """Config should normalize fingerprint bool-like wizard/session values."""

        for value in [True, 'true', 'True', '1', 'yes', 'on']:
            with self.subTest(value=value):
                self.assertTrue(Config({'reports': 'std', 'fingerprint': value}).is_fingerprint)

        for value in [False, 'false', 'False', '0', 'no', 'off', None]:
            with self.subTest(value=value):
                self.assertFalse(Config({'reports': 'std', 'fingerprint': value}).is_fingerprint)

    def test_fingerprint_rejects_invalid_values(self):
        """Config should reject malformed fingerprint bool values."""

        with self.assertRaises(ValueError):
            Config({'reports': 'std', 'fingerprint': 'maybe'})


    def test_waf_flags_default_to_false_when_missing(self):
        """Config should keep WAF features disabled by default."""

        cfg = Config({'reports': 'std'})

        self.assertFalse(cfg.is_waf_detect)
        self.assertFalse(cfg.is_waf_safe_mode)
        self.assertFalse(cfg.is_waf_guard)

    def test_waf_flags_normalize_string_values(self):
        """Config should normalize WAF bool-like wizard/session values."""

        cfg = Config({
            'reports': 'std',
            'waf_detect': 'true',
            'waf_safe_mode': '1',
            'waf_guard': 'yes',
        })

        self.assertTrue(cfg.is_waf_detect)
        self.assertTrue(cfg.is_waf_safe_mode)
        self.assertTrue(cfg.is_waf_guard)

        cfg = Config({
            'reports': 'std',
            'waf_detect': 'false',
            'waf_safe_mode': '0',
            'waf_guard': 'no',
        })

        self.assertFalse(cfg.is_waf_detect)
        self.assertFalse(cfg.is_waf_safe_mode)
        self.assertFalse(cfg.is_waf_guard)

    def test_waf_flags_reject_invalid_values(self):
        """Config should reject malformed WAF bool values."""

        for key in ['waf_detect', 'waf_safe_mode', 'waf_guard']:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    Config({'reports': 'std', key: 'maybe'})

    def test_waf_safe_mode_enables_waf_detect(self):
        """Config should enable passive WAF detection when WAF safe mode is enabled."""

        cfg = Config({'reports': 'std', 'waf_safe_mode': True})

        self.assertTrue(cfg.is_waf_safe_mode)
        self.assertTrue(cfg.is_waf_detect)

    def test_waf_detect_does_not_enable_waf_safe_mode(self):
        """Config should not enable WAF safe mode when only detection is requested."""

        cfg = Config({'reports': 'std', 'waf_detect': True})

        self.assertTrue(cfg.is_waf_detect)
        self.assertFalse(cfg.is_waf_safe_mode)

    def test_waf_guard_enables_waf_detect_without_safe_mode(self):
        """Config should enable passive WAF detection when WAF guard is enabled."""

        cfg = Config({'reports': 'std', 'waf_guard': True})

        self.assertTrue(cfg.is_waf_guard)
        self.assertTrue(cfg.is_waf_detect)
        self.assertFalse(cfg.is_waf_safe_mode)


    def test_config_should_enable_auto_calibration(self):
        """Config should expose auto-calibration settings."""

        config = Config({
            'host': 'example.com',
            'auto_calibrate': True,
            'calibration_samples': 7,
            'calibration_threshold': 0.91,
        })

        self.assertTrue(config.is_auto_calibrate)
        self.assertEqual(config.calibration_samples, 7)
        self.assertEqual(config.calibration_threshold, 0.91)

    def test_config_should_force_get_when_auto_calibration_is_enabled(self):
        """Config.method should override HEAD to GET when auto-calibration is enabled."""

        config = Config({
            'host': 'example.com',
            'method': 'HEAD',
            'auto_calibrate': True,
        })

        self.assertEqual(config.method, 'GET')
        self.assertIn('--auto-calibrate', config.method_override_items)

    def test_config_should_expose_network_transport_settings(self):
        """Config should expose network transport settings."""

        config = Config({
            'host': 'example.com',
            'transport': 'wireguard',
            'transport_profile': '/tmp/wg.conf',
            'transport_profiles': '/tmp/profiles.txt',
            'transport_rotate': 'per-target',
            'transport_timeout': 15,
            'transport_healthcheck_url': 'https://example.com/ip',
            'transport_bin': '/usr/bin/wg-quick',
            'openvpn_auth': '/tmp/auth.txt',
        })

        self.assertEqual(config.transport, 'wireguard')
        self.assertEqual(config.transport_profile, '/tmp/wg.conf')
        self.assertEqual(config.transport_profiles, '/tmp/profiles.txt')
        self.assertEqual(config.transport_rotate, 'per-target')
        self.assertEqual(config.transport_timeout, 15)
        self.assertEqual(config.transport_healthcheck_url, 'https://example.com/ip')
        self.assertEqual(config.transport_bin, '/usr/bin/wg-quick')
        self.assertEqual(config.openvpn_auth, '/tmp/auth.txt')

    def test_config_should_default_to_direct_transport(self):
        """Config should default to direct network transport."""

        config = Config({'host': 'example.com'})

        self.assertEqual(config.transport, 'direct')
        self.assertIsNone(config.transport_profile)
        self.assertIsNone(config.transport_profiles)
        self.assertEqual(config.transport_rotate, 'none')
        self.assertEqual(config.transport_timeout, 30)
        self.assertIsNone(config.transport_healthcheck_url)
        self.assertIsNone(config.transport_bin)
        self.assertIsNone(config.openvpn_auth)

    def test_method_defaults_to_head_when_missing(self):
        """Config.requested_method should default to HEAD when method is absent."""

        cfg = Config({'reports': 'std'})

        self.assertEqual(cfg.requested_method, 'HEAD')
        self.assertEqual(cfg.method, 'HEAD')

    def test_method_normalizes_lowercase_values(self):
        """Config.requested_method should normalize methods restored from wizard/session."""

        cfg = Config({'reports': 'std', 'method': 'post'})

        self.assertEqual(cfg.requested_method, 'POST')
        self.assertEqual(cfg.method, 'POST')

    def test_explicit_get_is_not_reported_as_head_override(self):
        """Config.method_override_warning should stay empty for explicit GET requests."""

        cfg = Config({'reports': 'std', 'method': 'GET', 'sniff': 'secret'})

        self.assertEqual(cfg.method, 'GET')
        self.assertEqual(cfg.method_override_warning, '')

    def test_crawl_defaults_to_get_when_method_is_omitted(self):
        """Config.method should use GET for --crawl when --method is omitted."""

        cfg = Config({'reports': 'std', 'crawl': True})

        self.assertTrue(cfg.is_crawl)
        self.assertEqual(cfg.requested_method, 'HEAD')
        self.assertEqual(cfg.method, 'GET')
        self.assertIn('--crawl', cfg.method_override_items)
        self.assertIn('--crawl', cfg.method_override_warning)

    def test_crawl_rejects_subdomain_scan_from_wizard_or_session(self):
        """Config should reject restored crawl + subdomain scan combinations."""

        with self.assertRaises(ValueError) as context:
            Config({'reports': 'std', 'crawl': True, 'scan': 'subdomains'})

        self.assertIn('crawl can be used only with scan directories', str(context.exception))

    def test_crawl_preserves_explicit_get_method(self):
        """Config.method should preserve explicit GET when crawl is enabled."""

        cfg = Config({'reports': 'std', 'crawl': True, 'method': 'GET'})

        self.assertTrue(cfg.is_crawl)
        self.assertEqual(cfg.requested_method, 'GET')
        self.assertEqual(cfg.method, 'GET')
        self.assertEqual(cfg.method_override_warning, '')

    def test_crawl_rejects_explicit_head_from_wizard_or_session(self):
        """Config should reject restored crawl + HEAD combinations that bypass CLI filtering."""

        with self.assertRaises(ValueError) as context:
            Config({'reports': 'std', 'crawl': True, 'method': 'HEAD'})

        self.assertIn('crawl requires response bodies', str(context.exception))


class TestBrowserConfigDefensiveCopies(unittest.TestCase):
    """Config defensive-copy regression tests."""

    def test_config_list_getters_return_fresh_lists(self):
        """Config list getters should not expose mutable internal lists."""

        cfg = Config({
            'reports': ['json'],
            'sniff': ['indexof'],
            'extensions': ['php'],
            'ignore_extensions': ['jpg'],
        })

        reports = cfg.reports
        sniffers = cfg.sniffers
        extensions = cfg.extensions
        ignore_extensions = cfg.ignore_extensions

        reports.append('xml')
        sniffers.append('file')
        extensions.append('html')
        ignore_extensions.append('png')

        self.assertEqual(cfg.reports, ['json', 'std'])
        self.assertEqual(cfg.sniffers, ['indexof'])
        self.assertEqual(cfg.extensions, ['php'])
        self.assertEqual(cfg.ignore_extensions, ['jpg'])

    def test_normalize_csv_copies_input_lists(self):
        """Config._normalize_csv() should copy list inputs."""

        source = ['200', '403']
        normalized = Config._normalize_csv(source)

        normalized.append('404')

        self.assertEqual(source, ['200', '403'])
        self.assertEqual(normalized, ['200', '403', '404'])



class TestBrowserConfigCoverageOnly(unittest.TestCase):
    """Coverage-only tests for config normalization edge branches."""

    def test_should_normalize_scheme_without_slashes_and_false_retries(self):
        """Config should normalize short schemes and explicit false retries."""

        self.assertEqual(Config._normalize_scheme('http'), 'http://')
        self.assertEqual(Config._normalize_scheme('https'), 'https://')
        self.assertFalse(Config._normalize_retries(False))

    def test_should_ignore_empty_range_tokens_and_normalize_integer_delay(self):
        """Config should ignore empty range tokens and coerce whole-second delays."""

        self.assertEqual(Config._expand_integer_ranges(['', '10-20', '  ']), [(10, 20)])

        cfg = Config({'reports': 'std', 'delay': 1.5})

        self.assertEqual(cfg.delay, 1.5)

    def test_delay_preserves_fractional_values_from_strings(self):
        """Config.delay should preserve fractional values loaded from wizard/session strings."""

        cfg = Config({'delay': '0.1'})

        self.assertEqual(cfg.delay, 0.1)

    def test_delay_rejects_negative_values(self):
        """Config.delay should reject negative values before they reach workers."""

        cfg = Config({'delay': '-0.1'})

        with self.assertRaises(ValueError):
            _ = cfg.delay


if __name__ == '__main__':
    unittest.main()


class TestBrowserConfigCoverageGaps(unittest.TestCase):
    """Additional Config normalization edge coverage."""

    def test_recursive_status_deduplicates_and_rejects_empty_values(self):
        """Recursive status normalization should deduplicate and reject empty lists."""

        cfg = Config({'reports': 'std', 'recursive': True, 'recursive_status': '200,200,301'})
        self.assertEqual(cfg.recursive_status, ['200', '301'])

        with self.assertRaises(ValueError):
            Config({'reports': 'std', 'recursive': True, 'recursive_status': ',,'})

    def test_recursive_exclude_deduplicates_extensions(self):
        """Recursive exclude normalization should deduplicate normalized extensions."""

        cfg = Config({'reports': 'std', 'recursive': True, 'recursive_exclude': '.jpg,JPG,png'})

        self.assertEqual(cfg.recursive_exclude, ['jpg', 'png'])

    def test_reports_normalization_ignores_none_tokens_and_empty_path_lists(self):
        """Reports and optional paths should ignore none-like list values safely."""

        cfg = Config({'reports': ['json', '', 'none', 'std', 'json'], 'reports_dir': []})

        self.assertEqual(cfg.reports, ['json', 'std'])
        self.assertIsNone(cfg.reports_dir)
