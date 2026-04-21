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
            'HEAD overridden to GET because selected sniffers require response body: indexof, collation'
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


if __name__ == '__main__':
    unittest.main()