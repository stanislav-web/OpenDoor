# -*- coding: utf-8 -*-

import builtins
import codecs
import collections
import collections.abc
import importlib
import unittest
from unittest.mock import patch

helper_module = importlib.import_module('src.core.helper.helper')
Helper = helper_module.Helper


class TestHelperExtra(unittest.TestCase):
    """Extra branch coverage tests for Helper."""

    def test_decode_handles_partial_utf8_bom_prefix(self):
        """Helper.decode() should return an empty string for incomplete UTF-8 BOM prefixes."""

        payload = codecs.BOM_UTF8[:2]
        self.assertEqual(Helper.decode(payload), '')

    def test_decode_handles_full_utf8_bom(self):
        """Helper.decode() should decode UTF-8 BOM-prefixed payloads."""

        payload = codecs.BOM_UTF8 + 'hello'.encode('utf-8')
        self.assertEqual(Helper.decode(payload), 'hello')

    def test_decode_handles_utf16_bom(self):
        """Helper.decode() should decode UTF-16 BOM-prefixed payloads."""

        payload = codecs.BOM_UTF16 + 'hello'.encode('utf-16')[2:]
        self.assertEqual(Helper.decode(payload), 'hello')

    def test_helper_module_fallback_import_uses_collections_callable(self):
        """helper module should support the legacy Callable fallback branch."""

        original_import = builtins.__import__
        original_callable = getattr(collections, 'Callable', None)
        setattr(collections, 'Callable', collections.abc.Callable)

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'collections.abc' and 'Callable' in fromlist:
                raise ImportError('forced fallback for coverage')
            return original_import(name, globals, locals, fromlist, level)

        try:
            with patch('builtins.__import__', side_effect=fake_import):
                reloaded = importlib.reload(helper_module)

            self.assertIs(reloaded.Callable, collections.abc.Callable)
            self.assertTrue(reloaded.Helper.is_callable(lambda: True))
        finally:
            if original_callable is None:
                delattr(collections, 'Callable')
            else:
                setattr(collections, 'Callable', original_callable)
            importlib.reload(helper_module)


if __name__ == '__main__':
    unittest.main()