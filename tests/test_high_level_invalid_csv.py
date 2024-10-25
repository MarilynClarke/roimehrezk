import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .config import COLUMNS_1, is_number
from .base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class HighLevelInvalidCSVTestCase(BaseSmartCSVTestCase):
    def test_invalid_header_fails_creating_the_reader(self):
        """Should fail to create the reader if the header is invalid"""
        # Missing category header column
        csv_data = """
title,subcategory,currency,price,url,image_url
iPhone 5c blue,Phones,Smartphones,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg
"""
        self.assertRaises(InvalidCSVHeaderException, lambda: smartcsv.reader(
            StringIO(csv_data), columns=COLUMNS_1))

    def test_if_number_of_fields_is_invalid(self):
        """Should fail if the number of fields provided by the CSV is invalid"""
        # Missing category field
        csv_data = """
title,category,subcategory,currency,price,url,image_url
iPhone 5c blue,Smartphones,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg
        """
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('row_length' in e.errors)
