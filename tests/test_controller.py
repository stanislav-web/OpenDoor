"""Controller class test"""

import unittest
from Libraries import Controller;

class TestController(unittest.TestCase):
    """ Controller test"""

    @unittest.skip("update_action")
    def test_update_action(self):
        ''' update action test '''

        Controller.update_action();
        pass

    @unittest.skip("update_action")
    def test_version_action(self):
        ''' version action test '''

        Controller.version_action()
        pass

    @unittest.skip("url_action")
    def test_url_action(self):
        ''' url action test '''

        Controller.url_action(None)
        pass

    @unittest.skip("examples_action")
    def test_examples_action(self):
        ''' examples action test '''

        Controller.examples_action()
        pass

if __name__ == "__main__":
    unittest.main()
