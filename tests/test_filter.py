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

if __name__ == "__main__":
    unittest.main()