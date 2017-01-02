"""Filter class test"""

import unittest

from Libraries import Filter;


class TestFilter(unittest.TestCase):
    """ Filter test"""

    def test_threads(self):
        ''' filter threads test '''

        threads = Filter.threads(0)

        if isinstance(threads, (int, float)):
            self.assertGreater(threads, 0)
        try:
            float(threads)
        except ValueError:
            return False
        else:
            return True

    def test_check(self):
        ''' filter check test '''

        check = Filter.check('unknown')
        self.assertEqual(check, 'directories')

    def test_sheme(self):
        ''' filter sheme test '''

        url = Filter.scheme('test.com')
        self.assertRegexpMatches(url, r'^http')

    def test_port(self):
        ''' filter port test '''

        port = Filter.port(8080)
        self.assertEqual(port, 8080)

    def test_debug(self):
        ''' filter debug test '''

        debug = Filter.debug(1)
        self.assertEqual(debug, 1)

    def test_delay(self):
        ''' filter delay test '''

        delay = Filter.delay(1)
        self.assertEqual(delay, 1)


if __name__ == "__main__":
    unittest.main()
