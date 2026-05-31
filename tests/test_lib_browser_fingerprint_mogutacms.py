# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.fingerprint import Fingerprint


class TestFingerprintMogutaCMS(unittest.TestCase):

    def _detect_candidates(self, body='', generator=''):
        fingerprint = Fingerprint(None, None)
        fingerprint._apply_detection_rules(
            body=body,
            body_lower=str(body or '').lower(),
            headers={},
            cookies=[],
            generator=generator,
            probe_statuses={},
            final_root_url='https://example.test/',
            not_found_status=404,
            not_found_body='not found',
            not_found_headers={},
        )
        return fingerprint._build_candidates()

    def _candidate(self, candidates, name):
        for candidate in candidates:
            if candidate.get('name') == name:
                return candidate
        return None

    def test_detects_mogutacms_from_generator_meta(self):
        candidates = self._detect_candidates(generator='Moguta.CMS')
        candidate = self._candidate(candidates, 'MogutaCMS')

        self.assertIsNotNone(candidate)
        self.assertEqual('ecommerce', candidate.get('category'))
        self.assertGreaterEqual(candidate.get('score'), 8)

    def test_detects_mogutacms_from_powered_by_footer(self):
        body = '''
            <footer>
                Сайт работает на движке:
                <a href="https://moguta.ru/" target="_blank">Moguta. CMS</a>
            </footer>
        '''
        candidates = self._detect_candidates(body=body)
        candidate = self._candidate(candidates, 'MogutaCMS')

        self.assertIsNotNone(candidate)
        self.assertEqual('ecommerce', candidate.get('category'))
        self.assertGreaterEqual(candidate.get('score'), 9)

    def test_detects_mogutacms_from_multiple_engine_paths(self):
        body = '''
            <link rel="stylesheet" href="/mg-templates/shop/css/style.css">
            <script src="/mg-core/script/jquery.js"></script>
        '''
        candidates = self._detect_candidates(body=body)
        candidate = self._candidate(candidates, 'MogutaCMS')

        self.assertIsNotNone(candidate)
        self.assertEqual('ecommerce', candidate.get('category'))
        self.assertGreaterEqual(candidate.get('score'), 8)

    def test_ignores_portfolio_or_comparison_text_without_site_signals(self):
        body = '''
            MogutaCMS portfolio examples and ecommerce CMS comparison.
            See moguta.ru for product information and implementation cases.
        '''
        candidates = self._detect_candidates(body=body)

        self.assertIsNone(self._candidate(candidates, 'MogutaCMS'))

    def test_ignores_single_generic_mg_path_without_brand_context(self):
        body = '<link rel="stylesheet" href="/mg-templates/shop/css/style.css">'
        candidates = self._detect_candidates(body=body)

        self.assertIsNone(self._candidate(candidates, 'MogutaCMS'))

    def test_uses_single_engine_path_only_as_brand_corroboration(self):
        body = '<link rel="stylesheet" href="/mg-templates/shop/css/style.css">'
        fingerprint = Fingerprint(None, None)

        fingerprint._apply_detection_rules(
            body=body,
            body_lower=body.lower(),
            headers={},
            cookies=[],
            generator='Moguta.CMS',
            probe_statuses={},
            final_root_url='https://example.test/',
            not_found_status=404,
            not_found_body='not found',
            not_found_headers={},
        )

        signals = getattr(fingerprint, '_Fingerprint__signals')['MogutaCMS']
        self.assertIn(
            {'type': 'asset+brand', 'value': '/mg-templates/', 'weight': 4.0},
            signals,
        )


if __name__ == '__main__':
    unittest.main()
