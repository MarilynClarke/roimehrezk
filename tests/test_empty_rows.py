import csv
import six

if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .base import BaseSmartCSVTestCase
from .config import (
    COLUMNS_1, IPHONE_DATA, IPAD_DATA, VALID_TEMPLATE_STR, EMPTY_DATA
)

import smartcsv
from smartcsv.exceptions import InvalidCSVException


class ReaderWithEmtpyRowsTestCase(BaseSmartCSVTestCase):
    def setUp(self):
        self.csv_data = """
title,category,subcategory,currency,price,url,image_url
{iphone_data}
{ipad_data}""".format(
            iphone_data=VALID_TEMPLATE_STR.format(**IPHONE_DATA),
            ipad_data=VALID_TEMPLATE_STR.format(**IPAD_DATA)
        )
        self.csv_data_with_empty_rows = """
title,category,subcategory,currency,price,url,image_url
{empty_data}
{empty_data}
{empty_data}
{iphone_data}
{empty_data}
{empty_data}
{ipad_data}
{empty_data}
{empty_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**IPHONE_DATA),
            ipad_data=VALID_TEMPLATE_STR.format(**IPAD_DATA),
            empty_data=VALID_TEMPLATE_STR.format(**EMPTY_DATA),
        )

    def test_csv_with_empty_rows_and_flag_enabled(self):
        """Should be valid and return the proper objects"""
        reader = smartcsv.reader(StringIO(self.csv_data_with_empty_rows),
                                 columns=COLUMNS_1, allow_empty_rows=True)
        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, IPHONE_DATA)
        self.assertModelsEquals(ipad, IPAD_DATA)

    def test_csv_with_empty_rows_and_flag_disabled(self):
        """Should fail if empty rows are not allowed"""
        reader = smartcsv.reader(StringIO(self.csv_data_with_empty_rows),
                                 columns=COLUMNS_1, allow_empty_rows=False)

        self.assertRaises(InvalidCSVException, lambda: reader.next())

    def test_csv_with_empty_rows_and_flag_omited(self):
        """Should fail because the flag should be false by default"""
        reader = smartcsv.reader(StringIO(self.csv_data_with_empty_rows),
                                 columns=COLUMNS_1)

        self.assertRaises(InvalidCSVException, lambda: reader.next())

    def test_csv_without_empty_rows_and_flag_enabled(self):
        """Shouldn't fail and return the proper objects"""
        csv_data_without_empty_rows = """
title,category,subcategory,currency,price,url,image_url
{iphone_data}
{ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**IPHONE_DATA),
            ipad_data=VALID_TEMPLATE_STR.format(**IPAD_DATA)
        )
        reader = smartcsv.reader(StringIO(csv_data_without_empty_rows),
                                 columns=COLUMNS_1, allow_empty_rows=True)

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, IPHONE_DATA)
        self.assertModelsEquals(ipad, IPAD_DATA)
