# -*- coding: utf-8 -*-

import socket as py_socket
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core.http.exceptions import SocketError
from src.core.http.providers.request import RequestProvider
from src.core.http.socks import Socket


class TestRequestProviderExtra(unittest.TestCase):
    """TestRequestProviderExtra class."""

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal config namespace for RequestProvider tests."""

        base = {
            'keep_alive': False,
            'is_random_user_agent': False,
            'user_agent': 'UA',
            'method': 'HEAD',
            'header': None,
            'cookie': None,
            'scheme': 'http://',
            'host': 'example.com',
            'port': 80,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def test_request_returns_none(self):
        """RequestProvider.request() should be a no-op placeholder."""

        provider = RequestProvider(self.make_cfg(), agent_list=['UA'])
        self.assertIsNone(provider.request('http://example.com'))

    def test_cookies_middleware_adds_cookie_header_when_accepted(self):
        """RequestProvider.cookies_middleware() should forward fetched cookies to request headers."""

        provider = RequestProvider(self.make_cfg(), agent_list=['UA'])
        response = SimpleNamespace(headers={'set-cookie': ' session=1 '})

        with patch.object(provider, 'add_header') as add_header_mock:
            provider.cookies_middleware(True, response)

        add_header_mock.assert_called_once_with('Cookie', 'session=1')

    def test_cookies_middleware_ignores_unaccepted_or_headerless_responses(self):
        """RequestProvider.cookies_middleware() should ignore unaccepted or headerless responses."""

        provider = RequestProvider(self.make_cfg(), agent_list=['UA'])

        with patch.object(provider, 'add_header') as add_header_mock:
            provider.cookies_middleware(False, SimpleNamespace(headers={'set-cookie': 'x=1'}))
            provider.cookies_middleware(True, SimpleNamespace())

        add_header_mock.assert_not_called()

    def test_init_applies_custom_request_headers(self):
        """RequestProvider should apply custom headers from config during initialization."""

        provider = RequestProvider(
            self.make_cfg(header=['Authorization: Bearer test']),
            agent_list=['UA']
        )

        headers = provider._headers
        self.assertEqual(headers.get('Authorization'), 'Bearer test')

    def test_init_applies_multiple_custom_request_headers(self):
        """RequestProvider should apply multiple custom headers from config."""

        provider = RequestProvider(
            self.make_cfg(header=['Authorization: Bearer test', 'X-Test: 1']),
            agent_list=['UA']
        )

        headers = provider._headers
        self.assertEqual(headers.get('Authorization'), 'Bearer test')
        self.assertEqual(headers.get('X-Test'), '1')

    def test_init_ignores_invalid_custom_request_headers(self):
        """RequestProvider should ignore invalid custom header values without a separator."""

        provider = RequestProvider(
            self.make_cfg(header=['Authorization: Bearer test', 'BrokenHeader']),
            agent_list=['UA']
        )

        headers = provider._headers
        self.assertEqual(headers.get('Authorization'), 'Bearer test')
        self.assertIsNone(headers.get('BrokenHeader'))

    def test_init_applies_custom_request_cookie(self):
        """RequestProvider should apply a custom cookie from config during initialization."""

        provider = RequestProvider(
            self.make_cfg(cookie=['sid=abc123']),
            agent_list=['UA']
        )

        headers = provider._headers
        self.assertEqual(headers.get('Cookie'), 'sid=abc123')

    def test_init_applies_multiple_custom_request_cookies(self):
        """RequestProvider should join multiple custom cookies into a single Cookie header."""

        provider = RequestProvider(
            self.make_cfg(cookie=['sid=abc123', 'locale=en']),
            agent_list=['UA']
        )

        headers = provider._headers
        self.assertEqual(headers.get('Cookie'), 'sid=abc123; locale=en')

    def test_init_ignores_empty_custom_request_cookies(self):
        """RequestProvider should ignore empty custom cookie values."""

        provider = RequestProvider(
            self.make_cfg(cookie=['sid=abc123', '   ', 'locale=en']),
            agent_list=['UA']
        )

        headers = provider._headers
        self.assertEqual(headers.get('Cookie'), 'sid=abc123; locale=en')

class TestSocketExtra(unittest.TestCase):
    """TestSocketExtra class."""

    def test_ping_success_sets_timeout_connects_and_closes_socket(self):
        """Socket.ping() should set timeout, connect, and close the socket."""

        sock = MagicMock()

        with patch('src.core.http.socks.socket.socket', return_value=sock):
            Socket.ping('example.com', 80, timeout=5)

        sock.settimeout.assert_called_once_with(5)
        sock.connect.assert_called_once_with(('example.com', 80))
        sock.close.assert_called_once()

    def test_ping_wraps_socket_errors_and_still_closes_socket(self):
        """Socket.ping() should wrap socket-level errors and still close the socket."""

        sock = MagicMock()
        sock.connect.side_effect = py_socket.timeout('boom')

        with patch('src.core.http.socks.socket.socket', return_value=sock):
            with self.assertRaises(SocketError):
                Socket.ping('example.com', 80, timeout=5)

        sock.close.assert_called_once()

    def test_get_ip_address_wraps_gaierror(self):
        """Socket.get_ip_address() should wrap name-resolution failures."""

        with patch('src.core.http.socks.socket.gethostbyname', side_effect=py_socket.gaierror(-2, 'fail')):
            with self.assertRaises(SocketError):
                Socket.get_ip_address('example.com')

    def test_get_ips_addresses_returns_empty_string_when_no_ips(self):
        """Socket.get_ips_addresses() should return an empty string for empty DNS answers."""

        with patch('src.core.http.socks.socket.gethostbyname_ex', return_value=('host', [], [])):
            self.assertEqual(Socket.get_ips_addresses('example.com'), '')

    def test_get_ips_addresses_returns_empty_string_on_gaierror(self):
        """Socket.get_ips_addresses() should return an empty string on DNS errors."""

        with patch('src.core.http.socks.socket.gethostbyname_ex', side_effect=py_socket.gaierror(-2, 'fail')):
            self.assertEqual(Socket.get_ips_addresses('example.com'), '')


if __name__ == '__main__':
    unittest.main()