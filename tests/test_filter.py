"""Filter class test"""

import unittest
from Libraries import Filter;

class TestFilter(unittest.TestCase):
    """ Filter test"""

    @staticmethod
    def isNumeric(val):
        ''' check for numbers '''

        if isinstance(val, (int, float)):
            return True
        try:
            float(val)
        except ValueError:
            return False
        else:
            return True

    def test_threads(self):
        ''' filter threads test '''

        threads = Filter.threads(0)
        self.assertTrue(self.isNumeric(threads));
        self.assertGreater(threads, 0)

    def test_check(self):
        ''' filter check test '''

        check = Filter.check('unknown')
        self.assertEqual(check, 'directories')

    def test_debug(self):
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
