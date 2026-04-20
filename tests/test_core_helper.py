# -*- coding: utf-8 -*-

import collections
import unittest
from unittest.mock import patch

from src.core.helper.helper import Helper


class _BrokenSplitter(object):
    def split(self, _delimiter):
        raise TypeError('broken split')


class _BrokenBytes(bytes):
    def decode(self, *args, **kwargs):
        raise UnicodeDecodeError('codec', b'', 0, 1, 'fail')


class TestHelper(unittest.TestCase):
    """TestHelper class."""

    def test_counter_returns_counter_instance(self):
        """Helper.counter() should return a collections.Counter instance."""

        counter = Helper.counter()
        self.assertIsInstance(counter, collections.Counter)
        counter.update(['a', 'a', 'b'])
        self.assertEqual(counter['a'], 2)

    def test_list_returns_defaultdict_list(self):
        """Helper.list() should return a defaultdict(list)."""

        container = Helper.list()
        container['items'].append('value')
        self.assertEqual(container['items'], ['value'])
        self.assertEqual(container['missing'], [])

    def test_parse_url_returns_parsed_result(self):
        """Helper.parse_url() should return a parsed URL object."""

        parsed = Helper.parse_url('https://example.com:8443/path?q=1')
        self.assertEqual(parsed.scheme, 'https')
        self.assertEqual(parsed.netloc, 'example.com:8443')
        self.assertEqual(parsed.path, '/path')

    def test_to_json_respects_sort_and_indents(self):
        """Helper.to_json() should format JSON using the requested options."""

        payload = {'b': 1, 'a': 2}
        rendered = Helper.to_json(payload, sort=True, indents=2)

        self.assertTrue(rendered.index('"a"') < rendered.index('"b"'))
        self.assertIn('\n  "a": 2', rendered)

    def test_to_list_uses_custom_delimiter(self):
        """Helper.to_list() should split strings using a custom delimiter."""

        self.assertEqual(Helper.to_list('a|b|c', delimiter='|'), ['a', 'b', 'c'])

    def test_to_list_raises_attribute_error_for_none(self):
        """Helper.to_list() currently raises AttributeError for None input."""

        with self.assertRaises(AttributeError):
            Helper.to_list(None)

    def test_to_list_wraps_type_error_from_splitter(self):
        """Helper.to_list() should re-raise TypeError coming from a split implementation."""

        with self.assertRaises(TypeError):
            Helper.to_list(_BrokenSplitter())

    def test_openbrowser_delegates_to_webbrowser(self):
        """Helper.openbrowser() should delegate to webbrowser.open()."""

        with patch('src.core.helper.helper.webbrowser.open', return_value=True) as open_mock:
            self.assertTrue(Helper.openbrowser('https://example.com'))

        open_mock.assert_called_once_with('https://example.com')

    def test_percent_formats_rounded_percentage(self):
        """Helper.percent() should format a rounded percentage string."""

        self.assertEqual(Helper.percent(1, 3), '33.3%')

    def test_version_comparisons_work(self):
        """Helper version comparison helpers should compare semantic versions."""

        self.assertTrue(Helper.is_less('5.0.1', '5.0.2'))
        self.assertTrue(Helper.is_more('5.0.2', '5.0.1'))

    def test_is_callable_and_is_jsonable(self):
        """Helper.is_callable() and Helper.is_jsonable() should classify values correctly."""

        self.assertTrue(Helper.is_callable(lambda: None))
        self.assertFalse(Helper.is_callable('not-callable'))
        self.assertTrue(Helper.is_jsonable({'ok': True}))
        self.assertFalse(Helper.is_jsonable({1, 2, 3}))

    def test_decode_hostname_returns_idna(self):
        """Helper.decode_hostname() should convert unicode domains to IDNA."""

        self.assertEqual(Helper.decode_hostname('пример.рф'), 'xn--e1afmkfd.xn--p1ai')

    def test_decode_handles_short_bom_prefix(self):
        """Helper.decode() should return an empty string for incomplete UTF-8 BOM prefixes."""

        self.assertEqual(Helper.decode(b'\xef\xbb'), '')

    def test_decode_handles_utf8_bytes(self):
        """Helper.decode() should decode regular UTF-8 bytes."""

        self.assertEqual(Helper.decode('test'.encode('utf-8')), 'test')

    def test_decode_falls_back_to_cp1251(self):
        """Helper.decode() should fall back to cp1251 when UTF-8 decoding fails."""

        self.assertEqual(Helper.decode('тест'.encode('cp1251')), 'тест')

    def test_decode_returns_empty_string_when_all_decoders_fail(self):
        """Helper.decode() should return an empty string when all decoders fail."""

        with patch('src.core.helper.helper.codecs.utf_8_decode', side_effect=UnicodeDecodeError('codec', b'', 0, 1, 'fail')):
            self.assertEqual(Helper.decode(_BrokenBytes(b'abc')), '')

    def test_filter_directory_string_normalizes_path(self):
        """Helper.filter_directory_string() should strip newlines and leading slashes."""

        self.assertEqual(Helper.filter_directory_string('/admin/login\n'), 'admin/login')

    def test_filter_domain_string_normalizes_and_defaults(self):
        """Helper.filter_domain_string() should normalize content and default empty values to underscore."""

        self.assertEqual(Helper.filter_domain_string('WWW.Example.COM\n'), 'wwwexamplecom')
        self.assertEqual(Helper.filter_domain_string('!!!'), '_')


if __name__ == '__main__':
    unittest.main()