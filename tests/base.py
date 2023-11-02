import unittest


class BaseSmartCSVTestCase(unittest.TestCase):
    def assertModelsEquals(self, model1, model2):
        for k, v in model1.items():
            self.assertEqual(v, model2[k])