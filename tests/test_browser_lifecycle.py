import unittest
import unittest.mock
from src.lib.browser.browser import Browser
from src.core import helper

class TestBrowserLifecycle(unittest.TestCase):
    def setUp(self):
        self.params = {
            'host': 'localhost',
            'port': 80,
            'scheme': 'http',
            'threads': 1,
            'wordlist': 'data/directories.dat',
            'scan': 'directories',
            'reports': [],
        }

    def test_scan_done_result_survives_close_lifecycle(self):
        # We need to mock enough of Browser to make scan() run without real work
        with unittest.mock.patch('src.lib.browser.browser.Browser._Browser__start_request_provider'), \
             unittest.mock.patch('src.lib.browser.browser.Browser._Browser__ensure_session_runtime_state'), \
             unittest.mock.patch('src.lib.browser.browser.Browser._Browser__verify_active_scan_list_size'), \
             unittest.mock.patch('src.lib.browser.browser.ThreadPool') as mock_pool:

            # Setup mock pool
            pool_instance = mock_pool.return_value
            pool_instance.is_started = True
            pool_instance.total_items_size = 10
            pool_instance.workers_size = 1
            pool_instance.size = 1

            brows = Browser(self.params)

            # Simulate some results before scan finishes (scan calls close() in finally)
            brows._Browser__result['report_items']['found'].append('finding1')

            # Browser.scan() calls close() in finally
            brows.scan()

            # After scan(), close() was called, but result should survive
            brows.done()
            result = brows.result

            self.assertIsInstance(result, dict)
            self.assertIn('report_items', result)
            self.assertEqual(len(result['report_items']['found']), 1)
            self.assertEqual(result['report_items']['found'][0], 'finding1')

            # Verify diagnostics from pool are still there
            self.assertEqual(result['total']['items'], 10)

    def test_close_does_not_destroy_result_before_done(self):
        brows = Browser.__new__(Browser)
        report_items = helper.list()
        report_items['found'].append('finding')
        brows._Browser__result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': report_items,
            'filtered_items': [],
        }
        # In actual Browser, these are initialized in __init__
        brows._Browser__seen_scan_urls = set(['url'])

        brows.close()

        # Result should still be accessible via property
        result = brows.result
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result['report_items']['found']), 1)

        # Internal cache should NOT be cleared by close() anymore, but by release_runtime_state()
        self.assertEqual(len(brows._Browser__seen_scan_urls), 1)

    def test_release_runtime_state_clears_caches(self):
        brows = Browser.__new__(Browser)
        brows._Browser__seen_scan_urls = set(['url1', 'url2'])
        brows._Browser__transient_request_keys = set(['key1'])
        brows._Browser__report_item_keys = {'key': 'val'}
        brows._Browser__request_state_lock = unittest.mock.MagicMock()

        brows.release_runtime_state()

        self.assertEqual(len(brows._Browser__seen_scan_urls), 0)
        self.assertEqual(len(brows._Browser__transient_request_keys), 0)
        self.assertEqual(len(brows._Browser__report_item_keys), 0)
        # Ensure lock was used
        brows._Browser__request_state_lock.__enter__.assert_called_once()

    def test_close_keeps_result_created_by_catch_report_data(self):
        """
        Browser.close() should not remove report data created by the normal report path.
        """
        brows = Browser.__new__(Browser)
        mock_pool = unittest.mock.MagicMock()
        mock_pool.total_items_size = 10
        brows._Browser__pool = mock_pool
        brows._Browser__result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
            'filtered_items': [],
        }
        # Mocking __ensure_report_dedup_state to avoid full init
        brows._Browser__report_item_keys = {}
        brows._Browser__catch_report_data('success', 'http://example.com/admin', '10B', '200')
        brows.close()
        brows.done()
        result = brows.result
        self.assertEqual(result['total']['success'], 1)
        self.assertEqual(result['items']['success'], ['http://example.com/admin'])
        self.assertEqual(result['report_items']['success'][0]['url'], 'http://example.com/admin')

    def test_done_uses_pool_counters_after_scan_close(self):
        """
        Browser.done() should still read pool counters after Browser.scan() closes resources.
        """
        brows = Browser.__new__(Browser)
        mock_pool = unittest.mock.MagicMock()
        mock_pool.total_items_size = 123
        mock_pool.workers_size = 5
        mock_pool.size = 10
        brows._Browser__pool = mock_pool
        brows._Browser__result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
            'filtered_items': [],
        }
        # In a real scenario, pool.close() is called in Browser.close()
        brows.close()
        mock_pool.close.assert_called_once()

        brows.done()
        self.assertEqual(brows.result['total']['items'], 123)

    def test_crawl_state_survives_close_for_diagnostics(self):
        """
        crawl_state should not be closed in close(), but in release_runtime_state().
        """
        brows = Browser.__new__(Browser)
        mock_pool = unittest.mock.MagicMock()
        mock_pool.total_items_size = 0
        mock_pool.size = 0 # Ensure report path is taken in done()
        brows._Browser__pool = mock_pool
        brows._Browser__config = unittest.mock.MagicMock()
        brows._Browser__config.reports = []
        # Mock __is_scan_debug_enabled to True to trigger __emit_runtime_diagnostics
        brows._Browser__is_scan_debug_enabled = unittest.mock.MagicMock(return_value=True)
        # Mock __emit_runtime_diagnostics and related to avoid real output
        brows._Browser__finish_filtered_progress_line = unittest.mock.MagicMock()
        brows._Browser__format_runtime_diagnostics = unittest.mock.MagicMock()

        mock_crawl = unittest.mock.MagicMock()
        mock_crawl.diagnostics_payload.return_value = {'stats': 'ok'}
        brows._Browser__crawl_state = mock_crawl
        brows._Browser__result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
            'filtered_items': [],
        }

        brows.close()
        mock_crawl.close.assert_not_called()

        brows.done()
        # verify that __runtime_diagnostics_payload was called and used crawl_state
        # In actual Browser, done() calls __emit_runtime_diagnostics -> __format_runtime_diagnostics -> __runtime_diagnostics_payload
        # But wait, done() DOES NOT put 'crawl' into self.__result. It only uses it for diagnostics.
        # So test should verify that diagnostics payload HAS it.

        payload = brows._Browser__runtime_diagnostics_payload()
        self.assertEqual(payload['crawl'], {'stats': 'ok'})

        brows.release_runtime_state()
        mock_crawl.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
