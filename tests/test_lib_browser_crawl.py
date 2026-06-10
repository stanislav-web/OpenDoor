# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.crawl import (
    CrawlExtractionResult,
    CrawlState,
    _CrawlHTMLParser,
    extract_crawl_candidates,
    is_crawl_content_type,
    normalize_crawl_url,
)


class CrawlExtractionTestCase(unittest.TestCase):
    """Bounded one-hop crawl extraction tests."""

    def test_extracts_supported_html_attributes(self):
        """Extractor should collect supported same-origin URL-bearing attributes."""

        html = '''
            <a href="/login">Login</a>
            <link href="/assets/app.css">
            <script src="/assets/app.js"></script>
            <img src="/logo.png">
            <iframe src="/frame"></iframe>
            <form action="/search" method="get"></form>
            <form action="/browse"></form>
        '''

        result = extract_crawl_candidates('https://example.com/', html, 'text/html')

        self.assertEqual([candidate.url for candidate in result.candidates], [
            'https://example.com/login',
            'https://example.com/assets/app.css',
            'https://example.com/assets/app.js',
            'https://example.com/logo.png',
            'https://example.com/frame',
            'https://example.com/search',
            'https://example.com/browse',
        ])
        self.assertEqual(result.discovered, 7)

    def test_skips_non_get_form_actions(self):
        """Extractor should avoid POST/PUT/PATCH/DELETE form actions."""

        html = '''
            <form action="/search" method="GET"></form>
            <form action="/login" method="post"></form>
            <form action="/user/1" method="put"></form>
            <form action="/user/1" method="patch"></form>
            <form action="/user/1" method="delete"></form>
        '''

        result = extract_crawl_candidates('https://example.com/', html, 'text/html')

        self.assertEqual([candidate.url for candidate in result.candidates], ['https://example.com/search'])

    def test_normalizes_same_origin_urls_and_strips_fragments(self):
        """URL normalization should keep query strings and remove fragments."""

        cases = {
            '/admin#top': 'https://example.com/admin',
            'https://EXAMPLE.com:443/search?q=admin#result': 'https://example.com/search?q=admin',
            '../settings': 'https://example.com/settings',
        }

        for raw_url, expected in cases.items():
            with self.subTest(raw_url=raw_url):
                normalized, reason = normalize_crawl_url(raw_url, 'https://example.com/app/page.html')
                self.assertIsNone(reason)
                self.assertEqual(normalized, expected)

    def test_treats_trailing_slash_and_query_as_distinct_urls(self):
        """Extractor should not over-deduplicate path and query variants."""

        html = '''
            <a href="/admin"></a>
            <a href="/admin/"></a>
            <a href="/search?q=admin"></a>
            <a href="/search?q=user"></a>
        '''

        result = extract_crawl_candidates('https://example.com/', html, 'text/html')

        self.assertEqual([candidate.url for candidate in result.candidates], [
            'https://example.com/admin',
            'https://example.com/admin/',
            'https://example.com/search?q=admin',
            'https://example.com/search?q=user',
        ])

    def test_skips_external_and_non_http_urls(self):
        """Extractor should keep crawl one-hop and same-origin only."""

        html = '''
            <a href="https://api.example.com/admin"></a>
            <a href="http://example.com/admin"></a>
            <a href="//cdn.example.com/app.js"></a>
            <a href="mailto:admin@example.com"></a>
            <a href="javascript:alert(1)"></a>
            <a href="data:text/plain,admin"></a>
            <a href="#top"></a>
        '''

        result = extract_crawl_candidates('https://example.com/', html, 'text/html')

        self.assertEqual(result.candidates, ())
        self.assertEqual(result.skipped_external, 3)
        self.assertEqual(result.skipped_invalid, 4)

    def test_respects_ignore_extensions_before_candidates_are_returned(self):
        """Extractor should skip ignored static assets before runtime dedup/queue accounting."""

        html = '''
            <script src="/assets/app.js"></script>
            <link href="/assets/app.css">
            <img src="/logo.png">
            <a href="/admin"></a>
        '''

        result = extract_crawl_candidates(
            'https://example.com/',
            html,
            'text/html',
            ignore_extensions=['js', '.css', 'png'],
        )

        self.assertEqual([candidate.url for candidate in result.candidates], ['https://example.com/admin'])
        self.assertEqual(result.skipped_extension, 3)

    def test_deduplicates_candidates_inside_one_response(self):
        """Extractor should avoid returning duplicate candidates from repeated page menus."""

        html = '''
            <a href="/login"></a>
            <a href="/login#top"></a>
            <a href="https://example.com:443/login"></a>
        '''

        result = extract_crawl_candidates('https://example.com/', html, 'text/html')

        self.assertEqual([candidate.url for candidate in result.candidates], ['https://example.com/login'])
        self.assertEqual(result.skipped_duplicate, 2)

    def test_enforces_body_size_cap(self):
        """Extractor should skip oversized bodies without keeping parsed links."""

        result = extract_crawl_candidates(
            'https://example.com/',
            '<a href="/admin"></a>',
            'text/html',
            max_body_bytes=5,
        )

        self.assertEqual(result.candidates, ())
        self.assertEqual(result.skipped_body_size, 1)

    def test_enforces_links_per_response_cap(self):
        """Extractor should bound the number of links collected from one response."""

        result = extract_crawl_candidates(
            'https://example.com/',
            '<a href="/one"></a><a href="/two"></a><a href="/three"></a>',
            'text/html',
            max_links_per_response=2,
        )

        self.assertEqual([candidate.url for candidate in result.candidates], [
            'https://example.com/one',
            'https://example.com/two',
        ])
        self.assertEqual(result.skipped_limit, 1)

    def test_extract_skips_non_html_response_bodies(self):
        """Extractor should not parse explicitly non-HTML response bodies."""

        result = extract_crawl_candidates(
            'https://example.com/',
            b'{"next":"/admin"}',
            'application/json',
        )

        self.assertEqual(result.candidates, ())
        self.assertEqual(result.skipped_content_type, 1)

    def test_content_type_policy_accepts_html_and_rejects_non_html(self):
        """Content-type policy should keep crawl parsing focused on HTML."""

        self.assertTrue(is_crawl_content_type('text/html; charset=utf-8'))
        self.assertTrue(is_crawl_content_type('application/xhtml+xml'))
        self.assertTrue(is_crawl_content_type(None, b'<!doctype html><a href="/admin">'))
        self.assertFalse(is_crawl_content_type('application/json'))
        self.assertFalse(is_crawl_content_type(None, b'{"url":"/admin"}'))

    def test_handles_empty_or_missing_body_without_storing_content(self):
        """Extractor should safely handle empty HTML responses and missing bodies."""

        empty = extract_crawl_candidates('https://example.com/', None, 'text/html')

        self.assertEqual(empty.candidates, ())
        self.assertEqual(empty.discovered, 0)

        html_like = extract_crawl_candidates('https://example.com/', '<html><a href="/admin"></a>', None)

        self.assertEqual([candidate.url for candidate in html_like.candidates], ['https://example.com/admin'])

    def test_content_type_policy_handles_string_fallback_and_missing_body(self):
        """Content-type fallback should accept HTML-like strings and reject empty bodies."""

        self.assertFalse(is_crawl_content_type(None, None))
        self.assertTrue(is_crawl_content_type(None, '  <html><a href="/admin"></a>'))
        self.assertTrue(is_crawl_content_type(None, '  <a href="/admin"></a>'))
        self.assertFalse(is_crawl_content_type(None, '  {"url":"/admin"}'))

    def test_skips_invalid_origin_and_malformed_port_inputs(self):
        """Normalizer should reject invalid source/target origins without raising."""

        cases = [
            ('/admin', 'https://example.com:bad/'),
            ('ftp://example.com/admin', 'https://example.com/'),
            ('/admin', 'ftp://example.com/'),
            ('https://user@example.com/admin', 'https://example.com/'),
        ]

        for raw_url, source_url in cases:
            with self.subTest(raw_url=raw_url, source_url=source_url):
                normalized, reason = normalize_crawl_url(raw_url, source_url)

                self.assertIsNone(normalized)
                self.assertEqual(reason, 'invalid')

    def test_preserves_non_default_ports_and_ipv6_hosts(self):
        """Normalizer should keep non-default ports and render IPv6 netlocs safely."""

        normalized, reason = normalize_crawl_url('/admin', 'https://example.com:8443/root')

        self.assertIsNone(reason)
        self.assertEqual(normalized, 'https://example.com:8443/admin')

        normalized, reason = normalize_crawl_url('/admin', 'https://[2001:db8::1]/root')

        self.assertIsNone(reason)
        self.assertEqual(normalized, 'https://[2001:db8::1]/admin')

    def test_ignored_extension_policy_handles_empty_config_and_paths_without_dots(self):
        """Ignore-extension handling should avoid false skips for empty config/path values."""

        normalized, reason = normalize_crawl_url('/admin', 'https://example.com/', ignore_extensions=[])

        self.assertIsNone(reason)
        self.assertEqual(normalized, 'https://example.com/admin')

        normalized, reason = normalize_crawl_url('/admin', 'https://example.com/', ignore_extensions=['', 'js'])

        self.assertIsNone(reason)
        self.assertEqual(normalized, 'https://example.com/admin')

        normalized, reason = normalize_crawl_url('/assets/app.JS', 'https://example.com/', ignore_extensions=['js'])

        self.assertIsNone(normalized)
        self.assertEqual(reason, 'extension')

    def test_parser_private_append_guard_handles_missing_urls_and_manual_limit(self):
        """Parser append guard should ignore missing values and count manual overflow safely."""

        parser = _CrawlHTMLParser(max_links=1)
        parser._append_link('a', 'href', None)
        parser._append_link('a', 'href', '/one')
        parser._append_link('a', 'href', '/two')

        self.assertEqual(parser.links, [('a', 'href', '/one')])
        self.assertEqual(parser.skipped_limit, 1)


