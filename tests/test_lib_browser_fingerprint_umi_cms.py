# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.fingerprint import Fingerprint


class _FingerprintConfig(object):
    """Minimal browser config for isolated fingerprint tests."""

    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443

    scheme = 'https://'
    host = 'example.com'
    port = 443
    prefix = ''
    _method = 'HEAD'


class _Response(object):
    """Small HTTP response stub used by the fingerprint detector."""

    def __init__(self, status=200, headers=None, data=b''):
        """
        Initialize a deterministic response object.

        :param int status: HTTP status code
        :param dict|None headers: response headers
        :param bytes data: response body
        :return: None
        """

        self.status = status
        self.headers = headers or {}
        self.data = data


class _Client(object):
    """Static client returning root headers and generic 404 for probes."""

    def __init__(self, root_headers):
        """
        Initialize the client with root response headers.

        :param dict root_headers: headers returned for the target root URL
        :return: None
        """

        self.root_headers = root_headers

    def request(self, url):
        """
        Return the root response or a neutral 404 response for probes.

        :param str url: requested URL
        :return: response stub
        :rtype: _Response
        """

        if str(url) == 'https://example.com/':
            return _Response(
                status=200,
                headers=self.root_headers,
                data=b'<html><head></head><body>plain page</body></html>',
            )

        return _Response(
            status=404,
            headers={'Server': 'Apache/2'},
            data=b'not found',
        )


class FingerprintUmiCmsTestCase(unittest.TestCase):
    """Regression tests for passive UMI.CMS header fingerprinting."""

    def test_detects_umi_cms_from_x_generated_by_header(self):
        result = Fingerprint(
            _FingerprintConfig(),
            _Client({'X-Generated-By': 'UMI.CMS', 'X-CMS-Version': '22', 'Server': 'Apache/2'}),
        ).detect()

        self.assertEqual('UMI.CMS', result['name'])
