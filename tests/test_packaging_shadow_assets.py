# -*- coding: utf-8 -*-

import ast
from pathlib import Path
import unittest


class TestPackagingShadowAssets(unittest.TestCase):
    """Packaging coverage for bundled shadow sniffer data assets."""

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    SHADOW_SUFFIXES = 'data/shadow-suffixes.dat'

    @classmethod
    def _setup_call_keywords(cls):
        """
        Parse setup.py and return setup() keyword arguments.

        :return: setup() keyword arguments keyed by name
        :rtype: dict[str, ast.AST]
        """

        tree = ast.parse((cls.PROJECT_ROOT / 'setup.py').read_text(encoding='utf-8'))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if getattr(node.func, 'id', None) != 'setup':
                continue
            return {keyword.arg: keyword.value for keyword in node.keywords}

        raise AssertionError('setup.py must call setup()')

    def test_should_include_shadow_suffixes_in_wheel_data_files(self):
        """setup.py data_files should install data/shadow-suffixes.dat into wheels."""

        keywords = self._setup_call_keywords()
        data_files = ast.literal_eval(keywords['data_files'])
        installed_files = [filename for _target, filenames in data_files for filename in filenames]

        self.assertIn(self.SHADOW_SUFFIXES, installed_files)

    def test_should_include_all_dat_assets_in_source_distribution_manifest(self):
        """MANIFEST.in should include bundled data/*.dat assets for source distributions."""

        manifest = (self.PROJECT_ROOT / 'MANIFEST.in').read_text(encoding='utf-8')

        self.assertIn('recursive-include data *.dat', manifest)
        self.assertTrue((self.PROJECT_ROOT / self.SHADOW_SUFFIXES).is_file())

    def test_should_keep_shadow_suffix_dictionary_clean(self):
        """data/shadow-suffixes.dat should stay comment-free and duplicate-free."""

        lines = (self.PROJECT_ROOT / self.SHADOW_SUFFIXES).read_text(encoding='utf-8').splitlines()
        suffixes = [line.strip() for line in lines if line.strip()]

        self.assertEqual(lines, suffixes)
        self.assertEqual(len(suffixes), len(set(suffixes)))
        self.assertTrue(all(not suffix.startswith('#') for suffix in suffixes))


if __name__ == '__main__':
    unittest.main()
