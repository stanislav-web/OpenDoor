# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.collation import CollationResponsePlugin
from src.core.http.plugins.response.file import FileResponsePlugin
from src.core.http.plugins.response.indexof import IndexofResponsePlugin
from src.core.http.plugins.response.skipempty import SkipemptyResponsePlugin


class TestHttpResponsePluginsBranchCoverage(unittest.TestCase):
    """Branch coverage tests for response sniff plugins."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_file_helper_and_fallback_branches(self):
        """FileResponsePlugin should cover helper branches and no-match paths."""

        plugin = FileResponsePlugin(None)

        plugin._headers = {}
        self.assertIsNone(plugin._get_header('Content-Type'))
        self.assertIsNone(plugin._extract_content_length())
        self.assertEqual(plugin._extract_content_type(), '')
        self.assertFalse(plugin._is_binary_content_type(''))
        self.assertFalse(plugin._is_binary_content_type('application/x-custom'))
        self.assertFalse(plugin._is_binary_content_type('text/html'))
        self.assertTrue(plugin._is_binary_content_type('image/png'))
        self.assertTrue(plugin._is_binary_content_type('application/pdf'))

        plugin._headers = {
            'content-disposition': 'attachment; filename="dump.bin"',
            'content-type': 'application/octet-stream; charset=binary',
            'content-length': 'invalid',
        }
        self.assertEqual(plugin._get_header('Content-Disposition'), 'attachment; filename="dump.bin"')
        self.assertIsNone(plugin._extract_content_length())
        self.assertEqual(plugin._extract_content_type(), 'application/octet-stream')

        response = self.make_response(
            body=b'abc',
            headers={'content-disposition': 'attachment; filename="dump.bin"'}
        )
        self.assertEqual(plugin.process(response), 'file')

        response = self.make_response(
            body=b'abc',
            headers={'Content-Type': 'application/x-custom'}
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=b'x' * 1000001,
            headers={}
        )
        self.assertEqual(plugin.process(response), 'file')

    def test_indexof_helper_and_negative_branches(self):
        """IndexofResponsePlugin should cover helper branches and falsey paths."""

        plugin = IndexofResponsePlugin(None)

        self.assertEqual(plugin._count_matches((r'zzz',), 'abc'), 0)
        self.assertIsNone(plugin.process(self.make_response(status=404, body=b'Index of /')))
        self.assertIsNone(plugin.process(self.make_response(body=b'')))

        links_body = (
            '<a href=""></a>'
            '<a href="#top">top</a>'
            '<a href="?sort=name">sort</a>'
            '<a href="javascript:void(0)">js</a>'
            '<a href="mailto:test@example.com">mail</a>'
            '<a href="http://example.com/ext">ext</a>'
            '<a href="https://example.com/ext2">ext2</a>'
            '<a href="/login">login</a>'
            '<a href="/logout">logout</a>'
            '<a href="../">Parent</a>'
            '<a href="file.txt">file</a>'
            '<a href="dir/">dir</a>'
        )
        self.assertEqual(plugin._count_listing_links(links_body.lower()), 3)

        response = self.make_response(
            body=b'<html><body><h1>Sign in</h1><form><input type="password" name="password"></form></body></html>'
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=b'<html><body><a href="../">../</a><p>No listing metadata here</p></body></html>'
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=(
                b'<html><head><title>Directory Listing -- /pub</title></head>'
                b'<body><a href="../">../</a><a href="logs/">logs/</a></body></html>'
            )
        )
        self.assertEqual(plugin.process(response), 'indexof')

    def test_skipempty_helper_and_semantic_branches(self):
        """SkipemptyResponsePlugin should cover helper and semantic-empty branches."""

        plugin = SkipemptyResponsePlugin(None)

        plugin._headers = {}
        self.assertIsNone(plugin._get_header('Content-Type'))
        self.assertIsNone(plugin._extract_content_length())
        self.assertEqual(plugin._extract_content_type(), '')
        self.assertFalse(plugin._is_binary_content_type(''))
        self.assertFalse(plugin._contains_any((r'zzz',), 'abc'))

        plugin._headers = {
            'content-length': 'invalid',
            'content-type': 'application/problem+json; charset=utf-8',
        }
        self.assertEqual(plugin._get_header('Content-Type'), 'application/problem+json; charset=utf-8')
        self.assertIsNone(plugin._extract_content_length())
        self.assertEqual(plugin._extract_content_type(), 'application/problem+json')

        self.assertFalse(plugin._is_meaningful_json('not-json'))
        self.assertFalse(plugin._is_meaningful_json('null'))
        self.assertFalse(plugin._is_meaningful_json('[]'))
        self.assertFalse(plugin._is_meaningful_json('""'))
        self.assertTrue(plugin._is_meaningful_json('[1]'))
        self.assertTrue(plugin._is_meaningful_json('1'))
        self.assertTrue(plugin._is_meaningful_json('{"status":"ok"}'))
        self.assertEqual(plugin._extract_visible_text('<div>   </div>'), '')
        self.assertEqual(plugin._extract_visible_text('<div>Hello <b>world</b></div>'), 'Hello world')

        self.assertIsNone(plugin.process(self.make_response(status=404, body=b'x' * 10)))
        self.assertIsNone(plugin.process(self.make_response(body=b'x' * 600, headers={})))
        self.assertIsNone(plugin.process(self.make_response(body=b'x' * 10, headers={'Content-Length': '700'})))

        response = self.make_response(
            body=b'abc',
            headers={'Content-Disposition': 'attachment; filename="dump.sql"'}
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=b'abc',
            headers={'Content-Type': 'application/octet-stream'}
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=b'<html><body><form><input type="password" name="password"></form></body></html>',
            headers={'Content-Type': 'text/html'}
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=(
                b'<html><head><title>Index of /backup/</title></head>'
                b'<body><a href="../">Parent Directory</a></body></html>'
            ),
            headers={'Content-Type': 'text/html'}
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=b'{"status":"ok","id":1}',
            headers={'Content-Type': 'application/json'}
        )
        self.assertIsNone(plugin.process(response))

        response = self.make_response(
            body=b'[]',
            headers={'Content-Type': 'application/problem+json'}
        )
        self.assertEqual(plugin.process(response), 'skip')

        response = self.make_response(
            body=b'<div>   </div>',
            headers={'Content-Type': 'text/html'}
        )
        self.assertEqual(plugin.process(response), 'skip')

        response = self.make_response(
            body=b'hello',
            headers={}
        )
        self.assertEqual(plugin.process(response), 'skip')

        response = self.make_response(
            body=b'This is a short but useful plain text response.',
            headers={'Content-Length': 'invalid'}
        )
        self.assertIsNone(plugin.process(response))

    def test_collation_helper_and_rotation_branches(self):
        """CollationResponsePlugin should cover helper, exclusion, and rotation branches."""

        plugin = CollationResponsePlugin(None)

        self.assertFalse(plugin._contains_any((r'zzz',), 'abc'))
        self.assertEqual(plugin._extract_title('<html><body>x</body></html>'), '')
        self.assertFalse(plugin._legacy_match({}, {}))
        self.assertFalse(plugin._ratio_match('a' * 120, 'b' * 120))

        normalized = plugin._normalize_template(
            'https://example.com/demo/123456 '
            '123e4567-e89b-12d3-a456-426614174000 '
            'abcdefabcdefabcdefabcdefabcdefab '
            '9876543210 '
            + ('x' * 700)
        )
        self.assertIn('URL', normalized)
        self.assertIn('UUID', normalized)
        self.assertIn('HEX', normalized)
        self.assertIn('NUM', normalized)
        self.assertLessEqual(len(normalized), plugin.BODY_SAMPLE_SIZE)

        response = self.make_response(
            body=b'body',
            headers={
                'content-type': 'application/json; charset=utf-8',
                'location': '/error/not-found',
            }
        )
        signature = plugin._build_signature(response, 'body')
        self.assertEqual(signature[2], 'application/json; charset=utf-8')
        self.assertEqual(signature[3], '/error/not-found')

        self.assertFalse(plugin._is_explicit_soft404('<html><body><form><input type="password"></form></body></html>'))
        self.assertFalse(plugin._is_explicit_soft404('<html><title>Index of /</title><a href="../">Parent Directory</a></html>'))
        self.assertTrue(plugin._is_excluded_from_collation('<html><body><form><input type="password"></form></body></html>'))
        self.assertTrue(plugin._is_excluded_from_collation('<html><title>Index of /</title><a href="../">Parent Directory</a></html>'))

        plugin2 = CollationResponsePlugin(None)
        plugin2._body = 'a' * 120
        invalid_length_response = self.make_response(body=b'', headers={'Content-Length': 'invalid'})
        self.assertEqual(plugin2._extract_length(invalid_length_response), 120)

        self.assertIsNone(plugin.process(self.make_response(status=404, body=b'a' * 120)))
        self.assertIsNone(plugin.process(self.make_response(body=b'')))

        login_response = self.make_response(
            body=b'<html><body><form><input type="password" name="password"></form></body></html>'
        )
        self.assertIsNone(plugin.process(login_response))

        plugin3 = CollationResponsePlugin(None)
        json_404 = self.make_response(
            body=b'{"message":"Not Found"}',
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(plugin3.process(json_404), 'failed')

        plugin4 = CollationResponsePlugin(None)
        first = self.make_response(body=b'a' * 120, headers={'Content-Length': 'invalid'})
        self.assertIsNone(plugin4.process(first))
        self.assertEqual(plugin4.previous_item['length'], 120)
        self.assertEqual(plugin4.previous_item['text'], 'a' * 120)

        plugin5 = CollationResponsePlugin(None)
        zero_header = self.make_response(body=b'a' * 120, headers={'Content-Length': '0'})
        self.assertIsNone(plugin5.process(zero_header))
        self.assertEqual(plugin5.previous_item, {})

        plugin6 = CollationResponsePlugin(None)
        short = self.make_response(body=b'a' * 99, headers={})
        self.assertIsNone(plugin6.process(short))
        self.assertEqual(plugin6.previous_item, {})

        plugin7 = CollationResponsePlugin(None)
        one = self.make_response(body=b'a' * 120, headers={})
        two = self.make_response(body=b'b' * 130, headers={})
        three = self.make_response(body=b'c' * 140, headers={})

        with patch.object(plugin7, '_legacy_match', return_value=False), \
             patch.object(plugin7, '_build_signature', side_effect=[
                 ('sig1',),
                 ('sig2',),
                 ('sig3',),
             ]):
            self.assertIsNone(plugin7.process(one))
            self.assertIsNone(plugin7.process(two))
            self.assertIsNone(plugin7.process(three))

        self.assertEqual(plugin7.previous_item['text'], 'b' * 130)
        self.assertEqual(plugin7.current_item['text'], 'c' * 140)