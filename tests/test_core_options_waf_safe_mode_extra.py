# -*- coding: utf-8 -*-

import sys
import unittest
from unittest.mock import patch

from src.core.options.options import Options


class TestOptionsWafSafeModeExtra(unittest.TestCase):
    """Extra tests for --waf-safe-mode option wiring."""

    def test_waf_safe_mode_auto_enables_waf_detect(self):
        """Options should auto-enable --waf-detect when --waf-safe-mode is used."""

        argv = ['opendoor.py', '--host', 'http://example.com', '--waf-safe-mode']

        with patch.object(sys, 'argv', argv), \
                patch('src.core.options.options.Filter.filter', side_effect=lambda data: data):
            actual = Options().get_arg_values()

        self.assertTrue(actual['waf_safe_mode'])
        self.assertTrue(actual['waf_detect'])


if __name__ == '__main__':
    unittest.main()