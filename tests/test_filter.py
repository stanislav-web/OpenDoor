import unittest
from Libraries import Filter;

class TestFilter(unittest.TestCase):
    """ Filter test"""

    @staticmethod
    def __isNumeric(val):

        if isinstance(val, (int, float)):
            return True
        try:
            float(val)
        except ValueError:
            return False
        else:
            return True

    def test_threads(self):
        threads = Filter.threads(0)
        self.assertTrue(self.__isNumeric(threads));
        self.assertGreater(threads, 0)

    def test_check(self):
        check = Filter.check('unknown')
        self.assertEqual(check, 'directories')

    def test_debug(self):
        debug = Filter.debug(1)
        self.assertEqual(debug, 1)

    def test_delay(self):
        delay = Filter.delay(1)
        self.assertEqual(delay, 1)

if __name__ == "__main__":
    unittest.main()