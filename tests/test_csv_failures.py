import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .config import COLUMNS_1
from .base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException

ROW0 = "iPhone 5c blue,Smartphones,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg"
ROW1 = "iPhone 5c green,,Smartphones,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg"
ROW2 = "iPhone 5c red,Phones,Smartphones,INVALID,699,http://apple.com/iphone,http://apple.com/iphone.jpg"
ROW3 = "iPhone 5c white,Phones,Smartphones,USD,699,apple.com/iphone,http://apple.com/iphone.jpg"
ROW4 = "iPad mini,Tablets,Apple,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg"


class CSVModelReaderFailingCountTestCase(BaseSmartCSVTestCase):
    def setUp(self):
        # Several failures:
        # * Missing field
        #  * Category is missing
        #  * Invalid choice
        #  * Validator doesn't pass
        #  * Last column is ok
        csv_data = """
                title,category,subcategory,currency,price,url,image_url
{r0}
{r1}
{r2}
{r3}
{r4}
"""
        self.csv_data = csv_data.format(
            r0=ROW0, r1=ROW1, r2=ROW2, r3=ROW3, r4=ROW4)

    def test_fail_fast_disabled_and_max_failures_in_none(self):
        """Shouldn't fail if there are many fails but fail_fast is False and max_failures is deactivated (None)"""
        reader = smartcsv.reader(StringIO(self.csv_data), columns=COLUMNS_1,
                                 max_failures=None, fail_fast=False)
        ipad = next(reader)
        self.assertEqual(ipad['title'], 'iPad mini')

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)

        self.assertEqual(len(reader.errors['rows']), 4)

        self.assertRowError(reader.errors, ROW0, 0, 'row_length')
        self.assertRowError(reader.errors, ROW1, 1, 'category')
        self.assertRowError(reader.errors, ROW2, 2, 'currency')
        self.assertRowError(reader.errors, ROW3, 3, 'url')

    def test_fail_fast_is_disabled_and_max_failures_is_not_reached(self):
        """Shouldn't fail if the number of failures doesn't reach max_failures"""
        reader = smartcsv.reader(StringIO(self.csv_data), columns=COLUMNS_1,
                                 max_failures=5, fail_fast=False)

        ipad = next(reader)
        self.assertEqual(ipad['title'], 'iPad mini')

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)

        self.assertEqual(len(reader.errors['rows']), 4)

        self.assertRowError(reader.errors, ROW0, 0, 'row_length')
        self.assertRowError(reader.errors, ROW1, 1, 'category')
        self.assertRowError(reader.errors, ROW2, 2, 'currency')
        self.assertRowError(reader.errors, ROW3, 3, 'url')

    def test_fail_fast_is_disabled_and_max_failures_is_reached(self):
        """Should fail if max_failures number is reached"""
        reader = smartcsv.reader(StringIO(self.csv_data), columns=COLUMNS_1,
                                 max_failures=3, fail_fast=False)

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)

            self.assertTrue('currency' in e.errors)
            self.assertTrue('rows' in reader.errors)

        self.assertEqual(len(reader.errors['rows']), 2)

        self.assertRowError(reader.errors, ROW0, 0, 'row_length')
        self.assertRowError(reader.errors, ROW1, 1, 'category')