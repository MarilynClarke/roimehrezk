import unittest


class BaseSmartCSVTestCase(unittest.TestCase):
    def assertModelsEquals(self, model1, model2):
        for k, v in model1.items():
            self.assertEqual(v, model2[k])

    def assertRowError(self, errors, data_row, index, error_type):
        error_row = errors['rows'][index]
        self.assertEqual(error_row['row'], data_row.split(','))
        self.assertTrue(error_type in error_row['errors'], error_row['errors'])