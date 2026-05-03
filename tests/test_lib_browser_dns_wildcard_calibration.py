# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from src.core import helper
from src.lib.browser.browser import Browser
from src.lib.browser.calibration import Calibration
from src.lib.browser.config import Config


class TestBrowserDnsWildcardCalibration(unittest.TestCase):
    """DNS wildcard auto-calibration runtime tests."""

    def make_browser(self, params=None):
        """Create a Browser instance without running full initialization."""

        params = params or {}
        defaults = {
            'reports': 'std',
            'host': 'example.com',
            'scan': 'subdomains',
            'auto_calibrate': True,
            'calibration_samples': 3,
        }
        defaults.update(params)

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__config', Config(defaults))
        setattr(br, '_Browser__calibration', None)
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })
        return br

    @staticmethod
    def addrinfo(address):
        """Build a minimal getaddrinfo-like record."""

        return [(None, None, None, '', (address, 0))]

    def test_dns_wildcard_addresses_require_subdomain_auto_calibration(self):
        """DNS wildcard baseline should run only for subdomain auto-calibration."""

        br = self.make_browser({'scan': 'directories'})

        self.assertFalse(br._Browser__is_subdomain_dns_calibration_enabled())
        self.assertEqual(br._Browser__build_dns_wildcard_addresses(), [])

    def test_dns_wildcard_addresses_collect_random_subdomain_baseline(self):
        """DNS wildcard baseline should collect addresses from random subdomain probes."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.uuid.uuid4') as uuid4_mock,                 patch('src.lib.browser.browser.net_socket.getaddrinfo') as getaddrinfo_mock:
            uuid4_mock.return_value.hex = 'abcdef1234567890'
            getaddrinfo_mock.return_value = self.addrinfo('203.0.113.10')

            actual = br._Browser__build_dns_wildcard_addresses()

        self.assertEqual(actual, ['203.0.113.10'])
        self.assertEqual(getaddrinfo_mock.call_count, 3)
        self.assertEqual(
            getaddrinfo_mock.call_args_list[0].args[0],
            'cdn-abcdef123456-0.example.com'
        )

    def test_dns_wildcard_addresses_ignore_single_random_resolution(self):
        """DNS wildcard baseline should require at least two resolved random samples."""

        br = self.make_browser()

        def resolver(hostname, _port):
            if hostname.endswith('-0.example.com'):
                return self.addrinfo('203.0.113.10')
            raise OSError('not found')

        with patch('src.lib.browser.browser.net_socket.getaddrinfo', side_effect=resolver):
            self.assertEqual(br._Browser__build_dns_wildcard_addresses(), [])

    def test_match_dns_wildcard_response_should_match_wildcard_only_candidate(self):
        """Subdomain candidate resolving only to wildcard IPs should be calibrated."""

        br = self.make_browser()
        setattr(br, '_Browser__calibration', Calibration(dns_wildcard_addresses=['203.0.113.10']))

        with patch('src.lib.browser.browser.net_socket.getaddrinfo', return_value=self.addrinfo('203.0.113.10')):
            actual = br._Browser__match_dns_wildcard_response('http://ghost.example.com')

        self.assertIsNotNone(actual)
        self.assertEqual(actual['calibration_reason'], 'dns-wildcard')
        self.assertEqual(actual['dns_wildcard_host'], 'ghost.example.com')

    def test_match_dns_wildcard_response_should_skip_root_host_and_real_candidate(self):
        """DNS wildcard matching should not hide root host or candidates with real IPs."""

        br = self.make_browser()
        setattr(br, '_Browser__calibration', Calibration(dns_wildcard_addresses=['203.0.113.10']))

        self.assertIsNone(br._Browser__match_dns_wildcard_response('http://example.com'))

        with patch('src.lib.browser.browser.net_socket.getaddrinfo', return_value=self.addrinfo('198.51.100.5')):
            self.assertIsNone(br._Browser__match_dns_wildcard_response('http://api.example.com'))

    def test_http_request_should_record_dns_wildcard_candidate_without_http_call(self):
        """Browser.__http_request() should short-circuit wildcard DNS candidates as calibrated."""

        br = self.make_browser()
        setattr(br, '_Browser__calibration', Calibration(dns_wildcard_addresses=['203.0.113.10']))
        setattr(br, '_Browser__client', MagicMock())
        setattr(br, '_Browser__pool', MagicMock(items_size=0, total_items_size=1))
        setattr(br, '_Browser__reader', MagicMock())
        setattr(br, '_Browser__response', MagicMock())

        with patch('src.lib.browser.browser.net_socket.getaddrinfo', return_value=self.addrinfo('203.0.113.10')):
            br._Browser__http_request('http://ghost.example.com')

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['items']['calibrated'], ['http://ghost.example.com'])
        self.assertEqual(result['report_items']['calibrated'][0]['code'], 'DNS')
        self.assertEqual(result['report_items']['calibrated'][0]['calibration_reason'], 'dns-wildcard')
        self.assertEqual(result['report_items']['calibrated'][0]['dns_wildcard_host'], 'ghost.example.com')
        self.assertEqual(result['report_items']['calibrated'][0]['dns_wildcard_addresses'], ['203.0.113.10'])
        getattr(br, '_Browser__client').request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
