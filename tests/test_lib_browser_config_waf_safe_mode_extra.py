# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.config import Config


class TestConfigWafSafeModeExtra(unittest.TestCase):
    """Extra tests for WAF safe mode config."""

    def test_waf_safe_mode_auto_enables_waf_detect(self):
        """Config should enable WAF detection when safe mode is enabled."""

        cfg = Config({'waf_safe_mode': True})

        self.assertTrue(cfg.is_waf_safe_mode)
        self.assertTrue(cfg.is_waf_detect)


if __name__ == '__main__':
    unittest.main()