class CrawlStateTestCase(unittest.TestCase):
    """Crawl runtime state tests."""

    def test_reserve_deduplicates_and_enforces_scan_limit(self):
        """CrawlState should reserve unique URLs before queue integration."""

        state = CrawlState(max_enqueued=2)

        self.assertEqual(state.reserve('https://example.com/one'), 'queued')
        self.assertEqual(state.reserve('https://example.com/one'), 'duplicate')
        self.assertEqual(state.reserve('https://example.com/two'), 'queued')
        self.assertEqual(state.reserve('https://example.com/three'), 'limit')
        self.assertEqual(state.enqueued, 2)
        self.assertEqual(state.duplicates, 1)
        self.assertEqual(state.skipped_limit, 1)
        self.assertEqual(state.skipped, 1)

    def test_close_releases_runtime_state(self):
        """CrawlState.close should release memory and reset counters."""

        state = CrawlState(max_enqueued=1)
        state.reserve('https://example.com/one')
        state.reserve('https://example.com/one')
        state.reserve('https://example.com/two')

        state.close()

        self.assertEqual(state.enqueued, 0)
        self.assertEqual(state.duplicates, 0)
        self.assertEqual(state.skipped_limit, 0)
        self.assertEqual(state.skipped, 0)
        self.assertEqual(state.reserve('https://example.com/one'), 'queued')

    def test_records_extraction_result_for_runtime_diagnostics(self):
        """CrawlState should aggregate extraction counters for diagnostics without storing bodies."""

        state = CrawlState(max_enqueued=10)

        state.record_extraction_result(CrawlExtractionResult(
            candidates=(),
            skipped_invalid=1,
            skipped_external=2,
            skipped_extension=3,
            skipped_duplicate=4,
            skipped_limit=5,
        ))

        self.assertEqual(state.duplicates, 4)
        self.assertEqual(state.skipped, 11)
        self.assertEqual(state.diagnostics_payload(), {
            'queued': 0,
            'processed': 0,
            'discovered': 0,
            'consumed': 0,
            'pending': 0,
            'duplicate': 4,
            'skipped': 11,
        })


    def test_records_optional_results_and_duplicate_skips(self):
        """CrawlState should aggregate optional results and direct duplicate skips."""

        state = CrawlState(max_enqueued=10)
        state.record_extraction_result(None)
        state.skip_duplicate()
        state.record_extraction_result(CrawlExtractionResult(
            candidates=(),
            skipped_invalid=1,
            skipped_external=2,
            skipped_extension=3,
            skipped_duplicate=4,
            skipped_limit=5,
        ))

        self.assertEqual(state.duplicates, 5)
        self.assertEqual(state.skipped, 11)
        self.assertEqual(state.diagnostics_payload(), {
            'queued': 0,
            'processed': 0,
            'discovered': 0,
            'consumed': 0,
            'pending': 0,
            'duplicate': 5,
            'skipped': 11,
        })


    def test_crawl_state_records_processed_requests_and_close_resets(self):
        """CrawlState should track processed crawl-owned requests and clear them on close."""

        state = CrawlState(max_enqueued=10)

        self.assertEqual(1, state.record_processed())
        self.assertEqual(2, state.record_processed())
        self.assertEqual(2, state.processed)

        state.close()

        self.assertEqual(0, state.processed)
