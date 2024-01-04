import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .config import COLUMNS_1, is_number
from .base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class InvalidCSVTestCase(BaseSmartCSVTestCase):
    def test_invalid_header_fails_creating_the_reader(self):
        """Should fail to create the reader if the header is invalid"""
        # Missing category header column
        csv_data = """
title,subcategory,currency,price,url,image_url
iPhone 5c blue,Phones,Smartphones,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg
"""
        self.assertRaises(InvalidCSVHeaderException, lambda: smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1))

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

    def test_required_fields_fail_if_no_value_is_provided(self):
        """Should fail if a required field is missing"""
        # Category data is missing (and it's required)
        csv_data = """
title,category,subcategory,currency,price,url,image_url
iPhone 5c blue,,Smartphones,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg
"""
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('category' in e.errors)

    def test_fail_if_choices_doesnt_match(self):
        """Should fail if the provided value is not contained in the model choices"""
        csv_data = """
title,category,subcategory,currency,price,url,image_url
iPhone 5c blue,Phones,Smartphones,INVALID,699,http://apple.com/iphone,http://apple.com/iphone.jpg
        """
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('currency' in e.errors)

    def test_fail_if_validator_doesnt_validate(self):
        """Should fail if the custom validator doesn't pass"""

        # Preconditions. test if `is_number` works as expected
        self.assertTrue(is_number(699))
        self.assertTrue(is_number("699"))
        self.assertTrue(is_number(699.23))
        self.assertTrue(is_number("699.23"))
        self.assertFalse(is_number("ABC"))

        csv_data = """
title,category,subcategory,currency,price,url,image_url
iPhone 5c blue,Phones,Smartphones,USD,INVALID,http://apple.com/iphone,http://apple.com/iphone.jpg
        """
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('price' in e.errors)

    def test_invalid_validator_in_columns_argument(self):
        columns = COLUMNS_1[:]
        image_url_column = columns.pop(-1).copy()
        image_url_column['validator'] = 3  # Not a callable. Invalid
        columns.append(image_url_column)

        csv_data = """
title,category,subcategory,currency,price,url,image_url
iPhone 5c blue,Phones,Smartphones,USD,399,http://apple.com/iphone,http://apple.com/iphone.jpg
        """
        reader = smartcsv.reader(StringIO(csv_data), columns=columns)

        self.assertRaises(AttributeError, lambda: list(next(reader)))
