import unittest
from Libraries import Controller;

class ControllerTest(unittest.TestCase):

    @unittest.skip("update_action")
    def test_update_action(self):
        Controller.update_action();
        pass

    @unittest.skip("update_action")
    def test_version_action(self):
        Controller.version_action()
        pass

    @unittest.skip("url_action")
    def test_url_action(self):
        Controller.url_action(None)
        pass

    @unittest.skip("examples_action")
    def test_examples_action(self):
        Controller.examples_action()
        pass